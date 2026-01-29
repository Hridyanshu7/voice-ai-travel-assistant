# 🚨 Deployment Quick Fix Checklist

Use this checklist when your deployment breaks or when deploying for the first time.

---

## ❌ CORS Error: "Access-Control-Allow-Origin"

**Symptoms:**
- Frontend loads but gets stuck on "Thinking..."
- Browser console shows: `Access to fetch at 'https://...onrender.com/api/...' has been blocked by CORS policy`

**Root Cause:**
Backend doesn't allow requests from your frontend domain.

**Fix (Choose ONE):**

### Option 1: Add Environment Variable on Render (Immediate Fix)
1. Go to https://dashboard.render.com/
2. Select your backend service
3. Click **Environment** tab
4. Add or update:
   ```
   ALLOWED_ORIGINS=http://localhost:3000,https://voice-ai-travel-assistant.vercel.app
   ```
5. Click **Save Changes**
6. Wait 2-3 minutes for redeploy

### Option 2: Code Already Fixed (Wait for Auto-Deploy)
- The latest code includes the Vercel URL in the default CORS origins
- If you pushed the fix, just wait for Render to auto-deploy (~3-5 min)
- Check deployment status at: https://dashboard.render.com/

---

## 🐌 Backend Returns 503/504

**Symptoms:**
- Frontend shows "Failed to fetch" or timeout errors
- Backend URL returns 503 Service Unavailable

**Root Cause:**
Render free tier spins down after 15 minutes of inactivity.

**Fix:**
1. Wait 30-60 seconds for cold start
2. Refresh the page
3. **For Production**: Upgrade to Render Starter plan ($7/mo) for always-on service

---

## 🔑 API Key Errors

**Symptoms:**
- Backend logs show: "API key not found" or "Invalid API key"
- Features like voice or AI responses don't work

**Root Cause:**
Missing or incorrect API keys in Render environment variables.

**Fix:**
1. Go to https://dashboard.render.com/
2. Select your backend service
3. Click **Environment** tab
4. Verify these are set:
   - `ANTHROPIC_API_KEY` (required for AI)
   - `OPENAI_API_KEY` (required for voice transcription)
   - `DEEPGRAM_API_KEY` (optional, alternative STT)
   - `ELEVENLABS_API_KEY` (optional, TTS has browser fallback)
5. Click **Save Changes**

---

## 🚀 Fresh Deployment Checklist

Starting from scratch? Follow this order:

### 1. Backend (Render)
- [ ] Push code to GitHub
- [ ] Create new Web Service on Render
- [ ] Connect GitHub repo
- [ ] Set Root Directory: `backend`
- [ ] Set Build Command: `pip install -r requirements.txt`
- [ ] Set Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- [ ] Add environment variables (see below)
- [ ] Deploy and note the URL

**Required Environment Variables:**
```
ALLOWED_ORIGINS=http://localhost:3000,https://YOUR-VERCEL-URL.vercel.app
ANTHROPIC_API_KEY=your-key-here
OPENAI_API_KEY=your-key-here
DEEPGRAM_API_KEY=your-key-here
ELEVENLABS_API_KEY=your-key-here
```

### 2. Frontend (Vercel)
- [ ] Go to https://vercel.com/new
- [ ] Import your GitHub repo
- [ ] Set Root Directory: `frontend`
- [ ] Add environment variable:
  ```
  NEXT_PUBLIC_API_URL=https://YOUR-RENDER-URL.onrender.com
  ```
- [ ] Deploy

### 3. Verify
- [ ] Visit: `https://YOUR-RENDER-URL.onrender.com/health` → Should return `{"status":"healthy"}`
- [ ] Visit: `https://YOUR-VERCEL-URL.vercel.app` → Should load the app
- [ ] Send a test message → Should get AI response
- [ ] Check browser console (F12) → Should have no CORS errors

---

## 🔄 After Updating Code

### If you changed backend code:
```bash
git add .
git commit -m "Update backend"
git push origin main
```
- Render auto-deploys in ~3-5 minutes
- Check logs at: https://dashboard.render.com/

### If you changed frontend code:
```bash
git add .
git commit -m "Update frontend"
git push origin main
```
- Vercel auto-deploys in ~2-3 minutes
- Check logs at: https://vercel.com/dashboard

---

## 📞 Quick Links

- **Render Dashboard**: https://dashboard.render.com/
- **Vercel Dashboard**: https://vercel.com/dashboard
- **Backend Health Check**: https://voice-ai-travel-assistant.onrender.com/health
- **Backend API Docs**: https://voice-ai-travel-assistant.onrender.com/docs
- **Frontend**: https://voice-ai-travel-assistant.vercel.app
- **GitHub Repo**: https://github.com/Hridyanshu7/voice-ai-travel-assistant

---

## 🆘 Still Broken?

1. **Check Render Logs**: Dashboard → Your Service → Logs
2. **Check Vercel Logs**: Dashboard → Your Project → Deployments → View Logs
3. **Check Browser Console**: F12 → Console tab
4. **Verify Environment Variables**: Make sure all API keys are set correctly
5. **Try Manual Redeploy**: Render Dashboard → Manual Deploy → Deploy Latest Commit

---

**Last Updated**: 2026-01-29
**Version**: 1.1.0
