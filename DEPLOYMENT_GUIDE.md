# 🚀 Deployment Guide: Voice Travel Assistant

Follow these steps to deploy your application publicly.

## 1. Backend (FastAPI)
The backend is a Python FastAPI app. You can deploy it to **Render**, **Railway**, or **Fly.io**.

### Steps for Render:
1. Create a new **Web Service** on Render.
2. Connect your GitHub repository.
3. Set **Environment**: `Python 3`.
4. Set **Build Command**: `pip install -r requirements.txt`.
5. Set **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
6. **Environment Variables**: Add all variables from `backend/.env` (ANTHROPIC_API_KEY, GEMINI_API_KEY, DEEPGRAM_API_KEY, etc.).
7. Add `ALLOWED_ORIGINS`: Set this to your frontend URL (e.g., `https://your-app.vercel.app`).

## 2. Frontend (Next.js)
The frontend is best deployed on **Vercel**.

### Steps for Vercel:
1. Push your code to GitHub.
2. Import the project into Vercel.
3. Select the `frontend` directory as the root.
4. **Environment Variables**: Add `NEXT_PUBLIC_API_URL` and set it to your **Backend URL** (e.g., `https://your-backend.onrender.com`).
5. Deploy!

## ⚠️ Important Considerations

### 1. Persistent Storage (ChromaDB)
The current RAG system uses a local folder (`./chroma_db`).
- On **Render/Railway**, local files are wiped on redeploy unless you use **Persistent Disks/Volumes**.
- For a simple demo, the app will re-populate the seed data every time it boots if the folder is missing.

### 2. API Keys
Ensure all your API keys are added to the deployment platforms as environment variables. **Never commit your `.env` files to GitHub**.

### 3. Costs
- **ElevenLabs**: Your free quota is currently used up. The app has been updated to switch to **Browser TTS** if the API fails, so it will still work publicly!
- **Gemini/Claude**: Monitor your usage on their respective dashboards.

---
**The code is now production-ready with environment variable support for API URLs and CORS!**
