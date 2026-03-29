# Chatwoot Broadcast Message Logging - Feature PRD

**Project:** PMG Broadcast Service  
**Feature:** Log outbound broadcast messages to Chatwoot conversations  
**Priority:** High  
**Status:** To Implement

---

## Problem Statement

Currently, when broadcast messages are sent via Meta Cloud API, they do NOT appear in Chatwoot conversation history. This creates a gap where:
- Agents can't see what broadcasts were sent to a contact
- No record of outbound communication exists in Chatwoot
- Follow-up context is lost

**Why this happens:** Meta Cloud API webhooks only notify about INBOUND messages, not outbound API-sent messages.

---

## Solution

After successfully sending a message via Meta API, programmatically create the message in Chatwoot's conversation history.

### Workflow

```
1. Broadcast sends message via Meta Cloud API
2. Meta confirms delivery (returns message_id)
3. Find or create conversation in Chatwoot for that contact
4. Post the message content to Chatwoot conversation
5. Mark as "outgoing" message from system
```

---

## Technical Requirements

### File to Modify

**Location:** `/var/www/chatwoot-services/broadcast/lib/chatwoot.js`

Add two new methods to `ChatwootService` class:

### Method 1: Get or Create Conversation

```javascript
/**
 * Find existing conversation or create new one for contact
 * @param {number} contactId - Chatwoot contact ID
 * @param {number} inboxId - Chatwoot inbox ID to use
 * @returns {Object} Conversation object with id
 */
async getOrCreateConversation(contactId, inboxId) {
  await this.initialize();
  
  try {
    // Search for existing open conversation with this contact in this inbox
    const response = await this.client.get('/conversations', {
      params: {
        inbox_id: inboxId,
        status: 'open'
      }
    });
    
    const conversations = response.data.payload;
    const existing = conversations.find(c => c.meta?.sender?.id === contactId);
    
    if (existing) {
      this.logger.debug(`Found existing conversation: ${existing.id}`);
      return existing;
    }
    
    // Create new conversation
    const createResponse = await this.client.post('/conversations', {
      contact_id: contactId,
      inbox_id: inboxId
    });
    
    const conversation = createResponse.data;
    this.logger.debug(`Created new conversation: ${conversation.id}`);
    return conversation;
    
  } catch (error) {
    throw new Error(`Failed to get/create conversation: ${error.message}`);
  }
}
```

### Method 2: Send Outbound Message

```javascript
/**
 * Post an outbound message to Chatwoot conversation
 * @param {number} conversationId - Conversation ID
 * @param {string} content - Message content
 * @param {string} messageType - 'outgoing' (default)
 * @returns {Object} Created message object
 */
async sendOutboundMessage(conversationId, content, messageType = 'outgoing') {
  await this.initialize();
  
  try {
    const response = await this.client.post(`/conversations/${conversationId}/messages`, {
      content: content,
      message_type: messageType,
      private: false
    });
    
    const message = response.data;
    this.logger.debug(`Posted message to conversation ${conversationId}`);
    return message;
    
  } catch (error) {
    throw new Error(`Failed to post message: ${error.message}`);
  }
}
```

---

## Inbox Mapping Configuration

### Current Inboxes (from PRD Section 1.4)

| Phone Number | Display Name | Inbox Name | Inbox ID | Business Unit |
|--------------|--------------|------------|----------|---------------|
| +62 813-3939-4907 | Padma Bahtera Medical Centre - B | Clinics CS | ??? | Clinics CS |
| +62 822-6632-3030 | Padma - Managed Care | Padma Care | ??? | Padma Care + Crew Care |
| +62 821-3109-676 | Crew Care - Padma Medical Group | Crew Care | ??? | Crew Care |

**TODO:** Get actual Chatwoot Inbox IDs

### How to Get Inbox IDs

```bash
# Via Chatwoot API
curl -X GET "https://app.chatwoot.com/api/v1/accounts/152163/inboxes" \
  -H "api_access_token: <REDACTED — see AWS Secrets Manager>"
```

Or check Chatwoot UI: Settings → Inboxes → Click inbox → Check URL for ID

### Configuration File

Create: `config/inboxes.json`

```json
{
  "default_inbox_id": 123456,
  "phone_to_inbox": {
    "6281339394907": {
      "inbox_id": 123456,
      "inbox_name": "Clinics CS",
      "phone_number_id": "103690329051884"
    },
    "6282266323030": {
      "inbox_id": 123457,
      "inbox_name": "Padma Care",
      "phone_number_id": "184707274733826"
    },
    "6282131096676": {
      "inbox_id": 123458,
      "inbox_name": "Crew Care",
      "phone_number_id": "104226354229334"
    }
  }
}
```

**Note:** Phone numbers are stored without '+' or leading zeros for matching

---

## Integration Points

### In broadcast.js

**Current code (around line 349):**
```javascript
const result = await meta.sendTemplate({
  phone: recipient.phone,
  templateName: templateConfig.meta_template_name,
  variables: recipient.variables,
  languageCode: templateConfig.language_code || 'id'
});

logger.info(`${progress} ✓ Sent - Message ID: ${result.messageId}`);
results.sent++;
```

**Add after successful send:**
```javascript
const result = await meta.sendTemplate({
  phone: recipient.phone,
  templateName: templateConfig.meta_template_name,
  variables: recipient.variables,
  languageCode: templateConfig.language_code || 'id'
});

logger.info(`${progress} ✓ Sent - Message ID: ${result.messageId}`);

// NEW: Log message to Chatwoot
try {
  const inboxId = await getInboxIdForTemplate(templateConfig);
  const conversation = await chatwoot.getOrCreateConversation(recipient.contactId, inboxId);
  
  // Format message content (reconstruct what was sent)
  const messageContent = formatTemplateMessage(templateConfig, recipient.variables);
  
  await chatwoot.sendOutboundMessage(conversation.id, messageContent);
  logger.debug(`${progress} Logged to Chatwoot conversation ${conversation.id}`);
} catch (error) {
  // Don't fail the broadcast if Chatwoot logging fails
  logger.warn(`${progress} Failed to log to Chatwoot: ${error.message}`);
}

results.sent++;
```

