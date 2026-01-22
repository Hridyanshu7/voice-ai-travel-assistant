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
        from app.services.claude_api import generate_response_with_claude
        
        # 1. Retrieve Knowledge
        query = question
        if context and context.get("poi_name"):
            query = f"{context['poi_name']} {question}"
        
        retrieved_docs = rag_engine.query(query)
        knowledge_text = "\n".join(retrieved_docs) if retrieved_docs else "No specific travel tips found."

        # 2. Synthesize Answer using Claude
        prompt = f"""Based on the Context and Itinerary provided, answer the user's question.

Context (Travel Knowledge):
{knowledge_text}
        
Itinerary Context: {context if context else 'None'}
        
User Question: "{question}"

Instructions:
- Answer concisely (under 60 words).
- If the answer isn't in the context, use your general knowledge.
- Be helpful and maintain a travel-expert tone."""
        
        answer = await generate_response_with_claude(prompt)
        return answer or "I'm sorry, I couldn't generate an answer right now."

    except Exception as e:
        logger.error(f"Explanation error: {str(e)}")
        return "I encountered an error trying to explain that."

