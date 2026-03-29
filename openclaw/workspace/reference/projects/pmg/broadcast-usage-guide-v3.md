# PMG WhatsApp Broadcast Service - Usage Guide

**Version:** 3.0  
**Last Updated:** February 14, 2026  
**Server:** 10.10.3.7 (EC2)  
**Location:** `/var/www/chatwoot-services/broadcast/`

**Changelog:**
- **v3.0 (Feb 14, 2026):** Added conditional template filtering, Chatwoot message logging, 3 new pending signature templates, phone number fallback, improved validation
- **v2.0 (Feb 14, 2026):** Sheet name dictionary, auto-header detection, column mapping
- **v1.0 (Feb 13, 2026):** Initial release with basic broadcast functionality

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Daily Operations](#daily-operations)
3. [Available Sheets](#available-sheets)
4. [Available Templates](#available-templates)
5. [Command Reference](#command-reference)
6. [Google Sheet Requirements](#google-sheet-requirements)
7. [Adding New Sheets](#adding-new-sheets)
8. [Adding New Templates](#adding-new-templates)
9. [Troubleshooting](#troubleshooting)
10. [Common Scripts](#common-scripts)

---

## Quick Start

### 1. Connect to Server

```bash
ssh -i '/path/to/your/key.pem' centos@10.10.3.7
```

### 2. Navigate to Broadcast Directory

```bash
cd /var/www/chatwoot-services/broadcast
```

### 3. Run a Test (Dry Run)

```bash
./broadcast.sh \
  --sheet-id=mcu_status \
  --tab="Laporan Serah Terima" \
  --template=mcustatus_ready_pick_up \
  --dry-run
```

**What this does:**
- Fetches data from the MCU Status sheet
- Validates all recipients
- Shows preview of what would be sent
- **Does NOT send any messages** (dry-run mode)

### 4. Send For Real

Remove `--dry-run` to send actual messages:

```bash
./broadcast.sh \
  --sheet-id=mcu_status \
  --tab="Laporan Serah Terima" \
  --template=mcustatus_ready_pick_up
```

You'll be asked to confirm before sending.

---

## Daily Operations

### When to Use Broadcast vs Manual Send

**Use Broadcast System (this tool):**
- 5+ recipients with the same message
- Systematic notifications (MCU results, signatures)
- Need to track who was sent what
- Want message logged in Chatwoot automatically

**Use Manual Send (Chatwoot UI):**
- Less than 5 people
- One-off messages
- Quick replies or follow-ups
- Faster than running a broadcast script

### MCU Ready for Pickup Notification

**When to use:** Daily, when MCU results are ready for patients to collect.

```bash
# 1. Test first (dry-run)
./broadcast.sh \
  --sheet-id=mcu_status \
  --tab="Laporan Serah Terima" \
  --template=mcustatus_ready_pick_up \
  --dry-run

# 2. Review the preview output

# 3. Send for real
./broadcast.sh \
  --sheet-id=mcu_status \
  --tab="Laporan Serah Terima" \
  --template=mcustatus_ready_pick_up
```

### MCU Pending Patient Signature (Conditional Templates)

**When to use:** When MCU certificates need patient signatures - automatically selects the correct template based on MCU type.

**Three different templates based on MCU Name:**
- **Carnival** → Uses simple signature reminder (no appointment needed)
- **Panama** → Uses Panama-specific instructions
- **Viking/NSI/NMA/OGUK** → Uses template with scheduled appointment time

**Run 3 separate broadcasts:**

```bash
# 1. Carnival patients
./broadcast.sh \
  --sheet-id=mcu_status \
  --tab="Patient Sign Broadcast" \
  --template=mcustatus_pending_patient_sign_carnival \
  --filter-column=mcu_name \
  --filter-contains=carnival \
  --dry-run

# 2. Panama patients  
./broadcast.sh \
  --sheet-id=mcu_status \
  --tab="Patient Sign Broadcast" \
  --template=mcustatus_pending_patient_sign_panama \
  --filter-column=mcu_name \
  --filter-contains=panama \
  --dry-run

# 3. Viking/NSI/NMA/OGUK patients (everything else)
./broadcast.sh \
  --sheet-id=mcu_status \
  --tab="Patient Sign Broadcast" \
  --template=mcustatus_pending_patient_sign_viking_nsi_nma_oguk \
  --filter-column=mcu_name \
  --filter-not-contains=carnival,panama \
  --dry-run
```

**Note:** Remove `--dry-run` to send for real.

### Send to Limited Recipients (Testing)

**When to use:** Testing with just 1-2 people before full broadcast.

```bash
# Send to first 2 people only
./broadcast.sh \
  --sheet-id=mcu_status \
  --tab="Laporan Serah Terima" \
  --template=mcustatus_ready_pick_up \
  --limit=2
```

---

## Available Sheets

Current sheets configured in `config/sheets.json`:

| Sheet Name | Description | Common Tabs |
|------------|-------------|-------------|
| `test_sheet` | Testing/development | Sheet1 |
| `mcu_status` | MCU Status Report (main) | Laporan Serah Terima |

**Note:** You can use either the sheet name OR the full Google Sheet ID.

---

## Available Templates

Current templates configured in `config/templates.json`:

| Template Name | Description | Variables | Use Case |
|---------------|-------------|-----------|----------|
| `mcustatus_ready_pick_up` | MCU ready for pickup | day_part, name | Daily: Results ready |
| `mcustatus_pending_patient_sign_carnival` | Carnival MCU - pending signature | day_part, name | Certificate signatures (Carnival) |
| `mcustatus_pending_patient_sign_panama` | Panama MCU - pending signature | day_part, name | Certificate signatures (Panama) |
| `mcustatus_pending_patient_sign_viking_nsi_nma_oguk` | Viking/NSI/NMA/OGUK - pending signature with appointment | day_part, name, date, time | Certificate signatures with scheduled appointment |
| `kyoo_appointment_in` | Appointment confirmation | name, booking_code, date, time, service_type | Auto: Kyoo integration |

---

## Command Reference

### Basic Syntax

```bash
./broadcast.sh \
  --sheet-id=<SHEET_NAME_OR_ID> \
  --tab="<TAB_NAME>" \
  --template=<TEMPLATE_NAME> \
  [OPTIONS]
```

### Required Parameters

- `--sheet-id=NAME_OR_ID` - Sheet name from config OR full Google Sheet ID
- `--tab="TAB_NAME"` - Exact tab name in the Google Sheet (case-sensitive)
- `--template=NAME` - Template name from config

### Optional Parameters

- `--dry-run` - Preview only, don't send messages
- `--limit=N` - Send to first N recipients only (useful for testing)
- `--skip-confirm` or `-y` - Skip confirmation prompt (use with caution!)
- `--filter-column=COLUMN_NAME` - Which column to filter on (e.g., `mcu_name`)
- `--filter-contains=VALUE` - Keep only rows where column contains this value (case-insensitive)
- `--filter-not-contains=VALUE1,VALUE2` - Keep only rows where column does NOT contain any of these values (case-insensitive, comma-separated)

### Examples

```bash
# Dry run (safe, always test first)
./broadcast.sh --sheet-id=mcu_status --tab="Laporan Serah Terima" --template=mcustatus_ready_pick_up --dry-run

# Send to 3 people (testing)
./broadcast.sh --sheet-id=mcu_status --tab="Laporan Serah Terima" --template=mcustatus_ready_pick_up --limit=3

# Filter by MCU type (Carnival only)
./broadcast.sh --sheet-id=mcu_status --tab="Patient Sign Broadcast" --template=mcustatus_pending_patient_sign_carnival --filter-column=mcu_name --filter-contains=carnival

# Filter out multiple values (everything EXCEPT carnival and panama)
./broadcast.sh --sheet-id=mcu_status --tab="Patient Sign Broadcast" --template=mcustatus_pending_patient_sign_viking_nsi_nma_oguk --filter-column=mcu_name --filter-not-contains=carnival,panama

# Send to everyone (production)
./broadcast.sh --sheet-id=mcu_status --tab="Laporan Serah Terima" --template=mcustatus_ready_pick_up

# Skip confirmation (careful!)
./broadcast.sh --sheet-id=mcu_status --tab="Laporan Serah Terima" --template=mcustatus_ready_pick_up -y

# Use full Sheet ID instead of name
./broadcast.sh --sheet-id=1F6jYDngeDRiamwUlzn4g2mRrAZg9xNWVAY8xJ-iWtck --tab="Laporan Serah Terima" --template=mcustatus_ready_pick_up
```

---

## Google Sheet Requirements

### Required Columns

Your Google Sheet MUST have these columns (case-insensitive):

1. **Nama** or **Name** - Patient/recipient name
2. **No HP** or **Phone** - Primary phone number

### Optional Columns

- **No HP 2** or **Phone_2** - Secondary phone (used if primary is empty)
- **day_part** - Time of day (pagi/siang/sore) - uses "pagi" if missing
- **mcu_name** - Type of MCU (for filtering: carnival, panama, viking, etc.)
- **date** - Appointment date (required for Viking/NSI/NMA/OGUK template)
- **time** - Appointment time (required for Viking/NSI/NMA/OGUK template)
- Any other columns - Will be ignored but won't cause errors

### Sheet Structure

- **Headers can be in any row** - System automatically finds them
- **Row 1-3 can be title/empty rows** - No problem
- **Data starts after header row** - System detects automatically

### Example Sheet Structure

```
Row 1: [Title/Empty]
Row 2: [Subtitle/Empty]
Row 3: [Empty]
Row 4: Nama | No HP | No HP 2 | Other columns...
Row 5: I Ketut Suryawan | 81238304604 | 81217274323 | ...
Row 6: Nitiya Santi Devi | 85858131249 | | ...
```

### Phone Number Format

- With or without country code: `081234567890` OR `+6281234567890`
- System adds +62 automatically if missing
- Both formats work

---

## Adding New Sheets

### Step 1: Get the Google Sheet ID

From the URL:
```
https://docs.google.com/spreadsheets/d/1F6jYDngeDRiamwUlzn4g2mRrAZg9xNWVAY8xJ-iWtck/edit
                                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                                      This is the Sheet ID
```

### Step 2: Edit sheets.json

```bash
nano config/sheets.json
```

Add your new sheet:

```json
{
  "test_sheet": {
    "id": "1HzyPMn6VdCPHcT7DSz7dybOd-vibLmHwUT1_euoEr44",
    "description": "Test sheet for development",
    "tabs": {
      "Sheet1": "Test data"
    }
  },
  "mcu_status": {
    "id": "1F6jYDngeDRiamwUlzn4g2mRrAZg9xNWVAY8xJ-iWtck",
    "description": "MCU Status Report - Daily broadcasts",
    "tabs": {
      "Laporan Serah Terima": "Ready for pickup notifications"
    }
  },
  "YOUR_NEW_SHEET": {
    "id": "YOUR_SHEET_ID_HERE",
    "description": "Description of what this sheet is for",
    "tabs": {
      "Tab Name 1": "What this tab contains",
      "Tab Name 2": "What this tab contains"
    }
  }
}
```

Save: `Ctrl+X`, then `Y`, then `Enter`

### Step 3: Test

```bash
./broadcast.sh --sheet-id=YOUR_NEW_SHEET --tab="Tab Name 1" --template=TEMPLATE_NAME --dry-run
```

---

## Adding New Templates

### Step 1: Get Template Details from Meta

1. Go to Meta Business Manager
2. Find your approved template
3. Note down:
   - Template name (exact match)
   - Language code (usually `id` for Indonesian)
   - Variables and their order

### Step 2: Edit templates.json

```bash
nano config/templates.json
```

Add your new template:

```json
{
  "existing_template": {
    ...existing template config...
  },
  "YOUR_NEW_TEMPLATE": {
    "meta_template_name": "YOUR_TEMPLATE_NAME_IN_META",
    "description": "What this template is for",
    "language_code": "id",
    "variables": {
      "day_part": {
        "required": false,
        "position": 1,
        "description": "Greeting time (pagi/siang/sore)",
        "fallback": "pagi"
      },
      "name": {
        "required": true,
        "position": 2,
        "description": "Patient name"
      }
    },
    "variable_order": ["day_part", "name"]
  }
}
```

**Important:**
- `position` - Must match Meta's template variable position ({{1}}, {{2}}, etc.)
- `required: true` - Script will skip if missing
- `required: false` - Will use fallback if missing
- `variable_order` - Must match Meta's template order

Save: `Ctrl+X`, then `Y`, then `Enter`

### Step 3: Test

```bash
./broadcast.sh --sheet-id=test_sheet --tab="Sheet1" --template=YOUR_NEW_TEMPLATE --dry-run
```

---

## Troubleshooting

### Error: "Template not found"

**Problem:** Template name doesn't match config

**Solution:**
```bash
# Check available templates
cat config/templates.json | grep "meta_template_name"

# Use exact name shown
./broadcast.sh --sheet-id=mcu_status --tab="..." --template=EXACT_NAME_HERE --dry-run
```

### Error: "Sheet tab not found"

**Problem:** Tab name is case-sensitive or has extra spaces

**Solution:**
```bash
# List all tabs in a sheet
# (Coming soon - manual check in Google Sheets for now)

# Make sure tab name is exact, including spaces
--tab="Laporan Serah Terima"  # Correct
--tab="laporan serah terima"  # Wrong (case matters)
--tab="Laporan Serah Terima " # Wrong (extra space)
```

### Error: "Missing required columns"

**Problem:** Sheet doesn't have Nama/Name or No HP/Phone columns

**Solution:**
- Check your Google Sheet has a column named "Nama" or "Name"
- Check your Google Sheet has a column named "No HP" or "Phone"
- Column names are case-insensitive
- Make sure headers are in a row (not split across multiple rows)

### Warning: "Missing optional columns (fallbacks will be used)"

**Not an error!** This is normal.

**What it means:** Your sheet is missing an optional column (like `day_part`), so the script will use the fallback value ("pagi").

**If you want to customize:**
- Add a `day_part` column to your sheet
- Fill with values: `pagi`, `siang`, or `sore`

### Error: "Number of parameters does not match"

**Problem:** Template variable mismatch

**Solution:**
1. Check Meta template - how many {{1}}, {{2}} variables?
2. Check config - does `variable_order` match?
3. Make sure variable positions match Meta's template

### Phone Number Shows "undefined"

**Problem:** Phone number format issue

**Solution:**
- Check phone number in sheet doesn't have text/spaces
- Try both "No HP" and "No HP 2" columns
- Phone should be numbers only: `081234567890`

### Messages Failed to Send

**Check the log file:**
```bash
# Find today's log
ls -lt logs/ | head -5

# View the log
cat logs/broadcast_2026-02-14T10-11-54.log
```

**Common causes:**
- Phone number invalid
- Meta template not approved
- Rate limiting (too many messages too fast)

---

## Common Scripts

Copy and paste these commands for common operations.

### Daily MCU Ready for Pickup

```bash
# Navigate to broadcast directory
cd /var/www/chatwoot-services/broadcast

# Test first (DRY RUN)
./broadcast.sh \
  --sheet-id=mcu_status \
  --tab="Laporan Serah Terima" \
  --template=mcustatus_ready_pick_up \
  --dry-run

# If preview looks good, send for real
./broadcast.sh \
  --sheet-id=mcu_status \
  --tab="Laporan Serah Terima" \
  --template=mcustatus_ready_pick_up
```

### Pending Signature Broadcasts (Run all 3)

```bash
cd /var/www/chatwoot-services/broadcast

# 1. Test Carnival
./broadcast.sh \
  --sheet-id=mcu_status \
  --tab="Patient Sign Broadcast" \
  --template=mcustatus_pending_patient_sign_carnival \
  --filter-column=mcu_name \
  --filter-contains=carnival \
  --dry-run

# 2. Test Panama
./broadcast.sh \
  --sheet-id=mcu_status \
  --tab="Patient Sign Broadcast" \
  --template=mcustatus_pending_patient_sign_panama \
  --filter-column=mcu_name \
  --filter-contains=panama \
  --dry-run

# 3. Test Viking/NSI/NMA/OGUK
./broadcast.sh \
  --sheet-id=mcu_status \
  --tab="Patient Sign Broadcast" \
  --template=mcustatus_pending_patient_sign_viking_nsi_nma_oguk \
  --filter-column=mcu_name \
  --filter-not-contains=carnival,panama \
  --dry-run

# If all look good, remove --dry-run and send for real
```

### Test with 2 Recipients Only

```bash
cd /var/www/chatwoot-services/broadcast

./broadcast.sh \
  --sheet-id=mcu_status \
  --tab="Laporan Serah Terima" \
  --template=mcustatus_ready_pick_up \
  --limit=2
```

### Check Recent Logs

```bash
cd /var/www/chatwoot-services/broadcast

# List recent logs
ls -lt logs/ | head -10

# View most recent log
tail -100 logs/broadcast_$(ls -t logs/ | head -1)
```

### Check Available Templates

```bash
cd /var/www/chatwoot-services/broadcast

# List all template names
grep '"meta_template_name"' config/templates.json
```

### Check Available Sheets

```bash
cd /var/www/chatwoot-services/broadcast

# View sheets config
cat config/sheets.json
```

### Update Sheet Dictionary (Add New Sheet)

```bash
cd /var/www/chatwoot-services/broadcast

# Edit sheets config
nano config/sheets.json

# Add new entry following the existing format
# Save: Ctrl+X, Y, Enter
```

---

## Getting Help

### If Something Goes Wrong

1. **Always test with `--dry-run` first**
2. **Check the log files** in `logs/` directory
3. **Start with `--limit=2`** to test with few people
4. **Copy error message** and search in this document

### Need Technical Support

Contact: Alex Knecht (IT Director)
- Share the error message
- Share the command you ran
- Share the relevant log file

### Share Context with AI Assistant

If asking Claude or another AI for help:

```bash
# Copy this info to share:
1. The command you ran
2. The error message
3. Recent log output:

tail -50 logs/YOUR_LOG_FILE.log
```

---

## Best Practices

### Always Follow This Workflow

1. ✅ **Prepare your Google Sheet** - Check columns are correct
2. ✅ **Check recipient count** - If < 5 people, consider sending manually via Chatwoot instead
3. ✅ **Test with dry-run** - Preview before sending
4. ✅ **For new/untested templates:** Test with --limit=2 first, verify messages look correct
5. ✅ **For established templates:** Skip test send, go straight to full broadcast
6. ✅ **Check Chatwoot after sending** - Verify messages logged correctly
7. ✅ **Check logs if any failures** - Review error messages

### When to Use Manual vs Broadcast

- **< 5 recipients:** Send manually via Chatwoot UI (faster, easier)
- **5+ recipients:** Use broadcast system (systematic, tracked, logged)
- **Uncertain about recipients:** Always dry-run first

### Never

- ❌ Skip dry-run on first attempt
- ❌ Send to 100+ people without testing
- ❌ Ignore validation warnings without understanding them
- ❌ Use `-y` (skip confirm) unless you're 100% sure

### Daily Checklist

- [ ] Google Sheet is updated with current data
- [ ] Sheet has "Nama" and "No HP" columns
- [ ] Phone numbers are valid
- [ ] Run dry-run first
- [ ] Review preview output
- [ ] Send to 2 people as test
- [ ] Confirm test messages received
- [ ] Send to everyone
- [ ] Check final log for errors

---

## Quick Reference Card

**Connect to Server:**
```bash
ssh -i 'YOUR_KEY.pem' centos@10.10.3.7
cd /var/www/chatwoot-services/broadcast
```

**Test (Dry Run):**
```bash
./broadcast.sh --sheet-id=mcu_status --tab="Laporan Serah Terima" --template=mcustatus_ready_pick_up --dry-run
```

**Send (Production):**
```bash
./broadcast.sh --sheet-id=mcu_status --tab="Laporan Serah Terima" --template=mcustatus_ready_pick_up
```

**Test 2 People:**
```bash
./broadcast.sh --sheet-id=mcu_status --tab="Laporan Serah Terima" --template=mcustatus_ready_pick_up --limit=2
```

**Check Logs:**
```bash
ls -lt logs/ | head -5
tail -50 logs/LATEST_LOG_FILE.log
```

**Need Help:**
Contact Alex Knecht or copy error + command to Claude

---

**Document Version:** 3.0  
**Last Updated:** February 14, 2026  
**Maintained By:** Alex Knecht, IT Director - PMG

**Major Features in v3.0:**
- ✅ Conditional template selection with row filtering
- ✅ Chatwoot message logging (outbound messages appear in conversations)
- ✅ Phone number fallback (primary → secondary)
- ✅ Smart header detection (works with any sheet structure)
- ✅ Enhanced validation with helpful error messages
- ✅ Template variable display in logs