---

## Helper Functions Needed

### 1. Get Inbox ID for Template

```javascript
/**
 * Determine which inbox to use based on template/business unit
 * @param {Object} templateConfig - Template configuration
 * @returns {number} Chatwoot inbox ID
 */
async function getInboxIdForTemplate(templateConfig) {
  // Load inbox mapping
  const configPath = path.join(__dirname, 'config', 'inboxes.json');
  const config = JSON.parse(await fs.readFile(configPath, 'utf8'));
  
  // For now, use template name to determine inbox
  // TODO: Make this more robust (could add inbox_id to template config)
  if (templateConfig.meta_template_name.includes('mcu')) {
    return config.phone_to_inbox['6281339394907'].inbox_id; // Clinics CS
  }
  
  // Default inbox
  return config.default_inbox_id;
}
```

### 2. Format Template Message

```javascript
/**
 * Reconstruct the message content that was sent
 * @param {Object} templateConfig - Template configuration
 * @param {Object} variables - Variable values used
 * @returns {string} Formatted message content
 */
function formatTemplateMessage(templateConfig, variables) {
  // For now, just show what was sent
  // TODO: Could fetch actual template text from Meta or store in config
  const varList = Object.entries(variables)
    .map(([k, v]) => `${k}: ${v}`)
    .join(', ');
  
  return `📤 Broadcast sent: ${templateConfig.meta_template_name}\n\nVariables: ${varList}`;
}
```

**Better approach:** Store template preview text in `config/templates.json`:

```json
{
  "mcustatus_ready_pick_up": {
    "meta_template_name": "mcustatus_ready_pick_up",
    "preview_text": "Selamat {{day_part}} Bapak/Ibu {{name}}, hasil MCU Anda sudah siap...",
    ...
  }
}
```

Then reconstruct by replacing placeholders.

---

## Testing Plan

### Phase 1: Manual Testing

```bash
# 1. Test with dry-run (should NOT post to Chatwoot)
./broadcast.sh --sheet-id=test_sheet --tab="Sheet1" --template=mcustatus_ready_pick_up --dry-run

# 2. Test with limit=1 (SHOULD post to Chatwoot)
./broadcast.sh --sheet-id=test_sheet --tab="Sheet1" --template=mcustatus_ready_pick_up --limit=1

# 3. Check Chatwoot conversation for that contact
# Verify message appears as outgoing

# 4. Send to 2-3 more people, verify all conversations updated
```

### Phase 2: Validation

- [ ] Message appears in correct inbox
- [ ] Message marked as "outgoing"
- [ ] Message content matches what was sent
- [ ] Conversation exists for contact
- [ ] No duplicate conversations created
- [ ] Broadcast still succeeds even if Chatwoot logging fails

---

## Edge Cases to Handle

1. **Chatwoot API fails** - Don't fail the entire broadcast, just log warning
2. **Contact doesn't exist in Chatwoot** - Should already be created by broadcast script
3. **Multiple conversations exist** - Use most recent open conversation
4. **Inbox ID not found** - Fall back to default inbox
5. **Rate limiting** - Chatwoot API may rate limit, handle gracefully

---

## Success Criteria

- ✅ All broadcast messages appear in Chatwoot conversations
- ✅ Messages show correct timestamp (when sent, not when logged)
- ✅ Messages are attributed to system/broadcast (not individual agent)
- ✅ Broadcast performance not significantly impacted
- ✅ Failures in Chatwoot logging don't break broadcasts

---

## Future Enhancements

### Phase 2 (Later)
- Store actual template text and reconstruct exact message content
- Add delivery status updates (delivered/read) via Meta webhooks
- Link to Meta message ID for tracking
- Add custom message attributes (broadcast_id, campaign_name, etc.)
- Batch conversation creation for performance

---

## Questions for Implementation

1. **Which inbox to use?** 
   - Option A: Map template → inbox (mcu templates → Clinics CS)
   - Option B: Add inbox_id to template config
   - Option C: Detect from phone number used (if Meta API tells us which number sent)

2. **Message format in Chatwoot?**
   - Option A: Store template preview text in config, reconstruct exact message
   - Option B: Simple format: "Broadcast: [template_name] with [variables]"
   - Option C: Fetch template from Meta API (complex, slow)

3. **Timing?**
   - Post immediately after Meta confirms? (Current plan)
   - Or batch at end of broadcast? (Faster but less real-time)

4. **Error handling?**
   - Fail entire broadcast if Chatwoot fails? (No - too risky)
   - Log warning and continue? (Yes - recommended)
   - Retry failed logs? (Future enhancement)

---

## Files to Create/Modify

### Create
- `config/inboxes.json` - Inbox mapping configuration

### Modify
- `lib/chatwoot.js` - Add getOrCreateConversation() and sendOutboundMessage()
- `broadcast.js` - Add Chatwoot logging after successful Meta send

### Reference
- PRD: `prd_padma_chatwoot_v3.0.md` - Section 1.4 for phone/inbox mapping

---

**Next Steps:**
1. Get actual Chatwoot inbox IDs
2. Implement two new methods in chatwoot.js
3. Add logging call in broadcast.js after Meta send
4. Test with limit=1
5. Verify in Chatwoot UI
6. Deploy to production

**Estimated Effort:** 2-3 hours implementation + testing
