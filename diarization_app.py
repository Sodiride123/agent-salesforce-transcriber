"""
Speaker Diarization Application
Combines SuperNinja transcription with AI-powered speaker identification
Port: 9001
"""

from flask import Flask, request, jsonify, send_from_directory, render_template_string
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os
import json
import sys
from datetime import datetime
import uuid
import openai

app = Flask(__name__)
CORS(app)

# Configuration
UPLOAD_FOLDER = 'diarization_uploads'
RESULTS_FOLDER = 'diarization_results'
ALLOWED_EXTENSIONS = {'mp3', 'wav', 'm4a', 'ogg', 'webm'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 25 * 1024 * 1024  # 25MB

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULTS_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def transcribe_with_ninja(file_path):
    """Transcribe audio using SuperNinja transcription"""
    try:
        client = openai.OpenAI(
            api_key="sk-uwdHrdHO6TE7Hnj1azmb9g",
            base_url="https://model-gateway.public.beta.myninja.ai"
        )
        
        with open(file_path, "rb") as audio_file:
            response = client.audio.transcriptions.create(
                model="superninja-transcribe",
                file=audio_file,
                response_format="text"
            )
        
        transcription = response if isinstance(response, str) else response.text
        return {"success": True, "transcription": transcription}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def add_speaker_labels_with_ai(transcription):
    """Use AI to identify and label speakers in the transcription"""
    try:
        client = openai.OpenAI(
            api_key="sk-uwdHrdHO6TE7Hnj1azmb9g",
            base_url="https://model-gateway.public.beta.myninja.ai"
        )
        
        prompt = f"""You are a conversation analyst. Analyze this sales call transcription and identify the different speakers.

Add speaker labels to the transcription. Format each speaker's dialogue as:
[Speaker 1]: their dialogue
[Speaker 2]: their dialogue

Rules:
1. Identify speaker changes based on conversation flow and context
2. Use [Speaker 1] for the first person who speaks
3. Use [Speaker 2] for the second person
4. If there are more speakers, use [Speaker 3], [Speaker 4], etc.
5. Group consecutive statements from the same speaker together
6. Add line breaks between different speakers
7. Preserve the exact words from the transcription

Transcription to analyze:
{transcription}

Return ONLY the formatted transcription with speaker labels, nothing else."""

        response = client.chat.completions.create(
            model="superninja-complex",
            messages=[
                {"role": "system", "content": "You are an expert at analyzing conversations and identifying speakers."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        
        labeled_transcription = response.choices[0].message.content
        return {"success": True, "transcription": labeled_transcription}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def analyze_speakers(labeled_transcription):
    """Analyze the conversation to identify speaker roles"""
    try:
        client = openai.OpenAI(
            api_key="sk-uwdHrdHO6TE7Hnj1azmb9g",
            base_url="https://model-gateway.public.beta.myninja.ai"
        )
        
        prompt = f"""Analyze this labeled sales call transcription and identify who each speaker is.

Transcription:
{labeled_transcription}

Provide:
1. Speaker 1 role (e.g., "Sales Representative", "Customer", etc.)
2. Speaker 2 role
3. Brief description of each speaker's communication style
4. Key topics discussed by each speaker

Format as JSON:
{{
    "speakers": [
        {{"id": "Speaker 1", "role": "...", "style": "...", "topics": ["..."]}},
        {{"id": "Speaker 2", "role": "...", "style": "...", "topics": ["..."]}}
    ]
}}"""

        response = client.chat.completions.create(
            model="superninja-complex",
            messages=[
                {"role": "system", "content": "You are an expert at analyzing sales conversations."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        
        analysis = response.choices[0].message.content
        # Try to parse as JSON
        try:
            analysis_json = json.loads(analysis)
            return {"success": True, "analysis": analysis_json}
        except:
            return {"success": True, "analysis": {"raw": analysis}}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

# HTML Template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Speaker Diarization App</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 40px 20px;
        }
        
        .container {
            max-width: 900px;
            margin: 0 auto;
        }
        
        .header {
            text-align: center;
            color: white;
            margin-bottom: 40px;
        }
        
        .header h1 {
            font-size: 48px;
            margin-bottom: 10px;
        }
        
        .header p {
            font-size: 18px;
            opacity: 0.9;
        }
        
        .card {
            background: white;
            border-radius: 16px;
            padding: 40px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            margin-bottom: 30px;
        }
        
        .upload-area {
            border: 3px dashed #667eea;
            border-radius: 12px;
            padding: 60px 40px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        .upload-area:hover {
            border-color: #764ba2;
            background: #f8f9ff;
        }
        
        .upload-area.dragover {
            border-color: #764ba2;
            background: #f0f0ff;
        }
        
        .upload-icon {
            font-size: 64px;
            margin-bottom: 20px;
        }
        
        .upload-text {
            font-size: 20px;
            color: #333;
            margin-bottom: 10px;
        }
        
        .upload-hint {
            font-size: 14px;
            color: #666;
        }
        
        #fileInput {
            display: none;
        }
        
        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 16px 40px;
            border-radius: 30px;
            font-size: 18px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
            margin-top: 20px;
        }
        
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 30px rgba(102, 126, 234, 0.4);
        }
        
        .btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: none;
        }
        
        .status {
            margin-top: 30px;
            padding: 20px;
            border-radius: 12px;
            display: none;
        }
        
        .status.processing {
            background: #fff3cd;
            border: 2px solid #ffc107;
            display: block;
        }
        
        .status.success {
            background: #d4edda;
            border: 2px solid #28a745;
            display: block;
        }
        
        .status.error {
            background: #f8d7da;
            border: 2px solid #dc3545;
            display: block;
        }
        
        .result {
            margin-top: 30px;
            display: none;
        }
        
        .result.show {
            display: block;
        }
        
        .transcription {
            background: #f8f9fa;
            padding: 30px;
            border-radius: 12px;
            white-space: pre-wrap;
            line-height: 1.8;
            font-size: 16px;
            max-height: 600px;
            overflow-y: auto;
        }
        
        .speaker-line {
            margin-bottom: 15px;
        }
        
        .speaker-label {
            font-weight: 700;
            color: #667eea;
        }
        
        .analysis {
            margin-top: 30px;
            padding: 25px;
            background: #e7f3ff;
            border-radius: 12px;
        }
        
        .analysis h3 {
            color: #333;
            margin-bottom: 15px;
        }
        
        .speaker-info {
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 15px;
        }
        
        .speaker-info h4 {
            color: #667eea;
            margin-bottom: 10px;
        }
        
        .loading {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid rgba(255,255,255,.3);
            border-radius: 50%;
            border-top-color: white;
            animation: spin 1s ease-in-out infinite;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎤 Speaker Diarization</h1>
            <p>Upload audio and get speaker-labeled transcriptions</p>
        </div>
        
        <div class="card">
            <div class="upload-area" id="uploadArea" onclick="document.getElementById('fileInput').click()">
                <div class="upload-icon">🎵</div>
                <div class="upload-text">Click to upload or drag & drop</div>
                <div class="upload-hint">MP3, WAV, M4A, OGG, WEBM (max 25MB)</div>
            </div>
            <input type="file" id="fileInput" accept=".mp3,.wav,.m4a,.ogg,.webm">
            
            <div style="text-align: center;">
                <button class="btn" id="processBtn" onclick="processAudio()" disabled>
                    Process Audio
                </button>
            </div>
            
            <div class="status" id="status"></div>
        </div>
        
        <div class="card result" id="result">
            <h2>📝 Transcription with Speaker Labels</h2>
            <div class="transcription" id="transcription"></div>
            
            <div class="analysis" id="analysis"></div>
        </div>
    </div>
    
    <script>
        let selectedFile = null;
        
        const uploadArea = document.getElementById('uploadArea');
        const fileInput = document.getElementById('fileInput');
        const processBtn = document.getElementById('processBtn');
        const status = document.getElementById('status');
        const result = document.getElementById('result');
        
        // Drag and drop
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });
        
        uploadArea.addEventListener('dragleave', () => {
            uploadArea.classList.remove('dragover');
        });
        
        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                handleFile(files[0]);
            }
        });
        
        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                handleFile(e.target.files[0]);
            }
        });
        
        function handleFile(file) {
            selectedFile = file;
            uploadArea.querySelector('.upload-text').textContent = `Selected: ${file.name}`;
            processBtn.disabled = false;
        }
        
        async function processAudio() {
            if (!selectedFile) return;
            
            processBtn.disabled = true;
            result.classList.remove('show');
            
            showStatus('processing', 'Processing audio... This may take a minute.');
            
            const formData = new FormData();
            formData.append('audio', selectedFile);
            
            try {
                const response = await fetch('/api/process', {
                    method: 'POST',
                    body: formData
                });
                
                const data = await response.json();
                
                if (data.success) {
                    showStatus('success', 'Processing complete!');
                    displayResult(data);
                } else {
                    showStatus('error', `Error: ${data.error}`);
                }
            } catch (error) {
                showStatus('error', `Error: ${error.message}`);
            } finally {
                processBtn.disabled = false;
            }
        }
        
        function showStatus(type, message) {
            status.className = `status ${type}`;
            status.textContent = message;
        }
        
        function displayResult(data) {
            document.getElementById('transcription').textContent = data.labeled_transcription;
            
            if (data.analysis && data.analysis.speakers) {
                let analysisHTML = '<h3>Speaker Analysis</h3>';
                data.analysis.speakers.forEach(speaker => {
                    analysisHTML += `
                        <div class="speaker-info">
                            <h4>${speaker.id}: ${speaker.role}</h4>
                            <p><strong>Style:</strong> ${speaker.style}</p>
                            <p><strong>Topics:</strong> ${speaker.topics.join(', ')}</p>
                        </div>
                    `;
                });
                document.getElementById('analysis').innerHTML = analysisHTML;
            }
            
            result.classList.add('show');
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/process', methods=['POST'])
def process_audio():
    """Process audio file: transcribe and add speaker labels"""
    try:
        if 'audio' not in request.files:
            return jsonify({"success": False, "error": "No audio file provided"}), 400
        
        file = request.files['audio']
        if file.filename == '':
            return jsonify({"success": False, "error": "No file selected"}), 400
        
        if not allowed_file(file.filename):
            return jsonify({"success": False, "error": "Invalid file type"}), 400
        
        # Save file
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(file_path)
        
        print(f"[DIARIZATION] Processing: {unique_filename}", file=sys.stderr)
        
        # Step 1: Transcribe with SuperNinja
        print(f"[DIARIZATION] Step 1: Transcribing...", file=sys.stderr)
        transcription_result = transcribe_with_ninja(file_path)
        
        if not transcription_result.get('success'):
            return jsonify({
                "success": False,
                "error": f"Transcription failed: {transcription_result.get('error')}"
            }), 500
        
        transcription = transcription_result['transcription']
        print(f"[DIARIZATION] Transcribed {len(transcription)} characters", file=sys.stderr)
        
        # Step 2: Add speaker labels with AI
        print(f"[DIARIZATION] Step 2: Adding speaker labels...", file=sys.stderr)
        labeling_result = add_speaker_labels_with_ai(transcription)
        
        if not labeling_result.get('success'):
            return jsonify({
                "success": False,
                "error": f"Speaker labeling failed: {labeling_result.get('error')}"
            }), 500
        
        labeled_transcription = labeling_result['transcription']
        print(f"[DIARIZATION] Added speaker labels", file=sys.stderr)
        
        # Step 3: Analyze speakers
        print(f"[DIARIZATION] Step 3: Analyzing speakers...", file=sys.stderr)
        analysis_result = analyze_speakers(labeled_transcription)
        
        # Save result
        result_id = str(uuid.uuid4())
        result_data = {
            "id": result_id,
            "filename": filename,
            "original_transcription": transcription,
            "labeled_transcription": labeled_transcription,
            "analysis": analysis_result.get('analysis') if analysis_result.get('success') else None,
            "created_at": datetime.now().isoformat()
        }
        
        result_path = os.path.join(RESULTS_FOLDER, f"{result_id}.json")
        with open(result_path, 'w') as f:
            json.dump(result_data, f, indent=2)
        
        print(f"[DIARIZATION] Complete! Result ID: {result_id}", file=sys.stderr)
        
        return jsonify({
            "success": True,
            "result_id": result_id,
            "labeled_transcription": labeled_transcription,
            "analysis": result_data['analysis']
        })
        
    except Exception as e:
        print(f"[DIARIZATION] Error: {str(e)}", file=sys.stderr)
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/results', methods=['GET'])
def get_results():
    """Get all processing results"""
    results = []
    for filename in os.listdir(RESULTS_FOLDER):
        if filename.endswith('.json'):
            with open(os.path.join(RESULTS_FOLDER, filename), 'r') as f:
                result = json.load(f)
                results.append({
                    "id": result['id'],
                    "filename": result['filename'],
                    "created_at": result['created_at']
                })
    
    results.sort(key=lambda x: x['created_at'], reverse=True)
    return jsonify(results)

@app.route('/api/results/<result_id>', methods=['GET'])
def get_result(result_id):
    """Get specific result"""
    result_path = os.path.join(RESULTS_FOLDER, f"{result_id}.json")
    if os.path.exists(result_path):
        with open(result_path, 'r') as f:
            result = json.load(f)
        return jsonify(result)
    return jsonify({"error": "Result not found"}), 404

if __name__ == '__main__':
    print("=" * 60)
    print("🎤 Speaker Diarization App Starting...")
    print("=" * 60)
    print(f"Port: 9001")
    print(f"URL: http://localhost:9001")
    print("=" * 60)
    app.run(host='0.0.0.0', port=9001, debug=True)