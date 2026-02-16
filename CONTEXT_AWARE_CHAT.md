# Context-Aware Chat System Documentation

## Overview

The SalesIQ application now features an intelligent, context-aware chat system powered by Claude AI. Users can upload sales call recordings and then ask natural language questions about the content, with the AI providing accurate answers based on the actual transcription.

---

## 🎯 Key Features

### 1. **Session Management**
- Each user gets a unique session ID stored in browser localStorage
- Sessions persist across page refreshes
- Multiple transcriptions can be loaded into a single session context

### 2. **Automatic Context Linking**
- When you upload an audio file, it's automatically added to your session context
- The transcription becomes immediately available for Q&A
- Context indicator shows how many calls are currently loaded

### 3. **Intelligent Q&A**
- Ask questions in natural language
- AI answers based on actual transcription content
- Maintains conversation history for follow-up questions
- References specific parts of the call when relevant

### 4. **Multi-Call Context**
- Upload multiple audio files to compare across calls
- Ask aggregate questions like "What were the common concerns?"
- Context indicator shows total number of calls loaded

---

## 🔄 How It Works

### **Step 1: Upload Audio**
```
User uploads MP3 → Transcription API → Report Generated → Linked to Session
```

### **Step 2: Ask Questions**
```
User asks question → Retrieve session context → Build context from reports → 
Claude AI processes with context → Return intelligent answer
```

### **Step 3: Follow-up Questions**
```
Conversation history maintained → Follow-up questions use full context → 
Natural conversation flow
```

---

## 💻 Technical Architecture

### **Backend Components**

#### **Session Class** (`app.py`)
```python
class Session:
    - session_id: Unique identifier
    - active_reports: List of report IDs in context
    - conversation_history: Chat message history
    - created_at: Session creation timestamp
    - last_activity: Last interaction timestamp
```

#### **Context Building** (`build_context_from_reports()`)
- Loads all reports linked to the session
- Extracts transcription and analysis data
- Formats into structured context for AI
- Includes: transcription, summary, key points, sentiment, needs, actions

#### **AI Integration** (`ask_claude_with_context()`)
- Uses `ninja-cline-complex` model
- Sends question with full transcription context
- Maintains conversation history (last 10 messages)
- Returns intelligent, context-aware responses

#### **Chat Endpoint** (`/api/chat`)
- Validates session and context availability
- Retrieves relevant transcriptions
- Calls Claude AI with context
- Tracks conversation history
- Returns structured responses

### **Frontend Components**

#### **Session Management** (`app.js`)
```javascript
- Generates UUID on first visit
- Stores in localStorage as 'salesiq_session_id'
- Sends with every API request
- Persists across page refreshes
```

#### **Context Indicator**
- Visual indicator showing number of calls in context
- Updates automatically after uploads
- Green badge with call count
- Animated appearance

#### **Enhanced Upload Flow**
```javascript
uploadAudioFile(file) {
    - Sends file + session_id
    - Receives context confirmation
    - Updates context indicator
    - Shows success message with context info
}
```

#### **Enhanced Chat Flow**
```javascript
sendChatMessage(message) {
    - Sends message + session_id
    - Receives AI response with context
    - Updates context indicator if needed
    - Displays response in chat
}
```

---

## 📊 Data Flow Diagram

```
┌─────────────────┐
│   User Browser  │
│  (Session ID)   │
└────────┬────────┘
         │
         │ 1. Upload MP3 + session_id
         ↓
┌─────────────────────────┐
│  /api/upload-audio      │
│  - Save file            │
│  - Transcribe           │
│  - Generate report      │
│  - Link to session      │
└────────┬────────────────┘
         │
         │ 2. Report ID added to session.active_reports
         ↓
┌─────────────────────────┐
│   Session Store         │
│   {                     │
│     session_id: "..."   │
│     active_reports: []  │
│     history: []         │
│   }                     │
└────────┬────────────────┘
         │
         │ 3. User asks question + session_id
         ↓
┌─────────────────────────┐
│  /api/chat              │
│  - Get session          │
│  - Check context        │
│  - Build context        │
│  - Call Claude AI       │
│  - Return answer        │
└────────┬────────────────┘
         │
         │ 4. Context from active_reports
         ↓
┌─────────────────────────┐
│  build_context_from_    │
│  reports()              │
│  - Load report files    │
│  - Extract transcripts  │
│  - Format context       │
└────────┬────────────────┘
         │
         │ 5. Question + Context + History
         ↓
┌─────────────────────────┐
│  ask_claude_with_       │
│  context()              │
│  - Build system prompt  │
│  - Add history          │
│  - Call Claude API      │
│  - Return response      │
└────────┬────────────────┘
         │
         │ 6. AI Response
         ↓
┌─────────────────────────┐
│   User Browser          │
│   (Display answer)      │
└─────────────────────────┘
```

---

## 🧪 Testing

### **Automated Tests**
Run the test script:
```bash
cd agent-salesforce-transcriber
python test_context_chat.py
```

Tests include:
- Chat without context (should fail gracefully)
- Chat with missing session_id
- Chat with empty message
- Error handling validation

