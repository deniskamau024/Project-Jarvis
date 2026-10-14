import os
import base64
import smtplib
import imaplib
import email
from email.mime.text import MIMEText
from datetime import datetime
import pytz
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv
from duckduckgo_search import DDGS

load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

app = FastAPI(title="Project JARVIS Automation Mainframe")
client = OpenAI()

JARVIS_SYSTEM_PROMPT = (
    "You are J.A.R.V.I.S., a highly intelligent, witty, and sophisticated AI assistant. "
    "You are assisting Mr. Denis from Kenya. Be direct, helpful, and address him as Sir. "
    "You have access to integrated communication subroutines including email telemetry, "
    "web research protocols, and audio transcription engines."
)

conversation_history = [{"role": "system", "content": JARVIS_SYSTEM_PROMPT}]

# --- HELPER PROTOCOL 1: WEB SEARCH ENGINE ---
def perform_web_search(query: str) -> str:
    try:
        with DDGS() as ddgs:
            results = [r for r in ddgs.text(query, max_results=3)]
            return "\n".join([f"Source: {r['title']}\nSnippet: {r['body']}" for r in results]) if results else "No telemetry found."
    except Exception as e:
        return f"Search node offline: {str(e)}"

# --- HELPER PROTOCOL 2: SECURE OUTBOUND EMAIL MAILROOM ---
def send_automated_email(to_address: str, subject: str, body_content: str) -> str:
    smtp_server = "://gmail.com"
    smtp_port = 587
    sender_email = os.getenv("JARVIS_EMAIL_USER")
    sender_password = os.getenv("JARVIS_EMAIL_PASS") # App Password
    
    if not sender_email or not sender_password:
        return "Mailroom failure: Credentials missing from environment variables."
        
    try:
        msg = MIMEText(body_content)
        msg['Subject'] = subject
        msg['From'] = sender_email
        msg['To'] = to_address
        
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
        return f"Email transmitted successfully to {to_address}, Sir."
    except Exception as e:
        return f"Mailroom deployment failed: {str(e)}"

# --- MAIN UNIFIED PROCESSING MATRIX ---
@app.post("/v1/chat")
async def process_mainframe_command(
    message: str = Form(...),
    file: UploadFile = File(None)
):
    global conversation_history
    user_text = message.strip()
    content_payload = []
    
    # 1. Sync Live Kenya Clock Telemetry Automatically
    kenya_tz = pytz.timezone('Africa/Nairobi')
    live_time = datetime.now(kenya_tz).strftime("%A, %B %d, %Y, %I:%M %p EAT")
    
    # 2. Evaluate Core Intent Triggers
    lower_msg = user_text.lower()
    
    # Check for real-time data lookup triggers
    if any(k in lower_msg for k in ["weather", "news", "search", "latest", "time", "date", "today"]):
        search_data = perform_web_search(user_text)
        context = f"--- LIVE TELEMETRY ---\nCurrent Kenya Time: {live_time}\n\nSearch Results:\n{search_data}"
        conversation_history.append({"role": "system", "content": context})
        
    # Check for automated email dispatch intents
    if "send an email to" in lower_msg:
        # Simple extraction helper logic for testing
        conversation_history.append({"role": "system", "content": f"System Alert: Outbound mail utility active. Time context: {live_time}"})

    # 3. Handle Media Assets Safely
    if file:
        file_ext = os.path.splitext(file.filename)[1].lower()
        
        # Scenario A: Image Telemetry (Vision Model Processing)
        if file_ext in [".png", ".jpg", ".jpeg", ".webp"]:
            file_bytes = await file.read()
            base64_image = base64.b64encode(file_bytes).decode("utf-8")
            content_payload.append({"type": "text", "text": user_text})
            content_payload.append({
                "type": "image_url",
                "image_url": {"url": f"data:{file.content_type};base64,{base64_image}"}
            })
            conversation_history.append({"role": "user", "content": content_payload})
            
        # Scenario B: Audio/Video Telemetry (Whisper Transcription Processing)
        elif file_ext in [".mp3", ".wav", ".m4a", ".mp4", ".mpeg", ".webm", ".ogg"]:
            temp_file_path = f"temp_media_stream{file_ext}"
            with open(temp_file_path, "wb") as buffer:
                buffer.write(await file.read())
                
            # Submit raw audio stream to Whisper core nodes
            with open(temp_file_path, "rb") as audio_data:
                transcript_obj = client.audio.transcriptions.create(model="whisper-1", file=audio_data)
            os.remove(temp_file_path)
            
            transcription_text = transcript_obj.text
            injected_transcript_prompt = f"--- AUDIO TRANSCRIPT TELEMETRY ---\n\"{transcription_text}\"\n-----------------------------------\nUser instruction relative to this transcript: {user_text}"
            conversation_history.append({"role": "user", "content": injected_transcript_prompt})
    else:
        # Standard structural text packet routing
        content_payload.append({"type": "text", "text": user_text})
        conversation_history.append({"role": "user", "content": content_payload})

    # 4. Generate Mainframe Response Package
    try:
        response = client.chat.completions.create(model="gpt-4o-mini", messages=conversation_history)
        jarvis_reply = response.choices[0].message.content
        conversation_history.append({"role": "assistant", "content": jarvis_reply})
        return {"reply": jarvis_reply}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Mainframe Core execution loop fractured: {str(e)}")

@app.get("/")
async def health_check():
    return {"status": "online", "system": "JARVIS Automation Hub Stable"}

