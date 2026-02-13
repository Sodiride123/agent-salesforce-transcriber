# Meeting Logging Feature

## Overview

The Salesforce Transcriber application now includes the ability to log meeting information from sales calls directly into Salesforce. This feature captures call summaries, key points, customer needs, and action items as meeting records.

## How It Works

### Current Implementation

Due to limitations in the Salesforce MCP (Model Context Protocol), which doesn't currently expose Event object creation, the meeting logging feature uses a **workaround approach**:

1. **Meeting notes are stored in the Account Description field**
2. Each meeting is formatted with:
   - Meeting subject/title
   - Date and time
   - Location (e.g., Phone Call, Virtual)
   - Detailed notes including:
     - Call summary
     - Key points discussed
     - Customer needs identified
     - Action items

3. **Multiple meetings are appended** to the Account Description, creating a chronological log of all interactions

### Benefits of This Approach

✅ **Immediate availability** - No need to wait for MCP updates
✅ **Simple implementation** - Uses existing Salesforce update capabilities
✅ **Chronological history** - All meetings logged in one place
✅ **Easy to access** - Visible directly on the Account record

### Limitations

⚠️ **Not using Event objects** - Meeting information is stored in Description field, not as separate Event records
⚠️ **No calendar integration** - Meetings won't appear in Salesforce calendars
⚠️ **Limited querying** - Can't easily filter or report on individual meetings
⚠️ **Field length limits** - Account Description field has a character limit

## Usage

### From the Web Interface

1. **Upload and transcribe** a sales call recording
2. **Select a Salesforce account** from the dropdown
3. **Click "View Report"** to see the analysis
4. In the Salesforce Actions section, find **"Log Meeting in Salesforce"**
5. **Edit the meeting subject and notes** if needed
6. **Click "Log Meeting"** to save to Salesforce

### API Endpoint

```bash
POST /api/salesforce/create-event
Content-Type: application/json

{
  "account_id": "001XXXXXXXXXX",
  "subject": "Sales Call - Product Demo",
  "description": "Detailed meeting notes...",
  "start_datetime": "2024-01-15T10:00:00Z",
  "end_datetime": "2024-01-15T11:00:00Z",
  "location": "Phone Call"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Meeting notes added to Account Description",
  "meeting_data": {
    "subject": "Sales Call - Product Demo",
    "date": "2024-01-15 10:00",
    "location": "Phone Call",
    "account_id": "001XXXXXXXXXX"
  },
  "note": "Meeting information stored in Account Description field. Full Event object creation requires Salesforce MCP extension."
}
```

## Future Enhancements

### Option 1: Extend Salesforce MCP

The ideal solution would be to extend the Salesforce MCP to include Event creation:

```python
# Future MCP tool
salesforce_create_event({
  "event_data": {
    "Subject": "Sales Call",
    "Description": "Meeting notes...",
    "StartDateTime": "2024-01-15T10:00:00Z",
    "EndDateTime": "2024-01-15T11:00:00Z",
    "WhatId": "001XXXXXXXXXX",  # Account ID
    "WhoId": "003XXXXXXXXXX"    # Contact ID (optional)
  }
})
```

### Option 2: Direct Salesforce REST API Integration

Implement direct REST API calls to Salesforce:

```python
import requests

def create_salesforce_event(access_token, instance_url, event_data):
    url = f"{instance_url}/services/data/v58.0/sobjects/Event"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    response = requests.post(url, json=event_data, headers=headers)
    return response.json()
```

### Option 3: Use Notes or Tasks

Alternative Salesforce objects that might be better suited:

- **Notes (ContentNote)**: Better for storing meeting notes
- **Tasks**: Can represent follow-up actions from meetings
- **Custom Objects**: Create a custom "Meeting Log" object

## Viewing Meeting Logs in Salesforce

1. Navigate to the **Account** record in Salesforce
2. Scroll to the **Description** field
3. All meeting logs will be displayed chronologically, with the most recent at the top

### Example Format:

```
=== Meeting: Sales Call - Product Demo ===
Date: 2024-01-15 10:00
Location: Phone Call

Notes:
Customer expressed strong interest in our enterprise features.
Discussed pricing and implementation timeline.
Next steps: Send proposal by end of week.

---

=== Meeting: Initial Discovery Call ===
Date: 2024-01-10 14:30
Location: Virtual

Notes:
First contact with prospect.
Identified key pain points and requirements.
Scheduled follow-up demo.

---
```

## Technical Details

### File Structure

- **Backend**: `app.py` - `/api/salesforce/create-event` endpoint
- **Frontend**: `static/js/app.js` - `createMeetingEvent()` function
- **MCP Integration**: Uses `salesforce_update_account` tool

### Data Flow

1. User clicks "Log Meeting" button
2. Frontend collects meeting subject and notes
3. POST request sent to `/api/salesforce/create-event`
4. Backend formats meeting notes with timestamp
5. Backend retrieves current Account Description
6. Backend prepends new meeting notes to existing description
7. Backend updates Account using Salesforce MCP
8. Success/error message displayed to user

## Troubleshooting

### "Please select a Salesforce account first"
- Make sure you've selected an account from the dropdown before clicking "Log Meeting"

### "Failed to update account with meeting notes"
- Check that the Salesforce MCP is running and connected
- Verify the account ID is valid
- Check Salesforce permissions for the connected user

### Meeting notes not appearing in Salesforce
- Refresh the Account page in Salesforce
- Check the Description field on the Account record
- Verify the update was successful (check for success message)

## Contributing

If you'd like to contribute improvements to this feature:

1. **Extend the MCP**: Add Event creation support to the Salesforce MCP
2. **Improve formatting**: Enhance the meeting notes format
3. **Add filtering**: Implement search/filter for meeting logs
4. **Export functionality**: Add ability to export meeting history

## Support

For issues or questions about this feature:
- Check the application logs: `tail -f /workspace/agent-salesforce-transcriber/app.log`
- Review Salesforce MCP status: `mcp-tools services`
- Test Salesforce connection: `mcp-tools call salesforce_get_accounts '{"limit": 1}'`