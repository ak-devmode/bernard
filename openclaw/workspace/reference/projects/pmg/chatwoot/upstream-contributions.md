# Upstream Contributions — Chatwoot OSS

Bugs and issues discovered during PMG customisation work that should be reported
back to the Chatwoot open source project. Each section is a draft bug report
ready to file on github.com/chatwoot/chatwoot/issues.

---

## 1. Status Filter Bug — Resolved Conversations Disappear from All Tab

**Upstream issue:** Not yet filed
**PMG fix:** `ChatList.vue` + `helpers.js` (see PMG-CHANGES.md §1.3)

**Summary:** The "All" tab in the conversation list never shows resolved conversations. `conversationFilters.status` always uses the `activeStatus` ref which defaults to `'open'`, so the API call never requests resolved conversations.

**Steps to reproduce:**
1. Open Chatwoot dashboard
2. Resolve a conversation
3. Switch to the "All" tab
4. The resolved conversation is not visible

**Expected:** All tab should show conversations in all statuses (open, pending, resolved, snoozed).

**Root cause:** `ChatList.vue` line where `conversationFilters` computed property uses `activeStatus` unconditionally. The "All" tab should override this to `status: 'all'`. Additionally, `filterByStatus()` in `helpers.js` doesn't handle array values.

---

## 2. Message Finder Cursor — Wrong Pagination Field

**Upstream issue:** Not yet filed
**PMG fix:** `message_finder.rb` (see PMG-CHANGES.md §2.2)

**Summary:** `MessageFinder#messages_before` uses `id` for cursor-based pagination, but the API consumer expects `created_at`-based ordering. When message IDs and timestamps diverge (e.g., imported messages, bulk operations), messages appear in the wrong order.

**Steps to reproduce:**
1. Have a conversation with messages where `id` order differs from `created_at` order
2. Scroll up to load older messages (triggers `messages_before`)
3. Messages appear out of chronological order

**Fix:** Change cursor field from `id` to `created_at` in the `messages_before` scope.

---

## 3. sass-embedded Compatibility — Build Failure with v1.98+

**Upstream issue:** Not yet filed
**PMG fix:** `package.json` pin (see PMG-CHANGES.md §1.4)

**Summary:** `sass-embedded@1.98+` injects `@use "sass:meta"` into Vue SFC style blocks, breaking `@import 'reset'` in Vite 5. Manifests as `assets:precompile` failure with cryptic Sass error during Docker build.

**Workaround:** Pin `sass-embedded` to `npm:sass@1.79.3`.

**Note:** This may already be fixed upstream or by a Vite upgrade. Check before filing.

---

## 4. Issue #13775 — Comment Draft

**Upstream issue:** https://github.com/chatwoot/chatwoot/issues/13775

Draft comment noting PMG's experience with the same issue and our workaround. Review before posting to ensure it adds value to the discussion.