### **Manual Testing**

1. **Upload and Ask Flow:**
   ```
   1. Open https://0011d.app.super.betamyninja.ai
   2. Upload an audio file
   3. Wait for "Audio processed successfully" message
   4. See context indicator: "📄 1 call in context"
   5. Ask: "What did the customer say about pricing?"
   6. Receive AI-powered answer based on transcription
   ```

2. **Follow-up Questions:**
   ```
   1. After first question, ask: "What were the main concerns?"
   2. Then ask: "What should we do next?"
   3. Verify conversation flows naturally
   ```

3. **Multiple Files:**
   ```
   1. Upload first audio file
   2. Upload second audio file
   3. Context indicator shows: "📄 2 calls in context"
   4. Ask: "What are the common themes across both calls?"
   ```

---

## 🎨 UI/UX Features

### **Context Indicator**
- **Location:** Top right of chat header
- **Appearance:** Green badge with emoji and count
- **Animation:** Slides in when context is added
- **Updates:** Automatically after each upload

### **Chat Messages**
- **User messages:** Right-aligned, blue background
- **AI responses:** Left-aligned, white background
- **Formatting:** Supports markdown, bullet points, line breaks
- **Timestamps:** Included with each message

### **Error Handling**
- **No context:** Friendly message asking to upload first
- **No session:** Clear error with instructions
- **API errors:** Graceful degradation with retry option

---

## 🔧 Configuration

### **API Settings**
Located in `/root/.claude/settings.json`:
```json
{
  "env": {
    "ANTHROPIC_AUTH_TOKEN": "sk-W0XKg7g1plzSyYiw2BDImw",
    "ANTHROPIC_BASE_URL": "https://model-gateway.public.beta.myninja.ai"
  }
}
```

### **Models Used**
- **Transcription:** `openai/openai/gpt-4o-transcribe`
- **Analysis:** `ninja-cline-complex`
- **Chat Q&A:** `ninja-cline-complex`

### **Limits**
- **Max file size:** 25 MB
- **Conversation history:** Last 10 messages
- **Max tokens per response:** 1500
- **Session timeout:** None (persists indefinitely)

---

## 🚀 Example Usage

### **Example 1: Basic Q&A**
```
User: "What was the main topic of the call?"

AI: "Based on the transcription, the main topic was discussing 
the implementation of a new CRM system. The customer expressed 
interest in features like automated lead scoring and integration 
with their existing email platform."
```

### **Example 2: Specific Information**
```
User: "Did they mention any budget constraints?"

AI: "Yes, the customer mentioned they have a budget of $50,000 
for the initial implementation and are looking for a solution 
that can scale as their team grows from 10 to 50 users over 
the next year."
```

### **Example 3: Action Items**
```
User: "What are the next steps we agreed on?"

AI: "According to the call, the agreed next steps are:
• Send detailed pricing proposal by end of week
• Schedule technical demo for next Tuesday at 2 PM
• Provide case studies from similar-sized companies
• Connect customer with implementation team for timeline discussion"
```

### **Example 4: Follow-up**
```
User: "What was their timeline?"

AI: "They mentioned wanting to have the system fully implemented 
by Q3, with a soft launch in June and full rollout by August. 
They emphasized this timeline is critical due to their upcoming 
product launch in September."
```

---

## 🔐 Security & Privacy

### **Session Management**
- Session IDs are randomly generated UUIDs
- Stored only in browser localStorage
- Not transmitted to external services
- Can be cleared by user

### **Data Storage**
- Transcriptions stored locally on server
- No data sent to third parties except AI API
- Reports saved as JSON files
- Audio files stored in media library

### **API Security**
- API key stored in secure settings file
- Not exposed to frontend
- Rate limiting on API calls
- Error messages don't expose sensitive info

---

## 📈 Future Enhancements

### **Planned Features**
1. **Context Management Commands**
   - "Clear context" - remove all reports
   - "Show context" - list loaded calls
   - "Remove call X" - selective removal

2. **Smart Context Selection**
   - Auto-load most recent calls
   - Suggest relevant calls based on question
   - Limit context size for performance

3. **Export & Sharing**
   - Export Q&A sessions
   - Share insights with team
   - Generate summary reports

4. **Advanced Search**
   - Search across all transcriptions
   - Filter by date, sentiment, keywords
   - Aggregate insights

---

## 🐛 Troubleshooting

### **Issue: Context indicator not showing**
- **Solution:** Refresh page after upload, check browser console for errors

### **Issue: AI not answering questions**
- **Solution:** Verify audio was uploaded successfully, check reports section

### **Issue: Session lost after refresh**
- **Solution:** Check localStorage is enabled, clear cache and try again

### **Issue: Slow responses**
- **Solution:** Large transcriptions take longer, wait for response

---

## 📞 Support

For issues or questions:
- GitHub: https://github.com/NinjaTech-AI/agent-salesforce-transcriber
- Check logs: `supervisorctl tail -f 9000_python`
- Test endpoint: `python test_context_chat.py`

---

**Version:** 2.0.0  
**Last Updated:** February 16, 2025  
**Author:** SuperNinja AI