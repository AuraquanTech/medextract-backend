# Connector Validation Fix - Summary

## Problem
The strict origin check was blocking ChatGPT's connector probe, causing 403 errors during discovery.

## Solution
Updated the Netlify function to:
1. ✅ **Widen allowed origins** - Accepts ChatGPT variants with wildcards
2. ✅ **Accept Referer header** - Falls back to Referer if Origin is missing
3. ✅ **Relax validation routes** - Allows GET `/mcp` and `/mcp/health` without Origin
4. ✅ **Handle OPTIONS preflight** - Properly handles CORS preflight requests
5. ✅ **Add CORS headers** - All responses include proper CORS headers

## Changes Made

### 1. Improved Origin Helpers
- `toOrigin()` - Extracts origin from URL
- `candidateOrigin()` - Prefers Origin, falls back to Referer
- `originAllowed()` - Checks against allowed patterns with wildcards

### 2. CORS Headers Function
- `corsHeaders()` - Returns proper CORS headers for allowed origins
- Includes `access-control-allow-origin`, `vary`, `access-control-allow-methods`, `access-control-allow-headers`

### 3. Relaxed Validation Gate
- **OPTIONS requests** - Always allowed (CORS preflight)
- **Safe validation routes** - GET `/mcp` and `/mcp/health` allowed without Origin
- **Normal enforcement** - All other routes require valid Origin

### 4. CORS Headers on All Responses
- All responses include `baseHeaders` (CORS headers)
- Errors also include CORS headers (prevents browser CORS errors)

## Testing

### Test Commands

```bash
# No Origin → GET /mcp allowed (discovery)
curl -i 'https://zingy-profiterole-f31cb8.netlify.app/mcp'

# Allowed Origin → 200 with CORS
curl -i -H 'Origin: https://chatgpt.com' \
  'https://zingy-profiterole-f31cb8.netlify.app/mcp'

# Health (same behavior)
curl -i 'https://zingy-profiterole-f31cb8.netlify.app/mcp/health'

curl -i -H 'Origin: https://chatgpt.com' \
  'https://zingy-profiterole-f31cb8.netlify.app/mcp/health'

# Preflight (OPTIONS) should be 200 with allow headers
curl -i -X OPTIONS -H 'Origin: https://chatgpt.com' \
  -H 'Access-Control-Request-Method: POST' \
  'https://zingy-profiterole-f31cb8.netlify.app/mcp'
```

## Expected Behavior

### ✅ Allowed (No 403)
- `GET /mcp` without Origin (discovery)
- `GET /mcp/health` without Origin (health check)
- `OPTIONS *` (CORS preflight)
- Any request with allowed Origin (`https://chatgpt.com`, `https://chat.openai.com`, etc.)

### ❌ Blocked (403)
- POST requests without Origin (except safe routes)
- Requests with disallowed origins
- Rate limit exceeded (429)

## Environment Variables

Set in Netlify → Site settings → Environment:

```
ALLOWED_ORIGINS=https://chatgpt.com,https://*.chatgpt.com,https://chat.openai.com,https://*.openai.com
MCP_HTTP_REQUIRE_ORIGIN=true
RATE_LIMIT_WINDOW_MS=60000
RATE_LIMIT_MAX_REQ=300
WORKSPACE_DIR=/opt/build/repo
```

## Connector Settings

After deployment:
- **Server URL:** `https://zingy-profiterole-f31cb8.netlify.app/mcp`
- **Authentication:** None

## Why This Works

1. **Discovery works** - GET `/mcp` without Origin is allowed
2. **CORS works** - Proper headers prevent browser CORS errors
3. **Preflight works** - OPTIONS requests are handled correctly
4. **Security maintained** - POST requests still require valid Origin
5. **Rate limiting** - Still protects against abuse

## Next Steps

1. ✅ Deploy the updated function
2. ✅ Set environment variables
3. ✅ Test with curl commands
4. ✅ Add connector in ChatGPT
5. ✅ Verify connection succeeds

## Troubleshooting

### Still Getting 403?

1. **Check debug endpoint** (if enabled):
   ```
   https://zingy-profiterole-f31cb8.netlify.app/mcp/debug?token=<secret>
   ```
   This shows what headers ChatGPT is sending.

2. **Verify environment variables** are set correctly

3. **Check Netlify logs** for errors

4. **Temporarily disable origin check** to test:
   ```
   MCP_HTTP_REQUIRE_ORIGIN=false
   ```
   Connect, verify it works, then turn it back on.

### CORS Errors in Browser?

- Ensure `corsHeaders()` is called for all responses
- Check that `access-control-allow-origin` header is present
- Verify Origin is in `ALLOWED_ORIGINS`

## Summary

The function now:
- ✅ Allows connector discovery without Origin
- ✅ Handles CORS preflight correctly
- ✅ Accepts Referer as fallback
- ✅ Includes CORS headers on all responses
- ✅ Maintains security for POST requests
- ✅ Keeps rate limiting enabled

This should eliminate 403 errors during connector validation while maintaining security.

