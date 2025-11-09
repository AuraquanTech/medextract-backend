# Final Fix Summary - Path Normalization + Discovery

## Problem
The function was denying ChatGPT's discovery requests because:
1. Netlify rewrites `/mcp` to `/.netlify/functions/mcp` - path check was failing
2. Discovery requests come **without Origin header**
3. Path normalization wasn't handling Netlify's internal routing

## Solution Applied

### 1. Path Normalization
Added `normalizedPath()` function that converts:
- `/.netlify/functions/mcp` → `/mcp`
- `/.netlify/functions/mcp/health` → `/mcp/health`
- Handles both `event.path` and `event.rawUrl`

### 2. Discovery Exception
Added `discoveryAllowed()` function that:
- Allows `GET /mcp` and `GET /mcp/health` **without Origin**
- Only applies to GET/HEAD requests
- Still enforces Origin for POST requests

### 3. Updated Handler Logic
- Normalizes path first
- Checks discovery exception before origin validation
- Properly handles CORS preflight (OPTIONS)
- Includes CORS headers on all responses

## Changes Made

### Function Updates (`netlify/functions/mcp.ts`)
- ✅ Added `normalizedPath()` function
- ✅ Added `discoveryAllowed()` function
- ✅ Updated handler to normalize paths
- ✅ Discovery routes allowed without Origin
- ✅ POST requests still require Origin

### Redirect Updates (`netlify.toml`)
- ✅ Added explicit `/mcp` redirect (important!)
- ✅ Kept `/mcp/*` redirect for other paths

## Testing

### Smoke Tests (After Deploy)

```bash
# No Origin -> should be 200 (manifest/discovery)
curl -i 'https://zingy-profiterole-f31cb8.netlify.app/mcp'

# No Origin -> should be 200 (health)
curl -i 'https://zingy-profiterole-f31cb8.netlify.app/mcp/health'

# With Origin -> should be 200 + CORS headers
curl -i -H 'Origin: https://chatgpt.com' \
  'https://zingy-profiterole-f31cb8.netlify.app/mcp'

# Preflight (OPTIONS) should be 200
curl -i -X OPTIONS -H 'Origin: https://chatgpt.com' \
  -H 'Access-Control-Request-Method: POST' \
  'https://zingy-profiterole-f31cb8.netlify.app/mcp'
```

## Environment Variables

Set in Netlify → Site settings → Environment:

```
ALLOWED_ORIGINS=https://chatgpt.com,https://*.chatgpt.com,https://chat.openai.com,https://*.openai.com
MCP_HTTP_REQUIRE_ORIGIN=true
RATE_LIMIT_WINDOW_MS=60000
RATE_LIMIT_MAX_REQ=300
```

## Connector Settings

After deployment:
- **Server URL:** `https://zingy-profiterole-f31cb8.netlify.app/mcp`
- **Authentication:** None

## If Still Getting 403

### Temporary Fallback
Set this env to register the connector, then flip back:

```
MCP_HTTP_REQUIRE_ORIGIN=false
```

**Steps:**
1. Set `MCP_HTTP_REQUIRE_ORIGIN=false`
2. Redeploy
3. Add connector in ChatGPT
4. Set `MCP_HTTP_REQUIRE_ORIGIN=true`
5. Redeploy

### Debug Endpoint
If you set `MCP_DEBUG_SECRET`, check what headers ChatGPT is sending:

```
https://zingy-profiterole-f31cb8.netlify.app/mcp/debug?token=<your-secret>
```

This shows:
- Actual path received
- Origin/Referer headers
- All request headers (redacted)

## Why This Works

1. **Path Normalization** - Handles Netlify's internal routing (`/.netlify/functions/mcp` → `/mcp`)
2. **Discovery Exception** - Allows GET `/mcp` and `/mcp/health` without Origin
3. **CORS Preflight** - Properly handles OPTIONS requests
4. **Security Maintained** - POST requests still require valid Origin
5. **CORS Headers** - All responses include proper CORS headers

## Key Functions

### `normalizedPath(evt)`
Converts Netlify's internal path to public path:
- `/.netlify/functions/mcp` → `/mcp`
- Handles both `event.path` and `event.rawUrl`

### `discoveryAllowed(method, path, origin)`
Checks if request is a safe discovery route:
- GET/HEAD requests only
- Path matches `/mcp` or `/mcp/health`
- No Origin header present

### `corsHeaders(origin)`
Returns proper CORS headers:
- `access-control-allow-origin` (if origin allowed)
- `vary: Origin` (always)
- `access-control-allow-methods`
- `access-control-allow-headers`

## Next Steps

1. ✅ Deploy the updated function
2. ✅ Verify `netlify.toml` has correct redirects
3. ✅ Set environment variables
4. ✅ Test with curl commands
5. ✅ Add connector in ChatGPT
6. ✅ Verify connection succeeds

## Summary

The function now:
- ✅ Normalizes paths from Netlify's internal routing
- ✅ Allows discovery without Origin
- ✅ Handles CORS preflight correctly
- ✅ Maintains security for POST requests
- ✅ Includes CORS headers on all responses

This should eliminate 403 errors during connector validation.

