# SalesIQ App Workflow

## Models Used

| Step | Model | API Type |
|------|-------|----------|
| Audio → Text | `openai/openai/gpt-4o-transcribe` | Audio transcription |
| Text → Analysis | `ninja-cline-complex` | Chat completions |
| Chat Q&A | `ninja-cline-complex` | Chat completions |

Both models go through the SuperNinja gateway at `model-gateway.public.beta.myninja.ai`.

## Step 1: User Uploads Audio

- Browser sends file to `POST /api/upload-audio`
- File saved to `uploads/`, then moved to `media_library/` with a UUID prefix
- Session created/retrieved using the browser's `session_id`

## Step 2: Audio → Text (Transcription)

- `real_transcribe.py` → `transcribe_audio_real()` sends the audio file to SuperNinja API
- **Model: `openai/openai/gpt-4o-transcribe`**
- Returns raw transcription text

## Step 3: Text → Analysis

- `app.py` → `analyze_sales_call()` sends the transcription to AI with a structured prompt
- **Model: `ninja-cline-complex`**
- Extracts: summary, key_points, sentiment, action_items, customer_needs, next_steps
- Result saved as a JSON report in `reports/`
- Report ID linked to the user's session

## Step 4: User Asks a Question (Chat)

- Browser sends question to `POST /api/chat`
- `build_context_from_reports()` loads all reports linked to the session
- `ask_claude_with_context()` sends context + last 10 messages + question to AI
- **Model: `ninja-cline-complex`**
- Response returned to browser and stored in session conversation history

## Step 5: Salesforce Integration (Optional)

After analysis, the user can:
- **Search** for a Salesforce account by company name
- **Create tasks** from the action items (assigned to the account, due in 7 days)
- **Update the account** description with customer needs from the call
- **Log a meeting/event** with notes from the call

## Visual Flow

```
                        Model: openai/openai/gpt-4o-transcribe
                        (OpenAI-compatible audio API)
  Audio File ──────────────────────────────────────────────► Transcription Text
                                                                    │
                                                                    ▼
                        Model: ninja-cline-complex          AI Analysis (JSON)
                        (Chat completions API)              - summary
                                                            - key_points
                                                            - sentiment
                                                            - action_items
                                                            - customer_needs
                                                            - next_steps
                                                                    │
                                                                    ▼
                                                            Report saved
                                                            + linked to session
                                                                    │
                                                                    ▼
  User Question ──► context (reports) + history ──────────► AI Answer
                        Model: ninja-cline-complex
                        (Chat completions API)
                                                                    │
                                                                    ▼
                                                      Salesforce Actions (optional)
                                                      - Create tasks
                                                      - Update account
                                                      - Log meeting
```
