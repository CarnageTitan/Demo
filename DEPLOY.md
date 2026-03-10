# Deploy to Render

## Change Runtime Without Creating a New Service

Render doesn't let you change Node → Python in the Dashboard, but you can do it via **Blueprint sync** or the **API**.

---

### Method 1: Blueprint Sync (if your service came from a Blueprint)

1. Push the latest code (includes `render.yaml` with `env: python`)
2. Go to [dashboard.render.com](https://dashboard.render.com)
3. Open your **Blueprint** (the parent of your service)
4. Click **Sync** or **Apply**
5. The service will update to Python and redeploy

---

### Method 2: Render API

1. Get your **API key**: [dashboard.render.com](https://dashboard.render.com) → **Account Settings** → **API Keys** → Create
2. Get your **service ID**: Dashboard → Your Service → Settings → check the URL, e.g. `.../services/srv-xxxxx`
3. Run this (replace `YOUR_API_KEY` and `srv-xxxxx`):

```bash
curl -X PATCH "https://api.render.com/v1/services/srv-xxxxx" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "serviceDetails": {
      "runtime": "python",
      "buildCommand": "pip install -r requirements.txt",
      "startCommand": "gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --threads 2 --timeout 120"
    }
  }'
```

4. Trigger a deploy: Dashboard → Manual Deploy

---

### Method 3: If you can edit Build/Start in the Dashboard

Some Render setups let you change build/start commands even when Runtime is locked. Try:

1. **Settings** → **Build & Deploy**
2. **Build Command** → `pip install -r requirements.txt`
3. **Start Command** → `gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --threads 2 --timeout 120`
4. **Save** and **Manual Deploy**

If Render still runs `npm install` first (Node build), this won't work—use Method 1 or 2.

---

## Start command (copy-paste)

```
gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --threads 2 --timeout 120
```
