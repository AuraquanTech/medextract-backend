# OAuth Setup (Auth0) + ChatGPT Connector

## Auth0 Setup

1. Create **Regular Web Application** and an **API** (Identifier: `https://cursor-mcp`).

2. In the Application → APIs, **authorize** access to the API.

3. While adding the connector in ChatGPT, copy its **Redirect URL** and paste into Auth0 → Application → **Allowed Callback URLs**.

4. Note these values for your deployment:

   - `AUTH_ISSUER` = `https://YOUR-TENANT.us.auth0.com/`
   - `AUTH_AUDIENCE` = `https://cursor-mcp`
   - `AUTH_JWKS_URL` = `https://YOUR-TENANT.us.auth0.com/.well-known/jwks.json`

## Deploy

### Render.com

- Push repo, then click **New Web Service**. Use `render.yaml` or set env manually.
- Start command: `uvicorn http_mcp_oauth_bridge:app --host 0.0.0.0 --port $PORT`

### Fly.io

```bash
fly launch --copy-config --no-deploy
fly secrets set AUTH_ISSUER=https://YOUR-TENANT.us.auth0.com/ AUTH_AUDIENCE=https://cursor-mcp AUTH_JWKS_URL=https://YOUR-TENANT.us.auth0.com/.well-known/jwks.json
fly deploy
```

### Netlify

1. Install Netlify CLI: `npm install -g netlify-cli`
2. Login: `netlify login`
3. Initialize: `netlify init`
4. Set environment variables in Netlify Dashboard → Site settings → Environment variables:
   - `AUTH_ISSUER` = `https://YOUR-TENANT.us.auth0.com/`
   - `AUTH_AUDIENCE` = `https://cursor-mcp`
   - `AUTH_JWKS_URL` = `https://YOUR-TENANT.us.auth0.com/.well-known/jwks.json`
   - `WORKSPACE_DIR` = `/workspace`
   - `MCP_HTTP_REQUIRE_ORIGIN` = `true`
   - `ALLOWED_ORIGINS` = `https://chatgpt.com,https://chat.openai.com`
5. Deploy: `netlify deploy --prod`

Or connect your Git repo in Netlify Dashboard for automatic deployments.

## Add Connector in ChatGPT (Developer Mode)

- **Server URL:** `https://YOUR-DOMAIN/mcp`
- **Auth:** OAuth
- **Authorization URL:** `https://YOUR-TENANT.us.auth0.com/authorize`
- **Token URL:** `https://YOUR-TENANT.us.auth0.com/oauth/token`
- **Client ID/Secret:** from Auth0 app
- **Scopes:** `openid profile email` and/or your API scope
- Paste the **Redirect URL** from ChatGPT back into Auth0 callbacks, then complete consent.

## Verify

In a Developer Mode chat, pick your connector:

- Call `get_diagnostics`
- `list_files` with `pattern:"**/*"`
- `read_file` on a safe file
- `write_file` preview → then apply with `require_confirmation:false`

## Troubleshooting

- **401 Invalid token**: Check `AUTH_ISSUER`, `AUTH_AUDIENCE`, and `AUTH_JWKS_URL` match your Auth0 config
- **403 Forbidden origin**: Verify `ALLOWED_ORIGINS` includes `https://chatgpt.com` and `https://chat.openai.com`
- **Connection refused**: Ensure the service is running and accessible at the Server URL

