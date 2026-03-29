# Product Requirements Document: Kyoo Integration via Broadcast System

**Document Version:** 3.0  
**Date:** February 16, 2026  
**Owner:** PMG Technical Team  
**Status:** URGENT - Deploy Today

**v3.0 Changes:**
- Template name: `kyoo_appt_confirmation_id` (recreated due to accidental deletion of original)
- Router hardcodes template name — Kyoo's payload stays unchanged (still sends `kyoo_appt_qr_in`)
- Kyoo only needs to change 2 things: URL and Authorization header
- Removed phone validation from scope

**v2.0 Changes:**
- Security model: Kyoo receives a scoped gateway token, never touches Meta Cloud API credentials
- Auth comparison upgraded to timing-safe (crypto.timingSafeEqual)
- HTTPS via existing chatwoot.pbmcgroup.com infrastructure
- `broadcast_name` passed through for traceability
- Kyoo partner instructions updated to explain why they get a different token

---

## Executive Summary

**Timeline:** Deploy today  
**Scope:** Add one endpoint to message router that translates Kyoo's existing WATI payload to our broadcast system format.

**Current:** Kyoo → WATI → WhatsApp  
**New:** Kyoo → Our Router (chatwoot.pbmcgroup.com) → Broadcast System → WhatsApp + Chatwoot

### Security Model Change

Previously, Kyoo held the WATI API key — effectively a direct pass-through to WhatsApp Cloud API. If that token leaked, anyone could send any template to any number through our WhatsApp Business Account.

Now, Kyoo receives a **scoped gateway token** that can only be used to submit appointment payloads to our router. Our broadcast system holds the Meta Cloud API credentials internally. Kyoo never sees or needs them.

**Blast radius if Kyoo's token leaks:** Someone could send appointment confirmation messages through our system. Bad, but recoverable — revoke the token, generate a new one. Nobody gets access to our Meta account, other templates, or Chatwoot.

---

## Part 1: Internal Implementation (Deploy Today)

### Prerequisites (15 minutes)

**1. Generate and Store API Token in AWS Parameter Store** ✅ DONE

```
Parameter Name: /pmg/kyoo/api_token
Type: SecureString
Value: <REDACTED — see AWS Secrets Manager: /pmg/kyoo/api_token>
```

Stored in SSM Parameter Store, verified readable from EC2 instance via `AWS_Cloudwatch_EC2` IAM role with `PMG_SSM_ReadAccess` policy.

This token is a gateway credential scoped to the Kyoo endpoint. It is NOT a WhatsApp API key.

**2. HTTPS Endpoint** ✅ ALREADY IN PLACE

Kyoo will call `https://chatwoot.pbmcgroup.com/api/v1/sendTemplateMessages` — this subdomain already has HTTPS termination and routes to the EC2 router on port 3000.

**3. Verify Meta Template Exists**
- Template name: `kyoo_appt_confirmation_id`
- Status: Must be APPROVED in Meta Business Manager
- If not approved, this blocks deployment
- Note: Original template `kyoo_appt_qr_in` was accidentally deleted. New template uses same structure. Router maps Kyoo's old template name to the new one.
- Template variables:
  - Header (image): `{{image}}` — receives QR code URL
  - Body: `{{1}}` through `{{7}}` — patient_name, appt_code, appt_date, appt_time, appt_type, appt_location, booking_url

**4. Add Template to Broadcast System**
Location: `config/templates.json`

```json
{
  "kyoo_appt_confirmation_id": {
    "meta_template_name": "kyoo_appt_confirmation_id",
    "description": "Kyoo appointment confirmation with QR code (Indonesian)",
    "language_code": "id",
    "variables": {
      "patient_name": {
        "required": true,
        "position": 1,
        "description": "Patient name"
      },
      "appt_code": {
        "required": true,
        "position": 2,
        "description": "Appointment/booking code"
      },
      "appt_date": {
        "required": true,
        "position": 3,
        "description": "Appointment date"
      },
      "appt_time": {
        "required": true,
        "position": 4,
        "description": "Appointment time"
      },
      "appt_type": {
        "required": true,
        "position": 5,
        "description": "Service/appointment type"
      },
      "appt_location": {
        "required": true,
        "position": 6,
        "description": "Clinic location"
      },
      "booking_url": {
        "required": true,
        "position": 7,
        "description": "Kyoo booking status URL"
      }
    },
    "variable_order": ["patient_name", "appt_code", "appt_date", "appt_time", "appt_type", "appt_location", "booking_url"],
    "header": {
      "type": "image",
      "variable": "qr_code"
    }
  }
}
```

