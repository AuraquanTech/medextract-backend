# Quick Start Guide

## 🚀 Deploy in 5 Minutes

### Step 1: Install Dependencies
```bash
npm install
```

### Step 2: Set Environment Variables

In Netlify → Site settings → Environment variables:

```
ALLOWED_ORIGINS=https://chatgpt.com,https://*.chatgpt.com,https://chat.openai.com,https://*.openai.com
MCP_HTTP_REQUIRE_ORIGIN=true
RATE_LIMIT_WINDOW_MS=60000
RATE_LIMIT_MAX_REQ=300
```

### Step 3: Deploy
```bash
netlify deploy --prod
```

### Step 4: Test
```bash
curl -i 'https://your-site.netlify.app/mcp'
# Expected: 200 OK
```

### Step 5: Connect in ChatGPT
- **Server URL:** `https://your-site.netlify.app/mcp`
- **Authentication:** None

## ✅ Done!

Your MCP server is now deployed and ready to use.

## Troubleshooting

### Still Getting 403?

1. Check `minimatch` is installed: `npm list minimatch`
2. Verify environment variables: `netlify env:list`
3. Check Netlify function logs
4. See `FALLBACK_STRATEGY.md` for emergency bypass

### Need More Help?

- See `PRODUCTION_DEPLOYMENT_CHECKLIST.md` for detailed steps
- See `EXPANDED_TEST_SUITE.md` for test cases
- See `CRITICAL_IMPLEMENTATION_NOTES.md` for important details

