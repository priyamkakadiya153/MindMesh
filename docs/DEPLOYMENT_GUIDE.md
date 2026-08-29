# MindMesh Production Deployment Guide

This guide provides step-by-step instructions to deploy MindMesh to production using free-tier friendly and battle-tested cloud providers.

---

## Architecture Overview

```
                          ┌───────────────────────────┐
                          │   Client Browser / PWA    │
                          └─────────────┬─────────────┘
                                        │
                         HTTPS / WSS    │
                                        ▼
    ┌───────────────────────────┐               ┌───────────────────────────┐
    │     Vercel / Netlify      │               │     Render / Railway      │
    │  (Frontend React + Vite)  │ ────────────> │     (FastAPI Backend)     │
    └───────────────────────────┘  REST / WS    └─────────────┬─────────────┘
                                                              │
                                   ┌──────────────────────────┼──────────────────────────┐
                                   ▼                          ▼                          ▼
                     ┌──────────────────────────┐ ┌────────────────────────┐ ┌───────────────────────┐
                     │    Supabase / Neon       │ │     Upstash Redis      │ │   Google Gemini AI    │
                     │ (PostgreSQL + pgvector)  │ │ (Caching & Rate Limit) │ │ (LLM & Embeddings)    │
                     └──────────────────────────┘ └────────────────────────┘ └───────────────────────┘
```

---

## Step 1: Database Setup (Supabase with pgvector)

1. Go to [supabase.com](https://supabase.com) and create a free account.
2. Click **New Project** and choose a project name (e.g. `mindmesh-db`) and a secure password.
3. Once the database is provisioned:
   - Go to **Project Settings** -> **Database**.
   - Under **Connection String**, select **URI** (choose `Transaction pooler` or `Direct connection`).
   - Copy the URI. It will look like:
     ```
     postgresql://postgres.[PROJECT_REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres
     ```
4. **Enable pgvector**:
   - In the Supabase Dashboard, go to **Database** -> **Extensions**.
   - Search for `vector` and ensure it is toggled **ON** (enabled).

---

## Step 2: Redis Setup (Upstash Redis)

1. Go to [upstash.com](https://upstash.com) and sign in.
2. Click **Create Database**.
3. Name: `mindmesh-redis`, select Primary Region closest to your database.
4. Once created, copy the **Redis Connection String (TLS / standard URL)**:
   ```
   rediss://default:[PASSWORD]@[HOST]:[PORT]
   ```

---

## Step 3: Backend Deployment (Render or Railway)

### Option A: Render (Recommended)
1. Go to [render.com](https://render.com) and sign in with GitHub.
2. Click **New +** -> **Web Service**.
3. Connect your **MindMesh** GitHub repository.
4. Configure the Web Service:
   - **Name**: `mindmesh-api`
   - **Region**: Same region as your Supabase DB (e.g., Frankfurt, Oregon, Singapore)
   - **Root Directory**: `apps/api`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Add **Environment Variables**:
   | Variable | Value | Notes |
   | :--- | :--- | :--- |
   | `PORT` | `4000` | Render assigns `$PORT` dynamically |
   | `NODE_ENV` | `production` | Production mode |
   | `DATABASE_URL` | `postgresql://...` | Your Supabase PostgreSQL URL |
   | `REDIS_URL` | `rediss://...` | Your Upstash Redis URL |
   | `JWT_SECRET` | *(Random 32+ char string)* | Access token signing key |
   | `JWT_REFRESH_SECRET` | *(Random 32+ char string)* | Refresh token signing key |
   | `GEMINI_API_KEY` | `AIzaSy...` | Your Google AI Studio API key |
   | `SMTP_HOST` | `smtp.gmail.com` | SMTP Server |
   | `SMTP_PORT` | `587` | SMTP Port |
   | `SMTP_USERNAME` | `your_email@gmail.com` | Gmail / SMTP sender |
   | `SMTP_PASSWORD` | `your_app_password` | Gmail 16-character App Password |
   | `SMTP_FROM_EMAIL` | `your_email@gmail.com` | From email address |
   | `SMTP_USE_TLS` | `true` | TLS encryption |

6. Click **Create Web Service**. Render will deploy the API and give you a URL (e.g., `https://mindmesh-api.onrender.com`).

---

## Step 4: Frontend Deployment (Vercel)

1. Go to [vercel.com](https://vercel.com) and log in with GitHub.
2. Click **Add New...** -> **Project**.
3. Import your **MindMesh** repository.
4. In the configuration screen:
   - **Framework Preset**: `Vite`
   - **Root Directory**: Click **Edit** and choose `apps/web`.
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
5. Add **Environment Variables**:
   | Variable | Value | Description |
   | :--- | :--- | :--- |
   | `VITE_API_URL` | `https://mindmesh-api.onrender.com` | Your Render Backend API URL |
6. Click **Deploy**. Vercel will build and launch your frontend at `https://mindmesh.vercel.app`.

---

## Step 5: Verification & Post-Deployment Checklist

1. Open your Vercel URL in your browser.
2. Verify you can sign up / login via OTP (check Gmail for the OTP code).
3. Test uploading a PDF or document in the Knowledge/Documents tab.
4. Test asking questions in the AI Chat tab to verify Gemini semantic search and pgvector retrieval.
