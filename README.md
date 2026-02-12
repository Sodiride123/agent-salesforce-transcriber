# SalesIQ - Sales Call Analysis Platform

A comprehensive web application for analyzing sales calls with AI-powered insights, integrated with Salesforce.

## 🚀 Features

### 1. **Chat Assistant (Landing Page)**
- Interactive AI chat interface for sales analysis
- Custom chibi 3D avatar representing SalesIQ assistant
- Upload MP3/WAV/M4A/OGG audio files directly in chat
- Real-time conversation with SalesIQ assistant
- Automatic audio processing and report generation

### 2. **Reports Section**
- View all generated sales call reports
- Detailed analysis including:
  - Full transcription of sales calls
  - Key discussion points
  - Sentiment analysis
  - Action items and next steps
  - Customer needs identification
- Delete unwanted reports
- Modal view for detailed report inspection

### 3. **Media Library**
- Central repository for all uploaded audio files
- File metadata (size, upload date)
- Easy file management and deletion
- Organized storage system

### 4. **Salesforce Integration**
- Connected to Salesforce MCP
- Access to Accounts, Opportunities, Contacts, Leads, Cases, and Campaigns
- Real-time data synchronization
- Available API endpoints for Salesforce operations

## 🎯 Application Access

**Live Application URL:** https://salesiq-000yl.app.super.betamyninja.ai

## 📋 How to Use

### Uploading and Analyzing Sales Calls

1. **Navigate to Chat Assistant** (default landing page)
2. **Upload Audio File:**
   - Click the "📎 Upload Sales Call Audio" button
   - Select your MP3, WAV, M4A, or OGG file
   - Click "Send" to process
3. **Wait for Processing:**
   - The system will transcribe your audio
   - AI will analyze the conversation
   - A comprehensive report will be generated
4. **View Results:**
   - Check the "Reports" section to see your analysis
   - Click on any report to view detailed insights

### Viewing Reports

1. Navigate to the **Reports** tab
2. Browse all generated reports
3. Click "View Details" to see full analysis
4. Review:
   - Summary and key points
   - Sentiment analysis
   - Action items
   - Customer needs
   - Full transcription

### Managing Media Files

1. Navigate to the **Media Library** tab
2. View all uploaded audio files
3. Check file sizes and upload dates
4. Delete files as needed

## 🔧 Technical Architecture

### Backend (Flask)
- **Port:** 9000
- **Framework:** Flask 3.0.0
- **CORS:** Enabled for cross-origin requests
- **File Upload:** Max 25MB per file

### API Endpoints

#### Chat
- `POST /api/chat` - Send messages to SalesIQ assistant

#### Audio Processing
- `POST /api/upload-audio` - Upload and process audio files

#### Reports
- `GET /api/reports` - List all reports
- `GET /api/reports/<report_id>` - Get specific report
- `DELETE /api/reports/<report_id>` - Delete report

#### Media Library
- `GET /api/media` - List all media files
- `DELETE /api/media/<filename>` - Delete media file

#### Salesforce Integration
- `GET /api/salesforce/accounts` - Get Salesforce accounts
- `GET /api/salesforce/opportunities` - Get Salesforce opportunities

### Frontend
- **HTML5** with semantic structure
- **CSS3** with modern gradients and animations
- **Vanilla JavaScript** for interactivity
- **Responsive Design** for all screen sizes

## 🗂️ Project Structure

```
/workspace/
├── app.py                      # Flask backend server
├── index.html                  # Main HTML file
├── requirements.txt            # Python dependencies
├── static/
│   ├── css/
│   │   └── styles.css         # Application styling
│   └── js/
│       └── app.js             # Frontend JavaScript
├── uploads/                    # Temporary upload directory
├── reports/                    # Generated reports storage
└── media_library/             # Permanent audio file storage
```

## 🔌 Salesforce MCP Integration

The application is connected to Salesforce MCP with access to:

- **Accounts:** Create, read, update, delete
- **Contacts:** Full CRUD operations
- **Opportunities:** Sales pipeline management
- **Leads:** Lead tracking and conversion
- **Cases:** Customer support cases
- **Campaigns:** Marketing campaign management
- **Attachments:** File management
- **Custom Queries:** SOQL query execution

### Using Salesforce Features

To integrate Salesforce data into your sales analysis:

```javascript
// Example: Fetch accounts
fetch('/api/salesforce/accounts?limit=10')
  .then(response => response.json())
  .then(data => console.log(data));

// Example: Fetch opportunities
fetch('/api/salesforce/opportunities?limit=10')
  .then(response => response.json())
  .then(data => console.log(data));
```

## 🎨 Design Features

- **Modern UI:** Clean, professional interface with gradient accents
- **Intuitive Navigation:** Left sidebar with clear section indicators
- **Responsive Layout:** Works on desktop and tablet devices
- **Smooth Animations:** Hover effects and transitions
- **Color Scheme:** Blue gradient theme with white content areas
- **Typography:** System fonts for optimal readability

## 🔒 Security Features

- File type validation (only audio files accepted)
- File size limits (25MB maximum)
- Secure filename handling
- CORS protection
- Input sanitization

## 📊 Report Analysis Components

Each generated report includes:

1. **Summary:** High-level overview of the call
2. **Key Points:** Important discussion topics
3. **Sentiment Analysis:** Overall tone and customer mood
4. **Action Items:** Tasks to complete post-call
5. **Customer Needs:** Identified requirements and pain points
6. **Next Steps:** Recommended follow-up actions
7. **Full Transcription:** Complete text of the conversation

## 🚀 Future Enhancements

Potential features for future development:
- Real-time audio transcription
- Advanced AI analysis with GPT-4
- Salesforce automatic data entry from calls
- Multi-language support
- Team collaboration features
- Analytics dashboard
- Export reports to PDF
- Email notifications
- Calendar integration

## 💡 Tips for Best Results

1. **Audio Quality:** Use clear recordings for better transcription
2. **File Format:** MP3 is recommended for best compatibility
3. **File Size:** Keep files under 25MB for optimal processing
4. **Regular Cleanup:** Delete old reports and media to save space
5. **Salesforce Sync:** Regularly check Salesforce integration status

## 🆘 Support

For issues or questions:
1. Check the chat assistant for help
2. Review this documentation
3. Verify Salesforce MCP connection status
4. Check browser console for errors

---

**Built with ❤️ using Flask, JavaScript, and Salesforce MCP**