# Node/TypeScript Netlify Deployment - Complete Guide

## ✅ What Changed

Switched from Python to **Node.js/TypeScript** using the **official MCP JS SDK**:

- ✅ **Node 18+** runtime (Netlify's strength)
- ✅ **Official MCP JS SDK** with Streamable HTTP transport
- ✅ **TypeScript** with proper type safety
- ✅ **OAuth 2.1 JWT validation** via JOSE + JWKS cache
- ✅ **CORS/Origin allowlist** enforcement
- ✅ **Per-IP rate limiting** (sliding window)
- ✅ **Body size/time guards**
- ✅ **Two invocation styles**:
  - JSON-RPC at `POST /mcp` (future-proof with SDK transport)
  - REST helpers: `GET /mcp` (manifest), `GET /mcp/health`, `POST /mcp/tool/:name`

---

## 🚀 Deployment Steps

### Step 1: Merge the Branch

The code is on branch `feat/netlify-node-mcp`. You can:

**Option A: Merge via GitHub**
1. Go to: https://github.com/AuraquanTech/cursor-mcp-http-bridge/pull/new/feat/netlify-node-mcp
2. Create a pull request
3. Merge to `main`

**Option B: Merge locally**
```bash
git checkout main
git merge feat/netlify-node-mcp
git push origin main
```

### Step 2: Update Environment Variables

Go to **Netlify → Site settings → Environment variables**:

Update `WORKSPACE_DIR`:
- **Old**: `/workspace`
- **New**: `/` (bundle root; read-only)

Keep these as-is:
- `AUTH_ISSUER` = `https://dev-qswa74vzeymf65ly.auth0.com/`
- `AUTH_AUDIENCE` = `https://cursor-mcp`
- `AUTH_JWKS_URL` = `https://dev-qswa74vzeymf65ly.auth0.com/.well-known/jwks.json`
- `MCP_HTTP_REQUIRE_ORIGIN` = `true`
- `ALLOWED_ORIGINS` = `https://chatgpt.com,https://chat.openai.com`

Optional hardening:
- `RATE_LIMIT_WINDOW_S` = `60` (default)
- `RATE_LIMIT_MAX_REQ` = `300` (default)
- `MCP_MAX_BODY_BYTES` = `262144` (default, 256 KB)

### Step 3: Netlify Auto-Deploys

After merging to `main`, Netlify will automatically:
1. Detect the new `package.json`
2. Run `npm ci || npm i`
3. Build the TypeScript function
4. Deploy

Watch the deploy logs for any errors.

---

## 🧪 Smoke Test

After deployment, test with curl (replace `YOUR_TOKEN` with a valid OAuth token):

```bash
BASE="https://zingy-profiterole-f31cb8.netlify.app"
TOKEN="YOUR_OAUTH_ACCESS_TOKEN"

# Health (REST)
curl -sS -H "Authorization: Bearer $TOKEN" "$BASE/mcp/health" | jq

# Manifest (REST)
curl -sS -H "Authorization: Bearer $TOKEN" "$BASE/mcp" | jq

# Tool helper: read_file
curl -sS -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"params":{"path":"README.md"}}' \
  "$BASE/mcp/tool/read_file" | jq

# JSON-RPC (future-proof)
curl -sS -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":"1","method":"tools/call","params":{"name":"list_files","arguments":{"base":".","pattern":"**/*","max_results":25}}}' \
  "$BASE/mcp" | jq
```

**Expected**: JSON responses; 401 if token is missing/invalid.

---

## 🔗 ChatGPT Connector Setup

1. **Open ChatGPT** → **Settings** → **Developer Mode** → **Connectors**
2. **Add MCP Server** → Choose **OAuth**
3. **Fill in**:
   - **Server URL**: `https://zingy-profiterole-f31cb8.netlify.app/mcp`
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
2. **Copy the CNAME target** (e.g., `zingy-profiterole-f31cb8.netlify.app`)
3. **Namecheap** → **nexusquan.com** → **Advanced DNS** → **Add record**:
   - **Type**: CNAME
   - **Host**: `mcp`
   - **Value**: `zingy-profiterole-f31cb8.netlify.app`
   - **TTL**: Automatic
4. **Wait** a few minutes for DNS + SSL certs
5. **Use**: `https://mcp.nexusquan.com/mcp` as your Server URL

---

## 📋 Files Changed

### New Files:
- ✅ `package.json` - Node dependencies (MCP SDK, JOSE, minimatch)
- ✅ `tsconfig.json` - TypeScript configuration
- ✅ `netlify/functions/mcp.ts` - Node/TypeScript function

### Updated Files:
- ✅ `netlify.toml` - Updated for Node functions with esbuild bundler

### Removed Files:
- ❌ `netlify/functions/mcp.py` - Old Python function (removed)
- ❌ `requirements.txt` - No longer needed (kept for reference)
- ❌ `.python-version` - No longer needed (kept for reference)

---

## 🎯 Why This is Better

- ✅ **Runs where Netlify is strongest**: Node Functions
- ✅ **Uses official MCP JS SDK** + Streamable HTTP (modern MCP transport)
- ✅ **Keeps OAuth** with strict issuer/audience checks and JWKS validation
- ✅ **Enforces origin allowlist**, rate limiting, body limits, JSON parsing safety
- ✅ **Exposes JSON-RPC** (for ChatGPT Developer Mode) and **REST helpers** (for humans and curl)

---

## 🐛 Troubleshooting

### Build Fails
- Check Node version (should be 18+)
- Verify `package.json` dependencies are correct
- Check build logs for TypeScript errors

### ModuleNotFoundError
- Ensure `package.json` is at repo root
- Verify function is at `netlify/functions/mcp.ts`
- Check Netlify is using Node bundler (esbuild)

### 401 Invalid Token
- Verify `AUTH_ISSUER` matches: `https://dev-qswa74vzeymf65ly.auth0.com/`
- Check `AUTH_AUDIENCE` is: `https://cursor-mcp`
- Verify `AUTH_JWKS_URL` is correct

### 403 Forbidden Origin
- Check `ALLOWED_ORIGINS` includes: `https://chatgpt.com,https://chat.openai.com`
- Verify `MCP_HTTP_REQUIRE_ORIGIN` is set to `true`

---

## ✅ Checklist

- [ ] Branch `feat/netlify-node-mcp` created and pushed (✅ Done)
- [ ] Merge branch to `main`
- [ ] Update `WORKSPACE_DIR` to `/` in Netlify environment variables
- [ ] Netlify auto-deploys after merge
- [ ] Build succeeds (check logs)
- [ ] Test endpoints with curl
- [ ] Add ChatGPT connector with OAuth
- [ ] Update Auth0 callback URL
- [ ] Complete OAuth flow

---

**You're ready to merge and deploy!** The Node/TypeScript implementation is complete and pushed to GitHub.

