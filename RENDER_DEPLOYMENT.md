# Render.com Deployment Guide

## Quick Deploy

### Option 1: Blueprint (Recommended)

1. Push this repo to GitHub
2. Go to [Render Dashboard](https://dashboard.render.com)
3. Click "New" → "Blueprint"
4. Connect your repository
5. Render will automatically use `render.yaml`

### Option 2: Manual

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click "New" → "Web Service"
3. Connect your GitHub repository
4. Configure:
    - **Name**: `bg-removal-api`
    - **Environment**: Docker
    - **Dockerfile Path**: `./Dockerfile.render`
    - **Branch**: `master`
    - **Plan**: Free (or Starter for better performance)

5. Add Environment Variables:

    ```
    ENABLE_WITHOUTBG=false
    LOG_LEVEL=INFO
    ```

6. Click "Create Web Service"

## Common Issues & Solutions

### Issue 1: "Out of Memory" Error

**Symptoms:**

```
==> Out of memory (used over 512Mi)
```

**Solutions:**

1. ✅ **Use Dockerfile.render** (already configured):
    - Pre-downloads models during build
    - Only loads rembg (lighter model)
    - Single worker process

2. ✅ **Set ENABLE_WITHOUTBG=false**:

    ```bash
    ENABLE_WITHOUTBG=false
    ```

3. 💰 **Upgrade Plan** (if you need both models):
    - Starter plan: 1GB RAM (~$7/month)
    - Standard plan: 2GB RAM (~$15/month)

### Issue 2: "No Open Ports Detected"

**Symptoms:**

```
==> No open ports detected, continuing to scan...
==> Port scan timeout reached
```

**Root Cause:** Server takes too long to start because models are downloading/initializing.

**Solutions:**

✅ **Already Fixed in Dockerfile.render**:

- Models are pre-downloaded during Docker build
- Server starts immediately without waiting for models
- Lazy-loading of models on first request

**Verify Fix:**

```bash
# Check that models are pre-downloaded in build logs
# You should see this during build:
# "Downloading data from 'https://github.com/danielgatis/rembg/...'"
```

### Issue 3: First Request is Slow

**Expected Behavior:**

- Docker build: 5-10 minutes (one-time, downloads model)
- Server startup: <30 seconds (binds to port immediately)
- Background initialization: 1-3 seconds (loads cached model)
- First API request: <2 seconds (model already initialized in background)
- Subsequent requests: <1 second

**How it works:**

1. ✅ Models downloaded during Docker build (baked into image)
2. ✅ Server starts immediately and binds to port
3. ✅ Models initialize in background (1-3 seconds)
4. ✅ First request is fast because model is already loaded

**If first request is still slow:**

1. Check build logs - you should see "Model downloaded and cached successfully"
2. Check runtime logs - you should see "Models initialized successfully"
3. If you see "Models will lazy-load on first request" - model init failed, will load on first request instead

### Issue 4: GPU Warning

**Symptoms:**

```
GPU device discovery failed
```

**Status:** ✅ **Safe to Ignore**

- This is just a warning
- Models fall back to CPU automatically
- No impact on functionality

## Environment Variables Reference

### Required

- `PORT` - Automatically set by Render (usually 10000)

### Optional

- `ENABLE_WITHOUTBG=false` - Disable second model (saves memory)
- `LOG_LEVEL=INFO` - Logging verbosity (DEBUG, INFO, WARNING, ERROR)
- `MAX_FILE_SIZE_MB=10` - Maximum upload size

## Testing Your Deployment

Once deployed, test with:

```bash
# Get your Render URL (e.g., https://bg-removal-api.onrender.com)
export API_URL="https://your-service.onrender.com"

# Health check
curl $API_URL/

# Test background removal
curl -X POST $API_URL/remove-background \
  -F "image=@test-image.jpg" \
  -F "model=rembg" \
  --output result.png
```

## Performance Tips

### Free Tier Limitations

- 512MB RAM
- Services spin down after 15 min inactivity
- Cold start: ~30 seconds
- Only 1 model at a time

### Optimization Strategies

1. **Use Dockerfile.render** ✅
    - Already optimized for Render
    - Pre-downloads models
    - Minimal dependencies

2. **Keep Service Warm** (optional):

    ```bash
    # Ping every 10 minutes to prevent spin-down
    */10 * * * * curl https://your-service.onrender.com/
    ```

3. **Upgrade for Production**:
    - Starter: No spin-down, 1GB RAM, both models
    - Standard: 2GB RAM, faster processing

## Monitoring

Check your service health:

```bash
# View logs in Render Dashboard
# Or use Render CLI
render logs -f
```

## Troubleshooting Checklist

- [ ] Using `Dockerfile.render` (not `Dockerfile`)
- [ ] Set `ENABLE_WITHOUTBG=false` for free tier
- [ ] Build completed successfully (check logs)
- [ ] Model downloaded during build (check "Downloading data..." in logs)
- [ ] Service shows as "Live" in dashboard
- [ ] Health check endpoint `/` returns 200

## Support

If issues persist:

1. Check [Render Status](https://status.render.com)
2. Review [Render Docs](https://render.com/docs)
3. Check build/deploy logs in Render Dashboard
