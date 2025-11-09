# Quick Deployment Checklist

## Auth0 Setup (5 minutes)

- [ ] Navigate to https://manage.auth0.com/
- [ ] Create Regular Web Application → Name: `cursor-mcp-oauth`
- [ ] Copy **Client ID** and **Client Secret** (save for ChatGPT connector)
- [ ] Create API → Identifier: `https://cursor-mcp`
- [ ] Authorize application to access API
- [ ] Note **Domain** from Settings → Domain
- [ ] Add temporary callback URLs: `https://chatgpt.com/*`, `https://chat.openai.com/*`

**Values to save:**
- `AUTH_ISSUER` = `https://YOUR-TENANT.us.auth0.com/`
- `AUTH_AUDIENCE` = `https://cursor-mcp`
- `AUTH_JWKS_URL` = `https://YOUR-TENANT.us.auth0.com/.well-known/jwks.json`
- Client ID: `[from Auth0 app]`
- Client Secret: `[from Auth0 app]`

---

## Netlify Deployment (5 minutes)

- [ ] Navigate to https://app.netlify.com/
- [ ] Add new site → Import from Git (or Deploy manually)
- [ ] Configure build: `pip install -r requirements.txt`
- [ ] Set environment variables:
  - `AUTH_ISSUER` = `https://YOUR-TENANT.us.auth0.com/`
  - `AUTH_AUDIENCE` = `https://cursor-mcp`
  - `AUTH_JWKS_URL` = `https://YOUR-TENANT.us.auth0.com/.well-known/jwks.json`
  - `WORKSPACE_DIR` = `/workspace`
  - `MCP_HTTP_REQUIRE_ORIGIN` = `true`
  - `ALLOWED_ORIGINS` = `https://chatgpt.com,https://chat.openai.com`
- [ ] Deploy site
- [ ] Copy site URL (e.g., `https://your-site.netlify.app`)

**MCP Endpoint:** `https://your-site.netlify.app/mcp`

---

## Render.com Alternative (5 minutes)

- [ ] Navigate to https://dashboard.render.com/
- [ ] New → Web Service
- [ ] Connect repository
- [ ] Build command: `pip install -r requirements.txt`
- [ ] Start command: `uvicorn http_mcp_oauth_bridge:app --host 0.0.0.0 --port $PORT`
- [ ] Set same environment variables as above
- [ ] Deploy

**MCP Endpoint:** `https://your-service.onrender.com/mcp`

---

## ChatGPT Connector Setup (3 minutes)

- [ ] Open ChatGPT → Settings → Developer Mode → Connectors
- [ ] Add MCP Server → Choose **OAuth**
- [ ] **Server URL:** `https://your-site.netlify.app/mcp`
- [ ] **Authorization URL:** `https://YOUR-TENANT.us.auth0.com/authorize`
- [ ] **Token URL:** `https://YOUR-TENANT.us.auth0.com/oauth/token`
- [ ] **Client ID:** `[from Auth0 app]`
- [ ] **Client Secret:** `[from Auth0 app]`
- [ ] **Scopes:** `openid profile email`
- [ ] Copy **Redirect URL** from ChatGPT
- [ ] Go back to Auth0 → Application → Allowed Callback URLs
- [ ] Add the ChatGPT Redirect URL
- [ ] Save and complete OAuth flow

---

## Verification (2 minutes)

In ChatGPT Developer Mode chat:
- [ ] Call `get_diagnostics` → Should return workspace info
- [ ] Call `list_files` with `pattern:"**/*"` → Should return file list
- [ ] Call `read_file` on `README.md` → Should return file content

---

## Troubleshooting Quick Fixes

| Issue | Fix |
|-------|-----|
| 401 Invalid token | Check AUTH_ISSUER, AUTH_AUDIENCE match Auth0 |
| 403 Forbidden origin | Verify ALLOWED_ORIGINS includes ChatGPT domains |
| 404 Not found | Check Netlify Functions path or start command |
| 500 Error | Check deploy logs for Python errors |
| App not authorized | Enable in Auth0 API → Machine to Machine tab |

---

**Total Time:** ~15 minutes

