# Speaker Diarization Guide for SalesIQ

## 🎯 Current Status

The SuperNinja transcription model (`superninja-transcribe`) provides **text-only transcription** without built-in speaker diarization (speaker identification).

## 📊 What We Currently Get

**Current Output:**
```
Bring, bring, bring. I'm calling you. Hello? Hey Larry, this is Cody from Active Life. 
Oh hey Cody, how's it going? It's going well. What's been the best part of your day so far?
```

**What We Want:**
```
[Speaker 1]: Bring, bring, bring. I'm calling you. Hello?
[Speaker 2]: Hey Larry, this is Cody from Active Life.
[Speaker 1]: Oh hey Cody, how's it going?
[Speaker 2]: It's going well. What's been the best part of your day so far?
```

## 🔧 Solutions for Speaker Differentiation

### Option 1: Use AssemblyAI (Recommended for Sales Calls)

AssemblyAI has excellent speaker diarization built-in.

**Pros:**
- Automatic speaker detection
- High accuracy for sales calls
- Timestamps included
- Easy to implement

**Implementation:**

```python
# Install
pip install assemblyai

# Update real_transcribe.py
import assemblyai as aai

aai.settings.api_key = "your-assemblyai-key"

def transcribe_audio_real(file_path):
    config = aai.TranscriptionConfig(
        speaker_labels=True  # Enable speaker diarization
    )
    
    transcriber = aai.Transcriber(config=config)
    transcript = transcriber.transcribe(file_path)
    
    # Format with speakers
    formatted_text = []
    for utterance in transcript.utterances:
        speaker = f"Speaker {utterance.speaker}"
        text = utterance.text
        formatted_text.append(f"[{speaker}]: {text}")
    
    return {
        "success": True,
        "transcription": "\n".join(formatted_text)
    }
```

**Cost:** ~$0.00025 per second (~$0.90 per hour)

---

### Option 2: Use Deepgram

Deepgram offers real-time transcription with speaker diarization.

**Pros:**
- Fast processing
- Good accuracy
- Real-time capable
- Competitive pricing

**Implementation:**

```python
# Install
pip install deepgram-sdk

# Update real_transcribe.py
from deepgram import Deepgram

dg_client = Deepgram("your-deepgram-key")

def transcribe_audio_real(file_path):
    with open(file_path, 'rb') as audio:
        source = {'buffer': audio, 'mimetype': 'audio/mp3'}
        response = dg_client.transcription.sync_prerecorded(
            source,
            {'punctuate': True, 'diarize': True}
        )
    
    # Format with speakers
    formatted_text = []
    for word in response['results']['channels'][0]['alternatives'][0]['words']:
        speaker = f"Speaker {word.get('speaker', 0)}"
        # Group by speaker changes
        # ... formatting logic
    
    return {"success": True, "transcription": formatted_text}
```

**Cost:** ~$0.0043 per minute (~$0.26 per hour)

---

### Option 3: Post-Process with AI (Current Setup Compatible)

Use the current transcription and add speaker labels using AI analysis.

**Pros:**
- Works with current setup
- No additional API needed
- Can use context clues

**Implementation:**

```python
def add_speaker_labels(transcription_text):
    """
    Use AI to identify and label speakers in the transcription
    """
    prompt = f"""
    Analyze this sales call transcription and identify the speakers.
    Add speaker labels (Speaker 1, Speaker 2, etc.) to each line.
    
    Transcription:
    {transcription_text}
    
    Format as:
    [Speaker 1]: text
    [Speaker 2]: text
    """
    
    # Call AI model to analyze and add labels
    # This could use the existing SuperNinja models
    
    return labeled_transcription
```

**Pros:**
- No additional transcription cost
- Works with existing setup
- Can identify speakers by context

**Cons:**
- Less accurate than dedicated diarization
- Requires additional AI call
- May miss speaker changes

---

### Option 4: Use Pyannote Audio (Local Processing)

Open-source speaker diarization that runs locally.

**Pros:**
- Free
- Runs locally
- Good accuracy
- No API costs

**Cons:**
- Requires more setup
- Slower processing
- Needs GPU for best performance

**Implementation:**

