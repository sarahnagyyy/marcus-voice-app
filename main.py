import os
import requests
import tempfile
from dotenv import load_dotenv
from fastapi import FastAPI, Request, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from marcus_logic import process_audio_input
import json

# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ELEVEN_API_KEY = os.getenv("ELEVEN_API_KEY")
ELEVEN_VOICE_ID = os.getenv("ELEVEN_VOICE_ID")

app = FastAPI()

# Mount static and template folders
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/transcribe/")
async def transcribe_audio(file: UploadFile = File(...)):
    try:
        # Get transcript and response
        transcript, response_text = await process_audio_input(file)

        # Generate speech with ElevenLabs
        voice_url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVEN_VOICE_ID}"
        headers = {
            "xi-api-key": ELEVEN_API_KEY,
            "Content-Type": "application/json"
        }
        data = {
            "text": response_text,
            "model_id": "eleven_monolingual_v1"
        }

        tts_response = requests.post(voice_url, headers=headers, json=data)

        # DEBUG OUTPUT
        print("📡 ElevenLabs request:", json.dumps(data))
        print("🔐 Voice ID:", ELEVEN_VOICE_ID)
        print("📥 Status Code:", tts_response.status_code)
        print("📥 Response Text:", tts_response.text)

        if tts_response.status_code != 200:
            return {"error": "Text-to-speech failed", "details": response.text}
            

        audio_path = "static/marcus_reply.mp3"
        with open(audio_path, "wb") as f:
            f.write(tts_response.content)

        return {
            "transcript": transcript,
            "response": response_text,
            "audio_url": "/static/marcus_reply.mp3"
        }

    except Exception as e:
        print("❌ Internal server error:", str(e))
        return JSONResponse(status_code=500, content={"error": "Internal server error", "details": str(e)})
