# Netlify Quick Start - Exact Steps

## ✅ Fixed Files (Pushed to GitHub)

- `requirements.txt` - Removed `uvicorn` (not needed for Netlify Functions)
- `netlify/functions/mcp.py` - Updated Mangum wrapper
- `netlify.toml` - Added redirects for `/mcp/*` routes

---

## 🚀 Netlify Deployment Steps

### Step 1: Import from GitHub

1. Go to: **https://app.netlify.com/**
2. Click **"Add new site"** → **"Import an existing project"**
3. Select **"GitHub"** and authorize
4. Find: **`AuraquanTech/cursor-mcp-http-bridge`**
5. Click **"Import"**

### Step 2: Configure Build (Optional - Netlify auto-detects)

- **Build command**: Leave empty (or `pip install -r requirements.txt`)
- **Publish directory**: Leave empty
- Click **"Deploy site"**

### Step 3: Set Environment Variables

Go to **Site settings** → **Environment variables** → Add these 6:

| Key | Value |
|-----|-------|
| `AUTH_ISSUER` | `https://dev-qswa74vzeymf65ly.auth0.com/` |
| `AUTH_AUDIENCE` | `https://cursor-mcp` |
| `AUTH_JWKS_URL` | `https://dev-qswa74vzeymf65ly.auth0.com/.well-known/jwks.json` |
| `WORKSPACE_DIR` | `/workspace` |
| `MCP_HTTP_REQUIRE_ORIGIN` | `true` |
| `ALLOWED_ORIGINS` | `https://chatgpt.com,https://chat.openai.com` |

### Step 4: Redeploy

1. Go to **"Deploys"** tab
2. Click **"Trigger deploy"** → **"Clear cache and deploy site"**
3. Wait for deployment to complete

### Step 5: Get Your Site URL

After deployment, your site URL will be: `https://your-site-name.netlify.app`

Your MCP endpoint: `https://your-site-name.netlify.app/mcp`

---

## 🧪 Smoke Test

After deployment, test with curl (replace `YOUR_SITE` and `YOUR_TOKEN`):

```bash
BASE="https://your-site-name.netlify.app"
TOKEN="YOUR_OAUTH_ACCESS_TOKEN"

# health
curl -sS -H "Authorization: Bearer $TOKEN" "$BASE/mcp/health"

# manifest
curl -sS -H "Authorization: Bearer $TOKEN" "$BASE/mcp"

# tool call
curl -sS -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"params":{"path":"README.md"}}' \
  "$BASE/mcp/tool/read_file"
```

**Expected**: JSON responses (401 if token is missing/invalid)

---

## 🔗 ChatGPT Connector Setup

1. **Open ChatGPT** → **Settings** → **Developer Mode** → **Connectors**
2. **Add MCP Server** → Choose **OAuth**
3. **Fill in**:
   - **Server URL**: `https://your-site-name.netlify.app/mcp`
   - **Authorization URL**: `https://dev-qswa74vzeymf65ly.auth0.com/authorize`
   - **Token URL**: `https://dev-qswa74vzeymf65ly.auth0.com/oauth/token`
   - **Client ID**: `Q0B9aUEQ3I0rj5PqrDQUiRfYHOM2XL`
   - **Client Secret**: `c_SwR1a7OpEaXJSsqXRD9wReshvloMgpaBngvUWg0AhL_LGraL`
   - **Scopes**: `openid profile email`
4. **Copy the Redirect URL** from ChatGPT
5. **Go to Auth0** → **Applications** → `cursor-mcp-oauth` → **Allowed Callback URLs**
6. **Add the ChatGPT Redirect URL**
7. **Save** and complete OAuth flow

---

## 🌐 Custom Domain (Optional)

If you want `mcp.nexusquan.com`:

1. **Netlify** → **Domain settings** → **Add custom domain**: `mcp.nexusquan.com`
2. **Copy the CNAME target** (e.g., `your-site.netlify.app`)
3. **Namecheap** → **nexusquan.com** → **Advanced DNS** → **Add record**:
   - **Type**: CNAME
   - **Host**: `mcp`
   - **Value**: `your-site.netlify.app`
   - **TTL**: Automatic
4. **Wait** a few minutes for DNS + SSL certs
5. **Use**: `https://mcp.nexusquan.com/mcp` as your Server URL

---

## 🐛 Common Issues

### Build Failed
- ✅ Fixed: `requirements.txt` no longer has `uvicorn` or `anthropic-mcp-sdk`
- Check build logs if still failing

### ModuleNotFoundError
- Ensure `requirements.txt` is at repo root
- Verify function is at `netlify/functions/mcp.py`

### `/mcp` Returns HTML (404)
- Check `netlify.toml` is at repo root
- Verify redirects are committed
- Redeploy after fixing

### 401 Invalid Token
- Verify `AUTH_ISSUER` matches: `https://dev-qswa74vzeymf65ly.auth0.com/`
- Check `AUTH_AUDIENCE` is: `https://cursor-mcp`
- Verify JWT `iss` and `aud` match env vars

---

## ✅ Checklist

- [ ] Code pushed to GitHub (✅ Done)
- [ ] `requirements.txt` fixed (✅ Done - no uvicorn)
- [ ] `netlify.toml` configured (✅ Done - redirects added)
- [ ] `netlify/functions/mcp.py` updated (✅ Done - Mangum wrapper)
- [ ] Netlify site created from GitHub
- [ ] All 6 environment variables set
- [ ] Site redeployed
- [ ] Site URL copied
- [ ] `/mcp/health` returns 401 (not 404)
- [ ] ChatGPT connector added with OAuth
- [ ] Auth0 callback URL updated
- [ ] OAuth flow completed

---

**You're ready to deploy!** All fixes are pushed to GitHub.

