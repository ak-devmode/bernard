# Chatwoot Migration Plan: app.chatwoot.com to Self-Hosted

**Version:** 1.1
**Date:** 11 March 2026
**Author:** Dev team + Claude
**Go-live target:** Tuesday 18 March 2026

---

## Contact Migration — What Was Actually Built & Tested

### Source Files
| File | Inbox | Total | Usable |
|------|-------|-------|--------|
| `CC_Contacts.csv` | Crew Care | 1,059 | 1,013 (46 skipped — corrupted phones) |
| `CS_Contacts.csv` | Clinics + Padma Care | 27,931 | 27,930 |
| **Total** | | **28,990** | **28,943** |

**Note on corrupted phones in CC file:** 46 CC contacts have phone numbers in scientific
notation (e.g., `6.28224E+12`) — caused by someone opening the CSV in Excel which truncated
the digits. These cannot be recovered and are skipped.

### Import Flow

```
 CC_Contacts.csv  ─┐
                    ├──→  prepare_contacts.py  ──→  data/contacts_import.json  ──→  import_contacts.js  ──→  POST /api/v1/accounts/{id}/contacts  ──→  Chatwoot DB
 CS_Contacts.csv  ─┘
       │                         │                           │                             │                              │                                    │
  WATI backup              cleans phones,             28,943 contacts              sends one contact              Chatwoot API creates               contact visible
  (2 accounts)             merges files,              ready to import              per request, 60ms              contact in DB one                  in dashboard +
                           strips WATI cols,                                       delay between each             at a time — no                     searchable by
                           rebuilds +62 phone                                                                     bulk import bug                    CS team
```

**Step 1 — `migration/prepare_contacts.py`**
- Reads both WATI CSV files
- Skips rows with corrupted/empty phones
- Reconstructs full E.164 phone: `+` + `CountryCode` + `Phone` → e.g., `+6282237572636`
- Keeps name as-is (phone-as-name contacts retained intentionally)
- Strips WATI-internal columns (AllowCampaign, ContactStatus, etc.)
- Maps remaining columns to `custom_attributes`
- Tags each contact with `_source: cc` or `_source: cs` (used for inbox assignment, stripped before API call)
- Output: `migration/data/contacts_import.json` (28,943 contacts)

**Step 2 — `migration/import_contacts.js`**
- Reads `contacts_import.json`
- For each contact, calls `POST /api/v1/accounts/{id}/contacts` with:
  ```json
  {
    "name": "I Gede Dharma Putra",
    "phone_number": "+6282237572636",
    "custom_attributes": { "day_part": "sore", "salutation_id": "bapak" }
  }
  ```
- One contact per API request, 60ms delay between each (~16 req/sec)
- Duplicates (HTTP 422) are logged and skipped — no crash
- Progress logged every 100 contacts
- Errors written to `data/import_errors.json`

**Usage:**
```bash
# Test: first 100 contacts on local dev
node import_contacts.js --url http://localhost:3000 --token TOKEN --account 1 --limit 100

# Full run on staging
node import_contacts.js --url https://staging-chat.pbmcgroup.com --token TOKEN --account ACCOUNT_ID

# Resume from offset (if interrupted)
node import_contacts.js --url URL --token TOKEN --account ID --offset 5000
```

### Test Results (11 March 2026)
- **Environment:** Local dev (`localhost:3000`)
- **Batch:** First 100 contacts
- **Result:** 100/100 ✅ — zero failures, zero mismatches
- **Speed:** ~5 contacts/sec (20 seconds for 100)
- **Full run estimate:** ~95 minutes for all 28,943 contacts

### Why Not the Built-in CSV Import?
The Chatwoot CSV import (Settings → Contacts → Import) uses `activerecord-import` with
`synchronize + on_duplicate_key_ignore` which causes the name/phone mismatch bug (see Part 1).
The API-based approach creates contacts one at a time — the bug never applies.

---

---

## Part 1: Diagnosis -- Contact Import Root Cause

### 1.1 How the CSV Import Pipeline Works

The import flow is:

