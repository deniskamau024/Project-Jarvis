import os
import base64
import smtplib
from datetime import datetime
import pytz
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv
from duckduckgo_search import DDGS

# Load environment configs safely
current_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(current_dir, ".env")
load_dotenv(dotenv_path=env_path)

app = FastAPI(title="Project JARVIS Automation Mainframe")
client = OpenAI()

JARVIS_SYSTEM_PROMPT = (
    "You are J.A.R.V.I.S., a highly intelligent, witty, and sophisticated AI assistant. "
    "You are assisting Mr. Denis from Kenya. Be direct, helpful, and address him as Sir. "
    "You are fully connected to the live internet and real-time telemetry pipelines. "
    "Always review the injected 'LIVE TELEMETRY MATRIX' context data provided in your "
    "messages to give accurate, current-day answers regarding dates, times, and live web lookups."
)


conversation_history = [{"role": "system", "content": JARVIS_SYSTEM_PROMPT}]

def perform_web_search(query: str) -> str:
    try:
        with DDGS() as ddgs:
            results = [r for r in ddgs.text(query, max_results=3)]
            if not results: 
                return "No real-time web search results found."
            return "\n".join([f"Source: {r['title']}\nSnippet: {r['body']}" for r in results])
    except Exception as e:
        return f"Search tool temporarily offline: {str(e)}"

# Unified Multimodal Endpoint
@app.post("/v1/chat")
async def process_mainframe_command(
    message: str = Form(...),
    file: UploadFile = File(None)
):
    global conversation_history
    user_text = message.strip()
    content_payload = []
    
    if not user_text:
        raise HTTPException(status_code=400, detail="Empty text packets received.")
        
    # 1. Resolve Time & Search Engine Overrides Automatically
    lower_msg = user_text.lower()
    real_time_triggers = ["weather", "news", "search", "latest", "time", "date", "today", "now", "who is"]
    
    if any(k in lower_msg for k in real_time_triggers):
        kenya_tz = pytz.timezone('Africa/Nairobi')
        live_time_string = datetime.now(kenya_tz).strftime("%A, %B %d, %Y, %I:%M %p EAT")
        search_results = perform_web_search(user_text)
        
        telemetry_payload = f"--- LIVE TELEMETRY MATRIX ---\nCurrent Kenya Time: {live_time_string}\n\nSearch Logs:\n{search_results}"
        conversation_history.append({"role": "system", "content": telemetry_payload})

    # 2. Parse Uploaded Media Pipelines
    if file:
        file_ext = os.path.splitext(file.filename).lower()
        
        # Scenario A: Image Framework (Multimodal Input Matrix)
        if file_ext in [".png", ".jpg", ".jpeg", ".webp"]:
            file_bytes = await file.read()
            base64_image = base64.b64encode(file_bytes).decode("utf-8")
            content_payload.append({"type": "text", "text": user_text})
            content_payload.append({
                "type": "image_url",
                "image_url": {"url": f"data:{file.content_type};base64,{base64_image}"}
            })
            conversation_history.append({"role": "user", "content": content_payload})
            
        # Scenario B: Audio/Video Framework (Whisper Transcription Matrix)
        elif file_ext in [".mp3", ".wav", ".m4a", ".mp4", ".webm", ".ogg"]:
            temp_path = f"temp_stream{file_ext}"
            with open(temp_path, "wb") as buffer:
                buffer.write(await file.read())
                
            with open(temp_path, "rb") as audio_file:
                transcription = client.audio.transcriptions.create(model="whisper-1", file=audio_file)
            os.remove(temp_path)
            
            audio_prompt = f"--- MEDIA TRANSCRIPT TELEMETRY ---\n\"{transcription.text}\"\nUser Command: {user_text}"
            conversation_history.append({"role": "user", "content": audio_prompt})
    else:
        content_payload.append({"type": "text", "text": user_text})
        conversation_history.append({"role": "user", "content": content_payload})

    # 3. Query OpenAI and Pack Output Object Cleanly
    try:
        response = client.chat.completions.create(model="gpt-4o-mini", messages=conversation_history)
        jarvis_reply = response.choices[0].message.content # Extracted cleanly
        conversation_history.append({"role": "assistant", "content": jarvis_reply})
        
        # FIXED STRUCTURE: Explicitly matches your laptop interface mapping dictionary!
        return {"reply": jarvis_reply}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Core Processing Loop Failure: {str(e)}")

@app.get("/")
async def status_check():
    return {"status": "online", "mainframe": "J.A.R.V.I.S. Core Matrix Stable"}
