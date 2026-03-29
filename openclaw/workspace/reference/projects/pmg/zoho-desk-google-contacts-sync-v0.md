# Zoho Desk to Google Contacts Sync - v1

## Overview
Custom Deluge function that syncs Zoho Desk contacts to Google Contacts for WhatsApp Business App integration.

## Current Functionality (v1)
- Fetches contact from Desk via REST API
- Normalizes Indonesian phone numbers to E.164 format (+62)
- Creates contact in Google Contacts with:
  - First Name
  - Last Name
  - Phone (mobile)
  - Email (if present)
  - Organization/Account Name (via lookup)
- Verbose logging for debugging
- Syncs to Google myContacts group (auto-syncs to WhatsApp Business)

## Working Code
```deluge
// Simple Google Contacts Sync - v1
// Syncs: First Name, Last Name, Phone, Email, Account Name → Organization
// Usage: Pass deskContactId from workflow rule

info "=== Starting Google Contacts Sync ===";
info "Contact ID received: " + deskContactId;

deskOrgId = 803415485;

// Fetch contact via REST API
info "Fetching contact record via API...";
contactResponse = invokeUrl
[
	url :"https://desk.zoho.com/api/v1/contacts/" + deskContactId
	type :GET
	connection:"zoho.desk"
];

info "API Response: " + contactResponse;

if(contactResponse != null)
{
	info "Contact record fetched successfully";
	
	// Get contact data
	firstName = contactResponse.get("firstName");
	lastName = contactResponse.get("lastName");
	phoneRaw = contactResponse.get("phone");
	email = contactResponse.get("email");
	accountId = contactResponse.get("accountId");
	
	// Fetch account name via lookup
	accountName = null;
	if(accountId != null && accountId != "")
	{
		info "Fetching account name for ID: " + accountId;
		accountResponse = invokeUrl
		[
			url :"https://desk.zoho.com/api/v1/accounts/" + accountId
			type :GET
			connection:"zoho.desk"
		];
		info "Account Response: " + accountResponse;
		accountName = accountResponse.get("accountName");
		info "Account Name: " + accountName;
	}
	
	info "First Name: " + firstName;
	info "Last Name: " + lastName;
	info "Phone (raw): " + phoneRaw;
	info "Email: " + email;
	info "Account Name: " + accountName;
	
	// Normalize phone to E.164 format
	if(phoneRaw != null && phoneRaw != "")
	{
		if(phoneRaw.startsWith("62") && !phoneRaw.startsWith("+"))
		{
			formattedPhone = "+" + phoneRaw;
		}
		else if(phoneRaw.startsWith("0"))
		{
			formattedPhone = "+62" + phoneRaw.subString(1);
		}
		else
		{
			formattedPhone = phoneRaw;
		}
		info "Phone (formatted): " + formattedPhone;
		
		// Build Google People API payload
		nameMap = Map();
		nameMap.put("givenName",firstName);
		nameMap.put("familyName",lastName);
		
		phoneMap = Map();
		phoneMap.put("value",formattedPhone);
		phoneMap.put("type","mobile");
		
		payload = Map();
		payload.put("names",{nameMap});
		payload.put("phoneNumbers",{phoneMap});
		
		// Add email if present
		if(email != null && email != "")
		{
			emailMap = Map();
			emailMap.put("value",email);
			emailMap.put("type","work");
			payload.put("emailAddresses",{emailMap});
			info "Email added to payload";
		}
		
		// Add organization (Account Name) if present
		if(accountName != null && accountName != "")
		{
			orgMap = Map();
			orgMap.put("name",accountName);
			payload.put("organizations",{orgMap});
			info "Organization: " + accountName + " added to payload";
		}
		
		info "Payload built: " + payload;
		
		// Call Google People API
		info "Calling Google People API...";
		payloadJSON = payload.toString();
		info "Payload JSON: " + payloadJSON;
		response = invokeUrl
		[
			url :"https://people.googleapis.com/v1/people:createContact"
			type :POST
			parameters:payloadJSON
			headers:{"Content-Type":"application/json"}
			connection:"googlecontactssync"
		];
		
		info "API Response: " + response;
		
		// Check if contact was created
		if(response.get("resourceName") != null)
		{
			resourceName = response.get("resourceName");
			info "SUCCESS: Contact created with resourceName: " + resourceName;
		}
		else
		{
			info "WARNING: No resourceName in response";
			info "Full response for debugging: " + response;
		}
	}
	else
	{
		info "Phone: EMPTY - skipping contact";
	}
}
else
{
	info "ERROR: Could not fetch contact record";
}
```

