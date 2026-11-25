# Deploying Precision Teaching AI to Render

This guide walks you through deploying the Precision Teaching AI Flask application to Render.

## Prerequisites

- **Render account**: Sign up at [render.com](https://render.com)
- **Git repository**: This project must be pushed to GitHub, GitLab, or Gitea
- **Environment variables**: Configured in Render dashboard
- **Gunicorn**: Added to requirements.txt (production WSGI server)

## Option 1: Deploy Using Render Dashboard (Recommended)

### Step 1: Prepare Your Repository

1. **Commit all changes locally:**
   ```powershell
   cd "C:\Users\BRAINWARE UNIVERSITY\Desktop\SMR Project"
   git add .
   git commit -m "Add deployment configuration for Render"
   git push origin main
   ```

   Files created for deployment:
   - `Procfile` - Runtime configuration
   - `render.yaml` - Infrastructure as code (optional)
   - `requirements.txt` - Updated with gunicorn
   - `.env.example` - Environment variables template
   - `DEPLOYMENT.md` - This file

2. **Ensure `.gitignore` excludes sensitive files:**
   - `.env` ✅ (excluded)
   - `*.db` ✅ (excluded)
   - `.venv/` ✅ (excluded)

### Step 2: Create a New Web Service on Render

1. Go to [render.com](https://render.com) and sign in
2. Click **New +** → **Web Service**
3. Connect your Git repository (GitHub/GitLab/Gitea)
4. Select the `precision-teaching-ai` repository

### Step 3: Configure the Web Service

Fill in the configuration form:

| Setting | Value |
|---------|-------|
| **Name** | `precision-teaching-ai` |
| **Environment** | `Python 3` |
| **Region** | `Oregon` (or closest to your users) |
| **Branch** | `main` |
| **Build Command** | `pip install -r requirements.txt` |
| **Pre-Deploy Command** | `python scripts/init_db.py` |
| **Start Command** | `gunicorn app.main:app` |
| **Plan** | `Standard` (free tier available for testing) |

### Step 4: Set Environment Variables

In the Render dashboard, add these environment variables:

```
APP_ENV=production
FLASK_SECRET_KEY=<long-random-secret>
DATABASE_URL=<Render Postgres connection string>
AI_TUTOR_PROVIDER=local
```

**Optional** (only if enabling OpenAI tutor):
```
AI_TUTOR_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_TUTOR_MODEL=gpt-4o-mini
```

### Step 5: Deploy

Click **Deploy**. Render will:
1. ✅ Install dependencies from `requirements.txt`
2. ✅ Run `python scripts/init_db.py` before deploy to create the database schema
3. ✅ Start the Flask app with Gunicorn
4. ✅ Assign a public URL (e.g., `https://precision-teaching-ai.onrender.com`)

---

## Option 2: Deploy Using Infrastructure as Code (render.yaml)

If you prefer to define infrastructure in code:

1. **Push your repository with `render.yaml`:**
   ```powershell
   git add render.yaml
   git commit -m "Add render.yaml infrastructure definition"
   git push origin main
   ```

2. **Go to Render dashboard → Blueprint:**
   - Click **New +** → **Blueprint**
   - Select your repository
   - Render will read `render.yaml` and auto-configure services

3. **Review and approve the preview**, then click **Create New Services**

---

## Post-Deployment: Usage

After successful deployment:

### Access the Application
- Open: `https://precision-teaching-ai.onrender.com`
- Create a student account
- Complete the diagnostic assessment
- View your learning dashboard

### Create Admin Account
There is no public admin-setup route. To promote an account:

1. Register a student account via the deployed web interface
2. Open the web service **Shell** in the Render dashboard
3. Run `python scripts/promote_admin.py` and enter that account's email
4. Sign out and sign back in
- Or use direct database access (see "Debugging" section)

### Monitor Logs
- Click your service on Render → **Logs**
- View real-time application and build logs

---

## Database Management

### SQLite on Render

By default, Precision Teaching AI uses SQLite (`precision_teaching.db`). 

**⚠️ Important Notes:**

1. **SQLite persists in `/tmp/`** (Render's ephemeral file system)
   - Database is lost when the service restarts
   - **Solution**: Upgrade to PostgreSQL or implement backup strategies

2. **To Use PostgreSQL** (recommended for production):
   - Provision a PostgreSQL database in Render
   - Update `DATABASE_URL` environment variable
   - Modify `app/config/settings.py` to use PostgreSQL connection string
   - SQLAlchemy will work with both databases automatically

### Add PostgreSQL Database

1. In Render dashboard: **New +** → **PostgreSQL**
2. Configure:
   - **Name**: `precision-teaching-db`
   - **Region**: Same as web service
   - **PostgreSQL Version**: 15
   - **Plan**: Free (or Starter for production)

3. Copy the **Internal Database URL**
4. Add to web service environment variables:
   ```
   DATABASE_URL=<paste_internal_url_here>
   ```

5. **Update connection string in code** (if needed):
   - Render provides the full URL; SQLAlchemy handles it automatically
   - No code changes required if using the `DATABASE_URL` env var

---

## Environment Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `FLASK_ENV` | `production` | Legacy environment mode (use `APP_ENV`) |
| `APP_ENV` | `development` | Set to `production` to disable Flask debug mode |
| `FLASK_SECRET_KEY` | random per process | Session signing key; must be set in production |
| `FLASK_DEBUG` | `1` when not production | Enable/disable the development debugger |
| `FLASK_HOST` | `127.0.0.1` | Host used by `python app/main.py` |
| `AI_TUTOR_PROVIDER` | `local` | AI provider: `local` or `openai` |
| `OPENAI_API_KEY` | — | OpenAI API key (required if `AI_TUTOR_PROVIDER=openai`) |
| `OPENAI_TUTOR_MODEL` | `gpt-4o-mini` | OpenAI model to use for tutor |
| `DATABASE_URL` | `sqlite:///precision_teaching.db` | Database connection string |

---

## Troubleshooting

### Build Fails: "ModuleNotFoundError: No module named 'gunicorn'"

**Solution**: Ensure `gunicorn>=21.0` is in `requirements.txt` ✅ (already added)

### Database Errors on Restart

**Symptoms**: "Database locked" or missing tables after service restart

**Causes**:
- SQLite database lost (Render uses ephemeral file system)
- Multiple processes accessing SQLite simultaneously

**Solution**:
1. Use PostgreSQL instead of SQLite (recommended)
2. Or implement database backup/restore mechanism
3. Or use `render.yaml` with persistent volumes (advanced)

### Secret Keys Not Working

**Error**: "Unsafe mode", "Secret key mismatch", or users are logged out after restart

**Solution**:
1. Set `FLASK_SECRET_KEY` to a strong random value in the environment; `render.yaml` generates one automatically
2. Set `APP_ENV=production` (or legacy `FLASK_ENV=production`) so Flask debug mode stays disabled
3. Keep the same `FLASK_SECRET_KEY` across all workers/restarts so sessions remain valid

### Service Won't Stay Running

**Check logs** in Render dashboard:
```
Render Logs → View all logs
```

Common issues:
- Port binding: Ensure app runs on port 5000 (or configurable via env)
- Memory: Upgrade plan if service runs out of memory
- Crashes: Review error messages in logs

---

## Scaling & Performance

### For Development/Testing
- **Plan**: Free tier (0.5 GB RAM, shared CPU)
- **Database**: SQLite or free PostgreSQL
- **Cost**: $0/month

### For Production
- **Plan**: Standard ($7/month base)
  - 2 GB RAM, shared CPU
  - Support for persistent data
  
- **Database**: PostgreSQL ($7/month)
  - Dedicated instance
  - Automatic backups
  - Better concurrency handling

- **Enhancements**:
  - Add Redis for caching (reduce AI API calls)
  - Use CDN for static files
  - Implement rate limiting for API endpoints

---

## Deployment Checklist

Before deploying to production:

- [ ] All changes committed and pushed to Git
- [ ] `requirements.txt` includes `gunicorn>=21.0`
- [ ] `Procfile` exists with correct build/start commands
- [ ] `.gitignore` excludes `.env`, `*.db`, `.venv/`
- [ ] Environment variables set in Render dashboard
- [ ] Database strategy chosen (SQLite for dev, PostgreSQL for prod)
- [ ] `app.secret_key` configured from environment variable
- [ ] Admin user creation workflow documented
- [ ] Logging enabled and monitored
- [ ] Backup/restore plan in place (if using SQLite)

---

## Useful Links

- **Render Docs**: https://render.com/docs
- **Flask Deployment**: https://flask.palletsprojects.com/deployment/
- **Gunicorn Docs**: https://docs.gunicorn.org/
- **SQLAlchemy Databases**: https://docs.sqlalchemy.org/core/engines.html

---

## Questions?

For issues or questions about deployment:
1. Check Render logs: **Logs** tab in service dashboard
2. Review `DEPLOYMENT.md` and `.env.example`
3. Test locally: `gunicorn app.main:app`
4. Consult Render support: https://render.com/support

---

**Happy deploying! 🚀**
