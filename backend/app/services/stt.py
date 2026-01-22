import os
import logging
import httpx

logger = logging.getLogger(__name__)

async def transcribe_audio(audio_data: bytes, mimetype: str = "audio/webm") -> str:
    """
    Transcribes the given audio data using Deepgram API.
    """
    try:
        api_key = os.getenv("DEEPGRAM_API_KEY")
        if not api_key:
            logger.warning("Deepgram API key not configured.")
            return "Error: Deepgram API key is missing. Please configure DEEPGRAM_API_KEY in backend/.env"

        # Deepgram API endpoint
        url = "https://api.deepgram.com/v1/listen"
        
        headers = {
            "Authorization": f"Token {api_key}",
            "Content-Type": mimetype
        }
        
        params = {
            "model": "nova-2",
            "smart_format": "true",
            "punctuate": "true"
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                url,
                headers=headers,
                params=params,
                content=audio_data
            )
            
            if response.status_code != 200:
                logger.error(f"Deepgram API error: {response.status_code} - {response.text}")
                return f"Error: Deepgram API returned {response.status_code}"
            
            result = response.json()
            
            # Extract transcript from Deepgram response
            transcript = result.get("results", {}).get("channels", [{}])[0].get("alternatives", [{}])[0].get("transcript", "")
            
            if not transcript:
                logger.warning("Deepgram returned empty transcript")
                return "Error: No speech detected in audio"
            
            return transcript.strip()

    except Exception as e:
        logger.error(f"Transcription error: {str(e)}")
        return f"Error during transcription: {str(e)}"