## Setup Requirements

### Zoho Desk Configuration
- **Function Type**: Workflow Function
- **Module**: Contacts
- **Argument**: 
  - Name: `deskContactId`
  - Type: Contact Id
- **Connection Required**: `zoho.desk` (Zoho Desk API connection)

### Google Configuration
- **Connection Required**: `googlecontactssync` 
  - Connected account: crewcare@pbmcgroup.com
  - Scopes: Google People API (contacts read/write)
- **API Endpoint**: `https://people.googleapis.com/v1/people:createContact`

### Organization ID
- Hardcoded: `803415485` (Padma Desk org)
- Can be moved to CONFIG map if needed for multi-org setup

## Key Technical Decisions

### Why REST API vs Built-in Functions?
- `zoho.desk.getRecordById()` has BIGINT type mismatch issues with Contact Id type in workflow functions
- `invokeUrl` with REST API works reliably with Contact Id arguments

### Phone Number Normalization
- Handles three formats:
  - `6289668215818` → `+6289668215818` (missing +)
  - `089668215818` → `+6289668215818` (local format)
  - `+6289668215818` → `+6289668215818` (already correct)
- E.164 format required for WhatsApp Business sync

### Account Name Lookup
- Account is a lookup field in Desk contacts
- Requires separate API call to `/accounts/{accountId}` endpoint
- Used as Organization field in Google Contacts

## Features to Add Later (v2+)

### High Priority
- [ ] **Duplicate checking**: Search Google Contacts by phone before creating
- [ ] **Sync updates**: Detect changes and update existing Google Contacts
- [ ] **Use `type` field**: Add contact type (Repatriation, Crew Care, Padma Care) as organization or custom label
- [ ] **Date of Birth**: Sync DOB to Google Contacts birthday field
- [ ] **Error handling**: Retry logic, better error messages, handle API failures gracefully

### Medium Priority
- [ ] **Custom fields mapping**: 
  - Membership ID
  - Primary Language
  - Emergency Contact
  - WhatsApp Opt-in Status
  - UHID/Medical Record Number
- [ ] **Notes/Bio field**: Sync relevant custom field data to Google Contacts notes
- [ ] **Batch processing**: Handle bulk syncs efficiently
- [ ] **Bidirectional sync**: Update Desk when Google Contact changes

### Low Priority / Future Considerations
- [ ] **Photo sync**: Sync contact photos if available
- [ ] **Address fields**: Map Desk address to Google Contacts
- [ ] **Secondary phone**: Handle multiple phone numbers
- [ ] **Contact groups**: Organize by service channel or status
- [ ] **Sync status tracking**: Custom field in Desk to track last sync time/status
- [ ] **Deletion handling**: Remove from Google Contacts when deleted/deactivated in Desk

## Testing Checklist
- [x] Single contact creation with phone only
- [x] Contact with email
- [x] Contact with account/organization
- [x] Phone number normalization (all 3 formats)
- [ ] Contact with DOB
- [ ] Contact with type field
- [ ] Duplicate detection
- [ ] Update existing contact
- [ ] Error handling (invalid data, API failures)
- [ ] WhatsApp Business sync verification

## Known Issues / Limitations
1. Creates duplicate contacts if run multiple times on same contact (no duplicate check yet)
2. Only syncs on contact creation (no update sync yet)
3. Verbose logging - may want to reduce for production
4. No retry logic for API failures
5. Account name lookup adds latency (extra API call)

## Integration Points
- **Trigger**: Workflow rule on contact create/update in Desk
- **Dependencies**: 
  - Zoho Desk API connection
  - Google People API connection via OAuth
  - WhatsApp Business App connected to crewcare@pbmcgroup.com Google account

## Notes
- Google Contacts automatically syncs to WhatsApp Business App when contacts are in "myContacts" group
- Phone format validation is critical - WhatsApp won't recognize incorrectly formatted numbers
- Function executes synchronously - consider async for batch operations in future