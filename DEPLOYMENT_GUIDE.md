# Netlify MCP Server Deployment Guide

## Quick Setup (5 Steps)

### 1) Put the function in the right place

The function file must be located at:
```
netlify/functions/mcp.ts
```

**Important:** Netlify only picks up functions inside the `netlify/functions/` directory.

### 2) Set Environment Variables

In Netlify → Site settings → Environment variables, add:

```
ALLOWED_ORIGINS=https://chatgpt.com,https://*.chatgpt.com,https://chat.openai.com,https://*.openai.com
MCP_HTTP_REQUIRE_ORIGIN=true
RATE_LIMIT_WINDOW_MS=60000
RATE_LIMIT_MAX_REQ=300
WORKSPACE_DIR=/opt/build/repo
```

**Optional (for debugging only):**
```
MCP_DEBUG_SECRET=<a-long-random-string>
```

⚠️ **Remove `MCP_DEBUG_SECRET` after debugging!**

### 3) Verify Dependencies

Ensure `package.json` includes:
```json
{
  "dependencies": {
    "@netlify/functions": "^2.0.0",
    "minimatch": "^10.0.0"
  }
}
```

### 4) Redeploy

Push to GitHub (or trigger a redeploy from the Netlify dashboard).

### 5) Quick Sanity Checks

Test the endpoints:

```bash
# Should be 403 without origin when REQUIRE_ORIGIN=true
curl -i 'https://zingy-profiterole-f31cb8.netlify.app/mcp'

# Should be 200 with allowed origin
curl -i -H 'Origin: https://chatgpt.com' \
  'https://zingy-profiterole-f31cb8.netlify.app/mcp'

# Health check
curl -i -H 'Origin: https://chatgpt.com' \
  'https://zingy-profiterole-f31cb8.netlify.app/mcp/health'

# Metrics (optional)
curl -i -H 'Origin: https://chatgpt.com' \
  'https://zingy-profiterole-f31cb8.netlify.app/mcp/metrics'

# Diagnostics (optional)
curl -i -H 'Origin: https://chatgpt.com' \
  'https://zingy-profiterole-f31cb8.netlify.app/mcp/tool/get_diagnostics'
```

**Optional debug endpoint (remove after debugging):**
```
https://zingy-profiterole-f31cb8.netlify.app/mcp/debug?token=<your MCP_DEBUG_SECRET>
```

### 6) Add Connector in ChatGPT

- **Server URL:** `https://zingy-profiterole-f31cb8.netlify.app/mcp`
- **Authentication:** None

## File Structure

Your project should have this structure:

```
your-project/
├── netlify/
│   └── functions/
│       └── mcp.ts          # Main MCP function
├── netlify.toml            # Netlify configuration
├── package.json            # Dependencies
└── README.md
```

## Common Gotchas

### ✅ Function Location
- **Correct:** `netlify/functions/mcp.ts`
- **Wrong:** `netlify_functions_mcp.ts` or `functions/mcp.ts`

### ✅ Dependencies
Ensure `package.json` includes:
- `@netlify/functions`
- `minimatch`

### ✅ netlify.toml
The `netlify.toml` file should have redirects:
```toml
[[redirects]]
  from = "/mcp/*"
  to = "/.netlify/functions/mcp/:splat"
  status = 200
```

### ✅ TypeScript vs JavaScript
- Function file is **TypeScript** (`mcp.ts`) or JavaScript (`mcp.js`)
- Not both - choose one

### ✅ Still Getting 403?

1. **Check debug endpoint** (if enabled):
   ```
   https://your-site.netlify.app/mcp/debug?token=<secret>
   ```
   This shows exactly what Origin/Referer ChatGPT is sending.

2. **Add the origin to ALLOWED_ORIGINS:**
   - If ChatGPT sends `https://subdomain.chatgpt.com`, add it
   - Or use wildcards: `https://*.chatgpt.com`

3. **Temporarily disable origin check:**
   ```
   MCP_HTTP_REQUIRE_ORIGIN=false
   ```
   Connect, verify it works, then turn it back on.

## Optional Features

### Metrics Endpoint

Access metrics at `/mcp/metrics`:
- Total requests count
- Last error message
- Last origin seen
- Last timestamp

### Diagnostics Endpoint

Access diagnostics at `/mcp/tool/get_diagnostics`:
- Full metrics
- Configuration values
- Rate limit settings

### Debug Endpoint

Access debug info at `/mcp/debug?token=<secret>`:
- Request headers (redacted)
- Origin/Referer values
- Configuration state

⚠️ **Remove `MCP_DEBUG_SECRET` after debugging!**

## Troubleshooting

### Function Not Found (404)

1. Check file is at `netlify/functions/mcp.ts`
2. Verify `netlify.toml` has correct redirects
3. Check Netlify build logs for errors

### Still Getting 403

1. Check environment variables are set
2. Verify `ALLOWED_ORIGINS` includes ChatGPT's origin
3. Use debug endpoint to see actual headers
4. Temporarily set `MCP_HTTP_REQUIRE_ORIGIN=false` to test

### Rate Limit Issues (429)

1. Check `RATE_LIMIT_WINDOW_MS` and `RATE_LIMIT_MAX_REQ`
2. Verify IP is not being blocked
3. Check Netlify logs for rate limit hits

## Next Steps

1. ✅ Deploy the function
2. ✅ Set environment variables
3. ✅ Test with curl commands
4. ✅ Add connector in ChatGPT
5. ✅ Monitor metrics endpoint
6. ✅ Remove debug secret after testing

## Security Notes

- **Keep rate limiting enabled** to prevent abuse
- **Remove debug secret** after debugging
- **Monitor metrics** for suspicious activity
- **Review Netlify logs** regularly
- **Update ALLOWED_ORIGINS** if ChatGPT changes domains

