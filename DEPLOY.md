# Deploy to Render

This project uses **Python** and must run with **Docker**. Render often cannot switch from Node to Docker on an existing service—**delete and recreate** is usually required.

---

## How to Change to Docker (or Create New)

### If you can edit the existing service

1. Go to [dashboard.render.com](https://dashboard.render.com)
2. Click your Web Service
3. Click **Settings** (left sidebar)
4. Scroll to **Build & Deploy**
5. Look for **Environment**, **Runtime**, or **Language**
6. Change it from **Node** to **Docker**
7. Set **Build Command** → `true`
8. Set **Start Command** → `python -m gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --threads 2 --timeout 120`
9. **Save** and **Manual Deploy**

### If Environment/Runtime is greyed out or missing

Render usually does not allow changing from Node to Docker on an existing service. Create a new service instead.

---

## Option A: New Service from Blueprint (recommended)

1. Delete your current Web Service (Dashboard → Service → Settings → Delete Web Service)
2. Click **New +** → **Blueprint**
3. Connect your GitHub repo
4. Select branch: **cursor/quant-trading-model-ae7f** (or main)
5. Render reads `render.yaml` and creates a Docker service
6. Click **Apply**

---

## Option B: New Web Service (manual)

1. Click **New +** → **Web Service**
2. Connect your GitHub repo
3. Select branch: **cursor/quant-trading-model-ae7f**
4. **Name**: `quant-trading-model` (or any name)
5. **Region**: Choose closest to you
6. **Root Directory**: leave blank
7. **Runtime** or **Environment** → **Docker**
8. **Build Command** → `true`
9. **Start Command** → `python -m gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --threads 2 --timeout 120`
10. Click **Create Web Service**

---

## Start command (copy-paste)

```
python -m gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --threads 2 --timeout 120
```
