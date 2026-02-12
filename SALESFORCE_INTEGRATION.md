# Salesforce Integration Guide

## Overview
SalesIQ now includes comprehensive Salesforce integration that allows you to take action on sales call insights directly from the application.

## Features

### 1. Account Linking
- **Search Salesforce Accounts**: Search for and link sales calls to specific Salesforce accounts
- **Manual Account Entry**: If Salesforce session expires, you can manually enter an Account ID
- **Visual Feedback**: Selected account is displayed prominently in the UI

### 2. Task Creation
- **Automatic Task Generation**: Convert action items from call analysis into Salesforce tasks
- **Selective Creation**: Choose which action items to create as tasks using checkboxes
- **Smart Defaults**: Tasks are created with:
  - Status: "Not Started"
  - Priority: "Normal"
  - Due Date: 7 days from creation
  - Linked to selected account

### 3. Meeting Scheduling
- **Follow-up Meetings**: Schedule follow-up meetings based on next steps from call analysis
- **Date/Time Picker**: Easy-to-use interface for selecting meeting date and time
- **Auto-populated Description**: Meeting description is pre-filled with next steps from the call

### 4. Account Updates
- **Customer Needs Tracking**: Update account information with customer needs identified in the call
- **Pre-filled Notes**: Customer needs are automatically formatted and ready to add to account
- **Editable Content**: Modify the notes before updating the account

## How to Use

### Step 1: Upload and Analyze a Call
1. Navigate to the Chat Assistant page
2. Upload an MP3 audio file of a sales call
3. Wait for transcription and AI analysis to complete
4. View the generated report in the Reports section

### Step 2: Open Report Details
1. Go to the Reports page
2. Click on any report to open the detailed view
3. Scroll down to the "Salesforce Actions" section (blue highlighted area)

### Step 3: Link to Salesforce Account
1. In the "Link to Salesforce Account" field, enter a search term
2. Click "Search" to find matching accounts
3. Click on an account from the results to select it
4. **Alternative**: If Salesforce session is expired, manually enter an Account ID

### Step 4: Create Tasks
1. Review the action items with checkboxes
2. Uncheck any items you don't want to create as tasks
3. Click "Create Selected Tasks"
4. View success confirmation

### Step 5: Schedule Follow-up Meeting
1. Review the suggested next steps
2. Select a date and time for the meeting
3. Click "Schedule Meeting"
4. View success confirmation

### Step 6: Update Account Information
1. Review the pre-filled customer needs in the text area
2. Edit the notes as needed
3. Click "Update Account"
4. View success confirmation

## Technical Details

### Salesforce MCP Integration
The application uses the Salesforce MCP (Model Context Protocol) to interact with Salesforce:

- **Available Tools**:
  - `salesforce_get_accounts`: Search and retrieve accounts
  - `salesforce_update_account`: Update account information
  - `salesforce_query`: Execute SOQL queries

### API Endpoints

#### Search Accounts
```
GET /api/salesforce/search-accounts?query=<search_term>
```

#### Create Tasks
```
POST /api/salesforce/create-tasks
Body: {
  "action_items": ["item1", "item2"],
  "account_id": "001..."
}
```

#### Create Event
```
POST /api/salesforce/create-event
Body: {
  "subject": "Follow-up Meeting",
  "description": "...",
  "start_datetime": "2024-02-15T10:00:00",
  "end_datetime": "2024-02-15T11:00:00",
  "account_id": "001..."
}
```

#### Update Account
```
POST /api/salesforce/update-account
Body: {
  "account_id": "001...",
  "updates": {
    "Description": "Customer needs: ..."
  }
}
```

## Session Management

### Handling Expired Sessions
If the Salesforce session expires, the application provides:
1. Clear error messaging
2. Manual account ID entry option
3. Guidance on reconnecting to Salesforce

### Reconnecting to Salesforce
To reconnect your Salesforce session:
1. Ensure the Salesforce MCP service is running
2. Re-authenticate through the MCP configuration
3. Refresh the SalesIQ application

## UI Components

### Salesforce Actions Section
- **Location**: Bottom of report detail modal
- **Styling**: Blue gradient background with Salesforce logo
- **Sections**:
  1. Account Search
  2. Task Creation
  3. Meeting Scheduling
  4. Account Updates

### Visual Indicators
- **Success Messages**: Green text with checkmark
- **Error Messages**: Red text with error details
- **Loading States**: Blue text indicating processing
- **Session Warnings**: Yellow background with warning icon

## Best Practices

1. **Always Link to Account First**: Select an account before creating tasks or scheduling meetings
2. **Review Before Creating**: Check the auto-generated content before submitting to Salesforce
3. **Edit Customer Needs**: Customize the customer needs text to match your organization's format
4. **Use Descriptive Meeting Titles**: Modify the default "Follow-up Meeting" title if needed

## Troubleshooting

### "Salesforce Session Expired" Error
- **Solution**: Use the manual account ID entry or reconnect to Salesforce

### "Please select a Salesforce account first" Error
- **Solution**: Search for and select an account before creating tasks or meetings

### Tasks Not Appearing in Salesforce
- **Note**: Task creation is currently queued and requires full Salesforce REST API integration
- **Workaround**: Tasks are logged in the application for manual creation in Salesforce

## Future Enhancements

Planned improvements for the Salesforce integration:
1. Direct Task and Event creation via Salesforce REST API
2. Real-time sync of created items
3. Opportunity linking
4. Contact association
5. Activity history tracking
6. Bulk operations support

## Support

For issues or questions about the Salesforce integration:
1. Check the application logs for detailed error messages
2. Verify Salesforce MCP service is running: `mcp-tools services`
3. Test Salesforce connectivity: `mcp-tools list salesforce`