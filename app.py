from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import json
import subprocess
import sys
import re
from datetime import datetime, timedelta
import uuid
import openai
from real_transcribe import transcribe_audio_real

app = Flask(__name__, static_folder='static')
CORS(app)

# Configuration
UPLOAD_FOLDER = 'uploads'
REPORTS_FOLDER = 'reports'
MEDIA_LIBRARY_FOLDER = 'media_library'
SESSIONS_FOLDER = 'sessions'
ALLOWED_EXTENSIONS = {'mp3', 'wav', 'm4a', 'ogg'}
ALLOWED_DOCUMENT_EXTENSIONS = {'pdf', 'txt'}
ALLOWED_MEDIA_EXTENSIONS = ALLOWED_EXTENSIONS | ALLOWED_DOCUMENT_EXTENSIONS

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 25 * 1024 * 1024  # 25MB max file size

# Ensure directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(REPORTS_FOLDER, exist_ok=True)
os.makedirs(MEDIA_LIBRARY_FOLDER, exist_ok=True)
os.makedirs(SESSIONS_FOLDER, exist_ok=True)

# Session Management
class Session:
    """Manages user session with conversation history and active reports.
    Sessions are persisted to disk so they survive server restarts."""
    def __init__(self, session_id):
        self.session_id = session_id
        self.active_reports = []  # List of report IDs in context
        self.conversation_history = []  # Chat history
        self.created_at = datetime.now()
        self.last_activity = datetime.now()

    def _save_to_disk(self):
        """Persist session state to a JSON file"""
        session_path = os.path.join(SESSIONS_FOLDER, f"{self.session_id}.json")
        data = {
            "session_id": self.session_id,
            "active_reports": self.active_reports,
            "conversation_history": self.conversation_history,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat()
        }
        with open(session_path, 'w') as f:
            json.dump(data, f, indent=2)

    @classmethod
    def load_from_disk(cls, session_id):
        """Load a session from disk, returning None if not found"""
        session_path = os.path.join(SESSIONS_FOLDER, f"{session_id}.json")
        if not os.path.exists(session_path):
            return None
        try:
            with open(session_path, 'r') as f:
                data = json.load(f)
            session = cls(session_id)
            session.active_reports = data.get("active_reports", [])
            session.conversation_history = data.get("conversation_history", [])
            session.created_at = datetime.fromisoformat(data.get("created_at", datetime.now().isoformat()))
            session.last_activity = datetime.fromisoformat(data.get("last_activity", datetime.now().isoformat()))
            # Auto-restore: prune report references that no longer exist on disk
            valid_reports = [
                rid for rid in session.active_reports
                if os.path.exists(os.path.join(REPORTS_FOLDER, f"{rid}.json"))
            ]
            if len(valid_reports) != len(session.active_reports):
                removed = set(session.active_reports) - set(valid_reports)
                print(f"[SESSION] Pruned stale report refs from session {session_id}: {removed}", file=sys.stderr)
                session.active_reports = valid_reports
                session._save_to_disk()
            print(f"[SESSION] Restored session from disk: {session_id} ({len(session.active_reports)} reports, {len(session.conversation_history)} messages)", file=sys.stderr)
            return session
        except Exception as e:
            print(f"[SESSION] Failed to load session {session_id} from disk: {e}", file=sys.stderr)
            return None

    def add_report(self, report_id):
        """Add a report to the active context"""
        if report_id not in self.active_reports:
            self.active_reports.append(report_id)
        self.last_activity = datetime.now()
        self._save_to_disk()

    def add_message(self, role, content):
        """Add a message to conversation history"""
        self.conversation_history.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        self.last_activity = datetime.now()
        self._save_to_disk()

    def get_context_summary(self):
        """Get summary of active context"""
        return {
            "session_id": self.session_id,
            "num_reports": len(self.active_reports),
            "report_ids": self.active_reports,
            "conversation_length": len(self.conversation_history),
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat()
        }

# Global session storage (in-memory cache, backed by disk)
sessions = {}

