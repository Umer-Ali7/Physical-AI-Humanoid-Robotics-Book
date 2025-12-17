# Quick Deploy Guide (15 Minutes)

This guide will get your app deployed on Render.com in under 15 minutes.

## Prerequisites
- [x] Code pushed to GitHub
- [x] Neon PostgreSQL database (you already have this)
- [x] Cohere API key

---

## Step 1: Push Code to GitHub (2 min)

```bash
# If not already done
git add .
git commit -m "Ready for deployment"
git push origin main
```

---

## Step 2: Deploy Auth Server (5 min)

1. Go to **https://render.com/signup**
2. Sign up/login with GitHub
3. Click **"New +"** → **"Web Service"**
4. Connect your repository
5. Fill in:
   - **Name**: `hackathon-auth-server`
   - **Root Directory**: `f-docusaurus`
   - **Build Command**: `npm install`
   - **Start Command**: `npm run auth-server`
   - **Instance Type**: **Free**

6. Click **"Advanced"** → Add Environment Variables:
   ```
   DATABASE_URL=postgresql://neondb_owner:npg_Aln14XfGRUBr@ep-wispy-butterfly-a4v5yy57-pooler.us-east-1.aws.neon.tech/neondb?sslmode=require

   BETTER_AUTH_SECRET=hackathon_secure_secret_key_min_32_chars_required_123456

   PORT=5000

   NODE_ENV=production

   FRONTEND_URL=http://localhost:3000
   ```

7. Click **"Create Web Service"**
8. **COPY YOUR URL**: `https://hackathon-auth-server.onrender.com`

---

## Step 3: Deploy Backend RAG API (5 min)

1. Render Dashboard → **"New +"** → **"Web Service"**
2. Select same repository
3. Fill in:
   - **Name**: `hackathon-rag-backend`
   - **Root Directory**: `backend`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type**: **Free**

4. Add Environment Variables:
   ```
   DATABASE_URL=postgresql://neondb_owner:npg_Aln14XfGRUBr@ep-wispy-butterfly-a4v5yy57-pooler.us-east-1.aws.neon.tech/neondb?sslmode=require

   COHERE_API_KEY=your_cohere_api_key_here

   EMBEDDING_MODEL=embed-multilingual-v3.0

   GENERATION_MODEL=command-r-plus

   LOG_LEVEL=INFO

   ADMIN_API_KEY=hackathon_admin_secret_key_123

   CORS_ORIGINS=http://localhost:3000
   ```

5. Click **"Create Web Service"**
6. **COPY YOUR URL**: `https://hackathon-rag-backend.onrender.com`

---

## Step 4: Update Frontend Code (2 min)

Update `f-docusaurus/src/lib/auth-client.ts`:

```typescript
// Replace line 1
const API_BASE_URL = 'https://hackathon-auth-server.onrender.com';
```

Update `f-docusaurus/src/services/chatApi.ts`:

```typescript
// Update the base URL
const API_BASE_URL = 'https://hackathon-rag-backend.onrender.com/api/v1';
```

Push changes:
```bash
git add .
git commit -m "Update API URLs for production"
git push origin main
```

---

## Step 5: Deploy Frontend (5 min)

1. Render Dashboard → **"New +"** → **"Static Site"**
2. Select same repository
3. Fill in:
   - **Name**: `hackathon-frontend`
   - **Root Directory**: `f-docusaurus`
   - **Build Command**: `npm install && npm run build`
   - **Publish Directory**: `build`

4. Click **"Create Static Site"**
5. **YOUR FRONTEND URL**: `https://hackathon-frontend.onrender.com`

---

## Step 6: Update CORS (2 min)

**A. Update Auth Server Environment Variable:**
1. Go to your auth server on Render
2. Environment → Edit `FRONTEND_URL`
3. Change to: `https://hackathon-frontend.onrender.com`
4. Save (will auto-redeploy)

**B. Update Backend CORS:**
1. Go to your backend on Render
2. Environment → Edit `CORS_ORIGINS`
3. Change to: `https://hackathon-frontend.onrender.com`
4. Save (will auto-redeploy)

---

## Step 7: Test Everything (1 min)

1. **Visit**: `https://hackathon-frontend.onrender.com`
2. **Click**: Login
3. **Test Signup**: Create an account
4. **Test Login**: Sign in with your account
5. **Test Chat**: Ask a question to the RAG chatbot

---

## Troubleshooting

### "Service is starting..." (Render)
- First deployment takes 3-5 minutes
- Free tier services sleep after 15 minutes of inactivity
- First request after sleep takes 30-60 seconds to wake up

### CORS Error
- Check `FRONTEND_URL` in auth server matches your frontend domain
- Check `CORS_ORIGINS` in backend matches your frontend domain
- Wait 1-2 minutes for services to redeploy after env var changes

### Database Error
- Verify `DATABASE_URL` is correct
- Check Neon DB is active (shouldn't suspend for free tier)
- Check SSL mode: `?sslmode=require`

### Auth Not Working
- Check auth server logs on Render dashboard
- Verify `BETTER_AUTH_SECRET` is at least 32 characters
- Check database tables were created (check Neon DB console)

---

## URLs Summary

After deployment, save these URLs:

```
Frontend:  https://hackathon-frontend.onrender.com
Auth API:  https://hackathon-auth-server.onrender.com
RAG API:   https://hackathon-rag-backend.onrender.com
Database:  ep-wispy-butterfly-a4v5yy57-pooler.us-east-1.aws.neon.tech
```

---

## Keep Services Awake (Bonus)

Free tier services sleep after 15 min. Keep them awake:

1. Go to **https://cron-job.org** (free)
2. Create account
3. Add 3 cron jobs (every 10 minutes):
   - `https://hackathon-auth-server.onrender.com/health`
   - `https://hackathon-rag-backend.onrender.com/api/v1/health`
   - `https://hackathon-frontend.onrender.com`

---

## Production Checklist

- [ ] All 3 services deployed and running
- [ ] Frontend can signup/login
- [ ] Frontend can chat with RAG backend
- [ ] CORS configured correctly
- [ ] Environment variables set
- [ ] Database connection working
- [ ] Services staying awake (cron-job setup)

---

## Need Help?

Check the full deployment guide: `DEPLOYMENT.md`

**Estimated Total Time**: 15-20 minutes

Good luck with your hackathon! 🚀
