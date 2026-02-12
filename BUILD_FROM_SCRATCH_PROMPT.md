# AI Prompt: Build SalesIQ Sales Call Analysis Platform from Scratch

## Project Brief

Build a complete web application called **SalesIQ** - a sales call analysis platform that integrates with Salesforce MCP. The application should allow users to upload sales call audio files, transcribe them, analyze the content, and generate detailed reports with insights.

## Core Requirements

### 1. Application Architecture

**Backend:**
- Flask server running on port 9000
- Host on 0.0.0.0 to be publicly accessible
- Enable CORS for API access
- File-based storage (JSON for reports, filesystem for audio)

**Frontend:**
- Single-page application with three main sections
- Modern, professional UI with blue-purple gradient theme
- Responsive design
- No framework dependencies (vanilla JavaScript)

**Integration:**
- Connect to Salesforce MCP (available at http://localhost:9082/mcp)
- Use mcp-tools command to interact with Salesforce

### 2. User Interface Structure

**Left Navigation Bar (250px width):**
- Header with application logo/avatar and name "SalesIQ"
- Three navigation items:
  1. Chat Assistant (landing page) - with chat bubble icon
  2. Reports - with bar chart icon
  3. Media Library - with music note icon
- Blue gradient background (#1e3a8a to #1e40af)
- White text with active state indicators

**Main Content Area:**
- Header with page title
- Content body with page-specific content
- White background with light gray page background

### 3. Feature Requirements

#### A. Chat Assistant (Landing Page)

**Requirements:**
- Interactive chat interface with message history
- Custom AI assistant avatar (chibi 3D character)
- Welcome message explaining capabilities
- Audio file upload section with drag-and-drop
- Support formats: MP3, WAV, M4A, OGG, WEBM
- Maximum file size: 25MB
- Text input for questions/messages
- Real-time message display (user and assistant messages)
- File validation before upload

**Avatar Specifications:**
- Chibi 3D professional businessman character
- Oversized cute head, small body
- Navy blue suit, white shirt, gradient blue-purple tie
- Holding tablet/smartphone showing sales charts
- Thoughtful pose (pointing upward - idea gesture)
- Blue-to-purple gradient background (#0A66C2 to #8B5CF6)
- 1024x1024 pixels
- Generate using image generation tool

**Chat Functionality:**
- Display messages in conversation format
- User messages aligned right
- Assistant messages aligned left with avatar
- Auto-scroll to latest message
- Show file upload confirmation
- Display processing status

#### B. Reports Section

**Requirements:**
- Grid layout of report cards
- Each card shows:
  - Audio filename
  - Creation date/time
  - Summary preview
  - "View Details" button
  - "Delete" button
- Modal view for detailed report with:
  - Full transcription
  - Summary
  - Key discussion points
  - Sentiment analysis
  - Action items
  - Customer needs identified
  - Next steps recommendations
- Empty state when no reports exist
- Delete confirmation dialog

**Report Generation:**
When audio is uploaded:
1. Transcribe the audio file
2. Analyze the transcription using AI
3. Generate structured report with:
   - Summary (high-level overview)
   - Key Points (bullet list of main topics)
   - Sentiment Analysis (positive/negative/neutral)
   - Action Items (tasks to complete)
   - Customer Needs (identified requirements)
   - Next Steps (recommended follow-up)
   - Full Transcription (complete text)
4. Save as JSON file with unique ID
5. Store in /workspace/reports/ directory

#### C. Media Library

**Requirements:**
- Grid layout of media file cards
- Each card shows:
  - Audio icon
  - Filename
  - File size
  - Upload date/time
  - Delete button
- Empty state when no files exist
- Delete confirmation dialog
- Files stored in /workspace/media_library/

### 4. Audio Transcription

**Implementation:**
- Use the transcribe-audio tool available in SuperNinja environment
- File path should be relative to /workspace (e.g., "media_library/audio.mp3")
- Handle transcription errors gracefully
- Show processing status to user
- Store transcription with report

**Note:** The transcribe-audio tool is an XML tool in the agent system. From Flask, you'll need to create a wrapper that:
1. Validates the audio file
2. Calls a transcription service (OpenAI Whisper API recommended)
3. Returns the transcription text

### 5. Salesforce Integration

**Requirements:**
- Verify Salesforce MCP connection on startup
- Create API endpoints for:
  - GET /api/salesforce/accounts
  - GET /api/salesforce/opportunities
- Use mcp-tools command to interact:
  ```bash
  mcp-tools services  # List available services
  mcp-tools list salesforce  # List Salesforce tools
  mcp-tools call <tool_name> '<json_args>'  # Call a tool
  ```

**Available Salesforce Tools:**
- Accounts (CRUD operations)
- Contacts (CRUD operations)
- Opportunities (CRUD operations)
- Leads (CRUD + conversion)
- Cases (CRUD operations)
- Campaigns (CRUD operations)

### 6. Design Specifications

**Color Palette:**
- Primary Blue: #1e3a8a to #1e40af (gradient)
- Accent Blue: #3b82f6
- Light Blue: #60a5fa
- Purple: #8B5CF6
- Background: #f5f7fa
- White: #ffffff
- Text Dark: #1f2937
- Text Medium: #4b5563
- Text Light: #6b7280

**Typography:**
- Font: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto
- Heading sizes: 24px (nav), 28px (page), 18-20px (cards)
- Body text: 15px
- Small text: 13px

**Icons:**
- Use SVG icons (not emojis)
- Chat: Speech bubble with dots
- Reports: Bar chart
- Media: Music note
- Upload: Audio file icon
- All icons should be 20x20px in navigation
- Use Material Design style

**Layout:**
- Navigation: 250px fixed width
- Content: Flexible width
- Max content width: 900px (chat), 800px (modal)
- Card spacing: 20px gap
- Border radius: 12px (cards), 24px (buttons)
- Box shadows for depth

### 7. API Endpoints

**Chat:**
- POST /api/chat
  - Body: { "message": "string" }
  - Returns: { "message": "string", "timestamp": "ISO date" }

**Audio Processing:**
- POST /api/upload-audio
  - Body: FormData with 'audio' file
  - Returns: { "success": boolean, "report_id": "string", "message": "string" }

**Reports:**
- GET /api/reports
  - Returns: Array of report summaries
- GET /api/reports/<report_id>
  - Returns: Full report object
- DELETE /api/reports/<report_id>
  - Returns: { "success": boolean, "message": "string" }

**Media Library:**
- GET /api/media
  - Returns: Array of file metadata
- DELETE /api/media/<filename>
  - Returns: { "success": boolean, "message": "string" }

**Salesforce:**
- GET /api/salesforce/accounts?limit=<number>
  - Returns: Salesforce account data
- GET /api/salesforce/opportunities?limit=<number>
  - Returns: Salesforce opportunity data

### 8. File Structure

Create the following structure:
```
/workspace/
├── app.py                      # Flask backend
├── index.html                  # Main HTML
├── requirements.txt            # Dependencies
├── static/
│   ├── css/
│   │   └── styles.css         # All styling
│   ├── js/
│   │   └── app.js             # Frontend logic
│   └── images/
│       └── salesiq-avatar.png # Generated avatar
├── uploads/                    # Temporary uploads
├── reports/                    # JSON reports
└── media_library/             # Permanent audio storage
```

### 9. Dependencies

**Python (requirements.txt):**
```
flask==3.0.0
flask-cors==4.0.0
werkzeug==3.0.1
```

**For transcription (choose one):**
- openai (for Whisper API)
- assemblyai (for AssemblyAI)
- openai-whisper (for local Whisper)

### 10. Implementation Steps

1. **Setup:**
   - Create directory structure
   - Install dependencies
   - Verify Salesforce MCP connection

2. **Generate Avatar:**
   - Use image generation tool with specifications above
   - Save to static/images/salesiq-avatar.png

3. **Backend (app.py):**
   - Create Flask app with CORS
   - Implement all API endpoints
   - Add file upload handling
   - Create transcription wrapper
   - Add Salesforce integration
   - Implement report generation logic

4. **Frontend HTML (index.html):**
   - Create navigation structure
   - Build chat interface
   - Create reports section
   - Build media library section
   - Add modal for report details

5. **Styling (styles.css):**
   - Implement color scheme
   - Style navigation bar
   - Style chat interface
   - Style report cards and modal
   - Style media library
   - Add responsive design
   - Create animations and transitions

6. **JavaScript (app.js):**
   - Implement navigation switching
   - Handle chat messages
   - Manage file uploads
   - Load and display reports
   - Handle report modal
   - Manage media library
   - API communication
   - Error handling

7. **Testing:**
   - Test file upload
   - Test transcription
   - Test report generation
   - Test navigation
   - Test Salesforce integration
   - Test all CRUD operations

8. **Deployment:**
   - Start Flask server on port 9000
   - Expose port using expose-port tool
   - Verify public access
   - Test complete workflow

### 11. Key Features to Implement

**File Upload Flow:**
1. User selects audio file
2. Validate file type and size
3. Show selected file name
4. On submit, upload to server
5. Save to media_library with unique filename
6. Transcribe audio
7. Generate AI analysis
8. Create report JSON
9. Notify user of completion
10. Update UI

**Report Analysis Logic:**
Create AI-generated analysis including:
- Extract key discussion points
- Identify customer sentiment
- List action items
- Identify customer needs
- Suggest next steps
- Provide summary

**Error Handling:**
- Invalid file types
- File too large
- Transcription failures
- Network errors
- Missing files
- Salesforce connection issues

### 12. Success Criteria

The application is complete when:
- ✅ Server runs on port 9000
- ✅ All three pages functional
- ✅ Audio upload works
- ✅ Transcription processes files
- ✅ Reports generate correctly
- ✅ Media library manages files
- ✅ Salesforce integration works
- ✅ UI is professional and responsive
- ✅ All CRUD operations work
- ✅ Error handling is robust
- ✅ Public URL is accessible

### 13. Important Notes

- All file paths must be relative to /workspace
- Never use absolute paths like /workspace/file.txt
- Use relative paths like media_library/file.txt
- Flask debug mode should be enabled for auto-reload
- Expose port 9000 after starting server
- Test with real audio files
- Document all API endpoints
- Create comprehensive README

### 14. Optional Enhancements

If time permits:
- Add user authentication
- Implement search functionality
- Add export to PDF
- Create analytics dashboard
- Add email notifications
- Implement team collaboration
- Add calendar integration
- Create mobile responsive design
- Add dark mode
- Implement real-time updates

## Deliverables

1. Fully functional web application
2. Complete source code
3. README.md with documentation
4. QUICKSTART.md for users
5. Public URL for access
6. All features working as specified

## Technical Constraints

- Must use Flask (not FastAPI or other frameworks)
- Must integrate with Salesforce MCP
- Must run on port 9000
- Must be accessible via public URL
- Must handle files up to 25MB
- Must support specified audio formats
- Must use file-based storage (no database)

## Design Constraints

- Must use specified color palette
- Must have custom avatar
- Must use SVG icons (not emojis)
- Must be professional appearance
- Must be responsive design
- Must follow Material Design principles

Start building! Create the complete SalesIQ application following all specifications above. 🚀