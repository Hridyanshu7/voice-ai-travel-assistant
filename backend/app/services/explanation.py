import httpx
import os
import logging
from app.services.rag_engine import rag_engine

logger = logging.getLogger(__name__)

async def generate_explanation(question: str, context: dict = None) -> str:
    """
    Generates an explanation for a user's question about the itinerary.
    Uses RAG to find relevant facts and OpenRouter to synthesize the answer.
    """
    try:
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
             return "I'm sorry, I can't explain that right now (API key missing)."
        
        # 1. Retrieve Knowledge
        query = question
        if context and context.get("poi_name"):
            query = f"{context['poi_name']} {question}"
        
        retrieved_docs = rag_engine.query(query)
        knowledge_text = "\n".join(retrieved_docs) if retrieved_docs else "No specific travel tips found."

        # 2. Synthesize Answer using OpenRouter
        prompt = f"""You are a travel assistant. Answer the user's question based on the Context provided.
        
Context (Travel Tips):
{knowledge_text}
        
Itinerary Context: {context if context else 'None'}
        
User Question: "{question}"
        
Answer concisely (under 50 words). If the answer isn't in the context, use general knowledge but mention it's general advice."""
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "google/gemini-2.0-flash-exp:free",
                    "messages": [{"role": "user", "content": prompt}]
                }
            )
            
            if response.status_code != 200:
                return "I'm having trouble generating an answer right now. Please try again in a moment."
            
            result = response.json()
            return result["choices"][0]["message"]["content"].strip()

    except Exception as e:
        logger.error(f"Explanation error: {str(e)}")
        return "I encountered an error trying to explain that."

