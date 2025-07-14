import os
import requests
from fastapi import FastAPI, Request, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv
from marcus_logic import process_audio_input

# Load environment variables from .env file
load_dotenv()

# Retrieve keys from environment
ELEVEN_API_KEY = os.getenv("ELEVEN_API_KEY")
ELEVEN_VOICE_ID = os.getenv("ELEVEN_VOICE_ID")

# Check that the necessary environment variables are present
if not ELEVEN_API_KEY or not ELEVEN_VOICE_ID:
    raise RuntimeError("Missing ELEVEN_API_KEY or ELEVEN_VOICE_ID in environment variables.")

# Initialize FastAPI app
app = FastAPI()

# Mount static and templates directories
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/transcribe/")
async def transcribe_audio(file: UploadFile = File(...)):
    try:
        # Step 1: Transcribe and generate response
        transcript, response_text = await process_audio_input(file)

        # Step 2: Call ElevenLabs for audio
        voice_url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVEN_VOICE_ID}"
        headers = {
            "xi-api-key": ELEVEN_API_KEY,
            "Content-Type": "application/json"
        }
        data = {
            "text": response_text,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75
            }
        }

        response = requests.post(voice_url, headers=headers, json=data)
        if response.status_code != 200:
            raise Exception(f"Text-to-speech failed: {response.text}")

        # Step 3: Save MP3 response
        audio_path = "static/marcus_reply.mp3"
        with open(audio_path, "wb") as f:
            f.write(response.content)

        # Step 4: Return result
        return {
            "transcript": transcript,
            "response": response_text,
            "audio_url": "/static/marcus_reply.mp3"
        }

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": "Text-to-speech failed", "detail": str(e)}
        )
