import os
import logging
from elevenlabs import ElevenLabs

logger = logging.getLogger(__name__)

def generate_audio(text: str) -> bytes:
    """
    Generates audio from text using ElevenLabs API.
    """
    try:
        api_key = os.getenv("ELEVENLABS_API_KEY")
        if not api_key:
            logger.warning("ElevenLabs API key not configured.")
            raise ValueError("ElevenLabs API key is missing.")

        client = ElevenLabs(api_key=api_key)

        # Generate audio using the correct v2.x syntax
        # Using Rachel's voice ID
        audio_generator = client.text_to_speech.convert(
            voice_id="21m00Tcm4TlvDq8ikWAM", # Rachel
            text=text,
            model_id="eleven_multilingual_v2",
            output_format="mp3_44100_128"
        )
        
        # Audio is returned as a generator of bytes
        audio_bytes = b"".join(audio_generator)
        return audio_bytes

    except Exception as e:
        logger.error(f"TTS error: {str(e)}")
        raise e