1. **Controller** (`contacts_controller.rb#import`): Receives a CSV file upload, creates a `DataImport` record, attaches the file via ActiveStorage.
2. **DataImport model** (`data_import.rb`): `after_create_commit` triggers `DataImportJob.set(wait: 1.minute).perform_later(self)`.
3. **DataImportJob** (`data_import_job.rb`): Reads the CSV, builds Contact objects via `DataImport::ContactManager`, then bulk-inserts via `activerecord-import`.
4. **ContactManager** (`data_import/contact_manager.rb`): For each CSV row, calls `find_or_initialize_contact` which looks up existing contacts by identifier, email, or phone_number (in that order). If found, it merges attributes. If not found, it initializes a new Contact.
5. **Bulk insert** (line 55 of `data_import_job.rb`):
   ```ruby
   Contact.import(contacts, synchronize: contacts, on_duplicate_key_ignore: true,
                  track_validation_failures: true, validate: true, batch_size: 1000)
   ```

### 1.2 Root Cause Analysis: Name/Phone Mismatch

**The bug is in the `synchronize` option combined with `on_duplicate_key_ignore`.**

Here is the critical sequence:

1. `parse_csv_and_build_contacts` iterates through all CSV rows and builds an in-memory array of Contact objects. For new contacts (no match by identifier/email/phone), these are **unsaved** objects with `id = nil`.

2. `Contact.import(contacts, synchronize: contacts, on_duplicate_key_ignore: true, batch_size: 1000)` does the following:
   - Splits the contacts array into batches of 1000.
   - For each batch, generates a bulk `INSERT` SQL statement.
   - `on_duplicate_key_ignore: true` means if a uniqueness constraint is violated (e.g., duplicate email or identifier), that row is **silently skipped** -- no error, no insertion.
   - `synchronize: contacts` means after the INSERT, the gem reads back the inserted IDs and assigns them to the in-memory objects **by array position**.

3. **HERE IS THE BUG**: When `on_duplicate_key_ignore` skips some rows, the database returns fewer IDs than were submitted. The `synchronize` step maps IDs back to the in-memory objects **positionally** -- the first returned ID goes to the first object, the second returned ID goes to the second object, etc. But if row 3 was skipped due to a duplicate, the database returns IDs for rows 1, 2, 4, 5... and `synchronize` assigns them as if they were rows 1, 2, 3, 4... **This causes a shift -- every contact after the first skipped duplicate gets the wrong ID assigned.**

4. **Why slicing made it worse**: When the 40k CSV was split into ~15 files and imported sequentially:
   - The first slice may import fine (no duplicates yet).
   - Starting from the second slice, any phone numbers or emails that appeared in a previous slice trigger `on_duplicate_key_ignore`, causing the positional shift described above.
   - Each subsequent slice has more potential duplicates (from prior slices), creating cascading mismatches.
   - The `update_contact_with_merged_attributes` in `find_existing_contact` also saves matched contacts inline (line 56: `contact.save`), meaning some contacts get updated during the build phase, creating a mix of pre-saved and unsaved objects in the array passed to `Contact.import`.

5. **Additional risk factor**: The `ContactManager#find_existing_contact` method does lookups by identifier, then email, then phone_number. If a CSV has contacts where the same email appears with different phone numbers (or vice versa), the lookup can match the wrong existing contact, and then `update_contact_with_merged_attributes` overwrites its phone/email with the new row's values.

### 1.3 Conclusion

| Factor | Contributes to Bug? | Severity |
|--------|---------------------|----------|
| `synchronize` + `on_duplicate_key_ignore` positional ID mismatch | **YES -- PRIMARY CAUSE** | Critical |
| Slicing into multiple files creates cross-file duplicates | **YES -- AMPLIFIER** | High |
| `find_existing_contact` inline `.save` during build phase | YES -- causes mixed saved/unsaved state | Medium |
| `batch_size: 1000` within a single import | Low risk if no duplicates within a single batch | Low |

### 1.4 Recommendation

**Do NOT use the built-in CSV import for the migration.** Instead, use the Chatwoot REST API to create contacts one-by-one (or in controlled small batches). This avoids the `activerecord-import` synchronize bug entirely.

---

## Part 2: Conversation Migration Plan

### 3.1 Export Conversations from app.chatwoot.com

