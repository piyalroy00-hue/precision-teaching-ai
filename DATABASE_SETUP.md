# Database Configuration for Render

This guide explains how to configure your database for Precision Teaching AI on Render.

## Quick Comparison

| Feature | SQLite (Default) | PostgreSQL (Recommended) |
|---------|------------------|-------------------------|
| **Setup** | Automatic | Manual provision |
| **Persistence** | ❌ Lost on restart | ✅ Permanent |
| **Cost** | Free | Free (or $7/month) |
| **Concurrency** | Poor | Excellent |
| **Best For** | Development | Production |

---

## SQLite (Development/Testing)

### Default Configuration
- Automatically included
- File: `precision_teaching.db` (created on first run)
- Rendered at `/tmp/precision_teaching.db`
- **Lost on service restart** ⚠️

### How to Use
1. No additional setup needed
2. Deploy normally to Render
3. Database auto-initializes via `release` command in `Procfile`

### Limitations
- Database recreated on every restart (data loss)
- Not suitable for production with real users
- Slower than PostgreSQL

### When to Use
- Local development
- Testing/demos
- Proof of concept

---

## PostgreSQL (Production)

### Why PostgreSQL?

✅ Persistent storage - data survives service restarts
✅ Better concurrency - supports multiple simultaneous users
✅ Professional-grade database
✅ Automatic backups (Render Standard plan)
✅ Easy migration path

### Setup Steps

#### 1. Create PostgreSQL Database on Render

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click **New +** → **PostgreSQL**
3. Configure:
   - **Name**: `precision-teaching-db`
   - **Database**: `precision_teaching`
   - **User**: `precision_teaching`
   - **Region**: Same as web service (e.g., Oregon)
   - **PostgreSQL Version**: 15
   - **Plan**: Free tier (or Starter for production)

4. Click **Create Database**

#### 2. Get Connection Details

After creation, you'll see:
- **Host**: Something like `dpg-xxx.oregon-postgres.render.com`
- **Port**: `5432`
- **Database**: `precision_teaching`
- **User**: `precision_teaching`
- **Password**: Auto-generated
- **Internal Database URL**: `postgresql://user:pass@host:port/db`
- **External Database URL**: For external tools (not needed for app)

**Copy the Internal Database URL** ✅

#### 3. Set Environment Variable in Web Service

1. Go to your web service (`precision-teaching-ai`)
2. Click **Environment**
3. Add new environment variable:
   ```
   DATABASE_URL=postgresql://user:password@host:5432/precision_teaching
   ```
   (Paste the Internal Database URL from step 2)

4. Click **Save Changes**

#### 4. Redeploy Application

1. Go to **Deployments**
2. Click **Manual Deploy** → **Latest Commit**
3. Wait for build to complete (~2-3 minutes)

---

## Switching from SQLite to PostgreSQL

### If you've already deployed with SQLite:

1. **Don't worry about lost data** - development data is temporary anyway
2. **Follow PostgreSQL setup above**
3. **Redeploy** to Render
4. **Database will auto-initialize** via `release` command in `Procfile`

### How to Migrate Real Data (Advanced)

If you have important data in SQLite:

```bash
# Export SQLite data
sqlite3 precision_teaching.db ".dump" > backup.sql

# Import to PostgreSQL (after connecting)
psql -U user -d database -f backup.sql
```

---

## Connection Pooling (Optional)

For production apps with many concurrent users, add connection pooling:

### Install pgBouncer (via Render)

Render Standard plan includes pgBouncer. No additional setup needed.

### Or Use SQLAlchemy Pooling

Update `app/database/db.py`:

```python
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=5,
    max_overflow=10,
    pool_recycle=3600,
)
```

---

## Monitoring & Backups

### Automatic Backups (Render Standard Plan)

- Render automatically backs up PostgreSQL daily
- Backups retained for 7 days
- Restore from dashboard if needed

### Manual Backups

For critical data, download backups manually:

1. Click database service
2. **Backups** tab
3. Click **Download** on latest backup

### Monitor Database

1. Click database service
2. **Metrics** tab
3. View CPU, storage, connections

---

## Troubleshooting

### "Connection refused" on deploy

**Cause**: Environment variable not set correctly

**Fix**:
1. Copy **Internal Database URL** from PostgreSQL service
2. Add to web service environment: `DATABASE_URL=...`
3. Redeploy

### "Authentication failed"

**Cause**: Wrong credentials in `DATABASE_URL`

**Fix**:
1. Go to PostgreSQL service
2. Click **Info**
3. Copy **Internal Database URL** again
4. Update in web service environment

### Database not persisting

**Cause**: Still using SQLite instead of PostgreSQL

**Fix**:
1. Verify `DATABASE_URL` is set in web service
2. Check it starts with `postgresql://` (not `sqlite://`)
3. Redeploy: **Manual Deploy** → **Latest Commit**

### "Too many connections"

**Cause**: Connection pool exhausted

**Fix**:
1. Upgrade database plan
2. Enable pgBouncer connection pooling
3. Reduce pool size in application

---

## Cost Comparison

### Free Tier (Development)
- **Web Service**: Free (auto-suspend after 15 min inactivity)
- **Database**: Free SQLite + Free PostgreSQL
- **Cost**: $0/month
- **Downside**: Services auto-suspend, lose SQLite data on restart

### Hobby Tier (Testing)
- **Web Service**: Free (always running) + $5/month upgrade
- **Database**: Free PostgreSQL
- **Cost**: $5/month
- **Good for**: Testing with persistent data

### Standard Tier (Production)
- **Web Service**: $7/month (always running, 2GB RAM)
- **Database**: $7/month (Starter PostgreSQL)
- **Cost**: $14/month minimum
- **Recommended for**: Real users, stable uptime

---

## Environment Variables Recap

### SQLite (Default)
```
DATABASE_URL=sqlite:///precision_teaching.db
```

### PostgreSQL
```
DATABASE_URL=postgresql://user:password@host:5432/database
```

The app automatically detects and uses the correct database type. No code changes needed! ✅

---

## Best Practices

1. **Use PostgreSQL for production** with real users
2. **Keep SQLite for local development** (easier, no setup)
3. **Set `DATABASE_URL` environment variable** (never hardcode credentials)
4. **Enable automatic backups** (Render Standard plan)
5. **Monitor database metrics** regularly
6. **Test locally before deploying** major schema changes
7. **Use connection pooling** for high-traffic apps

---

## Questions?

- Render Docs: https://render.com/docs/databases
- SQLAlchemy Docs: https://docs.sqlalchemy.org/
- PostgreSQL Docs: https://www.postgresql.org/docs/

---

**Next**: Continue with `RENDER_QUICKSTART.md` for final deployment steps!