---

### Implementation (30 minutes)

**File:** `router/package.json`
```bash
npm install @aws-sdk/client-ssm
```

**File:** `router/router.js` - Add this code:

```javascript
const crypto = require('crypto');
const { SSMClient, GetParameterCommand } = require('@aws-sdk/client-ssm');

// Initialize at top of file
const ssmClient = new SSMClient({ region: process.env.AWS_REGION || 'ap-southeast-1' });
let kyooApiToken = null;

// Template name mapping: Kyoo sends their old name, we use our new one
const KYOO_TEMPLATE_NAME = 'kyoo_appt_confirmation_id';

// Get token from Parameter Store (cached 1 hour)
async function getKyooToken() {
  if (kyooApiToken) return kyooApiToken;
  
  try {
    const cmd = new GetParameterCommand({
      Name: '/pmg/kyoo/api_token',
      WithDecryption: true
    });
    const response = await ssmClient.send(cmd);
    kyooApiToken = response.Parameter.Value;
    setTimeout(() => { kyooApiToken = null; }, 3600000);
    return kyooApiToken;
  } catch (error) {
    console.error('[Kyoo] Failed to fetch token from Parameter Store:', error.message);
    throw new Error('Internal auth configuration error');
  }
}

// Kyoo endpoint - exact path they're already calling
app.post('/api/v1/sendTemplateMessages', async (req, res) => {
  try {
    // 1. Auth check (timing-safe comparison)
    const token = await getKyooToken();
    const provided = Buffer.from(req.headers.authorization || '');
    const expected = Buffer.from(token);
    if (provided.length !== expected.length || !crypto.timingSafeEqual(provided, expected)) {
      return res.status(401).json({ success: false, error: 'AUTH_INVALID' });
    }
    
    // 2. Basic payload structure check
    if (!req.body.receivers || !Array.isArray(req.body.receivers) || req.body.receivers.length === 0) {
      return res.status(400).json({ success: false, error: 'VALIDATION_ERROR: receivers array is required' });
    }
    
    // 3. Transform payload: Kyoo format → Broadcast format
    const recipients = req.body.receivers.map(receiver => ({
      phoneNumber: receiver.whatsappNumber,
      variables: receiver.customParams.reduce((vars, param) => {
        vars[param.name] = param.value;
        return vars;
      }, {})
    }));
    
    // 4. Trigger broadcast
    //    Hardcode our template name — Kyoo still sends their old name (kyoo_appt_qr_in)
    //    which no longer exists in Meta. We map it to the new template on our side.
    const result = await triggerBroadcast({
      templateName: KYOO_TEMPLATE_NAME,
      broadcastName: req.body.broadcast_name || req.body.template_name,
      recipients: recipients
    });
    
    // 5. Success response
    res.json({
      success: true,
      broadcastId: result.id,
      recipientCount: recipients.length
    });
    
    console.log(`[Kyoo] Broadcast triggered: ${result.id} | recipients: ${recipients.length} | template: ${KYOO_TEMPLATE_NAME} | broadcast: ${req.body.broadcast_name || 'unnamed'}`);
    
  } catch (error) {
    console.error('[Kyoo] Error:', error);
    res.status(500).json({ 
      success: false, 
      error: 'INTERNAL_ERROR' 
    });
  }
});
```

