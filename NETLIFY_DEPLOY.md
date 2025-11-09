# Netlify Deployment Guide - Quick Steps

## Your Configuration Values

**Auth0:**
- Domain: `dev-qswa74vzeymf65ly.auth0.com`
- Client ID: `Q0B9aUEQ3I0rj5PqrDQUiRfYHOM2XL`
- Client Secret: `c_SwR1a7OpEaXJSsqXRD9wReshvloMgpaBngvUWg0AhL_LGraL`

**GitHub:**
- Repository: `https://github.com/AuraquanTech/cursor-mcp-http-bridge`

---

## Step-by-Step Netlify Deployment

### Step 1: Push Code to GitHub

```bash
cd C:\Users\Q3Trab\cursor-mcp-server
git init
git add .
git commit -m "Initial commit: OAuth MCP bridge"
git remote add origin https://github.com/AuraquanTech/cursor-mcp-http-bridge.git
git branch -M main
git push -u origin main
```

### Step 2: Deploy to Netlify (Web Dashboard)

1. **Go to Netlify**: https://app.netlify.com/
2. **Click "Add new site"** → **"Import an existing project"**
3. **Select "GitHub"** and authorize Netlify
4. **Find your repository**: `AuraquanTech/cursor-mcp-http-bridge`
5. **Click "Import"**

### Step 3: Configure Build Settings

On the deploy configuration page:

- **Build command**: `pip install -r requirements.txt`
- **Publish directory**: `.` (or leave empty)
- **Click "Deploy site"**

### Step 4: Set Environment Variables

After the site is created:

1. Go to **Site settings** (gear icon)
2. Click **"Environment variables"** in the left menu
3. Click **"Add variable"** and add each:

**Variable 1:**
- Key: `AUTH_ISSUER`
- Value: `https://dev-qswa74vzeymf65ly.auth0.com/`
- Scope: All scopes
- Click **"Save"**

**Variable 2:**
- Key: `AUTH_AUDIENCE`
- Value: `https://cursor-mcp`
- Scope: All scopes
- Click **"Save"**

**Variable 3:**
- Key: `AUTH_JWKS_URL`
- Value: `https://dev-qswa74vzeymf65ly.auth0.com/.well-known/jwks.json`
- Scope: All scopes
- Click **"Save"**

**Variable 4:**
- Key: `WORKSPACE_DIR`
- Value: `/workspace`
- Scope: All scopes
- Click **"Save"**

**Variable 5:**
- Key: `MCP_HTTP_REQUIRE_ORIGIN`
- Value: `true`
- Scope: All scopes
- Click **"Save"**

**Variable 6:**
- Key: `ALLOWED_ORIGINS`
- Value: `https://chatgpt.com,https://chat.openai.com`
- Scope: All scopes
- Click **"Save"**

### Step 5: Redeploy

1. Go to **"Deploys"** tab
2. Click **"Trigger deploy"** → **"Clear cache and deploy site"**
3. Wait for deployment to complete

### Step 6: Get Your Site URL

1. Go to **"Site overview"**
2. Your site URL will be: `https://your-site-name.netlify.app`
3. **Copy this URL** - you'll need it for ChatGPT connector
4. Your MCP endpoint: `https://your-site-name.netlify.app/mcp`

### Step 7: Test Deployment

Open a new browser tab and navigate to:
```
https://your-site-name.netlify.app/mcp/health
```

**Expected result**: You should see a 401 Unauthorized error (this is correct - it means the endpoint exists but requires authentication).

If you see 404, check your Netlify Functions configuration.

---

## Alternative: Deploy via CLI

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

## After Deployment: ChatGPT Connector Setup

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

## Troubleshooting

### 404 Error on `/mcp`
- Check that `netlify/functions/mcp.py` exists
- Verify `netlify.toml` has correct functions directory
- Check build logs for errors

### 500 Error
- Check deploy logs in Netlify dashboard
- Verify all dependencies in `requirements.txt` are installed
- Check Python version (should be 3.11+)

### 401 "Invalid token"
- Verify `AUTH_ISSUER` matches: `https://dev-qswa74vzeymf65ly.auth0.com/`
- Check `AUTH_AUDIENCE` is: `https://cursor-mcp`
- Verify `AUTH_JWKS_URL` is correct

### 403 "Forbidden origin"
- Check `ALLOWED_ORIGINS` includes: `https://chatgpt.com,https://chat.openai.com`
- Verify `MCP_HTTP_REQUIRE_ORIGIN` is set to `true`

---

## Quick Checklist

- [ ] Code pushed to GitHub
- [ ] Netlify site created from GitHub
- [ ] Build command set: `pip install -r requirements.txt`
- [ ] All 6 environment variables set
- [ ] Site redeployed with new environment variables
- [ ] Site URL copied (e.g., `https://your-site.netlify.app`)
- [ ] `/mcp/health` returns 401 (not 404)
- [ ] ChatGPT connector added with OAuth
- [ ] Auth0 callback URL updated
- [ ] OAuth flow completed

---

**You're all set!** Once deployed, you can connect ChatGPT to your MCP server via OAuth.

