# UI & Deployment Guide

## Question 1: Where does the time "25s" come from in the UI?

**Answer**: The time display (e.g., "25s") comes from **Gradio's built-in progress tracking**. Gradio automatically shows:

- A timer showing how long the function has been running
- A progress bar (if you use `progress=gr.Progress()`)
- Estimated time based on previous runs

The timer is **automatic** - you don't need to code it. It starts when you click "Remove Background" and stops when the function returns.

### To Customize Progress Display:

```python
def process_image(image, progress=gr.Progress()):
    progress(0.1, desc="Processing with rembg...")  # Shows "Processing with rembg..." at 10%
    # ... process rembg ...
    progress(0.5, desc="Processing with withoutbg...")  # Shows at 50%
    # ... process withoutbg ...
    progress(1.0, desc="Done!")  # Shows "Done!" at 100%
```

This is already in the updated UI code.

---

## Question 2: Why is withoutbg not showing / backend crashing?

### Problem Analysis

From your logs:

```
2026-01-21 19:18:15 | INFO | app.models.rembg_model | Initializing rembg with model: u2net
2026-01-21 19:18:30 | INFO | app.models.rembg_model | Rembg model loaded successfully
2026-01-21 19:18:45 | INFO | app.api | Successfully processed image with rembg
```

**Observation**:

- ✅ rembg works (initializes in 15s, processes in 15s)
- ❌ withoutbg crashes (no completion logs)
- Your Railway config: `INITIALIZE_MODELS=rembg` (only rembg pre-loaded)

### Root Cause: **Out of Memory (OOM) during lazy loading**

When the first `withoutbg` request arrives:

1. withoutbg is NOT pre-initialized (to save memory on startup)
2. It tries to lazy-load during the request
3. Downloads ~320MB of models from HuggingFace
4. Tries to load models into memory
5. **OOM crash** - Railway kills the container (memory limit exceeded)

### Solution Options

#### Option A: Pre-initialize withoutbg (Requires 4GB+ RAM)

Set in Railway environment variables:

```bash
INITIALIZE_MODELS=all
```

**Pros**: Both models fast
**Cons**: High memory usage (~3-4GB), may still OOM on Railway free tier

#### Option B: Use only rembg (Current safe setup)

Set in Railway:

```bash
INITIALIZE_MODELS=rembg
```

**Pros**: Stable, low memory (~1-2GB)
**Cons**: withoutbg will crash

#### Option C: Increase Railway memory allocation

1. Go to Railway project settings
2. Upgrade plan or increase memory limit
3. Set `INITIALIZE_MODELS=all`

**Recommended**: Option C if you have budget, otherwise stick with Option B (rembg only)

---

## Current Setup Summary

### Backend (Railway)

- **Service**: FastAPI background removal API
- **Environment Variables**:
    ```bash
    INITIALIZE_MODELS=rembg     # Only pre-load rembg to save memory
    PORT=<auto-set-by-railway>  # Railway sets this
    LOG_LEVEL=INFO
    ```
- **Memory**: ~1-2GB (rembg only), ~3-4GB (both models)
- **Status**: ✅ Stable with rembg only

### Frontend (Render)

- **Service**: Gradio UI
- **Environment Variables**:
    ```bash
    API_URL=https://your-railway-api.railway.app  # Your Railway API URL
    PORT=<auto-set-by-render>  # Render sets this
    ```
- **Features**:
    - Shows progress timer (automatic from Gradio)
    - Status messages for each step
    - Error warnings if API fails

---

## UI Updates Made

### 1. Better Error Handling

```python
# Now shows detailed error messages in UI
except requests.exceptions.Timeout:
    gr.Warning("Timeout - model may be downloading (first request takes 1-2 min)")
```

### 2. Longer Timeout

```python
timeout=300  # Increased from 120s to 300s (5 minutes)
```

### 3. Progress Tracking

```python
def process_image(image, progress=gr.Progress()):
    progress(0.1, desc="Processing with rembg...")
    # ... code ...
    progress(0.5, desc="Processing with withoutbg...")
```

### 4. Status Messages

- Shows which model is processing
- Shows success/failure for each model
- Warns about first-time delays

---

## Next Steps

### To Fix withoutbg Crash:

1. **Check Railway memory usage**:
    - Go to Railway dashboard → Metrics
    - Look for memory spikes/OOM errors

2. **If memory is the issue**, choose one:

    **A. Upgrade Railway plan** (recommended):

    ```bash
    # In Railway, increase memory allocation
    # Then set:
    INITIALIZE_MODELS=all
    ```

    **B. Remove withoutbg from UI** (free tier solution):
    - Edit UI to only show rembg
    - Users only get one model but it works reliably

3. **Deploy the updated UI**:
    ```bash
    git add ui/app.py
    git commit -m "Improve UI error handling and progress display"
    git push
    # Render will auto-deploy
    ```

---

## Testing

### Test rembg (should work):

1. Upload an image in UI
2. Click "Remove Background"
3. Watch progress: "Processing with rembg..." (~15-30s)
4. ✅ See result in middle column

### Test withoutbg (may crash):

1. Same as above
2. Watch progress: "Processing with withoutbg..."
3. If crashes: Check Railway logs for OOM
4. If timeout: Increase Railway memory

---

## Memory Recommendations

| Models      | Minimum RAM | Recommended RAM | Railway Plan     |
| ----------- | ----------- | --------------- | ---------------- |
| rembg only  | 1GB         | 2GB             | Free tier OK     |
| both models | 3GB         | 4GB             | Paid plan needed |

Current status: **rembg only = safe and stable** ✅
