# Netlify MCP Server 403 Fix

## Problem
403 Forbidden error when connecting to `https://zingy-profiterole-f31cb8.netlify.app/mcp`

**Root Cause:** Origin gate is rejecting ChatGPT's requests because ChatGPT uses different origins (`https://chatgpt.com`, `https://chat.openai.com`, and subdomains).

## Solution Options

### Option 1: Quick Fix (Temporary)
**Fastest unblock - no code change needed**

In Netlify → Site settings → Environment variables:
```
MCP_HTTP_REQUIRE_ORIGIN=false
```

**Steps:**
1. Add the environment variable in Netlify
2. Redeploy the site
3. Add the connector again
4. Once connected, turn the gate back on and use Option 2

### Option 2: Proper Fix (Recommended)
**Keep Origin gate on, but accept all ChatGPT origins**

This solution:
- ✅ Accepts both `Origin` and `Referer` headers
- ✅ Supports wildcards for subdomains (`https://*.chatgpt.com`)
- ✅ Keeps rate limiting enabled
- ✅ Includes debug endpoint for troubleshooting

## Implementation

### Step 1: Update Netlify Function

Update `netlify/functions/mcp.ts` with the improved origin checking (see `mcp.ts` file).

### Step 2: Set Environment Variables

In Netlify → Site settings → Environment variables:

```
ALLOWED_ORIGINS=https://chatgpt.com,https://*.chatgpt.com,https://chat.openai.com,https://*.openai.com
MCP_HTTP_REQUIRE_ORIGIN=true
RATE_LIMIT_WINDOW_MS=60000
RATE_LIMIT_MAX_REQ=300
```

**Optional (for debugging only):**
```
MCP_DEBUG_SECRET=some-long-random-string
```

### Step 3: Deploy

1. Commit the updated `mcp.ts` file
2. Push to trigger Netlify deployment
3. Wait for deployment to complete

### Step 4: Test Connection

```bash
# Without Origin (should be 403 when REQUIRE_ORIGIN=true)
curl -i 'https://zingy-profiterole-f31cb8.netlify.app/mcp'

# With ChatGPT origin (should be 200)
curl -i -H 'Origin: https://chatgpt.com' \
  'https://zingy-profiterole-f31cb8.netlify.app/mcp'

# Health check with origin
curl -i -H 'Origin: https://chatgpt.com' \
  'https://zingy-profiterole-f31cb8.netlify.app/mcp/health'
```

### Step 5: Debug (Optional)

If you set `MCP_DEBUG_SECRET`, you can inspect what headers ChatGPT is sending:

```
https://zingy-profiterole-f31cb8.netlify.app/mcp/debug?token=<your MCP_DEBUG_SECRET>
```

**⚠️ Important:** Remove `MCP_DEBUG_SECRET` after debugging for security.

## Connector Settings

After deployment, configure the connector:

- **Server URL:** `https://zingy-profiterole-f31cb8.netlify.app/mcp`
- **Authentication:** None

## Why This Works

1. **Wider Origin Support:** Accepts all ChatGPT variants (main domain + subdomains)
2. **Referer Fallback:** Some clients send `Referer` instead of `Origin`
3. **Wildcard Matching:** Uses `minimatch` for flexible subdomain matching
4. **Rate Limiting:** Still protects against abuse
5. **Debug Endpoint:** Helps troubleshoot header issues

## Troubleshooting

### Still Getting 403?

1. **Check environment variables** are set correctly in Netlify
2. **Verify deployment** completed successfully
3. **Test with curl** to see actual response
4. **Check Netlify logs** for errors
5. **Temporarily disable origin check** (`MCP_HTTP_REQUIRE_ORIGIN=false`) to verify other parts work

### Debug Endpoint Not Working?

1. Verify `MCP_DEBUG_SECRET` is set
2. Check the token matches in the URL
3. Ensure the path is `/mcp/debug` (not `/mcp/debug/`)
4. Check Netlify logs for errors

## Security Notes

- **Keep rate limiting enabled** to prevent abuse
- **Remove debug secret** after troubleshooting
- **Monitor Netlify logs** for suspicious activity
- **Consider IP whitelisting** for additional security if needed

## Next Steps

1. Choose Option 1 (quick fix) or Option 2 (proper fix)
2. If Option 2, update the `mcp.ts` file with the improved code
3. Set environment variables in Netlify
4. Deploy and test
5. Connect the MCP connector in ChatGPT

