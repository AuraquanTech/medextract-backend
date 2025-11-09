# Netlify Deployment Guide - Step by Step

## ✅ Fixed: requirements.txt

The `anthropic-mcp-sdk` package has been removed. The correct package is just `mcp`.

**Fixed requirements.txt:**
```
mcp>=0.1.0
pytest>=7.0.0
pytest-asyncio>=0.21.0
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
httpx>=0.25.0
python-jose[cryptography]>=3.3.0
mangum>=0.17.0
```

---

## 🚀 Netlify Deployment Steps

### Step 1: Navigate to Netlify Dashboard

1. Open browser and go to: **https://app.netlify.com/**
2. Log in with your GitHub account (or create an account)

### Step 2: Import from GitHub

1. Click **"Add new site"** button (top right or main area)
2. Select **"Import an existing project"**
3. Choose **"GitHub"** and authorize Netlify if prompted
4. Find and select your repository: **`AuraquanTech/cursor-mcp-http-bridge`**
5. Click **"Import"** or **"Deploy site"**

### Step 3: Configure Build Settings

On the deploy configuration page:

- **Build command**: `pip install -r requirements.txt`
- **Publish directory**: `.` (or leave empty)
- **Python version**: `3.11` (or leave default)
- Click **"Deploy site"**

### Step 4: Wait for Initial Deployment

- Netlify will start building and deploying
- Watch the deploy log for any errors
- Initial deployment may fail (that's OK - we'll fix it with environment variables)

### Step 5: Set Environment Variables

After the site is created:

1. Go to **Site settings** (gear icon or Settings in left sidebar)
2. Click **"Environment variables"** in the left menu
3. Click **"Add variable"** and add each of the following:

**Variable 1: AUTH_ISSUER**
- Key: `AUTH_ISSUER`
- Value: `https://dev-qswa74vzeymf65ly.auth0.com/`
- Scope: All scopes (or Production)
- Click **"Save"**

**Variable 2: AUTH_AUDIENCE**
- Key: `AUTH_AUDIENCE`
- Value: `https://cursor-mcp`
- Scope: All scopes
- Click **"Save"**

**Variable 3: AUTH_JWKS_URL**
- Key: `AUTH_JWKS_URL`
- Value: `https://dev-qswa74vzeymf65ly.auth0.com/.well-known/jwks.json`
- Scope: All scopes
- Click **"Save"**

**Variable 4: WORKSPACE_DIR**
- Key: `WORKSPACE_DIR`
- Value: `/workspace`
- Scope: All scopes
- Click **"Save"**

**Variable 5: MCP_HTTP_REQUIRE_ORIGIN**
- Key: `MCP_HTTP_REQUIRE_ORIGIN`
- Value: `true`
- Scope: All scopes
- Click **"Save"**

**Variable 6: ALLOWED_ORIGINS**
- Key: `ALLOWED_ORIGINS`
- Value: `https://chatgpt.com,https://chat.openai.com`
- Scope: All scopes
- Click **"Save"**

### Step 6: Configure Netlify Functions

1. In Site settings, click **"Functions"** in the left menu
2. Ensure **"Functions directory"** is set to: `netlify/functions`
3. If it's not set, change it to `netlify/functions` and save

### Step 7: Redeploy with Environment Variables

1. Go to **"Deploys"** tab
2. Click **"Trigger deploy"** → **"Clear cache and deploy site"**
3. Wait for deployment to complete
4. Check the deploy log for any errors

### Step 8: Get Your Site URL

1. Go to **"Site overview"**
2. Your site URL will be: `https://your-site-name.netlify.app` (or a random name)
3. **Copy this URL** - you'll need it for the ChatGPT connector
4. Your MCP endpoint will be: `https://your-site-name.netlify.app/mcp`

### Step 9: Test Deployment

Open a new browser tab and navigate to:
```
https://your-site-name.netlify.app/mcp/health
```

**Expected result**: You should see a 401 Unauthorized error (this is correct - it means the endpoint exists but requires authentication).

If you see 404, check:
- Netlify Functions configuration
- Functions directory is set to `netlify/functions`
- `netlify/functions/mcp.py` exists in your repo

---

## 🔧 Alternative: Deploy via Netlify CLI

If you prefer using the command line:

