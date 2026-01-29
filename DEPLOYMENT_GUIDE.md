# 🚀 Deployment Guide: Voice Travel Assistant

This guide will help you deploy your Voice AI Travel Assistant to production using Render (backend) and Vercel (frontend).

---

## 📋 Pre-Deployment Checklist

Before deploying, ensure you have:

- [ ] GitHub repository with your code
- [ ] Render account (https://render.com)
- [ ] Vercel account (https://vercel.com)
- [ ] All required API keys:
  - Anthropic API Key (Claude)
  - OpenAI API Key (Whisper STT)
  - Deepgram API Key (Alternative STT)
  - ElevenLabs API Key (TTS - optional, has browser fallback)

---

## 🔧 Part 1: Backend Deployment (Render)

### Option A: Using Render Blueprint (Recommended) ⭐

This project includes a `render.yaml` file that automates the deployment configuration.

1. **Push to GitHub**
   ```bash
   git add render.yaml
   git commit -m "Add Render Blueprint configuration"
   git push origin main
   ```

2. **Create New Blueprint on Render**
   - Go to https://dashboard.render.com/
   - Click **"New +"** → **"Blueprint"**
   - Connect your GitHub repository
   - Select the repository: `voice-ai-travel-assistant`
   - Render will automatically detect `render.yaml`

3. **Add Secret Environment Variables**
   
   The `render.yaml` file handles most configuration, but you need to manually add API keys for security:
   
   - Go to your service → **Environment** tab
   - Add these variables:
     - `ANTHROPIC_API_KEY` = `your-claude-api-key`
     - `OPENAI_API_KEY` = `your-openai-api-key`
     - `DEEPGRAM_API_KEY` = `your-deepgram-api-key`
     - `ELEVENLABS_API_KEY` = `your-elevenlabs-api-key` (optional)

4. **Deploy**
   - Click **"Apply"** or **"Create Blueprint"**
   - Wait for deployment to complete (~3-5 minutes)
   - Note your backend URL: `https://voice-ai-travel-assistant.onrender.com`

### Option B: Manual Setup (Alternative)

If you prefer manual setup:

1. **Create New Web Service**
   - Go to https://dashboard.render.com/
   - Click **"New +"** → **"Web Service"**
   - Connect your GitHub repository

2. **Configure Service**
   - **Name**: `voice-ai-travel-assistant`
   - **Region**: Choose closest to your users
   - **Branch**: `main`
   - **Root Directory**: `backend`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

3. **Add Environment Variables**
   
   Go to **Environment** tab and add:
   
   ```
   ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000,https://voice-ai-travel-assistant.vercel.app
   ANTHROPIC_API_KEY=your-claude-api-key
   OPENAI_API_KEY=your-openai-api-key
   DEEPGRAM_API_KEY=your-deepgram-api-key
   ELEVENLABS_API_KEY=your-elevenlabs-api-key
   TRAVEL_DATA_MCP_URL=http://localhost:8001
   ITINERARY_MCP_URL=http://localhost:8002
   PYTHON_VERSION=3.11.5
   ```

4. **Deploy**
   - Click **"Create Web Service"**
   - Wait for deployment (~3-5 minutes)

---

## 🎨 Part 2: Frontend Deployment (Vercel)

1. **Import Project to Vercel**
   - Go to https://vercel.com/new
   - Click **"Import Git Repository"**
   - Select your repository: `voice-ai-travel-assistant`

2. **Configure Project**
   - **Framework Preset**: Next.js (auto-detected)
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build` (default)
   - **Output Directory**: `.next` (default)

3. **Add Environment Variable**
   
   In the **Environment Variables** section, add:
   
   ```
   NEXT_PUBLIC_API_URL=https://voice-ai-travel-assistant.onrender.com
   ```
   
   ⚠️ **Important**: Replace with your actual Render backend URL from Part 1

4. **Deploy**
   - Click **"Deploy"**
   - Wait for deployment (~2-3 minutes)
   - Your app will be live at: `https://voice-ai-travel-assistant.vercel.app`

---

## ✅ Part 3: Verify Deployment

### Test Backend
1. Visit: `https://voice-ai-travel-assistant.onrender.com/health`
2. Should return: `{"status": "healthy"}`

### Test Frontend
1. Visit: `https://voice-ai-travel-assistant.vercel.app`
2. Try sending a message in the chat
3. Check browser console (F12) for any CORS errors

### Common Issues

**CORS Error: "Access-Control-Allow-Origin"**
- **Cause**: Backend doesn't allow frontend origin
- **Fix**: Add your Vercel URL to `ALLOWED_ORIGINS` on Render
  ```
  ALLOWED_ORIGINS=http://localhost:3000,https://voice-ai-travel-assistant.vercel.app
  ```

**Backend Returns 503/504**
- **Cause**: Render free tier spins down after inactivity
- **Fix**: Wait 30-60 seconds for cold start, or upgrade to paid plan

**API Key Errors**
- **Cause**: Missing or invalid API keys
- **Fix**: Double-check all API keys in Render environment variables

---

## 🔄 Part 4: Updating Your Deployment

### Update Backend
```bash
# Make changes to backend code
git add .
git commit -m "Update backend"
git push origin main
```
Render will automatically redeploy (if auto-deploy is enabled).

### Update Frontend
```bash
# Make changes to frontend code
git add .
git commit -m "Update frontend"
git push origin main
```
Vercel will automatically redeploy.

### Update Environment Variables
- **Render**: Dashboard → Your Service → Environment → Add/Edit
- **Vercel**: Dashboard → Your Project → Settings → Environment Variables

---

## ⚠️ Important Considerations

### 1. Persistent Storage (ChromaDB)
- The RAG system uses local storage (`./chroma_db`)
- **On Render Free Tier**: Files are wiped on redeploy
- **Solution**: The app re-populates seed data on startup if missing
- **For Production**: Consider using Render Persistent Disks or external vector DB

### 2. API Costs & Quotas
- **Claude (Anthropic)**: Pay-per-use, monitor at https://console.anthropic.com
- **OpenAI Whisper**: Pay-per-use, monitor at https://platform.openai.com/usage
- **Deepgram**: Free tier available, monitor at https://console.deepgram.com
- **ElevenLabs**: Free tier limited, app falls back to browser TTS if quota exceeded

### 3. Security Best Practices
- ✅ Never commit `.env` files to GitHub
- ✅ Use environment variables for all secrets
- ✅ Restrict CORS to specific domains (avoid `allow_origins=["*"]`)
- ✅ Enable HTTPS only in production
- ✅ Regularly rotate API keys

### 4. Performance Optimization
- **Render Free Tier**: Spins down after 15 min inactivity (cold start ~30s)
- **Upgrade to Starter ($7/mo)**: Always-on, faster performance
- **Vercel**: Free tier is generous for hobby projects

---

## 📊 Monitoring & Logs

### Render Logs
- Dashboard → Your Service → Logs
- Monitor API errors, startup issues, crashes

### Vercel Logs
- Dashboard → Your Project → Deployments → View Function Logs
- Monitor frontend errors, build issues

---

## 🎉 You're Done!

Your Voice AI Travel Assistant is now live! Share your deployment:
- **Frontend**: `https://voice-ai-travel-assistant.vercel.app`
- **Backend API Docs**: `https://voice-ai-travel-assistant.onrender.com/docs`

---

## 🆘 Need Help?

- **Render Docs**: https://render.com/docs
- **Vercel Docs**: https://vercel.com/docs
- **Check Issues**: Review browser console and server logs
- **CORS Issues**: Ensure `ALLOWED_ORIGINS` includes your Vercel URL