The Chatwoot API returns conversations with pagination (default 25 per page).

**Step 1: Export all conversations**

```bash
# migration/export_conversations.sh
SOURCE_URL="https://app.chatwoot.com"
SOURCE_TOKEN="YOUR_API_TOKEN"
ACCOUNT_ID="152163"

PAGE=1
while true; do
  RESPONSE=$(curl -s -H "api_access_token: ${SOURCE_TOKEN}" \
    "${SOURCE_URL}/api/v1/accounts/${ACCOUNT_ID}/conversations?page=${PAGE}")

  COUNT=$(echo "$RESPONSE" | jq '.data.meta.all_count // 0')
  PAYLOAD_COUNT=$(echo "$RESPONSE" | jq '.data.payload | length')

  if [ "$PAYLOAD_COUNT" -eq 0 ]; then
    break
  fi

  echo "$RESPONSE" | jq -c '.data.payload[]' >> conversations_export.jsonl
  echo "Page ${PAGE}: ${PAYLOAD_COUNT} conversations (total: ${COUNT})"
  PAGE=$((PAGE + 1))
  sleep 0.1
done
```

**Step 2: For each conversation, export its messages**

```bash
# migration/export_messages.sh
SOURCE_URL="https://app.chatwoot.com"
SOURCE_TOKEN="YOUR_API_TOKEN"
ACCOUNT_ID="152163"

# Read conversation IDs from export
cat conversations_export.jsonl | jq -r '.id' | while read CONV_ID; do
  # Conversations API returns messages with the conversation, but we need full message history
  # Use the messages endpoint with pagination
  AFTER=0
  while true; do
    RESPONSE=$(curl -s -H "api_access_token: ${SOURCE_TOKEN}" \
      "${SOURCE_URL}/api/v1/accounts/${ACCOUNT_ID}/conversations/${CONV_ID}/messages?after=${AFTER}")

    PAYLOAD_COUNT=$(echo "$RESPONSE" | jq '.payload | length')
    if [ "$PAYLOAD_COUNT" -eq 0 ]; then
      break
    fi

    # Save messages with conversation ID
    echo "$RESPONSE" | jq -c --arg cid "$CONV_ID" '{conversation_id: $cid, messages: .payload}' \
      >> messages_export.jsonl

    # Get the last message ID for pagination
    AFTER=$(echo "$RESPONSE" | jq '.payload[-1].id')
    sleep 0.05
  done

  echo "Exported messages for conversation ${CONV_ID}"
  sleep 0.05
done
```

### 3.2 Map Contacts by Phone Number

The phone-to-ID mapping from the contact import step (`phone_to_id_map.json`) is used to associate conversations with the correct contact on the target instance.

```javascript
// migration/build_contact_map.js
const fs = require('fs');

// Load source conversations
const convLines = fs.readFileSync('conversations_export.jsonl', 'utf8')
  .split('\n').filter(Boolean);
const conversations = convLines.map(l => JSON.parse(l));

// Load target contact mapping
const TARGET_URL = 'http://localhost:3000';
const TARGET_TOKEN = 'YOUR_TOKEN';
const ACCOUNT_ID = 'YOUR_ACCOUNT_ID';

async function buildMap() {
  const phoneToTargetContact = new Map();

  // For each conversation, get the source contact phone
  for (const conv of conversations) {
    const phone = conv.meta?.sender?.phone_number;
    if (!phone || phoneToTargetContact.has(phone)) continue;

    // Look up in target
    const response = await fetch(
      `${TARGET_URL}/api/v1/accounts/${ACCOUNT_ID}/contacts/search?q=${encodeURIComponent(phone)}`,
      { headers: { 'api_access_token': TARGET_TOKEN } }
    );
    const data = await response.json();
    const match = data.payload?.find(c => c.phone_number === phone);

    if (match) {
      phoneToTargetContact.set(phone, {
        targetContactId: match.id,
        targetContactInboxId: match.contact_inboxes?.[0]?.id || null
      });
    }

    await new Promise(r => setTimeout(r, 50));
  }

  fs.writeFileSync('contact_phone_map.json',
    JSON.stringify(Object.fromEntries(phoneToTargetContact), null, 2));
  console.log(`Mapped ${phoneToTargetContact.size} contacts`);
}

buildMap();
```

