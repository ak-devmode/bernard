# PMG Broadcast Service - Complete Package

## What's Included

This package contains everything needed to deploy the WhatsApp broadcast service to your EC2 instance.

### Files Overview

```
broadcast/
├── broadcast.js              # Main script (Node.js)
├── broadcast.sh              # CLI wrapper (bash)
├── test.js                   # Installation test script
├── package.json              # Node.js dependencies
├── .env.example              # Environment variables template
├── .gitignore                # Git ignore rules
│
├── lib/                      # Core modules
│   ├── sheets.js            # Google Sheets API integration
│   ├── chatwoot.js          # Chatwoot contact management
│   ├── meta.js              # Meta WhatsApp Cloud API
│   ├── validator.js         # Template validation & mapping
│   └── logger.js            # Logging to console & file
│
├── config/
│   └── templates.json       # Template definitions (5 Kyoo templates)
│
├── logs/                    # Auto-created, log files stored here
│
└── docs/
    ├── README.md            # Complete documentation
    ├── DEPLOYMENT.md        # Step-by-step deployment guide
    └── QUICKSTART.md        # Quick reference for Okto
```

## Key Features

✅ **Google Sheets Integration** - Reads contact data directly from sheets
✅ **Chatwoot Contact Sync** - Auto-creates missing contacts, validates existing
✅ **Name Conflict Resolution** - Chatwoot name wins, sheet overrides other fields
✅ **Template Validation** - Checks structure before sending
✅ **Fallback Handling** - Optional fields use defaults when blank
✅ **Rate Limiting** - Conservative 20 msg/sec with auto-backoff on 429
✅ **Verbose Progress** - Row-by-row status with clear skip reasons
✅ **Error Recovery** - Retries network errors, continues on single failures
✅ **Security** - All credentials in AWS Parameter Store
✅ **Comprehensive Logging** - Timestamped files in logs/ directory

## Deployment Quick Steps

1. **Upload to EC2**: Copy entire `broadcast/` directory to `/var/www/chatwoot-services/`
2. **Install dependencies**: `npm install`
3. **Configure AWS**: Put credentials in Parameter Store
4. **Set up Google**: Create service account, share sheet
5. **Test**: Run `./test.js` to verify installation
6. **Dry run**: Test with `--dry-run --limit=1`
7. **Go live**: Remove dry-run flag

## Ready-to-Use Templates

Configured in `config/templates.json`:

1. **kyoo_appointment_in** - Full appointment confirmation (7 variables)
2. **kyoo_hmin1_mcu_new** - MCU reminder H-1 (1 variable)
3. **kyoo_perubahan_jadwal_c** - Schedule change (2 variables, salutation optional)
4. **kyoo_pengingat_usg** - USG reminder (2 variables, salutation optional)
5. **kyoo_appt_qr_in** - QR appointment (2 variables, salutation optional)

## Example Usage

```bash
# Dry run to preview
./broadcast.sh \
  --sheet-id=1F6jYDngeDRiamwUlzn4g2mRrAZg9xNWVAY8xJ-iWtck \
  --tab="Feb 2026 Appointments" \
  --template=kyoo_appointment_in \
  --dry-run

# Send to first 5 for testing
./broadcast.sh \
  --sheet-id=1F6jYDngeDRiamwUlzn4g2mRrAZg9xNWVAY8xJ-iWtck \
  --tab="Feb 2026 Appointments" \
  --template=kyoo_appointment_in \
  --limit=5

# Full broadcast
./broadcast.sh \
  --sheet-id=1F6jYDngeDRiamwUlzn4g2mRrAZg9xNWVAY8xJ-iWtck \
  --tab="Feb 2026 Appointments" \
  --template=kyoo_appointment_in
```

## Architecture Decisions

### Why This Approach?

1. **Google Sheets as Source** - Your team already uses sheets, avoids CSV corruption
2. **Chatwoot as Contact DB** - Single source of truth for contact data
3. **AWS Parameter Store** - Secure credential management with instant revocation
4. **EC2 (not Lambda)** - Simpler for your existing infrastructure, easier debugging
5. **Node.js** - Fast, good ecosystem, matches your webhook router

### Contact Validation Flow

```
Sheet Row → Normalize phone → Search Chatwoot
  ├─ Found: Use Chatwoot name + sheet attributes
  └─ Not found: Create with sheet data
→ Validate required fields
→ Apply fallbacks for optional fields
→ Send via Meta API
```

### Error Handling Strategy

- **Missing columns**: Fail fast at validation
- **Missing required data**: Skip row, log clearly
- **Chatwoot API error**: Skip row, continue
- **Meta API error**: Retry 3x with backoff, then skip
- **Rate limit (429)**: Exponential backoff, continue
- **Network error**: Retry 3x, then skip

## Security Model

✅ No credentials in code or config files
✅ All secrets in AWS Parameter Store (encrypted)
✅ Service account has read-only Google Sheets access
✅ Chatwoot token is scoped to account
✅ Meta token can be instantly revoked
✅ Logs contain no sensitive data (phone numbers shown for debugging only)

## Phase 4 Integration Path

This standalone script is designed for easy integration into Chatwoot:

1. Core logic in discrete modules (lib/*.js)
2. Template system matches Meta's structure
3. Contact validation uses Chatwoot API (already compatible)
4. Error handling & logging patterns match production needs
5. Rate limiting & retry logic production-ready

Phase 4 will:
- Add web UI in Chatwoot (Vue.js)
- Add database tables for broadcast history
- Add API endpoints (Rails)
- Add scheduling & audience filtering
- Keep all core logic from these modules

## Testing Checklist

Before deploying to production:

- [ ] Run `./test.js` - all tests pass
- [ ] Dry run with limit=1 - processes correctly
- [ ] Send to own phone - message received & formatted correctly
- [ ] Check log file - contains expected output
- [ ] Test with missing required field - row skipped with clear message
- [ ] Test with optional field blank - fallback used
- [ ] Test with non-existent contact - created in Chatwoot
- [ ] Verify name conflict handling - Chatwoot name wins

## Support & Maintenance

### Regular Tasks

- Check logs weekly: `ls -lth logs/ | head -10`
- Rotate old logs: Automatic via logrotate
- Update templates: Edit `config/templates.json`
- Monitor Parameter Store: Quarterly token rotation

### When Things Go Wrong

1. Check log file for errors
2. Run with `--dry-run` to preview
3. Test with `--limit=1` 
4. Verify AWS credentials: `aws ssm get-parameter --name /pmg/meta/access_token`
5. Check Google Sheet access
6. Alert Alex if unsure

## Next Steps

1. Deploy to EC2 (see DEPLOYMENT.md)
2. Train Okto (see QUICKSTART.md)
3. Run first test broadcast
4. Document any adjustments needed
5. Plan monitoring/alerts (Phase 2)
6. Schedule regular broadcasts
7. Start planning Phase 4 Chatwoot integration

## Version & Status

- **Version**: 1.0.0
- **Status**: Phase 1 - Standalone Script
- **Deployed**: [Date]
- **Owner**: Alex Knecht
- **Operator**: Okto
- **Next Review**: After 10 successful broadcasts

---

**Questions?** See README.md for full documentation or contact Alex.
