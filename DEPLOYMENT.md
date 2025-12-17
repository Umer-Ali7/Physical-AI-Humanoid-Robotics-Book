# Deployment Guide

Complete deployment guide for your 3-service architecture:
1. **Auth Server** (Node.js/Express on port 5000)
2. **Frontend** (Docusaurus/React)
3. **Backend RAG API** (Python/FastAPI on port 8000)

---

## Quick Start - Deploy Everything in 15 Minutes

### Prerequisites
- [ ] GitHub repository (push your code)
- [ ] PostgreSQL database (✅ Already have Neon DB)
- [ ] Cohere API key (for RAG backend)

---

## Option 1: Render.com (Recommended - Free Tier Available)

### 1. Deploy Auth Server

**A. Update package.json**
Add this script to `f-docusaurus/package.json`:
```json
"scripts": {
  "auth-server": "node auth-server.js",
  "start": "docusaurus start"
}
```

**B. Create Render Web Service**
1. Go to https://render.com → New → Web Service
2. Connect your GitHub repo
3. Configure:
   - **Name**: `your-app-auth-server`
   - **Root Directory**: `f-docusaurus`
   - **Runtime**: Node
   - **Build Command**: `npm install`
   - **Start Command**: `npm run auth-server`
   - **Instance Type**: Free

**C. Environment Variables** (Add in Render Dashboard):
```bash
DATABASE_URL=postgresql://neondb_owner:npg_Aln14XfGRUBr@ep-wispy-butterfly-a4v5yy57-pooler.us-east-1.aws.neon.tech/neondb?sslmode=require
BETTER_AUTH_SECRET=your_production_secret_here_min_32_chars_123456789
BETTER_AUTH_URL=https://your-app-auth-server.onrender.com
PORT=5000
NODE_ENV=production
```

**D. Deploy**: Click "Create Web Service"
- Your auth server will be at: `https://your-app-auth-server.onrender.com`

---

### 2. Deploy Frontend (Docusaurus)

**A. Update CORS in auth-server.js**
Update line 22-24 to allow your frontend domain:
```javascript
app.use(cors({
  origin: process.env.FRONTEND_URL || 'http://localhost:3000',
  credentials: true
}));
```

**B. Update API Base URL in Frontend**
Update `f-docusaurus/src/lib/auth-client.ts` line 1:
```typescript
const API_BASE_URL = process.env.REACT_APP_AUTH_URL || 'https://your-app-auth-server.onrender.com';
```

**C. Create Render Static Site**
1. Render Dashboard → New → Static Site
2. Configure:
   - **Name**: `your-app-frontend`
   - **Root Directory**: `f-docusaurus`
   - **Build Command**: `npm install && npm run build`
   - **Publish Directory**: `build`

**D. Environment Variables**:
```bash
REACT_APP_AUTH_URL=https://your-app-auth-server.onrender.com
REACT_APP_RAG_API_URL=https://your-app-rag-backend.onrender.com
NODE_VERSION=20
```

---

### 3. Deploy Python RAG Backend

**A. Check if requirements.txt exists**
Already exists at `backend/requirements.txt`

**B. Create Render Web Service**
1. Render Dashboard → New → Web Service
2. Configure:
   - **Name**: `your-app-rag-backend`
   - **Root Directory**: `backend`
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type**: Free

**C. Environment Variables**:
```bash
DATABASE_URL=postgresql://neondb_owner:npg_Aln14XfGRUBr@ep-wispy-butterfly-a4v5yy57-pooler.us-east-1.aws.neon.tech/neondb?sslmode=require
COHERE_API_KEY=your_cohere_api_key
EMBEDDING_MODEL=embed-multilingual-v3.0
GENERATION_MODEL=command-r-plus
LOG_LEVEL=INFO
ADMIN_API_KEY=your_secure_admin_key_here
CORS_ORIGINS=https://your-app-frontend.onrender.com
```

---

### 4. Update CORS Settings

**Auth Server** (`f-docusaurus/auth-server.js`):
```javascript
app.use(cors({
  origin: [
    'http://localhost:3000',
    'https://your-app-frontend.onrender.com'
  ],
  credentials: true
}));
```

**RAG Backend** (`backend/app/config.py`):
Already configured with CORS_ORIGINS env var

---

## Option 2: Railway.app (Alternative - $5/month credit)

### Deploy All Services

**1. Install Railway CLI**
```bash
npm install -g @railway/cli
railway login
```

**2. Deploy Auth Server**
```bash
cd f-docusaurus
railway init
railway up
railway variables set DATABASE_URL="your_db_url"
railway variables set BETTER_AUTH_SECRET="your_secret"
railway domain  # Get your domain
```

