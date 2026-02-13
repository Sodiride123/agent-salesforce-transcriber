#!/usr/bin/env python3
"""
Real transcription using SuperNinja's transcription service
Integrates with the OpenAI-compatible transcription API
"""

import os
import sys
import json
import openai

def transcribe_audio_real(file_path):
    """
    Transcribe audio using SuperNinja's transcription service
    
    Args:
        file_path: Relative path from /workspace or absolute path
        
    Returns:
        dict with transcription results
    """
    try:
        # Ensure we have the full path
        if file_path.startswith('/workspace/'):
            full_path = file_path
            relative_path = file_path[11:]
        elif file_path.startswith('workspace/'):
            full_path = os.path.join('/workspace', file_path[10:])
            relative_path = file_path[10:]
        elif os.path.isabs(file_path):
            full_path = file_path
            relative_path = file_path
        else:
            # If relative path, check from current working directory first
            if os.path.exists(file_path):
                full_path = os.path.abspath(file_path)
                relative_path = file_path
            else:
                # Fall back to /workspace
                full_path = os.path.join('/workspace', file_path)
                relative_path = file_path
        
        # Verify file exists
        if not os.path.exists(full_path):
            return {
                "success": False,
                "error": f"File not found: {relative_path}"
            }
        
        # Get file info
        file_size = os.path.getsize(full_path)
        file_name = os.path.basename(relative_path)
        
        print(f"[TRANSCRIBE] Processing: {file_name}", file=sys.stderr)
        print(f"[TRANSCRIBE] Size: {file_size / 1024:.2f} KB", file=sys.stderr)
        
        # Initialize OpenAI client with SuperNinja endpoint
        client = openai.OpenAI(
            api_key="sk-bRi4jzJTrkmv4rdGUCAwsw",
            base_url="https://model-gateway.public.beta.myninja.ai"
        )
        
        # Open the audio file
        with open(full_path, "rb") as audio_file:
            print(f"[TRANSCRIBE] Sending to transcription service...", file=sys.stderr)
            
            # Make the transcription request
            # Note: The superninja-transcribe model uses 'text' format
            response = client.audio.transcriptions.create(
                model="superninja-transcribe",
                file=audio_file,
                response_format="text"
            )
        
        # Extract transcription text
        # Handle different response formats
        if isinstance(response, str):
            # Try to parse as JSON first
            try:
                response_json = json.loads(response)
                transcription_text = response_json.get('text', response)
            except:
                transcription_text = response
        elif hasattr(response, 'text'):
            transcription_text = response.text
        else:
            transcription_text = str(response)
        
        print(f"[TRANSCRIBE] Success! Transcribed {len(transcription_text)} characters", file=sys.stderr)
        
        return {
            "success": True,
            "transcription": transcription_text,
            "file_path": relative_path,
            "file_name": file_name,
            "file_size": file_size
        }
        
    except openai.APIError as e:
        error_msg = f"API Error: {str(e)}"
        print(f"[TRANSCRIBE] {error_msg}", file=sys.stderr)
        return {
            "success": False,
            "error": error_msg
        }
    except openai.APIConnectionError as e:
        error_msg = f"Connection Error: {str(e)}"
        print(f"[TRANSCRIBE] {error_msg}", file=sys.stderr)
        return {
            "success": False,
            "error": error_msg
        }
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        print(f"[TRANSCRIBE] {error_msg}", file=sys.stderr)
        return {
            "success": False,
            "error": error_msg
        }

if __name__ == "__main__":
    if len(sys.argv) > 1:
        result = transcribe_audio_real(sys.argv[1])
        print(json.dumps(result, indent=2))
    else:
        print("Usage: python real_transcribe.py <file_path>")
        sys.exit(1)