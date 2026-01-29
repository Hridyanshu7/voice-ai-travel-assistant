# 🌍 Voice AI Travel Assistant

A premium, voice-enabled AI travel companion that builds rich, personalized itineraries through natural conversation.

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![License](https://img.shields.io/badge/license-MIT-green)

## ✨ Core Features

- **🗣️ Natural Voice Conversation**: Built-in STT (Speech-to-Text) and TTS (Text-to-Speech) with fail-safe browser fallbacks.
- **🗺️ Expert Itinerary Curation**: Uses Claude 3.5 Sonnet to curate multi-page, professional travel guides.
- **📅 Smart Constraints Extraction**: understands destinations, budgets (e.g., "6,000 INR"), dates, and specific interests from natural speech.
- **📍 Real-time Knowledge**: Integrates with OpenStreetMap, Wikivoyage, and Open-Meteo for accurate POIs and weather forecasts.
- **📄 Portable Markdown Export**: Download your itinerary as a formatted Markdown file, perfect for saving to Notion or Obsidian.
- **🤖 Adaptive AI**: Multi-layered fallback system using Claude 3.5 Sonnet, Gemini Pro, and local RAG.

## 🛠️ Technology Stack

- **Frontend**: Next.js 15+, TypeScript, Tailwind CSS, Framer Motion (for smooth animations).
- **Backend**: FastAPI (Python), uvicorn.
- **AI Models**: Claude 3.5 Sonnet (Curation), Gemini Pro (Intent Analysis), Deepgram (STT).
- **Voice**: ElevenLabs (Premium Rachel Voice) + Web Speech API Fallback.
- **Database**: ChromaDB (Vector store for RAG).
- **Data APIs**: Overpass API (OSM), Wikivoyage API, Open-Meteo.

## 🚀 Quick Start

### Backend Setup
1. `cd backend`
2. Create virtual environment: `python -m venv venv`
3. Activate: `venv\Scripts\activate` (Windows) or `source venv/bin/activate` (Mac/Linux)
4. Install dependencies: `pip install -r requirements.txt`
5. Configure `.env` with API keys.
6. Run: `uvicorn app.main:app --reload`

### Frontend Setup
1. `cd frontend`
2. Install dependencies: `npm install`
3. Configure `.env.local` with `NEXT_PUBLIC_API_URL=http://localhost:8000`
4. Run: `npm run dev`

## 📖 Deployment

For detailed deployment instructions on Render/Vercel, please see [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md).

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.
