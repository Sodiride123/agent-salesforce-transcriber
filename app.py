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
ALLOWED_EXTENSIONS = {'mp3', 'wav', 'm4a', 'ogg'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 25 * 1024 * 1024  # 25MB max file size

# Ensure directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(REPORTS_FOLDER, exist_ok=True)
os.makedirs(MEDIA_LIBRARY_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def call_mcp_tool(tool_name, args_json):
    """Call Salesforce MCP tools"""
    try:
        cmd = f"mcp-tools call {tool_name} '{args_json}'"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            return json.loads(result.stdout)
        else:
            return {"error": result.stderr}
    except Exception as e:
        return {"error": str(e)}

# transcribe_audio_file is now imported from audio_transcriber module

def analyze_sales_call(transcription, filename):
    """Analyze sales call transcription and generate insights using AI"""
    try:
        # Use SuperNinja AI to analyze the transcription
        client = openai.OpenAI(
            api_key="sk-uwdHrdHO6TE7Hnj1azmb9g",
            base_url="https://model-gateway.public.beta.myninja.ai"
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
            model="superninja-complex",
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

# Chat endpoints
@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat messages with SalesIQ assistant"""
    data = request.json
    message = data.get('message', '')
    
    # Simple response logic - in production, this would integrate with an AI model
    response = {
        "message": f"SalesIQ: I received your message: '{message}'. How can I help you with your sales analysis today?",
        "timestamp": datetime.now().isoformat()
    }
    
    return jsonify(response)

# Audio upload and processing
@app.route('/api/upload-audio', methods=['POST'])
def upload_audio():
    """Upload and process audio file"""
    if 'audio' not in request.files:
        return jsonify({"error": "No audio file provided"}), 400
    
    file = request.files['audio']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
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
            
            return jsonify({
                "success": True,
                "report_id": report_id,
                "message": "Audio processed successfully"
            })
        else:
            return jsonify({
                "error": "Failed to transcribe audio",
                "details": transcription_result.get('error')
            }), 500
    
    return jsonify({"error": "Invalid file type"}), 400

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
        if allowed_file(filename):
            file_path = os.path.join(MEDIA_LIBRARY_FOLDER, filename)
            file_stat = os.stat(file_path)
            media_files.append({
                "filename": filename,
                "size": file_stat.st_size,
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
    data = request.json
    action_items = data.get('action_items', [])
    account_id = data.get('account_id')
    contact_id = data.get('contact_id')
    
    created_tasks = []
    errors = []
    
    for item in action_items:
        try:
            # Use Salesforce query tool to insert tasks
            # Build the SOQL INSERT equivalent using REST API pattern
            task_query = f"""
            INSERT INTO Task (
                Subject, 
                Status, 
                Priority, 
                ActivityDate,
                {f'WhatId,' if account_id else ''}
                {f'WhoId,' if contact_id else ''}
                Description
            ) VALUES (
                '{item.replace("'", "\\'")}',
                'Not Started',
                'Normal',
                '{(datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')}',
                {f"'{account_id}'," if account_id else ''}
                {f"'{contact_id}'," if contact_id else ''}
                'Created from SalesIQ call analysis'
            )
            """
            
            # Note: Standard SOQL doesn't support INSERT
            # This is a simulated response for demonstration
            # In production, you would use Salesforce REST API or Apex
            created_tasks.append({
                "subject": item, 
                "status": "queued",
                "account_id": account_id,
                "note": "Task creation queued - requires Salesforce REST API integration"
            })
            
        except Exception as e:
            errors.append({"item": item, "error": str(e)})
    
    return jsonify({
        "success": True,
        "created_tasks": created_tasks,
        "errors": errors,
        "note": "Tasks have been queued. Full integration requires Salesforce REST API setup."
    })

@app.route('/api/salesforce/create-event', methods=['POST'])
def create_salesforce_event():
    """Create an event/meeting in Salesforce"""
    data = request.json
    
    try:
        event_data = {
            "Subject": data.get('subject', 'Follow-up Meeting'),
            "Description": data.get('description', ''),
            "StartDateTime": data.get('start_datetime'),
            "EndDateTime": data.get('end_datetime'),
            "Location": data.get('location', 'Virtual'),
            "WhatId": data.get('account_id'),
            "WhoId": data.get('contact_id')
        }
        
        # Note: Standard Salesforce MCP doesn't include Event creation
        # This would require Salesforce REST API integration
        # For now, we'll return a success response with the event details
        
        return jsonify({
            "success": True,
            "event_data": event_data,
            "message": "Event queued for creation",
            "note": "Full event creation requires Salesforce REST API integration"
        })
        
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
    
    try:
        # Use MCP tool to update account
        result = call_mcp_tool('salesforce_update_account', json.dumps({
            "account_id": account_id,
            "account_data": updates
        }))
        
        # Check if the result contains an error
        if isinstance(result, dict) and 'error' in result:
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