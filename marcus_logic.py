import tempfile
import os
import requests
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables from .env file
load_dotenv()

# Load API keys from environment
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ELEVEN_API_KEY = os.getenv("ELEVEN_API_KEY")
ELEVEN_VOICE_ID = os.getenv("ELEVEN_VOICE_ID")

# Initialize OpenAI client
openai_client = OpenAI(api_key=OPENAI_API_KEY)

async def process_audio_input(file):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    # Transcribe audio
    with open(tmp_path, "rb") as audio_file:
        transcription = openai_client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file
        )

    transcript = transcription.text

    # Get response from Marcus
    response = openai_client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are Marcus Aurelius, respond with calm stoic wisdom."},
            {"role": "user", "content": transcript}
        ]
    )
    reply_text = response.choices[0].message.content

    return transcript, reply_text