**What this endpoint does:**
- Validates auth token from Parameter Store (timing-safe comparison)
- Validates basic payload structure (receivers array present)
- Transforms Kyoo's payload to broadcast format
- Hardcodes template name to `kyoo_appt_confirmation_id` (Kyoo's payload is unchanged)
- Passes `broadcast_name` through for log traceability
- Calls your existing `triggerBroadcast()` function
- Returns structured error codes on failure
- Never exposes internal error details to the caller

---

### Testing (10 minutes)

**Quick smoke test (simulating Kyoo's exact payload):**
```bash
curl -X POST https://chatwoot.pbmcgroup.com/api/v1/sendTemplateMessages \
  -H "Authorization: <REDACTED — see AWS Secrets Manager: /pmg/kyoo/api_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "broadcast_name": "kyoo_appt_qr_in",
    "template_name": "kyoo_appt_qr_in",
    "receivers": [{
      "whatsappNumber": "6281234567890",
      "customParams": [
        {"name": "patient_name", "value": "Test User"},
        {"name": "appt_code", "value": "TEST123"},
        {"name": "appt_date", "value": "2026-02-20"},
        {"name": "appt_time", "value": "10:00 - 11:00"},
        {"name": "appt_type", "value": "Checkup"},
        {"name": "appt_location", "value": "Test Clinic"},
        {"name": "booking_url", "value": "https://kyoo.id/test"},
        {"name": "qr_code", "value": "https://kyoo.id/qr/test.png"}
      ]
    }]
  }'
```

Note: The payload sends `kyoo_appt_qr_in` as template_name (Kyoo's old value). The router ignores this and uses `kyoo_appt_confirmation_id` internally.

**Expected results:**
- Valid payload: 200 OK, message appears in WhatsApp, logged in Chatwoot
- Wrong token: 401 with `AUTH_INVALID`
- Missing receivers: 400 with `VALIDATION_ERROR`

---

### Deployment Checklist

- [x] API token generated and stored in AWS Parameter Store (`/pmg/kyoo/api_token`)
- [x] HTTPS endpoint confirmed (`chatwoot.pbmcgroup.com`)
- [ ] Template `kyoo_appt_confirmation_id` APPROVED in Meta Business Manager
- [ ] Template added to broadcast config (`config/templates.json`)
- [ ] Code deployed to production
- [ ] Smoke test passes (valid payload → message delivered)
- [ ] Auth test passes (wrong token → 401 error)
- [ ] Share credentials with Kyoo team

**Total time:** ~1 hour

---

## Part 2: Kyoo Partner Instructions

### Important: New Security Model

Previously you were sending your WATI API key (which was effectively a WhatsApp Cloud API credential) with every request. That meant your system held direct access to our WhatsApp Business Account.

**This is no longer the case.**

The token we provide you is a **gateway credential** that authenticates your system to our messaging platform. It is NOT a WhatsApp API key. It can only be used to submit appointment messages through this specific endpoint.

- Do not reuse your old WATI credentials — they will not work
- Do not share this token with other services or partners
- If you suspect the token has been compromised, notify us immediately so we can rotate it

---

### What You Need to Change

You're already sending the right payload format. Only **2 things** change:

#### 1. Change the URL
**Old:** `https://wati-api-url.com/api/v1/sendTemplateMessages`  
**New:** `https://chatwoot.pbmcgroup.com/api/v1/sendTemplateMessages`

#### 2. Change the Authorization Header
**Old:** Your WATI token  
**New:** `<REDACTED — see AWS Secrets Manager: /pmg/kyoo/api_token>`

Send the token directly in the Authorization header (same format as WATI — no `Bearer` prefix).

#### 3. That's It
Your payload format stays **exactly the same**. No changes to `template_name`, `broadcast_name`, field names, or structure.

---

### Your Current Payload (Keep This — No Changes)

```json
{
  "broadcast_name": "kyoo_appt_qr_in",
  "template_name": "kyoo_appt_qr_in",
  "receivers": [
    {
      "whatsappNumber": "6281234567890",
      "customParams": [
        {"name": "patient_name", "value": "Budi Santoso"},
        {"name": "appt_date", "value": "2026-02-20"},
        {"name": "appt_time", "value": "10:00 - 11:00"},
        {"name": "appt_type", "value": "General Checkup"},
        {"name": "appt_location", "value": "Jl. Sudirman No. 10, Jakarta"},
        {"name": "booking_url", "value": "https://kyoo.id/customer/93/appointment-onsite/booking-status/123"},
        {"name": "appt_code", "value": "KY123ABC"},
        {"name": "qr_code", "value": "https://kyoo.id/storage/qrcode123.png"}
      ]
    }
  ]
}
```

**Don't change anything else.** Same structure, same field names, same template_name, same everything. We handle the template mapping on our side.

---

### Success Response

```json
{
  "success": true,
  "broadcastId": "bc_20260220_abc123",
  "recipientCount": 1
}
```

### Error Responses

**401 — Authentication failed:**
```json
{
  "success": false,
  "error": "AUTH_INVALID"
}
```
Fix: Check your Authorization header contains the exact token we provided.

**400 — Bad payload:**
```json
{
  "success": false,
  "error": "VALIDATION_ERROR: receivers array is required"
}
```
Fix: Check payload structure. Do not retry — fix the payload first.

**500 — Server error:**
```json
{
  "success": false,
  "error": "INTERNAL_ERROR"
}
```
Fix: Retry after 1 second. If persistent, contact us.

---

### Migration Steps (Today)

1. **Update your code:**
   - URL: `https://chatwoot.pbmcgroup.com/api/v1/sendTemplateMessages`
   - Authorization: `<REDACTED — see AWS Secrets Manager: /pmg/kyoo/api_token>`
2. **Deploy to your staging**
3. **Send one test message** (we'll verify it arrives)
4. **Deploy to production**
5. **Done** ✅

**Fallback:** Keep your WATI credentials handy for 24 hours just in case.

---

### Quick Test

After you deploy, send us one test message. We'll confirm:
- Message arrives in WhatsApp ✓
- All 7 text fields display correctly ✓
- QR code image shows ✓
- Logged in our system ✓

---

## Appendix A: Post-Launch Improvements (Later)

These are **nice to have** but not required for go-live today. We'll add them incrementally:

### Validation (Future Enhancement)

1. **Required Fields Validation**
   - Verify all 8 customParams are present before triggering broadcast
   - Return 400 with list of missing fields

2. **Date Format Validation**
   - `appt_date`: YYYY-MM-DD (e.g., `2026-02-20`)
   - `appt_time`: HH:MM - HH:MM (e.g., `10:00 - 11:00`)

3. **URL Validation**
   - `booking_url` and `qr_code` must be valid URLs
   - Should start with `https://`
   - QR code should be publicly accessible PNG/JPG

4. **Template Name Enforcement**
   - Currently hardcoded to single template
   - Future: support multiple templates with whitelist

5. **Idempotency**
   - Deduplicate on `appt_code` to prevent duplicate messages if Kyoo retries
   - Important for healthcare context — duplicate appointment messages confuse patients

### Security Enhancements (Future)

**Token Management:**
- Store token in environment variables or secrets manager (on Kyoo's side)
- Never commit to Git
- Rotate token quarterly (we'll notify you 30 days ahead)

**IP Allowlisting:**
- Future: restrict endpoint to Kyoo's known IP ranges
- Adds coordination overhead, so deferred for now

**Retry Logic (Kyoo-side recommendation):**
- Retry 5xx errors (server errors) — wait 1s, 5s, 30s between attempts
- Don't retry 4xx errors (client errors) — fix your payload instead
- Max 3 retry attempts

**Rate Limiting:**
- Current: No limit
- Future: 100 requests/minute per token
- Contact us if you need higher limits

**Error Handling (Recommended for Kyoo):**
```javascript
// Recommended (but not required today)
try {
  const response = await sendToOurAPI(payload);
  if (response.success) {
    return response;
  }
} catch (error) {
  // Log for manual review
  logError(error, payload);
  
  // Retry only 5xx errors
  if (error.status >= 500) {
    await retry(payload);
  }
  // Do NOT retry 4xx — fix payload instead
}
```

---

### Monitoring Recommendations (Future)

**What to Log:**
- Request timestamp
- Appointment code (for tracking)
- Response status
- Error messages (if any)
- Retry attempts

**What NOT to Log:**
- Full API token (only last 4 chars)
- Patient names
- Full phone numbers

**Alerts to Set Up:**
- Error rate > 10% for 5 minutes
- No successful requests for 1 hour (during business hours)
- API returns 401 (token issue — contact us)

---

### Advanced Features (Roadmap)

**Delivery Status Webhooks** (Q2 2026)
- We'll call your webhook when message is delivered/read/failed
- You can track end-to-end delivery

**Batch Optimization** (Q2 2026)
- Send multiple appointments in one request
- Faster processing for morning appointment batches

**Custom Templates** (Q3 2026)
- Support for additional appointment types
- Reminder messages
- Cancellation confirmations

---

## Appendix B: Technical Reference

### Template Name Mapping

| Kyoo Sends | Router Uses | Why |
|------------|-------------|-----|
| `kyoo_appt_qr_in` | `kyoo_appt_confirmation_id` | Original template was accidentally deleted in Meta. New template has same structure. Router maps automatically — Kyoo doesn't need to change anything. |

### Error Codes

| Code | Status | Meaning | Action |
|------|--------|---------|--------|
| `AUTH_INVALID` | 401 | Wrong or missing token | Check Authorization header matches the token we provided |
| `VALIDATION_ERROR` | 400 | Bad payload | Check payload structure — do not retry |
| `INTERNAL_ERROR` | 500 | Server issue | Retry with backoff (1s, 5s, 30s) or contact us |

### QR Code Requirements

- Format: PNG or JPEG
- Max size: 500KB (recommended)
- Dimensions: 500x500 to 1000x1000 pixels
- Must be publicly accessible HTTPS URL
- Valid for at least 30 days

---

## Document Approval

**Target Go-Live:** Today (February 16, 2026)

| Role | Name | Status |
|------|------|--------|
| Technical Lead | | ☐ Approved |
| Kyoo Contact | | ☐ Approved |

---

**Questions?** Contact us immediately — we need to deploy today.

**End of Document**