### 3.3 Replay Conversations and Messages via API

```javascript
// migration/import_conversations.js
const fs = require('fs');

const TARGET_URL = 'http://localhost:3000';
const TARGET_TOKEN = 'YOUR_TOKEN';
const ACCOUNT_ID = 'YOUR_ACCOUNT_ID';
const INBOX_ID = 'YOUR_INBOX_ID';
const DELAY_MS = 100;

const contactMap = JSON.parse(fs.readFileSync('contact_phone_map.json', 'utf8'));
const convLines = fs.readFileSync('conversations_export.jsonl', 'utf8')
  .split('\n').filter(Boolean);
const conversations = convLines.map(l => JSON.parse(l));
const msgLines = fs.readFileSync('messages_export.jsonl', 'utf8')
  .split('\n').filter(Boolean);
const messageGroups = msgLines.map(l => JSON.parse(l));

// Status mapping: Chatwoot uses 0=open, 1=resolved, 2=pending, 3=snoozed
const STATUS_MAP = { open: 'open', resolved: 'resolved', pending: 'pending', snoozed: 'snoozed' };

async function importConversation(conv) {
  const phone = conv.meta?.sender?.phone_number;
  const mapping = contactMap[phone];

  if (!mapping) {
    return { error: `No target contact for phone ${phone}`, sourceId: conv.id };
  }

  // Create conversation
  const createResponse = await fetch(
    `${TARGET_URL}/api/v1/accounts/${ACCOUNT_ID}/conversations`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'api_access_token': TARGET_TOKEN
      },
      body: JSON.stringify({
        contact_id: mapping.targetContactId,
        inbox_id: INBOX_ID,
        status: STATUS_MAP[conv.status] || 'resolved',
        additional_attributes: conv.additional_attributes || {},
        custom_attributes: conv.custom_attributes || {}
      })
    }
  );

  if (!createResponse.ok) {
    return { error: await createResponse.text(), sourceId: conv.id };
  }

  const newConv = await createResponse.json();
  const targetConvId = newConv.id;

  // Import messages for this conversation
  const convMessages = messageGroups
    .filter(mg => mg.conversation_id == conv.id)
    .flatMap(mg => mg.messages)
    .sort((a, b) => new Date(a.created_at) - new Date(b.created_at));

  for (const msg of convMessages) {
    // message_type: 0=incoming, 1=outgoing, 2=activity
    // Skip activity messages (status changes, etc.)
    if (msg.message_type === 2) continue;

    await fetch(
      `${TARGET_URL}/api/v1/accounts/${ACCOUNT_ID}/conversations/${targetConvId}/messages`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'api_access_token': TARGET_TOKEN
        },
        body: JSON.stringify({
          content: msg.content || '[attachment - not migrated]',
          message_type: msg.message_type === 0 ? 'incoming' : 'outgoing',
          private: msg.private || false,
          content_type: msg.content_type === 0 ? 'text' : 'text',
          content_attributes: msg.content_attributes || {}
        })
      }
    );

    await new Promise(r => setTimeout(r, 20));
  }

  // Update conversation status to match source (creation defaults to open)
  if (conv.status !== 'open') {
    await fetch(
      `${TARGET_URL}/api/v1/accounts/${ACCOUNT_ID}/conversations/${targetConvId}/toggle_status`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'api_access_token': TARGET_TOKEN
        },
        body: JSON.stringify({ status: conv.status })
      }
    );
  }

  return { success: true, sourceId: conv.id, targetId: targetConvId, messageCount: convMessages.length };
}

async function main() {
  const results = { success: 0, failed: 0, errors: [], convMap: [] };

  for (let i = 0; i < conversations.length; i++) {
    const result = await importConversation(conversations[i]);

    if (result.success) {
      results.success++;
      results.convMap.push(result);
    } else {
      results.failed++;
      results.errors.push(result);
    }

    if (i % 50 === 0) {
      console.log(`Progress: ${i}/${conversations.length} (ok: ${results.success}, fail: ${results.failed})`);
    }

    await new Promise(r => setTimeout(r, DELAY_MS));
  }

  console.log(`\nConversation import complete:`);
  console.log(`  Success: ${results.success}`);
  console.log(`  Failed: ${results.failed}`);

  fs.writeFileSync('conversation_map.json', JSON.stringify(results.convMap, null, 2));
  fs.writeFileSync('conversation_errors.json', JSON.stringify(results.errors, null, 2));
}

main();
```

