from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import openai
import requests
import tempfile
import os

# Initialize app
app = FastAPI()

# Allow frontend access (for local testing or deployed frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ELEVEN_API_KEY = os.getenv("ELEVEN_API_KEY")
ELEVEN_VOICE_ID = os.getenv("ELEVEN_VOICE_ID", "pqHfZKP75CvOlQylNhV4")

openai.api_key = OPENAI_API_KEY

@app.post("/ask")
async def ask_marcus(file: UploadFile = File(...)):
    # Save uploaded audio to a temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    # Transcribe with Whisper
    try:
        with open(tmp_path, "rb") as f:
            transcript = openai.Audio.transcribe(
                model="whisper-1",
                file=f
            )
        user_text = transcript["text"]
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"Transcription failed: {str(e)}"})

    # Get Marcus response from GPT-4
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": (
                    "You are Marcus Aurelius, Roman emperor and Stoic philosopher."
                    " Speak with calm wisdom, brevity, and grounded Stoic insight."
                    " Refer to your writings in 'Meditations' when relevant."
                )},
                {"role": "user", "content": user_text}
            ]
        )
        marcus_text = response.choices[0].message["content"]
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"GPT failed: {str(e)}"})

    # Generate audio with ElevenLabs
    try:
        eleven_url = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVEN_VOICE_ID}"
        headers = {
            "xi-api-key": ELEVEN_API_KEY,
            "Content-Type": "application/json"
        }
        data = {
            "text": marcus_text,
            "model_id": "eleven_monolingual_v1"
        }
        audio_resp = requests.post(eleven_url, headers=headers, json=data)

        audio_path = os.path.join(tempfile.gettempdir(), "marcus_reply.mp3")
        with open(audio_path, "wb") as f:
            f.write(audio_resp.content)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"ElevenLabs failed: {str(e)}"})

    return FileResponse(audio_path, media_type="audio/mpeg", filename="marcus_reply.mp3")
