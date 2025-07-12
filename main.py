import os
import requests
from dotenv import load_dotenv
from fastapi import FastAPI, Request, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from marcus_logic import process_audio_input

# Debugging: Print template path (optional)
print("TEMPLATES PATH:", os.path.abspath("templates"))

# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ELEVEN_API_KEY = os.getenv("ELEVEN_API_KEY")
ELEVEN_VOICE_ID = os.getenv("ELEVEN_VOICE_ID")

# FastAPI app setup
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/transcribe/")
async def transcribe_audio(file: UploadFile = File(...)):
    transcript, response_text = await process_audio_input(file)

    # Generate audio from Marcus's response using ElevenLabs
    voice_url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVEN_VOICE_ID}"
    headers = {
        "xi-api-key": ELEVEN_API_KEY,
        "Content-Type": "application/json"
    }
    data = {
        "text": response_text,
        "model_id": "eleven_monolingual_v1"
    }

    response = requests.post(voice_url, headers=headers, json=data)

    # Save MP3 file
    audio_path = "static/marcus_reply.mp3"
    with open(audio_path, "wb") as f:
        f.write(response.content)

    return {
        "transcript": transcript,
        "response": response_text,
        "audio_url": "/static/marcus_reply.mp3"
    }
