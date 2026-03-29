# Broadcast Hardening Plan

**Date:** 2026-03-26
**Trigger:** `mcustatus_ready_pick_up` broadcast failed universally 2x on 2026-03-26 09:05 (Padma Clinics inbox, sent by Febri)
**Goal:** Diagnose the failure, then harden the broadcast pipeline with proper error differentiation, structured per-broadcast logging, and phone normalization fixes.

---

## 1. Diagnose the immediate failure — COMPLETE

**Root cause identified:** Parameter count mismatch.

### 1.1 Findings

**Broadcasts #60 (00:48 UTC) and #61 (01:05 UTC):** 19/19 failed, identical error on every recipient.
**Broadcast #63 (01:39 UTC):** 19/19 succeeded — Febri fixed the sheet between attempts.

**Raw Meta API error (from Sidekiq logs):**
```json
{
  "error": {
    "message": "(#132000) Number of parameters does not match the expected number of params",
    "code": 132000,
    "error_data": {
      "details": "body: number of localizable_params (1) does not match the expected number of params (2)"
    }
  }
}
```

### 1.2 Failure chain

1. Google Sheet lacked a `day_part` column
2. `build_processed_params` (broadcast_from_sheet_service.rb:96-105) returned `{'1' => '', '2' => 'Name'}`
3. `process_body_components` (template_processor_service.rb:82) has `next if value.blank?` — **skipped the empty `day_part`**
4. Only 1 body param sent to Meta instead of 2 → Meta rejected with `#132000`
5. `process_response` → `handle_error` logged raw JSON response → returned `nil` (broadcast context, `message.blank?` short-circuit at base_service.rb:53)
6. `send_to` saw `nil` → stored generic Indonesian error message with zero diagnostic value
7. `broadcast_templates.json` defines `"fallback": "pagi"` for `day_part` — but **this fallback is never applied** by `build_processed_params`

### 1.3 Additional issues discovered

- **Deployed error messages are in Indonesian** (not matching local English codebase — deployed code has Indonesian strings)
- **Phone normalization:** Diantari's phone stored as `440121417` — sheet value passed through normalizer as-is (doesn't start with `0` or `8`). Sent as `+440121417` (UK country code, not Indonesian). Also `473640464` appeared similarly malformed.
- **No pre-send validation** — the parameter mismatch could have been caught on the first recipient and failed fast instead of making 19 API calls that all returned the same error

### 1.4 What Febri did to fix it

Added `day_part` values to the sheet between broadcast #61 and #63. Broadcast #63 succeeded 19/19.

---

