# Deploy to Render (Fix Node Error)

Render is using **Node.js** but this project is **Python**. You must switch to **Docker**.

## Option A: Edit Existing Service (fastest)

1. Go to [dashboard.render.com](https://dashboard.render.com)
2. Open your **quant-trading-model** (or whatever you named it) Web Service
3. Click **Settings** (left sidebar)
4. Under **Build & Deploy**:
   - **Environment** → Change from "Node" to **"Docker"**
   - **Dockerfile Path** → `./Dockerfile` (or leave blank if it finds it)
   - Clear **Build Command** (leave empty)
   - Clear **Start Command** (Docker uses the Dockerfile's CMD)
5. Click **Save Changes**
6. Go to **Manual Deploy** → **Deploy latest commit**

---

## Option B: Create New Service from Blueprint

1. Delete the current Web Service (if it keeps failing)
2. **New** → **Blueprint**
3. Connect your GitHub repo
4. Select branch: **cursor/quant-trading-model-ae7f** (or main if merged)
5. Render reads `render.yaml` and creates a Docker-based service
6. Click **Apply**

---

## Option C: Create New Service Manually

1. **New** → **Web Service**
2. Connect repo, select branch
3. **Environment** → **Docker** (important!)
4. Leave Build/Start commands empty (Dockerfile handles it)
5. Create Web Service

---

## Ensure Correct Branch

Render must deploy from a branch that has `Dockerfile` and `app.py`.  
Go to **Settings** → **Build & Deploy** → **Branch** → set to `cursor/quant-trading-model-ae7f` (or main).