**3. Deploy Frontend**
```bash
cd f-docusaurus
railway init
railway up
railway variables set REACT_APP_AUTH_URL="https://your-auth-domain"
```

**4. Deploy Backend**
```bash
cd backend
railway init
railway up
railway variables set DATABASE_URL="your_db_url"
railway variables set COHERE_API_KEY="your_key"
```

---

## Option 3: Vercel (Frontend) + Render (Backend Services)

### Frontend on Vercel (Best Performance)

**1. Deploy Frontend**
```bash
cd f-docusaurus
npm install -g vercel
vercel login
vercel
```

**2. Configure Vercel**
- Build Command: `npm run build`
- Output Directory: `build`
- Framework Preset: Other

**3. Environment Variables** (Vercel Dashboard):
```bash
REACT_APP_AUTH_URL=https://your-app-auth-server.onrender.com
REACT_APP_RAG_API_URL=https://your-app-rag-backend.onrender.com
```

**4. Deploy Auth & Backend on Render** (See Option 1)

---

## Option 4: DigitalOcean App Platform

### One-Click Deployment

**1. Create App**
- Go to https://cloud.digitalocean.com/apps
- Create App → GitHub → Select Repo

**2. Configure Components**:

**Auth Server**:
- Type: Web Service
- Source: `f-docusaurus`
- Run Command: `node auth-server.js`
- HTTP Port: 5000

**Frontend**:
- Type: Static Site
- Source: `f-docusaurus`
- Build Command: `npm run build`
- Output: `build`

**Backend**:
- Type: Web Service
- Source: `backend`
- Run Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- HTTP Port: 8000

---

## Option 5: AWS (Production-Ready)

### Using AWS App Runner

**Auth Server & Backend**:
1. Create ECR repositories
2. Build & push Docker images
3. Deploy via App Runner

**Frontend**:
- Deploy to S3 + CloudFront
- Or use Amplify Hosting

---

## Option 6: Docker Compose (VPS Deployment)

### Single Server Setup

**1. Create docker-compose.yml**
```yaml
version: '3.8'

services:
  auth-server:
    build:
      context: ./f-docusaurus
      dockerfile: Dockerfile.auth
    ports:
      - "5000:5000"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - BETTER_AUTH_SECRET=${BETTER_AUTH_SECRET}
      - NODE_ENV=production
    restart: unless-stopped

  frontend:
    build:
      context: ./f-docusaurus
      dockerfile: Dockerfile
    ports:
      - "80:80"
    environment:
      - REACT_APP_AUTH_URL=http://auth-server:5000
      - REACT_APP_RAG_API_URL=http://backend:8000
    restart: unless-stopped

  backend:
    build:
      context: ./backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - COHERE_API_KEY=${COHERE_API_KEY}
    restart: unless-stopped
```

**2. Create Dockerfiles**

`f-docusaurus/Dockerfile.auth`:
```dockerfile
FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install --production
COPY . .
EXPOSE 5000
CMD ["node", "auth-server.js"]
```

`f-docusaurus/Dockerfile`:
```dockerfile
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/build /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

**3. Deploy**
```bash
# On your VPS (Ubuntu/Debian)
sudo apt update
sudo apt install docker.io docker-compose
git clone <your-repo>
cd <your-repo>
docker-compose up -d
```

---

## Environment Variables Summary

### Auth Server (.env)
```bash
DATABASE_URL=postgresql://user:pass@host:5432/db?sslmode=require
BETTER_AUTH_SECRET=min_32_chars_random_string_here
BETTER_AUTH_URL=https://your-auth-domain.com
PORT=5000
NODE_ENV=production
FRONTEND_URL=https://your-frontend-domain.com
```

### Frontend (.env)
```bash
REACT_APP_AUTH_URL=https://your-auth-domain.com
REACT_APP_RAG_API_URL=https://your-rag-backend.com
```

### Backend (.env)
```bash
DATABASE_URL=postgresql://user:pass@host:5432/db?sslmode=require
COHERE_API_KEY=your_cohere_key
EMBEDDING_MODEL=embed-multilingual-v3.0
GENERATION_MODEL=command-r-plus
LOG_LEVEL=INFO
ADMIN_API_KEY=your_secure_admin_key
CORS_ORIGINS=https://your-frontend-domain.com,http://localhost:3000
```

---

## Security Checklist

- [ ] Change `BETTER_AUTH_SECRET` to a secure 32+ character string
- [ ] Update `ADMIN_API_KEY` for backend ingestion endpoints
- [ ] Configure CORS to only allow your frontend domain
- [ ] Enable HTTPS (automatic on Render/Vercel/Railway)
- [ ] Don't commit `.env` files to git
- [ ] Use PostgreSQL SSL connection (already configured)
- [ ] Set `NODE_ENV=production` for auth server
- [ ] Review database connection pool settings for production

---

## Post-Deployment Testing

### 1. Test Auth Server
```bash
curl https://your-auth-server.com/health
# Should return: {"status":"ok","message":"Auth server is running"}
```

### 2. Test Signup
```bash
curl -X POST https://your-auth-server.com/api/auth/signup-custom \
  -H "Content-Type: application/json" \
  -d '{"name":"Test","email":"test@test.com","password":"test123","technicalBackground":"Software"}'