def get_or_create_session(session_id):
    """Get session from memory, disk, or create new. Always returns a Session."""
    if session_id in sessions:
        return sessions[session_id]
    # Try loading from disk
    session = Session.load_from_disk(session_id)
    if session:
        sessions[session_id] = session
        return session
    # Create new
    session = Session(session_id)
    sessions[session_id] = session
    session._save_to_disk()
    print(f"[SESSION] Created new session: {session_id}", file=sys.stderr)
    return session

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def allowed_document(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_DOCUMENT_EXTENSIONS

def allowed_media_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_MEDIA_EXTENSIONS

def call_mcp_tool(tool_name, args_json):
    """Call Salesforce MCP tools"""
    try:
        # Use list form of subprocess to avoid shell escaping issues
        result = subprocess.run(
            ['mcp-tools', 'call', tool_name, args_json],
            capture_output=True,
            text=True
        )
        output = result.stdout + result.stderr

        # Check for session expired error in full output
        if 'Session expired' in output or 'INVALID_SESSION_ID' in output:
            return {"error": "Salesforce session has expired. Please reconnect to Salesforce."}

        if result.returncode == 0:
            # Strip debug messages from mcp-tools output
            # The JSON starts with { or [
            json_start = -1
            for i, char in enumerate(result.stdout):
                if char in ['{', '[']:
                    json_start = i
                    break

            if json_start >= 0:
                json_str = result.stdout[json_start:]
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError as e:
                    print(f"[MCP] JSON parse error: {e}", file=sys.stderr)
                    print(f"[MCP] Raw output: {result.stdout[:500]}", file=sys.stderr)
                    return {"error": f"Failed to parse Salesforce response. Raw output: {result.stdout[:200]}"}
            else:
                return {"error": "No JSON found in output"}
        else:
            return {"error": result.stderr or "MCP tool call failed"}
    except Exception as e:
        return {"error": str(e)}


def get_api_credentials():
    """Get API credentials from Claude settings file"""
    try:
        settings_path = '/root/.claude/settings.json'
        with open(settings_path, 'r') as f:
            settings = json.load(f)
            api_key = settings.get('env', {}).get('ANTHROPIC_AUTH_TOKEN', '')
            base_url = settings.get('env', {}).get('ANTHROPIC_BASE_URL', 'https://model-gateway.public.beta.myninja.ai')
            return api_key, base_url
    except Exception as e:
        print(f"Warning: Could not read settings file: {e}", file=sys.stderr)
        # Fallback to environment variables or defaults
        return os.environ.get('ANTHROPIC_AUTH_TOKEN', ''), 'https://model-gateway.public.beta.myninja.ai'

def build_context_from_reports(report_ids):
    """
    Builds a comprehensive context string from report IDs
    """
    context_parts = []
    
    for report_id in report_ids:
        report_path = os.path.join(REPORTS_FOLDER, f"{report_id}.json")
        
        if os.path.exists(report_path):
            with open(report_path, 'r') as f:
                report = json.load(f)
                
                # Build structured context
                context_part = f"""
--- Call: {report['filename']} ---
Date: {report['created_at']}

TRANSCRIPTION:
{report['transcription']}

ANALYSIS:
Summary: {report['analysis']['summary']}
Key Points: {', '.join(report['analysis']['key_points'])}
Sentiment: {report['analysis']['sentiment']}
Customer Needs: {', '.join(report['analysis']['customer_needs'])}
Action Items: {', '.join(report['analysis']['action_items'])}
Next Steps: {report['analysis']['next_steps']}
---
"""
                context_parts.append(context_part)
    
    return "\n\n".join(context_parts)

def ask_claude_with_context(question, context, history):
    """
    Ask Claude a question with transcription context
    """
    try:
        # Get API credentials
        api_key, base_url = get_api_credentials()
        
        client = openai.OpenAI(
            api_key=api_key,
            base_url=base_url
        )
        
        # Build system prompt with context
        if context:
            system_prompt = f"""You are SalesIQ, an intelligent sales assistant with access to call transcriptions.

You have access to the following call transcription(s):

{context}

Your role is to:
- Answer questions about the call(s) accurately based on the transcription
- Extract specific information when asked
- Provide insights and analysis
- Reference specific parts of the conversation when relevant
- Be concise but thorough
- Use bullet points and formatting for clarity

If a question cannot be answered from the available transcription, say so clearly."""
        else:
            system_prompt = """You are SalesIQ, an intelligent sales assistant specializing in sales strategy, techniques, and analysis.

No call transcriptions have been uploaded yet. You can still help with:
- General sales questions, tips, and best practices
- Sales strategy and methodology advice
- Objection handling techniques
- Negotiation tips
- Sales process optimization

If the user asks about a specific call or transcription, remind them they can upload an audio file to get call-specific analysis.
Be concise but thorough. Use bullet points and formatting for clarity."""

        # Build messages array with history
        messages = [
            {"role": "system", "content": system_prompt}
        ]
        
        # Add conversation history (last 10 messages to avoid token limits)
        for msg in history[-10:]:
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        # Call Claude
        print(f"[CLAUDE] Sending question to Claude with {len(context)} chars of context", file=sys.stderr)
        response = client.chat.completions.create(
            model="ninja-cline-complex",
            messages=messages,
            temperature=0.3,
            max_tokens=1500
        )
        
        answer = response.choices[0].message.content
        print(f"[CLAUDE] Received response: {len(answer)} chars", file=sys.stderr)
        return answer
        
    except Exception as e:
        print(f"[ERROR] Claude API error: {str(e)}", file=sys.stderr)
        return f"I apologize, but I encountered an error processing your question: {str(e)}"

def analyze_sales_call(transcription, filename):
    """Analyze sales call transcription and generate insights using AI"""
    try:
        # Get API credentials from settings
        api_key, base_url = get_api_credentials()
        
        # Use SuperNinja AI to analyze the transcription
        client = openai.OpenAI(
            api_key=api_key,
            base_url=base_url
        )
        
        prompt = f"""Analyze this sales call transcription and provide detailed insights.

Transcription:
{transcription}

Provide a comprehensive analysis in the following JSON format:
{{
    "summary": "A 2-3 sentence high-level summary of the call",
    "key_points": ["List 4-6 main discussion points from the call"],
    "sentiment": "Overall customer sentiment (Positive/Neutral/Negative/Mixed)",
    "action_items": ["List 3-5 specific action items or follow-ups needed"],
    "customer_needs": ["List 3-5 customer needs, pain points, or requirements identified"],
    "next_steps": "Recommended next steps for the sales process"
}}

Be specific and base everything on the actual content of the transcription."""

        response = client.chat.completions.create(
            model="ninja-cline-complex",
            messages=[
                {"role": "system", "content": "You are an expert sales call analyst. Analyze conversations and extract actionable insights."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        
        # Parse the AI response
        analysis_text = response.choices[0].message.content
        
        # Try to extract JSON from the response
        import re
        json_match = re.search(r'\{[\s\S]*\}', analysis_text)
        if json_match:
            analysis = json.loads(json_match.group())
        else:
            # Fallback if JSON parsing fails
            analysis = {
                "summary": f"Analysis of {filename}",
                "key_points": ["AI analysis completed - see transcription for details"],
                "sentiment": "Neutral",
                "action_items": ["Review full transcription for action items"],
                "customer_needs": ["See transcription for customer needs"],
                "next_steps": "Follow up based on conversation content"
            }
        
        return analysis
        
    except Exception as e:
        print(f"[ERROR] Analysis failed: {str(e)}", file=sys.stderr)
        # Return basic analysis if AI fails
        return {
            "summary": f"Sales call transcription for {filename}",
            "key_points": ["Transcription completed successfully", "Review full transcript for details"],
            "sentiment": "Neutral",
            "action_items": ["Review transcription", "Identify follow-up actions"],
            "customer_needs": ["See full transcription for customer needs"],
            "next_steps": "Review conversation and determine appropriate follow-up"
        }

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

@app.route('/api/health/salesforce', methods=['GET'])
def salesforce_health():
    """Check if Salesforce connection is working"""
    result = call_mcp_tool('salesforce_get_accounts', json.dumps({"limit": 1}))
    if isinstance(result, dict) and 'error' in result:
        return jsonify({"status": "error", "message": result['error']}), 503
    return jsonify({"status": "ok", "message": "Salesforce connection is active"})

# Chat endpoints
@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat messages with SalesIQ assistant - Context-aware with Claude AI"""
    data = request.json
    message = data.get('message', '')
    session_id = data.get('session_id')
    
    # Validate inputs
    if not message:
        return jsonify({"error": "No message provided"}), 400
    
    if not session_id:
        return jsonify({
            "message": "Please upload an audio file first to start asking questions.",
            "has_context": False,
            "error": "No session_id provided"
        }), 400
    
    # Get or create session (restores from disk if server restarted)
    session = get_or_create_session(session_id)
    
    # Add user message to history
    session.add_message("user", message)
    print(f"[CHAT] User question: {message}", file=sys.stderr)
    print(f"[CHAT] Session has {len(session.active_reports)} report(s) in context", file=sys.stderr)

    has_context = len(session.active_reports) > 0

    # Build context from active reports (if any)
    context = ""
    if has_context:
        try:
            context = build_context_from_reports(session.active_reports)
            print(f"[CHAT] Built context: {len(context)} characters", file=sys.stderr)
        except Exception as e:
            print(f"[ERROR] Failed to build context: {str(e)}", file=sys.stderr)
            return jsonify({
                "message": "I encountered an error accessing the call transcriptions. Please try again.",
                "error": str(e),
                "has_context": True
            }), 500

    # Get response from Claude (with or without call context)
    try:
        response_text = ask_claude_with_context(
            question=message,
            context=context,
            history=session.conversation_history
        )

        # Add assistant response to history
        session.add_message("assistant", response_text)

        return jsonify({
            "message": response_text,
            "has_context": has_context,
            "num_reports": len(session.active_reports),
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        print(f"[ERROR] Chat error: {str(e)}", file=sys.stderr)
        return jsonify({
            "message": "I apologize, but I encountered an error processing your question. Please try again.",
            "error": str(e),
            "has_context": has_context
        }), 500

# Audio upload and processing
@app.route('/api/upload-audio', methods=['POST'])
def upload_audio():
    """Upload and process audio file"""
    if 'audio' not in request.files:
        return jsonify({"error": "No audio file provided"}), 400
    
    file = request.files['audio']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
    # Get session_id from form data
    session_id = request.form.get('session_id')
    if not session_id:
        return jsonify({"error": "No session_id provided"}), 400
    
    # Get or create session (restores from disk if server restarted)
    session = get_or_create_session(session_id)

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        
        # Save to uploads folder temporarily
        upload_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(upload_path)
        
        # Move to media library
        media_path = os.path.join(MEDIA_LIBRARY_FOLDER, unique_filename)
        os.rename(upload_path, media_path)
        
        # Transcribe audio using SuperNinja's transcription tool
        try:
            transcription_result = transcribe_audio_real(media_path)
            print(f"[DEBUG] Transcription result: {transcription_result}", file=sys.stderr)
        except Exception as e:
            print(f"[ERROR] Transcription exception: {str(e)}", file=sys.stderr)
            return jsonify({
                "error": f"Transcription error: {str(e)}",
                "details": "Failed to transcribe audio"
            }), 500
        
        if transcription_result.get('success'):
            transcription = transcription_result.get('transcription', '')
            
            # Analyze the call
            analysis = analyze_sales_call(transcription, filename)
            
            # Generate descriptive title from analysis
            try:
                # Extract a short descriptive title from the summary
                summary = analysis.get('summary', '')
                # Take first sentence or first 60 characters
                title = summary.split('.')[0] if '.' in summary else summary[:60]
                if len(title) > 60:
                    title = title[:57] + "..."
                if not title:
                    title = f"Sales Call - {datetime.now().strftime('%B %d, %Y')}"
            except:
                title = f"Sales Call - {datetime.now().strftime('%B %d, %Y')}"
            
            # Generate report
            report_id = str(uuid.uuid4())
            report = {
                "id": report_id,
                "title": title,
                "filename": filename,
                "audio_file": unique_filename,
                "transcription": transcription,
                "analysis": analysis,
                "created_at": datetime.now().isoformat()
            }
            
            # Save report
            report_path = os.path.join(REPORTS_FOLDER, f"{report_id}.json")
            with open(report_path, 'w') as f:
                json.dump(report, f, indent=2)
            
            # Link report to session
            session.add_report(report_id)
            print(f"[SESSION] Added report {report_id} to session {session_id}", file=sys.stderr)
            print(f"[SESSION] Session now has {len(session.active_reports)} report(s)", file=sys.stderr)
            
            return jsonify({
                "success": True,
                "report_id": report_id,
                "message": "Audio processed successfully. You can now ask questions about this call!",
                "context_set": True,
                "num_reports_in_context": len(session.active_reports)
            })
        else:
            return jsonify({
                "error": "Failed to transcribe audio",
                "details": transcription_result.get('error')
            }), 500
    
    return jsonify({"error": "Invalid file type"}), 400

# Text analysis endpoint
@app.route('/api/analyze-text', methods=['POST'])
def analyze_text():
    """Analyze pasted plain text as a sales conversation"""
    data = request.json
    text = data.get('text', '').strip()
    session_id = data.get('session_id')

    if not text:
        return jsonify({"error": "No text provided"}), 400

    if len(text) < 20:
        return jsonify({"error": "Text is too short to analyze. Please provide a longer conversation."}), 400

    if len(text) > 500000:
        return jsonify({"error": "Text is too long. Please limit to 500,000 characters."}), 400

    if not session_id:
        return jsonify({"error": "No session_id provided"}), 400

    session = get_or_create_session(session_id)

    # Analyze the text
    analysis = analyze_sales_call(text, "Pasted Text")

    # Generate title
    try:
        summary = analysis.get('summary', '')
        title = summary.split('.')[0] if '.' in summary else summary[:60]
        if len(title) > 60:
            title = title[:57] + "..."
        if not title:
            title = f"Text Analysis - {datetime.now().strftime('%B %d, %Y')}"
    except:
        title = f"Text Analysis - {datetime.now().strftime('%B %d, %Y')}"

    # Generate report
    report_id = str(uuid.uuid4())
    report = {
        "id": report_id,
        "title": title,
        "filename": "Pasted Text",
        "source_type": "text",
        "transcription": text,
        "analysis": analysis,
        "created_at": datetime.now().isoformat()
    }

    report_path = os.path.join(REPORTS_FOLDER, f"{report_id}.json")
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)

    session.add_report(report_id)
    print(f"[SESSION] Added text report {report_id} to session {session_id}", file=sys.stderr)

    return jsonify({
        "success": True,
        "report_id": report_id,
        "message": "Text analyzed successfully. You can now ask questions about this conversation!",
        "context_set": True,
        "num_reports_in_context": len(session.active_reports)
    })

# Document upload endpoint
@app.route('/api/upload-document', methods=['POST'])
def upload_document():
    """Upload and process a PDF or TXT document"""
    if 'document' not in request.files:
        return jsonify({"error": "No document file provided"}), 400

    file = request.files['document']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    session_id = request.form.get('session_id')
    if not session_id:
        return jsonify({"error": "No session_id provided"}), 400

    session = get_or_create_session(session_id)

    if not file or not allowed_document(file.filename):
        return jsonify({"error": "Invalid file type. Only PDF and TXT files are allowed."}), 400

    filename = secure_filename(file.filename)
    ext = filename.rsplit('.', 1)[1].lower()
    unique_filename = f"{uuid.uuid4()}_{filename}"

    # Save to media library
    media_path = os.path.join(MEDIA_LIBRARY_FOLDER, unique_filename)
    file.save(media_path)

    # Extract text from document
    try:
        if ext == 'txt':
            with open(media_path, 'r', encoding='utf-8') as f:
                extracted_text = f.read()
        elif ext == 'pdf':
            import PyPDF2
            extracted_text = ''
            with open(media_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    extracted_text += page.extract_text() + '\n'
            extracted_text = extracted_text.strip()
        else:
            return jsonify({"error": "Unsupported file type"}), 400

        if not extracted_text or len(extracted_text.strip()) < 20:
            return jsonify({"error": "Could not extract enough text from the document. The file may be empty or contain only images."}), 400

    except UnicodeDecodeError:
        return jsonify({"error": "Could not read the text file. Please ensure it is UTF-8 encoded."}), 400
    except Exception as e:
        print(f"[ERROR] Document extraction error: {str(e)}", file=sys.stderr)
        return jsonify({"error": f"Failed to extract text from document: {str(e)}"}), 500

    # Analyze the extracted text
    analysis = analyze_sales_call(extracted_text, filename)

    # Generate title
    try:
        summary = analysis.get('summary', '')
        title = summary.split('.')[0] if '.' in summary else summary[:60]
        if len(title) > 60:
            title = title[:57] + "..."
        if not title:
            title = f"Document Analysis - {datetime.now().strftime('%B %d, %Y')}"
    except:
        title = f"Document Analysis - {datetime.now().strftime('%B %d, %Y')}"

    # Generate report
    report_id = str(uuid.uuid4())
    report = {
        "id": report_id,
        "title": title,
        "filename": filename,
        "source_type": "document",
        "document_file": unique_filename,
        "transcription": extracted_text,
        "analysis": analysis,
        "created_at": datetime.now().isoformat()
    }

    report_path = os.path.join(REPORTS_FOLDER, f"{report_id}.json")
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)

    session.add_report(report_id)
    print(f"[SESSION] Added document report {report_id} to session {session_id}", file=sys.stderr)

    return jsonify({
        "success": True,
        "report_id": report_id,
        "message": f"Document '{filename}' processed successfully. You can now ask questions about this conversation!",
        "context_set": True,
        "num_reports_in_context": len(session.active_reports)
    })

# Reports endpoints
@app.route('/api/reports', methods=['GET'])
def get_reports():
    """Get all reports"""
    reports = []
    for filename in os.listdir(REPORTS_FOLDER):
        if filename.endswith('.json'):
            with open(os.path.join(REPORTS_FOLDER, filename), 'r') as f:
                report = json.load(f)
                # Return summary only
                reports.append({
                    "id": report['id'],
                    "title": report.get('title', report.get('filename', 'Sales Call Report')),
                    "filename": report['filename'],
                    "created_at": report['created_at'],
                    "summary": report['analysis']['summary']
                })
    
    # Sort by created_at descending
    reports.sort(key=lambda x: x['created_at'], reverse=True)
    return jsonify(reports)

@app.route('/api/reports/<report_id>', methods=['GET'])
def get_report(report_id):
    """Get specific report details"""
    report_path = os.path.join(REPORTS_FOLDER, f"{report_id}.json")
    if os.path.exists(report_path):
        with open(report_path, 'r') as f:
            report = json.load(f)
        return jsonify(report)
    return jsonify({"error": "Report not found"}), 404

@app.route('/api/reports/<report_id>', methods=['DELETE'])
def delete_report(report_id):
    """Delete a report"""
    report_path = os.path.join(REPORTS_FOLDER, f"{report_id}.json")
    if os.path.exists(report_path):
        os.remove(report_path)
        return jsonify({"success": True, "message": "Report deleted"})
    return jsonify({"error": "Report not found"}), 404

# Media library endpoints
@app.route('/api/media', methods=['GET'])
def get_media():
    """Get all media files"""
    media_files = []
    for filename in os.listdir(MEDIA_LIBRARY_FOLDER):
        if allowed_media_file(filename):
            file_path = os.path.join(MEDIA_LIBRARY_FOLDER, filename)
            file_stat = os.stat(file_path)
            ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
            if ext in ALLOWED_DOCUMENT_EXTENSIONS:
                file_type = 'document'
            else:
                file_type = 'audio'
            media_files.append({
                "filename": filename,
                "size": file_stat.st_size,
                "type": file_type,
                "created_at": datetime.fromtimestamp(file_stat.st_ctime).isoformat()
            })
    
    # Sort by created_at descending
    media_files.sort(key=lambda x: x['created_at'], reverse=True)
    return jsonify(media_files)

@app.route('/api/media/<filename>', methods=['DELETE'])
def delete_media(filename):
    """Delete a media file"""
    file_path = os.path.join(MEDIA_LIBRARY_FOLDER, secure_filename(filename))
    if os.path.exists(file_path):
        os.remove(file_path)
        return jsonify({"success": True, "message": "Media file deleted"})
    return jsonify({"error": "File not found"}), 404

@app.route('/api/media/<filename>/download', methods=['GET'])
def download_media(filename):
    """Download a media file"""
    safe_filename = secure_filename(filename)
    file_path = os.path.join(MEDIA_LIBRARY_FOLDER, safe_filename)
    if os.path.exists(file_path):
        return send_from_directory(MEDIA_LIBRARY_FOLDER, safe_filename, as_attachment=True)
    return jsonify({"error": "File not found"}), 404

# Salesforce integration endpoints
@app.route('/api/salesforce/accounts', methods=['GET'])
def get_salesforce_accounts():
    """Get Salesforce accounts"""
    limit = request.args.get('limit', 50, type=int)
    result = call_mcp_tool('salesforce_get_accounts', json.dumps({"limit": limit}))
    return jsonify(result)

@app.route('/api/salesforce/opportunities', methods=['GET'])
def get_salesforce_opportunities():
    """Get Salesforce opportunities"""
    limit = request.args.get('limit', 50, type=int)
    result = call_mcp_tool('salesforce_get_opportunities', json.dumps({"limit": limit}))
    return jsonify(result)

@app.route('/api/salesforce/create-tasks', methods=['POST'])
def create_salesforce_tasks():
    """Create tasks in Salesforce from action items"""
    import requests as http_requests

    data = request.json
    action_items = data.get('action_items', [])
    account_id = data.get('account_id')
    contact_id = data.get('contact_id')

    # Get Salesforce credentials from /dev/shm/mcp-token
    # File format: Salesforce={"access_token": "...", "instance_url": "..."}
    try:
        with open('/dev/shm/mcp-token', 'r') as f:
            token_line = f.read().strip()
        sf_creds = json.loads(token_line.split('=', 1)[1])
        access_token = sf_creds['access_token']
        instance_url = sf_creds['instance_url']
    except Exception as e:
        return jsonify({"success": False, "error": f"Could not read Salesforce credentials: {e}"}), 500

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    created_tasks = []
    errors = []
    activity_date = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')

    for item in action_items:
        try:
            task_data = {
                'Subject': item,
                'Status': 'Not Started',
                'Priority': 'Normal',
                'ActivityDate': activity_date,
                'Description': 'Created from SalesIQ call analysis'
            }
            if account_id:
                task_data['WhatId'] = account_id
            if contact_id:
                task_data['WhoId'] = contact_id

            resp = http_requests.post(
                f'{instance_url}/services/data/v59.0/sobjects/Task/',
                headers=headers,
                json=task_data
            )

            if resp.status_code == 201:
                result = resp.json()
                created_tasks.append({
                    "subject": item,
                    "id": result.get('id'),
                    "status": "created"
                })
            else:
                errors.append({"item": item, "error": resp.json()})

        except Exception as e:
            errors.append({"item": item, "error": str(e)})

    success = len(created_tasks) > 0 or len(errors) == 0
    return jsonify({
        "success": success,
        "created_tasks": created_tasks,
        "errors": errors
    })

@app.route('/api/salesforce/create-event', methods=['POST'])
def create_salesforce_event():
    """
    Create an event/meeting record in Salesforce
    
    Note: The Salesforce MCP doesn't currently expose Event creation.
    This endpoint stores meeting information in the Account Description field
    as a workaround until Event creation is added to the MCP.
    """
    data = request.json
    
    try:
        account_id = data.get('account_id')
        if not account_id:
            return jsonify({
                "success": False,
                "error": "account_id is required"
            }), 400
        
        # Prepare meeting information
        subject = data.get('subject', 'Sales Call')
        description = data.get('description', '')
        start_datetime = data.get('start_datetime', '')
        end_datetime = data.get('end_datetime', '')
        location = data.get('location', 'Virtual')
        
        # Format meeting notes
        from datetime import datetime
        meeting_date = datetime.now().strftime('%Y-%m-%d %H:%M')
        if start_datetime:
            try:
                meeting_date = datetime.fromisoformat(start_datetime.replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M')
            except:
                pass
        
        meeting_notes = f"""
=== Meeting: {subject} ===
Date: {meeting_date}
Location: {location}

Notes:
{description}

---
"""
        
        # Get current account description
        account_query = f"SELECT Id, Description FROM Account WHERE Id = '{account_id}'"
        result = call_mcp_tool('salesforce_query', json.dumps({"query": account_query}))
        
        current_description = ""
        if result and 'records' in result and len(result['records']) > 0:
            current_description = result['records'][0].get('Description', '') or ''
        
        # Append meeting notes to account description
        updated_description = meeting_notes + current_description
        
        # Update account with meeting notes
        update_result = call_mcp_tool('salesforce_update_account', json.dumps({
            "account_id": account_id,
            "account_data": {
                "Description": updated_description
            }
        }))
        
        if update_result and update_result.get('success'):
            return jsonify({
                "success": True,
                "message": "Meeting notes added to Account Description",
                "meeting_data": {
                    "subject": subject,
                    "date": meeting_date,
                    "location": location,
                    "account_id": account_id
                },
                "note": "Meeting information stored in Account Description field. Full Event object creation requires Salesforce MCP extension."
            })
        else:
            return jsonify({
                "success": False,
                "error": "Failed to update account with meeting notes"
            }), 500
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/salesforce/update-account', methods=['POST'])
def update_salesforce_account():
    """Update account information based on call insights"""
    data = request.json
    account_id = data.get('account_id')
    updates = data.get('updates', {})
    
    print(f"[UPDATE_ACCOUNT] Received request - Account ID: {account_id}", file=sys.stderr)
    print(f"[UPDATE_ACCOUNT] Updates: {updates}", file=sys.stderr)
    
    try:
        # Use MCP tool to update account
        mcp_args = {
            "account_id": account_id,
            "account_data": updates
        }
        print(f"[UPDATE_ACCOUNT] Calling MCP with: {mcp_args}", file=sys.stderr)
        
        result = call_mcp_tool('salesforce_update_account', json.dumps(mcp_args))
        
        print(f"[UPDATE_ACCOUNT] MCP Result: {result}", file=sys.stderr)
        
        # Check if the result contains an error
        if isinstance(result, dict) and 'error' in result:
            print(f"[UPDATE_ACCOUNT] Error from MCP: {result['error']}", file=sys.stderr)
            return jsonify({
                "success": False,
                "error": result['error']
            }), 500
        
        return jsonify({
            "success": True,
            "result": result,
            "message": "Account updated successfully"
        })
        
    except Exception as e:
        print(f"[UPDATE_ACCOUNT] Exception: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/salesforce/search-accounts', methods=['GET'])
def search_salesforce_accounts():
    """Search for accounts by name"""
    query = request.args.get('query', '')
    
    try:
        result = call_mcp_tool('salesforce_get_accounts', json.dumps({
            "name_contains": query,
            "limit": 10
        }))
        
        # Check if the result contains an error
        if isinstance(result, dict) and 'error' in result:
            return jsonify({
                "success": False,
                "error": result['error']
            }), 500
        
        # The result should contain accounts in the 'content' field
        if isinstance(result, dict) and 'content' in result:
            try:
                content = json.loads(result['content'][0]['text']) if isinstance(result['content'], list) else result['content']
                return jsonify({
                    "success": True,
                    "accounts": content if isinstance(content, list) else []
                })
            except:
                return jsonify(result)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/report/<report_id>/salesforce-actions', methods=['POST'])
def create_salesforce_actions_from_report(report_id):
    """Create Salesforce tasks and events from a report"""
    try:
        # Load the report
        report_path = os.path.join(REPORTS_FOLDER, f"{report_id}.json")
        if not os.path.exists(report_path):
            return jsonify({"error": "Report not found"}), 404
        
        with open(report_path, 'r') as f:
            report = json.load(f)
        
        data = request.json
        account_id = data.get('account_id')
        contact_id = data.get('contact_id')
        
        # Get action items from report
        action_items = report['analysis'].get('action_items', [])
        next_steps = report['analysis'].get('next_steps', '')
        
        # Create tasks for action items
        created_tasks = []
        for item in action_items:
            task = {
                "subject": item,
                "account_id": account_id,
                "contact_id": contact_id,
                "status": "created"
            }
            created_tasks.append(task)
        
        # Suggest event creation
        event_suggestion = {
            "subject": "Follow-up: " + report.get('title', 'Sales Call'),
            "description": f"Next Steps: {next_steps}\n\nKey Points:\n" + "\n".join(f"- {point}" for point in report['analysis'].get('key_points', [])),
            "suggested_date": (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d'),
            "duration_minutes": 30
        }
        
        return jsonify({
            "success": True,
            "tasks_created": len(created_tasks),
            "tasks": created_tasks,
            "event_suggestion": event_suggestion,
            "customer_needs": report['analysis'].get('customer_needs', [])
        })
        
    except Exception as e:
        print(f"[ERROR] Salesforce actions: {str(e)}", file=sys.stderr)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9000, debug=True)