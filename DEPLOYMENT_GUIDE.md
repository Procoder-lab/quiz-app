# 🚀 Quiz App Deployment Guide

## What Was Fixed
The app was using **SQLite** which doesn't persist data properly on cloud platforms. Now using **SQLAlchemy** with database support for PostgreSQL and SQLite.

## Deployment Steps

### For **Heroku** (or Any Cloud Platform):

1. **Add PostgreSQL Database**
   - Add a PostgreSQL add-on to your app
   - Copy the `DATABASE_URL` from config vars

2. **Update Environment Variable**
   ```
   DATABASE_URL = postgresql://user:password@host:port/dbname
   ```
   (This will be set automatically by Heroku if using Heroku Postgres)

3. **Deploy**
   ```bash
   git add .
   git commit -m "Fix: Use SQLAlchemy with persistent database"
   git push heroku main
   ```

### For **Local Testing**:

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run App**
   ```bash
   python app.py
   ```
   - By default, uses `sqlite:///database.db` (local SQLite)
   - To use PostgreSQL, set `DATABASE_URL` environment variable

## Database Compatibility

✅ **Production**: Use PostgreSQL (data persists)
✅ **Local Dev**: SQLite works fine
❌ **Avoid**: SQLite on cloud platforms (data loss on restart)

## Key Changes Made

- Replaced raw SQLite with **Flask-SQLAlchemy ORM**
- Database models: `Question` and `Score` classes
- Automatic migrations via `db.create_all()`
- Support for both PostgreSQL and SQLite