### 3.4 Edge Cases

| Edge Case | Handling |
|-----------|----------|
| Contact not found on target | Log to `conversation_errors.json`, skip conversation. Investigate after import. |
| Inbox mismatch (contact linked to different inbox on source) | Use the primary WhatsApp inbox ID. If multiple inboxes exist, match by inbox name. |
| Attachments (images, files, audio) | Replace with placeholder text `[attachment - not migrated]`. Accepted trade-off per PRD. |
| Empty messages (attachment-only) | Create with placeholder text. |
| Message timestamps | The API does not allow setting `created_at` on messages. Messages will have import-time timestamps. **This is an accepted limitation of API-based migration.** |
| Rate limiting (429 responses) | Implement exponential backoff: wait 1s, 2s, 4s, then fail. |

### 3.5 Rate Limiting Strategy

- **Contact export**: 10 requests/second (100ms delay) -- conservative
- **Contact import**: 20 requests/second (50ms delay)
- **Conversation export**: 10 requests/second
- **Message import**: 50 requests/second (20ms delay) -- messages are lightweight
- If any request returns HTTP 429, back off exponentially (1s, 2s, 4s, 8s) then resume

---

## Part 4: Canned Responses Migration

### 4.1 Export from Source

```bash
curl -s -H "api_access_token: ${SOURCE_TOKEN}" \
  "${SOURCE_URL}/api/v1/accounts/${ACCOUNT_ID}/canned_responses" \
  | jq '.' > canned_responses_export.json
```

### 4.2 Import to Target

```bash
# migration/import_canned_responses.sh
TARGET_URL="http://localhost:3000"
TARGET_TOKEN="YOUR_TOKEN"
ACCOUNT_ID="YOUR_ACCOUNT_ID"

cat canned_responses_export.json | jq -c '.[]' | while read CR; do
  SHORT_CODE=$(echo "$CR" | jq -r '.short_code')
  CONTENT=$(echo "$CR" | jq -r '.content')

  curl -s -X POST \
    -H "api_access_token: ${TARGET_TOKEN}" \
    -H "Content-Type: application/json" \
    "${TARGET_URL}/api/v1/accounts/${ACCOUNT_ID}/canned_responses" \
    -d "{\"short_code\": \"${SHORT_CODE}\", \"content\": $(echo "$CR" | jq '.content')}"

  echo "Imported: /${SHORT_CODE}"
  sleep 0.1
done
```

---

## Part 5: Labels Migration

### 5.1 Export and Import

```bash
# Export labels
curl -s -H "api_access_token: ${SOURCE_TOKEN}" \
  "${SOURCE_URL}/api/v1/accounts/${ACCOUNT_ID}/labels" \
  | jq '.' > labels_export.json

# Import labels
cat labels_export.json | jq -c '.payload[]' | while read LABEL; do
  TITLE=$(echo "$LABEL" | jq -r '.title')
  DESCRIPTION=$(echo "$LABEL" | jq -r '.description // ""')
  COLOR=$(echo "$LABEL" | jq -r '.color // "#1f93ff"')
  SHOW=$(echo "$LABEL" | jq -r '.show_on_sidebar // false')

  curl -s -X POST \
    -H "api_access_token: ${TARGET_TOKEN}" \
    -H "Content-Type: application/json" \
    "${TARGET_URL}/api/v1/accounts/${ACCOUNT_ID}/labels" \
    -d "{\"title\": \"${TITLE}\", \"description\": \"${DESCRIPTION}\", \"color\": \"${COLOR}\", \"show_on_sidebar\": ${SHOW}}"

  echo "Imported label: ${TITLE}"
done
```

---

## Part 6: Testing & Validation Checklist

### 6.1 Pre-Migration Tests (on local dev, localhost:3000)