```python
# Install
pip install pyannote.audio

# Update real_transcribe.py
from pyannote.audio import Pipeline

pipeline = Pipeline.from_pretrained(
    "pyannote/speaker-diarization",
    use_auth_token="your-huggingface-token"
)

def transcribe_audio_real(file_path):
    # First, get transcription (current method)
    transcription = get_transcription(file_path)
    
    # Then, get speaker diarization
    diarization = pipeline(file_path)
    
    # Combine transcription with speaker labels
    # ... alignment logic
    
    return formatted_transcription
```

---

## 🎯 Recommendation

### For Production (Best Quality):
**Use AssemblyAI** - It's specifically designed for conversation analysis and has the best speaker diarization for sales calls.

### For Budget-Conscious:
**Use Option 3 (AI Post-Processing)** - Works with your current setup, just adds a post-processing step.

### For Privacy/Offline:
**Use Pyannote Audio** - Everything runs locally, no data leaves your server.

---

## 📝 Quick Implementation: AssemblyAI

Here's how to quickly add speaker diarization with AssemblyAI:

### Step 1: Get API Key
Sign up at https://www.assemblyai.com/ and get your API key.

### Step 2: Install Package
```bash
pip install assemblyai
```

### Step 3: Update real_transcribe.py

```python
import assemblyai as aai

def transcribe_audio_real(file_path):
    try:
        # Setup
        aai.settings.api_key = "your-api-key-here"
        
        # Get full path
        full_path = os.path.join('/workspace', file_path)
        
        # Configure with speaker labels
        config = aai.TranscriptionConfig(
            speaker_labels=True,
            speakers_expected=2  # For sales calls (rep + customer)
        )
        
        # Transcribe
        transcriber = aai.Transcriber(config=config)
        transcript = transcriber.transcribe(full_path)
        
        # Format with speakers
        formatted_lines = []
        current_speaker = None
        current_text = []
        
        for utterance in transcript.utterances:
            speaker_label = f"Speaker {utterance.speaker}"
            
            if speaker_label != current_speaker:
                # New speaker, save previous
                if current_speaker:
                    formatted_lines.append(
                        f"[{current_speaker}]: {' '.join(current_text)}"
                    )
                current_speaker = speaker_label
                current_text = [utterance.text]
            else:
                # Same speaker, continue
                current_text.append(utterance.text)
        
        # Add last speaker
        if current_speaker:
            formatted_lines.append(
                f"[{current_speaker}]: {' '.join(current_text)}"
            )
        
        transcription_text = "\n\n".join(formatted_lines)
        
        return {
            "success": True,
            "transcription": transcription_text,
            "speakers_detected": transcript.speakers_expected
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}
```

### Step 4: Test
```bash
python real_transcribe.py media_library/your_audio.mp3
```

---

## 🔍 Comparison Table

| Solution | Accuracy | Speed | Cost/Hour | Setup Time | Speaker Labels |
|----------|----------|-------|-----------|------------|----------------|
| **AssemblyAI** | ⭐⭐⭐⭐⭐ | Fast | $0.90 | 5 min | ✅ Automatic |
| **Deepgram** | ⭐⭐⭐⭐ | Very Fast | $0.26 | 5 min | ✅ Automatic |
| **AI Post-Process** | ⭐⭐⭐ | Medium | $0.01 | 10 min | ⚠️ Context-based |
| **Pyannote** | ⭐⭐⭐⭐ | Slow | Free | 30 min | ✅ Automatic |
| **Current (None)** | N/A | Fast | $0.36 | 0 min | ❌ No labels |

---

## 💡 My Recommendation

For your SalesIQ application, I recommend **AssemblyAI** because:

1. **Built for conversations** - Specifically designed for sales calls
2. **High accuracy** - Best-in-class speaker diarization
3. **Easy integration** - 5 minutes to implement
4. **Reasonable cost** - ~$0.90/hour is acceptable for sales analysis
5. **Additional features** - Sentiment analysis, topic detection available

**Would you like me to implement AssemblyAI speaker diarization right now?** I can have it working in 5 minutes if you provide an API key!

---

## 📞 Next Steps

1. Choose your preferred solution
2. Get API credentials (if needed)
3. I'll implement it immediately
4. Test with your sales call recordings
5. Enjoy speaker-labeled transcriptions!

Let me know which option you'd like to proceed with! 🚀