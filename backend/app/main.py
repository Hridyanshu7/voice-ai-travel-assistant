from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from dotenv import load_dotenv
import os
import logging
from app.services.stt import transcribe_audio
from app.services.tts import generate_audio
from pydantic import BaseModel

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

app = FastAPI(title="Voice Travel Assistant API")

# Configure CORS for frontend access
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8000,https://voice-ai-travel-assistant.vercel.app").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TextInput(BaseModel):
    text: str

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Voice Travel Assistant Backend is running"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.post("/api/transcribe")
async def transcribe_endpoint(file: UploadFile = File(...)):
    """
    Endpoint to transcribe audio files using OpenAI Whisper.
    """
    try:
        # Validate file type (basic check)
        if not file.content_type.startswith("audio/"):
            raise HTTPException(status_code=400, detail="Invalid file type. Please upload an audio file.")
            
        content = await file.read()
        transcript = await transcribe_audio(content, mimetype=file.content_type)
        
        if transcript.startswith("Error"):
            raise HTTPException(status_code=500, detail=transcript)
            
        return {"transcript": transcript}

    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/tts")
async def tts_endpoint(input: TextInput):
    """
    Endpoint to generate audio from text using ElevenLabs.
    """
    try:
        audio_bytes = generate_audio(input.text)
        return Response(content=audio_bytes, media_type="audio/mpeg")
    except Exception as e:
        logger.error(f"TTS endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

from typing import List, Dict, Optional, Any

class IntentInput(BaseModel):
    text: str
    existing_constraints: Optional[Dict[str, Any]] = None
    history: List[Dict[str, Any]] = []

@app.post("/api/analyze-intent")
async def analyze_intent_endpoint(input: IntentInput):
    """
    Endpoint to analyze text and extract trip constraints using Gemini.
    """
    try:
        from app.services.planner import extract_constraints
        constraints = await extract_constraints(input.text, input.existing_constraints, input.history)
        return constraints
    except Exception as e:
        logger.error(f"Intent analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/plan-trip")
async def plan_trip_endpoint(constraints: dict):
    """
    Endpoint to generate a trip itinerary based on constraints.
    """
    try:
        from app.mcp.itinerary import build_itinerary, BuildItineraryRequest
        
        if not constraints.get("destination_city"):
             raise HTTPException(status_code=400, detail="Missing destination city")
             
        # Map constraints to request model
        req = BuildItineraryRequest(
            city=str(constraints.get("destination_city")),
            days=int(constraints.get("duration_days", 3)),
            pace=str(constraints.get("pace", "moderate")),
            interests=constraints.get("interests", []),
            must_visit=constraints.get("must_visit", []),
            budget=str(constraints.get("budget_level", "Moderate")),
            start_date=constraints.get("start_date")
        )
        
        itinerary = await build_itinerary(req)
        return itinerary
    except Exception as e:
        logger.error(f"Trip planning error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/query-rag")
async def query_rag_endpoint(input: TextInput):
    """
    Endpoint to query the RAG system for travel tips.
    """
    try:
        from app.services.rag_engine import rag_engine
        results = rag_engine.query(input.text)
        return {"results": results}
    except Exception as e:
        logger.error(f"RAG query error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/explain")
async def explain_endpoint(input: TextInput):
    """
    Endpoint to answer questions or explain itinerary choices.
    """
    try:
        from app.services.explanation import generate_explanation
        answer = await generate_explanation(input.text)
        return {"answer": answer}
    except Exception as e:
        logger.error(f"Explanation endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/generate-pdf")
async def generate_pdf_endpoint(itinerary: dict, background_tasks: BackgroundTasks):
    """
    Endpoint to generate PDF for the given itinerary.
    """
    try:
        from app.services.pdf_generator import generate_pdf
        from fastapi.responses import FileResponse
        
        file_path = generate_pdf(itinerary)
        
        # Schedule file deletion after response is sent
        background_tasks.add_task(os.remove, file_path)
        
        return FileResponse(file_path, media_type='application/pdf', filename="trip_itinerary.pdf")
    except Exception as e:
        logger.error(f"PDF generation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