- [ ] **Test 1**: Import 10 contacts via API script. Verify all 10 have correct name, phone, email, custom_attributes.
- [ ] **Test 2**: Import 100 contacts via API script. Run verification script. Confirm 100% match rate.
- [ ] **Test 3**: Import 100 contacts that include 5 intentional duplicates (same phone). Confirm duplicates are handled gracefully (error logged, not imported twice, no name shifts).
- [ ] **Test 4**: Run contact_inbox association script. Verify all 100 contacts have a `contact_inbox` record linked to the test WhatsApp inbox.
- [ ] **Test 5**: Create 5 test conversations with messages via the import script. Verify:
  - Conversations appear in the Chatwoot dashboard
  - Messages are in correct order
  - Contact association is correct
  - Status (open/resolved) is correct

### 6.2 Validation Checks After Full Import

| Check | Method | Pass Criteria |
|-------|--------|---------------|
| Contact count | Compare source export count vs target `GET /api/v1/accounts/{id}/contacts?page=1` total_count | Within 1% (some may be filtered as invalid) |
| Name-phone match | Run `verify_contacts.js` on 500 random samples | >= 99% match rate |
| Custom attributes | Spot-check 20 contacts in dashboard | All custom attributes present |
| contact_inbox links | Rails console: `ContactInbox.where(inbox_id: INBOX_ID).count` | Matches number of contacts with phone numbers |
| Conversation count | Compare source vs target conversation count | Within 5% (some may fail due to missing contacts) |
| Message count | Spot-check 10 conversations, compare message counts | Match (excluding attachment-only messages) |
| Canned responses | List all on target dashboard | All present with correct content |
| Labels | List all on target dashboard | All present |

### 6.3 Go/No-Go Criteria

**GO** if all of the following are true:
1. Contact name-phone match rate >= 99%
2. All custom attributes are present on sampled contacts
3. contact_inbox associations created for all contacts with phone numbers
4. Conversation import success rate >= 95%
5. Canned responses all imported
6. CS team can log in to staging and see their contacts and conversations

**NO-GO** if any of the following are true:
- Name-phone match rate < 99%
- contact_inbox associations broken (contacts not visible in inbox)
- Conversation import success rate < 80%
- Any data corruption detected

**Fallback**: If conversation import fails or is too lossy, proceed with contacts-only migration. Keep app.chatwoot.com as the conversation archive until 10 April (per PRD fallback strategy).

---

## Part 7: Execution Timeline

### Week 1: 11-14 March (Preparation & Local Testing)