- [x] 1.1 Query production broadcast records — Done
- [x] 1.2 Check Meta template status — Template approved and working (broadcast #63 succeeded)
- [x] 1.3 Check Rails/Sidekiq logs for raw Meta API error — Found: `#132000` parameter count mismatch
- [x] 1.4 Check phone number issue — Diantari's phone `440121417` stored as-is from sheet (normalizer passthrough)
- [x] 1.5 Determine root cause — Parameter count mismatch due to missing `day_part` column + blank value skipping

---

## 2. Fix root cause + differentiate error types

**Objective:** (a) Apply template fallbacks so missing columns don't cause silent parameter omission. (b) Each failure path gets a unique, English, actionable error message with raw technical detail. No more generic messages.

**Files:**
- `app/services/whatsapp/broadcast_from_sheet_service.rb` (lines 96-152, 234-259)
- `app/services/whatsapp/template_processor_service.rb` (lines 79-93)
- `app/services/whatsapp/providers/base_service.rb` (lines 34-59)
- `config/broadcast_templates.json` (fallback definitions)

### 2.1 Apply template fallbacks for missing/blank variables
- [ ] In `build_processed_params`: after column lookup, check if value is blank and apply fallback from `broadcast_templates.json`
  ```ruby
  def build_processed_params(row)
    mapping = broadcast.template_params['variable_mapping'] || {}
    return {} if mapping.empty?
    row_ci = row.transform_keys { |k| k.to_s.downcase }
    template_config = load_template_config  # from broadcast_templates.json
    mapping.transform_values do |col_name|
      value = row_ci[col_name.to_s.downcase].to_s
      if value.blank? && template_config.dig('variables', col_name, 'fallback').present?
        template_config.dig('variables', col_name, 'fallback')
      else
        value
      end
    end
  end
  ```
- [ ] Add `load_template_config` helper that reads from `broadcast_templates.json` using the template name
- [ ] This directly prevents the #132000 error — missing `day_part` would use fallback `"pagi"`

### 2.2 Fix blank parameter skipping in template processor
- [ ] In `process_body_components` (template_processor_service.rb:82): the `next if value.blank?` line is dangerous — it silently drops parameters, causing count mismatches
- [ ] Change behavior: send empty string as parameter value rather than skipping (Meta accepts empty strings — it rejects missing positions)
- [ ] Alternative: raise an error if a required parameter is blank, so the broadcast fails with a clear message instead of a Meta 132000

### 2.3 Propagate raw Meta error into broadcast context
- [ ] In `base_service.rb` `process_response`: when `message.blank?` (broadcast context), always raise with full Meta error — not just when `error_code` is present
- [ ] Include `error.code`, `error.message`, and `error_data.details` from Meta response
- [ ] This ensures `send_to`'s rescue block always gets the real error, not a nil return

### 2.4 Store technical error alongside human message
- [ ] Change `record_failure` to accept both human message and raw technical detail:
  ```ruby
  def record_failure(recipient, human_error, technical_detail: nil)
    failed << {
      phone: recipient[:phone], name: recipient[:name],
      error: human_error, detail: technical_detail,
      at: Time.current.iso8601
    }
  end
  ```
- [ ] Update all callers of `record_failure` to pass `technical_detail`

### 2.5 Differentiate each error path in `send_to` — all English
- [ ] **Template not found locally** (line 119): `"Template '#{name}' not found in synced templates or not approved. Last sync: #{channel.message_templates_last_updated}."`
- [ ] **Meta API error with code** (rescue path): `"[Meta #{code}] #{meta_message} — #{details}"`
- [ ] **Meta API nil response** (safety): `"Meta API returned empty response — possible network issue or malformed request"`
- [ ] **All error messages in English** — replace deployed Indonesian strings

### 2.6 Improve `human_readable_error` mapping
- [ ] Add missing Meta error codes: `131009` (parameter mismatch), `132000` (template param count), `131031` (account locked), `131056` (pair rate limit)
- [ ] Include the raw error code in every message: `"[Meta 131052] Template is inactive or expired..."`
- [ ] Default: include full error string (not truncated to 120 chars)

---

## 3. Structured per-broadcast logging (broadcast_logs table)

**Objective:** Create a queryable audit trail for each broadcast that captures the full lifecycle — no more grepping Rails logs.

### 3.1 Create `broadcast_logs` migration
- [ ] New table `broadcast_logs`:
  ```ruby
  create_table :broadcast_logs do |t|
    t.references :broadcast, null: false, foreign_key: true, index: true
    t.string :event, null: false       # e.g. 'started', 'sheet_read', 'template_validated',
                                       #      'recipient_sent', 'recipient_failed', 'completed', 'error'
    t.string :phone                    # nullable — only for per-recipient events
    t.string :level, default: 'info'   # 'info', 'warn', 'error'
    t.text :message, null: false       # human-readable log line
    t.jsonb :metadata, default: {}     # structured data (meta_response, template_info, etc.)
    t.datetime :created_at, null: false
  end
  ```
- [ ] Add `has_many :broadcast_logs` to `Broadcast` model

### 3.2 Add logging helper to `BroadcastFromSheetService`
- [ ] Create a `log_event(event, message, level: 'info', phone: nil, metadata: {})` method
- [ ] Writes to both `broadcast_logs` table AND `Rails.logger` (dual-write for transition period)
- [ ] Replace all existing `Rails.logger` calls with `log_event` calls

### 3.3 Instrument the full broadcast lifecycle
- [ ] `started` — broadcast ID, template, inbox, user, total recipients
- [ ] `sheet_read` — sheet_id, tab, row count before/after filter
- [ ] `template_validated` — template name, language, status, parameter_format
- [ ] `recipient_sent` — phone, meta message_id, send duration_ms
- [ ] `recipient_failed` — phone, error, raw Meta response
- [ ] `recipient_skipped` — phone (blank/invalid), reason
- [ ] `contact_synced` / `contact_sync_failed` — phone, created vs updated
- [ ] `conversation_synced` / `conversation_sync_failed` — phone, conversation_id
- [ ] `completed` — sent_count, failed_count, duration_s
- [ ] `error` — exception class, message, backtrace (first 5 lines)

### 3.4 Add API endpoint to query broadcast logs
- [ ] `GET /api/v1/accounts/:account_id/broadcasts/:id/logs`
- [ ] Returns logs ordered by `created_at`, filterable by `level` and `event`
- [ ] **Checkpoint:** Confirm with Alex whether UI display is needed now or logs-via-API is sufficient

---

## 4. Harden the broadcast flow

**Objective:** Fix phone normalization, add pre-send validation, prevent silent failures.

### 4.1 Fix phone normalizer for non-Indonesian numbers
- [ ] Current `PhoneNormalizer` only handles `0xx` → `62xx` and `8xx` → `628xx` — everything else passes through as-is
- [ ] Add validation: if result doesn't look like a valid international number (10-15 digits, starts with country code), log a warning
- [ ] For PMG context (Indonesian healthcare), add a guard: numbers that don't resolve to `62xx` after normalization should be flagged, not silently sent to random country codes
- [ ] Log skipped recipients with reason (currently silently `next`-ed on line 83)

### 4.2 Add pre-send template validation
- [ ] Before the recipient loop, validate the template exists and is approved:
  ```ruby
  template = channel.message_templates.find { |t| t['name'] == template_name && t['status']&.downcase == 'approved' }
  if template.nil?
    broadcast.failed!
    log_event('error', "Template '#{template_name}' not found or not approved — aborting broadcast")
    return
  end
  ```
- [ ] This prevents looping through N recipients only to fail on every single one
- [ ] Log the template details (language, parameter_format, component count) for debugging

### 4.3 Add pre-send dry-run validation for first recipient
- [ ] Before sending to all recipients, do a parameter-build check on the first recipient
- [ ] If `processor.call` returns blank name or nil parameters, fail fast with a clear error
- [ ] Log: `"Pre-send validation failed on first recipient — template parameters could not be built"`

### 4.4 Fix `handle_error` broadcast path in `base_service.rb`
- [ ] Remove the `return if message.blank?` short-circuit (line 53)
- [ ] Instead, when `message.blank?`, raise with full error details so broadcast service always gets the real error
- [ ] Current behavior: Meta returns error → `handle_error` logs raw body → returns nil → broadcast gets generic "Message failed to send" with no detail
- [ ] New behavior: Meta returns error → raise with error code + message → broadcast catches it → stores real error

### 4.5 Add broadcast summary notification
- [ ] After broadcast completes or fails, log a summary event with:
  - Total/sent/failed counts
  - Duration
  - Unique error types encountered (grouped count)
  - Whether it was a systemic failure (>90% fail rate) vs partial
- [ ] **Future consideration:** webhook/Slack notification for systemic failures (flag for later, don't implement now)

---

## Execution order

1. ~~**Phase 1 (diagnose):** Steps 1.1–1.5~~ — **COMPLETE.** Root cause: missing `day_part` column → blank param skipped → Meta 132000.
2. **Phase 2 (root cause fix + error differentiation):** Steps 2.1–2.6 — Apply fallbacks, fix blank param skipping, propagate Meta errors, English-only messages
3. **Phase 3 (audit trail):** Steps 3.1–3.4 — `broadcast_logs` migration + lifecycle instrumentation
4. **Phase 4 (hardening):** Steps 4.1–4.5 — Phone normalizer, pre-send validation, fail-fast on systemic errors

Focus is application-side hardening. Sheet cleanup is separate/later.
Phases 2–4: develop together, test in order (error paths first → logging wraps around them → hardening prevents failures).

---

## Future TODO (not in scope for this plan)

### TODO-1: Fallback config in UI
Currently, template variable fallbacks are defined in `config/broadcast_templates.json` (a static file on the server). The broadcast creation UI in Chatwoot does NOT read or write this file. Future work: add a "Default value" field to the template variable mapping step in `BroadcastForm.vue`, stored in `broadcast.template_params`, so operators can set fallbacks without editing server files.

### TODO-2: Mid-broadcast error popup with cancel/retry
When a systemic error is detected mid-broadcast (e.g., template mismatch causing 100% failure), there is no way for the operator to see or stop it in real-time. Future work: implement real-time broadcast progress via ActionCable (or polling), with a popup that shows the error and offers "Cancel" and "Retry" buttons. This requires:
- ActionCable channel or polling endpoint for broadcast progress
- Frontend component to display live progress and error alerts
- Cancel mechanism to stop the Sidekiq job mid-iteration (e.g., broadcast status check before each send)
- Retry mechanism to re-queue with corrected parameters

### TODO-3: Sidekiq idempotency for broadcast retries
If Sidekiq crashes mid-broadcast and retries the job, all previously-sent recipients will be re-sent (duplicate messages). Future work: track sent phone numbers in a set (Redis or DB) and skip already-sent recipients on retry.
