# Quick Deploy Checklist

## ✅ Pre-Deployment

- [ ] Function file is at `netlify/functions/mcp.ts` (not `netlify_functions_mcp.ts`)
- [ ] `package.json` includes `@netlify/functions` and `minimatch`
- [ ] `netlify.toml` has redirects configured
- [ ] TypeScript file is `.ts` (not `.js`)

## ✅ Environment Variables (Netlify Dashboard)

- [ ] `ALLOWED_ORIGINS=https://chatgpt.com,https://*.chatgpt.com,https://chat.openai.com,https://*.openai.com`
- [ ] `MCP_HTTP_REQUIRE_ORIGIN=true`
- [ ] `RATE_LIMIT_WINDOW_MS=60000`
- [ ] `RATE_LIMIT_MAX_REQ=300`
- [ ] `WORKSPACE_DIR=/opt/build/repo`
- [ ] `MCP_DEBUG_SECRET=<secret>` (optional, remove after debugging)

## ✅ Deploy

- [ ] Push to GitHub (or trigger redeploy)
- [ ] Wait for deployment to complete
- [ ] Check Netlify build logs for errors

## ✅ Test

- [ ] Test without origin (should be 403):
  ```bash
  curl -i 'https://zingy-profiterole-f31cb8.netlify.app/mcp'
  ```

- [ ] Test with origin (should be 200):
  ```bash
  curl -i -H 'Origin: https://chatgpt.com' \
    'https://zingy-profiterole-f31cb8.netlify.app/mcp'
  ```

- [ ] Test health endpoint:
  ```bash
  curl -i -H 'Origin: https://chatgpt.com' \
    'https://zingy-profiterole-f31cb8.netlify.app/mcp/health'
  ```

- [ ] Test metrics (optional):
  ```bash
  curl -i -H 'Origin: https://chatgpt.com' \
    'https://zingy-profiterole-f31cb8.netlify.app/mcp/metrics'
  ```

## ✅ Connect

- [ ] Add connector in ChatGPT
- [ ] Server URL: `https://zingy-profiterole-f31cb8.netlify.app/mcp`
- [ ] Authentication: None
- [ ] Verify connection succeeds

## ✅ Post-Deployment

- [ ] Remove `MCP_DEBUG_SECRET` if used
- [ ] Monitor metrics endpoint
- [ ] Check Netlify logs for errors
- [ ] Verify tools are accessible in ChatGPT

## 🐛 If Still Getting 403

- [ ] Check debug endpoint (if enabled):
  ```
  https://zingy-profiterole-f31cb8.netlify.app/mcp/debug?token=<secret>
  ```
- [ ] Verify actual origin ChatGPT is using
- [ ] Add origin to `ALLOWED_ORIGINS` if needed
- [ ] Temporarily set `MCP_HTTP_REQUIRE_ORIGIN=false` to test
- [ ] Check Netlify function logs

