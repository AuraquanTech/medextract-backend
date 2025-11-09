# Deployment Instructions

## Non-Interactive Deployment

### Option 1: Use Deployment Scripts

**Windows:**
```powershell
.\deploy.bat
```

**PowerShell:**
```powershell
.\deploy.ps1
```

**Linux/Mac:**
```bash
chmod +x deploy.sh
./deploy.sh
```

### Option 2: Manual Deployment

#### Step 1: Install Dependencies
```bash
npm install
```

#### Step 2: Build TypeScript
```bash
npm run build
```

#### Step 3: Set Environment Variables

In Netlify Dashboard → Site settings → Environment variables:

```
ALLOWED_ORIGINS=https://chatgpt.com,https://*.chatgpt.com,https://chat.openai.com,https://*.openai.com
MCP_HTTP_REQUIRE_ORIGIN=true
RATE_LIMIT_WINDOW_MS=60000
RATE_LIMIT_MAX_REQ=300
WORKSPACE_DIR=/opt/build/repo
```

#### Step 4: Deploy

**Using Netlify CLI:**
```bash
# Install CLI (if not installed)
npm install -g netlify-cli

# Login (if not logged in)
netlify login

# Deploy
netlify deploy --prod
```

**Or push to GitHub** (if auto-deploy is enabled):
```bash
git add .
git commit -m "Deploy MCP server with 403 fixes"
git push
```

### Option 3: GitHub Auto-Deploy

If your Netlify site is connected to GitHub:

1. **Push to GitHub:**
   ```bash
   git add .
   git commit -m "Deploy MCP server with 403 fixes"
   git push
   ```

2. **Netlify will auto-deploy** (if auto-deploy is enabled)

3. **Set environment variables** in Netlify Dashboard (if not already set)

## Post-Deployment

### 1. Test Deployment

```bash
# Discovery (should work without Origin)
curl -i 'https://your-site.netlify.app/mcp'

# Health check
curl -i 'https://your-site.netlify.app/mcp/health'

# With Origin (should include CORS headers)
curl -i -H 'Origin: https://chatgpt.com' \
  'https://your-site.netlify.app/mcp'
```

### 2. Connect in ChatGPT

- **Server URL:** `https://your-site.netlify.app/mcp`
- **Authentication:** None

### 3. Monitor Logs

```bash
# Via Netlify CLI
netlify functions:log mcp --follow

# Or in Netlify Dashboard
# Site → Functions → mcp → Logs
```

## Troubleshooting

### Deployment Fails

1. **Check Netlify CLI is installed:**
   ```bash
   netlify --version
   ```

2. **Check you're logged in:**
   ```bash
   netlify status
   ```

3. **Check build logs:**
   - Netlify Dashboard → Deploys → Latest → Build log

### Still Getting 403 After Deployment

1. **Verify environment variables are set:**
   ```bash
   netlify env:list
   ```

2. **Check function logs:**
   ```bash
   netlify functions:log mcp
   ```

3. **Test with debug endpoint** (if enabled):
   ```bash
   curl "https://your-site.netlify.app/mcp/debug?token=<your-secret>"
   ```

4. **See `FALLBACK_STRATEGY.md`** for emergency bypass

## Quick Reference

### Required Environment Variables
```
ALLOWED_ORIGINS=https://chatgpt.com,https://*.chatgpt.com,https://chat.openai.com,https://*.openai.com
MCP_HTTP_REQUIRE_ORIGIN=true
RATE_LIMIT_WINDOW_MS=60000
RATE_LIMIT_MAX_REQ=300
```

### Deployment Commands
```bash
# Install dependencies
npm install

# Build
npm run build

# Deploy
netlify deploy --prod
```

### Test Commands
```bash
# Discovery
curl -i 'https://your-site.netlify.app/mcp'

# With Origin
curl -i -H 'Origin: https://chatgpt.com' \
  'https://your-site.netlify.app/mcp'
```

## Next Steps

1. ✅ Deploy using one of the methods above
2. ✅ Test with curl commands
3. ✅ Connect in ChatGPT
4. ✅ Monitor logs for issues
5. ✅ Remove debug secret (if used)

