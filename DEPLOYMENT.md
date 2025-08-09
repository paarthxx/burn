# Deployment Guide

This guide will help you deploy your Burning Man Expert Chatbot with a separate backend and frontend.

## Architecture
- **Frontend**: GitHub Pages (static hosting) - `https://paarthxx.github.io/burn/`
- **Backend**: Render (FREE Python hosting) - API endpoints
## 🛠️ IMPORTANT DEPLOYMENT FIX

**RESOLVED**: Updated `requirements.txt` with packages that have pre-built wheels to avoid Rust compilation errors:
- `fastapi==0.115.0` (latest stable with pre-built wheels)
- `uvicorn==0.30.0` (updated for compatibility)
- `sentence-transformers==3.0.1` (latest with pre-built wheels)
- `pydantic==2.9.0` (newer version with pydantic-core pre-built wheels)
- `numpy==1.26.4` (stable version with broad compatibility)

The deployment failures were due to `pydantic-core` needing Rust compilation in a read-only filesystem environment. These updated versions use pre-built wheels and avoid build dependency issues.


## Step 1: Deploy Backend to Render (FREE)

1. **Create Render Account**
   - Go to [render.com](https://render.com)
   - Sign up with your GitHub account (completely free)

2. **Deploy Web Service**
   - Click "New +" → "Web Service"
   - Connect your GitHub account
   - Select your `burn` repository
   - Configure the deployment:
     - **Name**: `burn-chatbot-api` (or any name you prefer)
     - **Environment**: `Python 3`
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `uvicorn backend.app:app --host 0.0.0.0 --port $PORT`
     - **Plan**: Select "Free" (750 hours/month, $0)

3. **Deploy**
   - Click "Create Web Service"
   - Render will automatically build and deploy your app
   - This takes 5-10 minutes for the first deployment

4. **Get Your API URL**
   - Once deployed, Render gives you a URL like: `https://burn-chatbot-api.onrender.com`
   - Copy this URL - you'll need it for Step 2

## Step 2: Update Frontend Configuration

1. **Update API URL**
   - Edit `assets/scripts/script.js`
   - Find this line:
   ```javascript
   production: 'https://your-app-name.railway.app' // You'll need to update this after deployment
   ```
   - Replace `https://your-app-name.railway.app` with your actual Render URL (e.g., `https://burn-chatbot-api.onrender.com`)

2. **Commit and Push to GitHub**
   ```bash
   git add assets/scripts/script.js
   git commit -m "Update API endpoint for production"
   git push origin main
   ```

3. **GitHub Pages will automatically update** (may take a few minutes)

## Step 3: Test the Deployment

1. Visit `https://paarthxx.github.io/burn/`
2. Try asking a question
3. Check browser console for any errors
4. Verify the API calls are going to your Railway backend

## Environment Detection

The frontend automatically detects the environment:
- **Local development**: Uses `http://localhost:8000`
- **Production**: Uses your Render backend URL

## Files Created for Deployment

- `requirements.txt` - Python dependencies
- `Procfile` - Railway deployment configuration
- `DEPLOYMENT.md` - This guide

## Troubleshooting

### Backend Issues
- Check Render logs in your dashboard
- Ensure all dependencies are in `requirements.txt`
- The start command should be: `uvicorn backend.app:app --host 0.0.0.0 --port $PORT`

### Frontend Issues  
- Check browser console for errors
- Verify the API URL is correct in `script.js`
- Ensure CORS is properly configured (already done)

### CORS Errors
The backend is configured to allow requests from:
- `https://paarthxx.github.io`
- `http://localhost:8000` (for local development)

## Updating After Deployment

1. **Backend changes**: Push to GitHub, Render auto-deploys from your main branch
2. **Frontend changes**: Push to GitHub, GitHub Pages auto-updates
3. **No need to redeploy both** - they're independent

## Why Render Free Tier is Perfect

- **750 hours/month free** (31 days × 24 hours = 744 hours)
- **Automatic HTTPS**
- **Auto-deployments** from GitHub
- **No credit card required**
- **Sleeps after 15 minutes of inactivity** (wakes up in ~30 seconds)
- **Perfect for personal projects**