```

### 3. Test RAG Backend
```bash
curl https://your-rag-backend.com/api/v1/health
# Should return: {"status":"healthy",...}
```

### 4. Test Frontend
- Visit `https://your-frontend.com/login`
- Try signing up and logging in
- Test chat functionality

---

## Troubleshooting

### Auth Server Issues

**"Database connection failed"**
- Check `DATABASE_URL` format
- Verify Neon DB allows connections from your hosting provider IP
- Check SSL mode: `?sslmode=require`

**CORS errors**
- Update `origin` in `auth-server.js` line 22
- Add your frontend URL to allowed origins
- Restart the auth server

### Frontend Issues

**"Cannot connect to auth server"**
- Update `API_BASE_URL` in `auth-client.ts`
- Check auth server is running: `curl https://your-auth.com/health`
- Verify CORS settings

### Backend Issues

**"Cohere API error"**
- Verify `COHERE_API_KEY` is set correctly
- Check Cohere API quota/limits

**"Database migration failed"**
- Run migrations: `cd backend && alembic upgrade head`
- Check if tables exist in Neon DB

---

## Scaling Considerations

### Free Tier Limits
- **Render**: 750 hours/month per service (sleeps after 15min inactivity)
- **Vercel**: 100GB bandwidth, 100 builds/month
- **Railway**: $5 free credit/month
- **Neon DB**: 3GB storage, 1 project (free tier)

### Performance Tips
1. **Keep services awake**: Use cron-job.org to ping health endpoints every 10 minutes
2. **Database connection pooling**: Already configured in `auth-server.js` and backend
3. **CDN**: Use Cloudflare in front of your services (free)
4. **Caching**: Add Redis for session storage (future improvement)

---

## Monitoring

### Health Check Endpoints
- Auth: `GET /health`
- Backend: `GET /api/v1/health`
- Frontend: Check if homepage loads

### Uptime Monitoring (Free)
- UptimeRobot: https://uptimerobot.com
- Pingdom: https://www.pingdom.com
- StatusCake: https://www.statuscake.com

---

## Rollback Strategy

### Quick Rollback on Render
1. Go to service → Deploys tab
2. Click "Rollback" on previous working deployment

### Git-based Rollback
```bash
git revert HEAD
git push origin main
# Services will auto-redeploy
```

---

## Next Steps After Deployment

1. **Custom Domain** (Optional)
   - Buy domain from Namecheap/GoDaddy
   - Point to Render/Vercel with CNAME records

2. **SSL Certificate**
   - Automatic on Render/Vercel/Railway
   - Use Let's Encrypt for VPS

3. **Email Verification** (Future)
   - Add email provider (SendGrid/Mailgun)
   - Implement email verification flow

4. **Analytics** (Optional)
   - Google Analytics
   - Plausible Analytics
   - PostHog

---

## Support & Resources

- **Render Docs**: https://render.com/docs
- **Railway Docs**: https://docs.railway.app
- **Vercel Docs**: https://vercel.com/docs
- **Neon DB Docs**: https://neon.tech/docs
- **Cohere API Docs**: https://docs.cohere.com

---

## Estimated Deployment Time

| Platform | Setup Time | Complexity |
|----------|------------|------------|
| Render.com | 15-20 min | Easy ⭐⭐ |
| Railway.app | 10-15 min | Easy ⭐⭐ |
| Vercel + Render | 20-25 min | Medium ⭐⭐⭐ |
| DigitalOcean | 25-30 min | Medium ⭐⭐⭐ |
| AWS | 45-60 min | Hard ⭐⭐⭐⭐ |
| Docker VPS | 30-40 min | Medium ⭐⭐⭐ |

**Recommended for Hackathon**: Start with Render.com (Option 1) for fastest deployment!
