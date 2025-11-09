# Cursor MCP Server - Netlify Deployment

## Overview

This is a production-ready MCP (Model Context Protocol) server deployed on Netlify with:
- ✅ Path normalization for Netlify routing
- ✅ Discovery exception for origin-less probes
- ✅ Proper CORS handling with wildcard origin support
- ✅ Rate limiting and security headers
- ✅ Structured logging for monitoring
- ✅ Debug endpoint for troubleshooting

## Quick Start

### 1. Install Dependencies

```bash
npm install
```

**Critical:** Ensure `minimatch` is installed:
```bash
npm list minimatch
```

### 2. Set Environment Variables

In Netlify → Site settings → Environment variables:

```
ALLOWED_ORIGINS=https://chatgpt.com,https://*.chatgpt.com,https://chat.openai.com,https://*.openai.com
MCP_HTTP_REQUIRE_ORIGIN=true
RATE_LIMIT_WINDOW_MS=60000
RATE_LIMIT_MAX_REQ=300
WORKSPACE_DIR=/opt/build/repo
```

### 3. Deploy

```bash
netlify deploy --prod
```

### 4. Test

```bash
# Discovery (should work without Origin)
curl -i 'https://your-site.netlify.app/mcp'

# With Origin (should include CORS headers)
curl -i -H 'Origin: https://chatgpt.com' \
  'https://your-site.netlify.app/mcp'
```

### 5. Connect in ChatGPT

- **Server URL:** `https://your-site.netlify.app/mcp`
- **Authentication:** None

## Documentation

- **`COMPREHENSIVE_TESTING_GUIDE.md`** - Complete testing protocol
- **`CRITICAL_IMPLEMENTATION_NOTES.md`** - Important implementation details
- **`PRODUCTION_DEPLOYMENT_CHECKLIST.md`** - Pre/post deployment checklist
- **`EXPANDED_TEST_SUITE.md`** - Full test coverage
- **`FALLBACK_STRATEGY.md`** - Emergency fallback procedures
- **`FINAL_FIX_SUMMARY.md`** - Summary of fixes applied

## Key Features

### Path Normalization
Handles Netlify's internal routing (`/.netlify/functions/mcp` → `/mcp`)

### Discovery Exception
Allows GET `/mcp` and `/mcp/health` without Origin header

### CORS Support
Proper CORS headers with wildcard origin matching (`https://*.chatgpt.com`)

### Security
- Origin validation for POST requests
- Rate limiting
- Security headers (X-Content-Type-Options, X-Frame-Options, etc.)

### Monitoring
- Structured logging
- Metrics endpoint
- Debug endpoint (optional)

## File Structure

```
cursor-mcp-server/
├── netlify/
│   └── functions/
│       └── mcp.ts          # Main MCP function
├── netlify.toml            # Netlify configuration
├── package.json            # Dependencies
├── tsconfig.json           # TypeScript configuration
└── README.md               # This file
```

## Testing

See `EXPANDED_TEST_SUITE.md` for complete test coverage.

**Quick test:**
```bash
# Discovery
curl -i 'https://your-site.netlify.app/mcp'

# Health
curl -i 'https://your-site.netlify.app/mcp/health'

# With Origin
curl -i -H 'Origin: https://chatgpt.com' \
  'https://your-site.netlify.app/mcp'
```

## Troubleshooting

### Still Getting 403?

1. Check `minimatch` is installed
2. Verify environment variables are set
3. Check Netlify function logs
4. Use debug endpoint (if enabled)
5. See `FALLBACK_STRATEGY.md` for emergency bypass

### CORS Errors?

1. Verify CORS headers are present
2. Check Origin is in `ALLOWED_ORIGINS`
3. Ensure `vary: Origin` is included

### Path Issues?

1. Check `normalizedPath()` is working
2. Verify redirect rules in `netlify.toml`
3. Check function logs for actual path

## Security Notes

- **Keep `MCP_HTTP_REQUIRE_ORIGIN=true` in production**
- **Remove `MCP_DEBUG_SECRET` after debugging**
- **Monitor function logs for suspicious activity**
- **Set up alerts for repeated 403s**

## Support

For issues:
1. Check `CRITICAL_IMPLEMENTATION_NOTES.md`
2. Review `PRODUCTION_DEPLOYMENT_CHECKLIST.md`
3. Check Netlify function logs
4. Use debug endpoint (if enabled)

## License

See LICENSE file for details.
