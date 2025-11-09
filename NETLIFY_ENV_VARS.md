# Netlify Environment Variables Configuration

## Required Variables

Set these in Netlify → Site settings → Environment variables:

### Core Configuration

```
ALLOWED_ORIGINS=https://chatgpt.com,https://*.chatgpt.com,https://chat.openai.com,https://*.openai.com
MCP_HTTP_REQUIRE_ORIGIN=true
```

### Rate Limiting

```
RATE_LIMIT_WINDOW_MS=60000
RATE_LIMIT_MAX_REQ=300
```

## Optional Variables

### Debug Endpoint (Remove after debugging!)

```
MCP_DEBUG_SECRET=some-long-random-string
```

**⚠️ Security Warning:** Remove this after debugging. It exposes request headers.

## Quick Fix (Temporary)

To quickly unblock the 403 error:

```
MCP_HTTP_REQUIRE_ORIGIN=false
```

**Note:** This disables origin checking. Use only for testing, then switch to proper fix.

## Variable Descriptions

### `ALLOWED_ORIGINS`
- **Type:** Comma-separated list of origins
- **Default:** `https://chatgpt.com,https://*.chatgpt.com,https://chat.openai.com,https://*.openai.com`
- **Description:** Origins allowed to access the MCP endpoint
- **Supports:** Wildcards (`*`) for subdomains

### `MCP_HTTP_REQUIRE_ORIGIN`
- **Type:** Boolean (string: "true" or "false")
- **Default:** `true`
- **Description:** Whether to require and check Origin header
- **Set to:** `false` to disable origin checking (temporary fix)

### `RATE_LIMIT_WINDOW_MS`
- **Type:** Number (milliseconds)
- **Default:** `60000` (1 minute)
- **Description:** Time window for rate limiting

### `RATE_LIMIT_MAX_REQ`
- **Type:** Number
- **Default:** `300`
- **Description:** Maximum requests per window per IP

### `MCP_DEBUG_SECRET`
- **Type:** String
- **Default:** (empty, disabled)
- **Description:** Secret token for debug endpoint
- **Usage:** `https://your-site.netlify.app/mcp/debug?token=<secret>`
- **⚠️ Remove after debugging!**

## Setup Steps

1. Go to Netlify Dashboard
2. Select your site
3. Go to **Site settings** → **Environment variables**
4. Click **Add a variable**
5. Add each variable above
6. Click **Save**
7. **Redeploy** your site for changes to take effect

## Testing

After setting variables and redeploying:

```bash
# Should return 403 (origin check enabled)
curl -i 'https://zingy-profiterole-f31cb8.netlify.app/mcp'

# Should return 200 (with ChatGPT origin)
curl -i -H 'Origin: https://chatgpt.com' \
  'https://zingy-profiterole-f31cb8.netlify.app/mcp'

# Health check
curl -i -H 'Origin: https://chatgpt.com' \
  'https://zingy-profiterole-f31cb8.netlify.app/mcp/health'
```

## Troubleshooting

### Variables Not Working?

1. **Check spelling** - Variable names are case-sensitive
2. **Redeploy** - Changes require a new deployment
3. **Check logs** - Netlify function logs show environment variable values
4. **Verify format** - No quotes needed in Netlify UI

### Still Getting 403?

1. Verify `ALLOWED_ORIGINS` includes the origin ChatGPT is using
2. Check `MCP_HTTP_REQUIRE_ORIGIN` is set correctly
3. Temporarily set `MCP_HTTP_REQUIRE_ORIGIN=false` to test
4. Check Netlify function logs for errors

