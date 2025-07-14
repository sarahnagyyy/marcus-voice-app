import os
import requests
import json
from fastapi import FastAPI, Request, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv
from marcus_logic import process_audio_input

load_dotenv()

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ELEVEN_API_KEY = os.getenv("ELEVEN_API_KEY")
ELEVEN_VOICE_ID = os.getenv("ELEVEN_VOICE_ID")

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


import json  # add at the top if not already present

@app.post("/transcribe/")
async def transcribe_audio(file: UploadFile = File(...)):
    transcript, response_text = await process_audio_input(file)

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

    # NEW: Check if ElevenLabs audio generation failed
    if response.status_code != 200:
        print("❌ ElevenLabs API Error:", response.status_code)
        print("Response:", response.text)
        return {"error": "Text-to-speech failed"}

    # Save the audio response
    audio_path = "static/marcus_reply.mp3"
    with open(audio_path, "wb") as f:
        f.write(response.content)

    return {
        "transcript": transcript,
        "response": response_text,
        "audio_url": "/static/marcus_reply.mp3"
    }
    except Exception as e:
    return JSONResponse(status_code=500, content={"error": "Internal Server Error", "detail": str(e)})
