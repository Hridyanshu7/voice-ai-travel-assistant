import google.generativeai as genai
import os
from dotenv import load_dotenv

# Run from backend/tests, so load from ../.env
load_dotenv(os.path.join(os.path.dirname(__file__), "../.env"))

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("Error: GEMINI_API_KEY not found in .env")
else:
    print(f"Using API Key: {api_key[:5]}...")
    try:
        genai.configure(api_key=api_key)
        print("Listing models that support generateContent:")
        found = False
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f"- {m.name}")
                found = True
        if not found:
            print("No models found supporting generateContent.")
    except Exception as e:
        print(f"Error listing models: {e}")