**Tuesday 11 March**
- [ ] Create `migration/` directory in project root
- [ ] Write all migration scripts (export, import, verify, contact_inbox)
- [ ] Confirm API token scope on app.chatwoot.com (OPEN QUESTION #1 from PRD)
- [ ] Test API token: `curl -H "api_access_token: TOKEN" https://app.chatwoot.com/api/v1/accounts/ACCOUNT_ID/contacts?page=1`
- [ ] Confirm account ID on app.chatwoot.com

**Wednesday 12 March**
- [ ] Run full contact export from app.chatwoot.com (~40k contacts, ~45 min)
- [ ] Run validation script on exported data
- [ ] Clean data (fix phone formats, remove true duplicates)
- [ ] Test import of 100 contacts on local dev (localhost:3000)
- [ ] Run verification script on local dev
- [ ] Test contact_inbox association script on local dev
- [ ] Begin conversation export from app.chatwoot.com (may take several hours)

**Thursday 13 March**
- [ ] Complete conversation + message export
- [ ] Test conversation import on local dev (50 conversations)
- [ ] Import canned responses and labels on local dev
- [ ] Run full validation checklist on local dev
- [ ] Fix any issues found
- [ ] **Decision point**: Go/no-go for staging import

**Friday 14 March (CS Team UAT)**
- [ ] Run full contact import on staging (~40k, ~33 min)
- [ ] Run verification on staging (500 random samples)
- [ ] Run contact_inbox associations on staging
- [ ] Run conversation import on staging
- [ ] Import canned responses and labels on staging
- [ ] Run full validation checklist on staging
- [ ] CS team UAT begins: verify they can see contacts and conversations
- [ ] Document any issues found during UAT

### Week 2: 15-18 March (Stabilization & Go-Live)

**Saturday-Sunday 15-16 March**
- [ ] Fix any issues from UAT
- [ ] Re-run any failed imports if needed

**Monday 17 March**
- [ ] Final delta sync: export any new contacts/conversations created on app.chatwoot.com since Friday
- [ ] Import delta into staging
- [ ] Final verification pass
- [ ] Confirm go-live readiness

**Tuesday 18 March (Go-Live)**
- [ ] Morning: Final delta sync (contacts + conversations from Monday)
- [ ] DNS cutover: `chat.pbmcgroup.com` points to self-hosted ALB
- [ ] Router points exclusively to self-hosted instance
- [ ] CS team begins using self-hosted instance
- [ ] Monitor for issues throughout the day
- [ ] app.chatwoot.com remains accessible as archive

---

## Appendix A: Open Questions Requiring Answers Before Execution

| # | Question | Owner | Needed By | Impact if Unanswered |
|---|----------|-------|-----------|---------------------|
| 1 | **API token scope on app.chatwoot.com**: Does the admin token have access to export all contacts and conversations via API? Test with a single paginated request. | @Alex | 11 March | Cannot export data at all |
| 2 | **Account ID on app.chatwoot.com**: Confirm it is `152163`. | @Alex | 11 March | Wrong data exported |
| 3 | **Account ID on self-hosted staging**: What is the account ID? | @Okto | 11 March | Import scripts need this |
| 4 | **Inbox IDs on self-hosted staging**: What are the WhatsApp inbox IDs for Padma Clinics, Padma Care, Crew Care? | @Okto | 12 March | contact_inbox script needs this |
| 5 | **Rate limits on app.chatwoot.com API**: Is there a hard rate limit? Test with 100 rapid requests. | @Dev | 11 March | May need to slow down export |
| 6 | **Delta sync strategy**: How to handle contacts/conversations created between initial migration and cutover? Re-export and merge, or accept the gap? | @Alex | 17 March | Data freshness at cutover |

## Appendix B: File Manifest

All scripts should be placed in `D:/2 - Padma/7 - Chatwoot/migration/`:

```
migration/
  export_contacts.sh          # Export contacts from app.chatwoot.com
  validate_contacts.js        # Validate and clean exported contacts
  import_contacts.js          # Import contacts via API to target
  verify_contacts.js          # Post-import verification
  contact_inbox.rb            # Rails console script for contact_inbox associations
  export_conversations.sh     # Export conversations from app.chatwoot.com
  export_messages.sh          # Export messages per conversation
  build_contact_map.js        # Map source phones to target contact IDs
  import_conversations.js     # Import conversations + messages to target
  import_canned_responses.sh  # Import canned responses
  import_labels.sh            # Import labels
  data/                       # Output directory for all export/import data
    contacts_export.jsonl
    contacts_clean.json
    phone_to_id_map.json
    import_errors.json
    verify_mismatches.json
    conversations_export.jsonl
    messages_export.jsonl
    contact_phone_map.json
    conversation_map.json
    conversation_errors.json
    canned_responses_export.json
    labels_export.json
```

## Appendix C: Key Chatwoot Code Files Referenced

| File | Path | Relevance |
|------|------|-----------|
| Contact model | `app/models/contact.rb` | Uniqueness constraints: email+account, identifier+account, phone format validation |
| ContactInbox model | `app/models/contact_inbox.rb` | Unique index on (inbox_id, source_id); source_id format validation per channel |
| DataImportJob | `app/jobs/data_import_job.rb` | **ROOT CAUSE**: `Contact.import()` with `synchronize` + `on_duplicate_key_ignore` causes positional ID mismatch |
| ContactManager | `app/services/data_import/contact_manager.rb` | `find_or_initialize_contact` lookup order: identifier > email > phone |
| ContactInboxBuilder | `app/builders/contact_inbox_builder.rb` | WhatsApp source_id = phone without '+'; handles RecordNotUnique |
| Contacts controller | `app/controllers/api/v1/accounts/contacts_controller.rb` | API endpoints for create, search, import |
