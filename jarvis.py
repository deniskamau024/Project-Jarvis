import os
from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv
from duckduckgo_search import DDGS
from fastapi.responses import FileResponse

# 1. Load Environment Variables
current_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(current_dir, ".env")
load_dotenv(dotenv_path=env_path)

app = FastAPI(title="Project JARVIS Cloud Matrix")
client = OpenAI()

JARVIS_SYSTEM_PROMPT = (
    "You are J.A.R.V.I.S., a highly intelligent, witty, and sophisticated AI assistant. "
    "You are assisting Mr. Denis from Kenya. Be direct, helpful, and address him as Sir. "
    "Keep answers relatively concise so they sound natural when spoken aloud."
)

conversation_history = [{"role": "system", "content": JARVIS_SYSTEM_PROMPT}]

def perform_web_search(query: str) -> str:
    try:
        with DDGS() as ddgs:
            results = [r for r in ddgs.text(query, max_results=3)]
            if not results: return "No search results found."
            return "\n".join([f"Source: {r['title']}\nSnippet: {r['body']}" for r in results])
    except:
        return "Search tool temporarily unavailable."

class TextRequest(BaseModel):
    text: str

# Helper to generate audio voice file
def generate_voice_file(text_content: str) -> str:
    output_path = "jarvis_voice.mp3"
    audio_response = client.audio.speech.create(
        model="tts-1",
        voice="onyx", # Sophisticated male tone
        input=text_content
    )
    audio_response.stream_to_file(output_path)
    return output_path

# PROTOCOL A: Text Input Endpoint
@app.post("/v1/chat/text")
async def chat_text(request: TextRequest):
    global conversation_history
    user_text = request.text.strip()
    
    if not user_text:
        raise HTTPException(status_code=400, detail="Empty text message.")
        
    if any(k in user_text.lower() for k in ["weather", "news", "search", "latest", "time"]):
        search_results = perform_web_search(user_text)
        conversation_history.append({"role": "system", "content": f"Live Data:\n{search_results}"})

    conversation_history.append({"role": "user", "content": user_text})
    
    response = client.chat.completions.create(model="gpt-4o-mini", messages=conversation_history)
    jarvis_reply = response.choices[0].message.content
    conversation_history.append({"role": "assistant", "content": jarvis_reply})
    
    audio_file = generate_voice_file(jarvis_reply)
    return {"reply": jarvis_reply, "has_audio": True}

# PROTOCOL B: Audio/Voice Input Endpoint
@app.post("/v1/chat/voice")
async def chat_voice(file: UploadFile = File(...)):
    global conversation_history
    
    # Save the incoming voice data temporarily
    temp_audio_path = "incoming_user_voice.wav"
    with open(temp_audio_path, "wb") as buffer:
        buffer.write(await file.read())
        
    # Transcribe speech to text using Whisper
    with open(temp_audio_path, "rb") as audio_file:
        transcription = client.audio.transcriptions.create(model="whisper-1", file=audio_file)
    user_text = transcription.text
    os.remove(temp_audio_path)
    
    # Process text through the brain
    if any(k in user_text.lower() for k in ["weather", "news", "search", "latest", "time"]):
        search_results = perform_web_search(user_text)
        conversation_history.append({"role": "system", "content": f"Live Data:\n{search_results}"})

    conversation_history.append({"role": "user", "content": user_text})
    
    response = client.chat.completions.create(model="gpt-4o-mini", messages=conversation_history)
    jarvis_reply = response.choices[0].message.content
    conversation_history.append({"role": "assistant", "content": jarvis_reply})
    
    generate_voice_file(jarvis_reply)
    return {"user_transcript": user_text, "reply": jarvis_reply}

# Audio Download Link Endpoint for local playback
@app.get("/get_audio")
async def get_audio():
    audio_path = "jarvis_voice.mp3"
    if os.path.exists(audio_path):
        return FileResponse(audio_path, media_type="audio/mp3", filename="jarvis_voice.mp3")
    raise HTTPException(status_code=404, detail="Audio file not generated yet.")

@app.get("/")
async def root():
    return {"status": "online", "system": "J.A.R.V.I.S. Core Online"}
