import asyncio
import os
from dotenv import load_dotenv

# Load env from backend/.env
load_dotenv("../.env")

try:
    from app.services.stt import transcribe_audio
except ImportError:
    import sys
    sys.path.append("..")
    from app.services.stt import transcribe_audio

async def test_stt():
    print("Testing STT...")
    api_key = os.getenv("OPENAI_API_KEY")
    print(f"API Key present: {bool(api_key)}")
    if api_key:
        print(f"API Key start: {api_key[:10]}...")
    
    # Create a dummy small wav/webm file in memory or just send random bytes 
    # (Whisper might reject random bytes, but checking if imports work and client headers are set)
    # Better: use a small real file if possible, but for now just check if the function runs.
    # We'll send a tiny valid wav header if possible, or just fail at the API level.
    
    # Tiny WAV header (44 bytes) for empty audio
    dummy_wav = b'RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00D\xac\x00\x00\x88X\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00'
    
    result = await transcribe_audio(dummy_wav, mimetype="audio/wav")
    print(f"Result: {result}")

if __name__ == "__main__":
    asyncio.run(test_stt())
