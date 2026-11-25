# Render Deployment Quick Start (5 minutes)

## 🚀 TL;DR - Deploy in 5 Minutes

### 1. **Prepare Repository** (2 min)
```powershell
cd "C:\Users\BRAINWARE UNIVERSITY\Desktop\SMR Project"
git add .
git commit -m "Add Render deployment files"
git push origin main
```

### 2. **Create Render Web Service** (1 min)
1. Go to [render.com](https://render.com)
2. Click **New +** → **Web Service**
3. Select your GitHub/GitLab repository (`precision-teaching-ai`)
4. Click **Connect**

### 3. **Configure Service** (1 min)
| Field | Value |
|-------|-------|
| **Name** | `precision-teaching-ai` |
| **Environment** | `Python 3` |
| **Build Command** | `pip install -r requirements.txt && python scripts/init_db.py` |
| **Start Command** | `gunicorn app.main:app` |

### 4. **Set Environment Variables** (1 min)
Click **Advanced** → **Environment Variables**, add:
```
FLASK_ENV=production
AI_TUTOR_PROVIDER=local
```

### 5. **Deploy**
Click **Deploy** and wait ~2-3 minutes.

✅ Done! Your app will be live at: `https://precision-teaching-ai.onrender.com`

---

## 📋 What Gets Deployed?

| File | Purpose |
|------|---------|
| `Procfile` | Build & start commands |
| `requirements.txt` | Python dependencies (+ gunicorn) |
| `.env.example` | Environment variables template |
| `DEPLOYMENT.md` | Full deployment guide |

---

## 🔧 Configuration Files Created

**Procfile** - Tells Render how to run your app:
```
web: gunicorn app.main:app
release: python scripts/init_db.py
```

**render.yaml** (optional) - Infrastructure as code:
```yaml
services:
  - type: web
    name: precision-teaching-ai
    buildCommand: "pip install -r requirements.txt && python scripts/init_db.py"
    startCommand: "gunicorn app.main:app"
```

---

## ⚠️ Important Notes

### Database (SQLite vs PostgreSQL)

**SQLite (Default - Dev/Testing)**
- Included in deployment
- Database lost on service restart
- Simple, no setup needed
- Plan: **Free tier OK**

**PostgreSQL (Production - Recommended)**
- Persistent storage
- Recommended for real users
- Add via Render dashboard
- Plan: **Standard ($7/month)**

### Secret Key (Security)

For production, add to Render dashboard:
```
SECRET_KEY=your-long-random-secret-string-here
```

Then update `app/main.py`:
```python
app.secret_key = os.getenv("SECRET_KEY", "dev-key")
```

---

## 🔍 Monitor Your Deployment

1. **Logs**: Click service → **Logs** tab
2. **Status**: Watch build progress in real-time
3. **Errors**: Scroll to see any build/runtime errors

Common error fixes:
- **"gunicorn not found"** → Ensure it's in `requirements.txt` ✅
- **"Database locked"** → Switch to PostgreSQL
- **Port errors** → App should run on port 5000 ✅

---

## 📱 After Deployment

Access your app:
```
https://precision-teaching-ai.onrender.com
```

1. Register a student account
2. Complete diagnostic assessment
3. View your learning dashboard
4. Start a learning plan

---

## 💡 Next Steps

- [ ] Set up PostgreSQL for persistent data
- [ ] Configure environment-specific secret key
- [ ] Enable OpenAI tutor (optional)
- [ ] Add monitoring/alerting
- [ ] Set up CI/CD for auto-deploy on push

---

## ❓ Troubleshooting

| Issue | Solution |
|-------|----------|
| **Build fails** | Check `requirements.txt` has `gunicorn>=21.0` |
| **App won't start** | Check logs, ensure `app.main:app` is correct |
| **Database errors** | Use PostgreSQL instead of SQLite |
| **Performance issues** | Upgrade to Standard plan |

---

**For detailed deployment guide, see `DEPLOYMENT.md`**

Happy deploying! 🎉