```bash
# Install Netlify CLI
npm install -g netlify-cli

# Login
netlify login

# Navigate to project
cd C:\Users\Q3Trab\cursor-mcp-server

# Initialize
netlify init
# Follow prompts to create new site or link existing

# Set environment variables
netlify env:set AUTH_ISSUER "https://dev-qswa74vzeymf65ly.auth0.com/"
netlify env:set AUTH_AUDIENCE "https://cursor-mcp"
netlify env:set AUTH_JWKS_URL "https://dev-qswa74vzeymf65ly.auth0.com/.well-known/jwks.json"
netlify env:set WORKSPACE_DIR "/workspace"
netlify env:set MCP_HTTP_REQUIRE_ORIGIN "true"
netlify env:set ALLOWED_ORIGINS "https://chatgpt.com,https://chat.openai.com"

# Deploy
netlify deploy --prod
```

---

## ⚠️ Important Notes for Netlify

### Netlify Functions Limitations

Netlify Functions have some limitations:
- **Timeout**: 10 seconds (Hobby plan) or 26 seconds (Pro plan)
- **Memory**: 1024 MB (Hobby plan) or 3008 MB (Pro plan)
- **Cold starts**: First request may be slower

### If Netlify Doesn't Work Well

If you encounter issues with Netlify, consider these alternatives:

1. **Render.com** (Recommended for Python apps)
   - You already have `render.yaml` in the repo
   - Better Python runtime support
   - Free tier available
   - See `README_OAUTH.md` for Render deployment

2. **Fly.io** (Good for Python apps)
   - You already have `fly.toml` in the repo
   - Docker-based deployment
   - See `README_OAUTH.md` for Fly.io deployment

3. **Railway** (Easy deployment)
   - Simple Python app deployment
   - Good free tier

---

## 🐛 Troubleshooting

### 404 Error on `/mcp`
- **Check**: Netlify Functions configuration
- **Verify**: Functions directory is `netlify/functions`
- **Check**: `netlify/functions/mcp.py` exists in repo
- **Check**: Build logs for errors

### 500 Error
- **Check**: Deploy logs in Netlify dashboard
- **Verify**: All dependencies in `requirements.txt` are installed
- **Check**: Python version (should be 3.11+)
- **Check**: Environment variables are set correctly

### 401 "Invalid token"
- **Verify**: `AUTH_ISSUER` matches: `https://dev-qswa74vzeymf65ly.auth0.com/`
- **Check**: `AUTH_AUDIENCE` is: `https://cursor-mcp`
- **Verify**: `AUTH_JWKS_URL` is correct
- **Check**: Auth0 API is configured correctly

### 403 "Forbidden origin"
- **Check**: `ALLOWED_ORIGINS` includes: `https://chatgpt.com,https://chat.openai.com`
- **Verify**: `MCP_HTTP_REQUIRE_ORIGIN` is set to `true`

### Build Fails
- **Check**: Build logs for Python errors
- **Verify**: `requirements.txt` is correct (no non-existent packages)
- **Check**: Python version compatibility
- **Try**: Clearing build cache and redeploying

---

## ✅ After Deployment: ChatGPT Connector Setup

Once your Netlify site is deployed:

1. **Open ChatGPT** → **Settings** → **Developer Mode** → **Connectors**
2. **Add MCP Server** → Choose **OAuth**
3. **Fill in the form**:
   - **Server URL**: `https://your-site-name.netlify.app/mcp`
   - **Authorization URL**: `https://dev-qswa74vzeymf65ly.auth0.com/authorize`
   - **Token URL**: `https://dev-qswa74vzeymf65ly.auth0.com/oauth/token`
   - **Client ID**: `Q0B9aUEQ3I0rj5PqrDQUiRfYHOM2XL`
   - **Client Secret**: `c_SwR1a7OpEaXJSsqXRD9wReshvloMgpaBngvUWg0AhL_LGraL`
   - **Scopes**: `openid profile email`
4. **Copy the Redirect URL** that ChatGPT shows you
5. **Go back to Auth0**:
   - Navigate to: https://manage.auth0.com/
   - Go to **Applications** → Select `cursor-mcp-oauth`
   - Scroll to **Application URIs** → **Allowed Callback URLs**
   - Add the ChatGPT Redirect URL
   - Click **"Save Changes"**
6. **Complete OAuth flow** in ChatGPT

---

## 📋 Quick Checklist

- [ ] Code pushed to GitHub (✅ Done)
- [ ] requirements.txt fixed (✅ Done)
- [ ] Netlify site created from GitHub
- [ ] Build command set: `pip install -r requirements.txt`
- [ ] All 6 environment variables set
- [ ] Functions directory set to `netlify/functions`
- [ ] Site redeployed with new environment variables
- [ ] Site URL copied (e.g., `https://your-site.netlify.app`)
- [ ] `/mcp/health` returns 401 (not 404)
- [ ] ChatGPT connector added with OAuth
- [ ] Auth0 callback URL updated
- [ ] OAuth flow completed

---

**You're ready to deploy!** Follow the steps above to deploy to Netlify.

