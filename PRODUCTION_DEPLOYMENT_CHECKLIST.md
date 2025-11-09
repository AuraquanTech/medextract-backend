# Production Deployment Checklist

## Pre-Deployment

### 1. Dependencies ✅
- [ ] `npm install` completed successfully
- [ ] `minimatch` is installed (`npm list minimatch`)
- [ ] All dependencies in `package.json` match production needs

### 2. Configuration Files ✅
- [ ] `tsconfig.json` has correct settings
- [ ] `netlify.toml` redirects are in correct order (most specific first)
- [ ] `netlify.toml` includes security headers
- [ ] `package.json` has correct build scripts

### 3. Environment Variables ✅
Set in Netlify → Site settings → Environment variables:

- [ ] `ALLOWED_ORIGINS=https://chatgpt.com,https://*.chatgpt.com,https://chat.openai.com,https://*.openai.com`
- [ ] `MCP_HTTP_REQUIRE_ORIGIN=true`
- [ ] `RATE_LIMIT_WINDOW_MS=60000`
- [ ] `RATE_LIMIT_MAX_REQ=300`
- [ ] `WORKSPACE_DIR=/opt/build/repo`

**Optional (for debugging only):**
- [ ] `MCP_DEBUG_SECRET=<long-random-string>` (remove after debugging)
- [ ] `DEBUG_ALLOWED_IPS=<your-ip>` (if using debug endpoint)

## Local Testing

### 1. Start Netlify Dev
```bash
netlify dev
```

### 2. Run Test Suite

**Test 1: Discovery without any headers**
```bash
curl -i http://localhost:8888/mcp
# Expected: 200 with manifest JSON
```

**Test 2: Discovery with Referer instead of Origin**
```bash
curl -i -H 'Referer: https://chatgpt.com/g/xyz' \
  http://localhost:8888/mcp
# Expected: 200 (candidateOrigin handles this)
```

**Test 3: POST without Origin (should fail)**
```bash
curl -i -X POST \
  -H 'Content-Type: application/json' \
  -d '{"method":"tools/list"}' \
  http://localhost:8888/mcp
# Expected: 403 Forbidden origin
```

**Test 4: POST with valid Origin (should succeed)**
```bash
curl -i -X POST \
  -H 'Origin: https://chatgpt.com' \
  -H 'Content-Type: application/json' \
  -d '{"method":"tools/list"}' \
  http://localhost:8888/mcp
# Expected: 200 with CORS headers
```

**Test 5: Preflight with wildcard subdomain**
```bash
curl -i -X OPTIONS \
  -H 'Origin: https://random.chatgpt.com' \
  -H 'Access-Control-Request-Method: POST' \
  http://localhost:8888/mcp
# Expected: 200 (tests minimatch wildcard)
```

**Test 6: Invalid subdomain (should fail)**
```bash
curl -i -H 'Origin: https://evil.com' \
  http://localhost:8888/mcp/tool/something
# Expected: 403
```

### 3. Verify CORS Headers

**Check for required headers:**
```bash
curl -i -H "Origin: https://chatgpt.com" \
  http://localhost:8888/mcp \
  | grep -i "access-control"

# Expected:
# access-control-allow-origin: https://chatgpt.com
# access-control-allow-methods: GET,POST,OPTIONS
# access-control-allow-headers: content-type,authorization
# vary: Origin
```

## Deployment

### 1. Build Verification
```bash
npm run build
# Should complete without errors
```

### 2. Deploy to Netlify
```bash
netlify deploy --prod
# Or push to GitHub (if auto-deploy is enabled)
```

### 3. Verify Deployment
- [ ] Deployment completed successfully
- [ ] No build errors in Netlify logs
- [ ] Function appears in Netlify dashboard

## Production Testing

### 1. Discovery Tests

**Test 1: Discovery without headers**
```bash
curl -i 'https://zingy-profiterole-f31cb8.netlify.app/mcp'
# Expected: 200 with manifest JSON
```

**Test 2: Health check**
```bash
curl -i 'https://zingy-profiterole-f31cb8.netlify.app/mcp/health'
# Expected: 200 with health JSON
```

### 2. CORS Tests

**Test 3: With valid Origin**
```bash
curl -i -H 'Origin: https://chatgpt.com' \
  'https://zingy-profiterole-f31cb8.netlify.app/mcp'
# Expected: 200 + CORS headers
```

**Test 4: With invalid Origin**
```bash
curl -i -H 'Origin: https://evil.com' \
  'https://zingy-profiterole-f31cb8.netlify.app/mcp'
# Expected: 403
```

**Test 5: OPTIONS preflight**
```bash
curl -i -X OPTIONS \
  -H 'Origin: https://chatgpt.com' \
  -H 'Access-Control-Request-Method: POST' \
  'https://zingy-profiterole-f31cb8.netlify.app/mcp'
# Expected: 200 + CORS headers
```

### 3. Verify Response Headers

**Check for required CORS headers:**
```bash
curl -i -H "Origin: https://chatgpt.com" \
  'https://zingy-profiterole-f31cb8.netlify.app/mcp' \
  | grep -i "access-control"

# Expected:
# access-control-allow-origin: https://chatgpt.com
# access-control-allow-methods: GET,POST,OPTIONS
# access-control-allow-headers: content-type,authorization
# vary: Origin
```

**Check for security headers:**
```bash
curl -i 'https://zingy-profiterole-f31cb8.netlify.app/mcp' \
  | grep -i "x-content-type-options\|x-frame-options\|x-xss-protection"

# Expected:
# X-Content-Type-Options: nosniff
# X-Frame-Options: DENY
# X-XSS-Protection: 1; mode=block
```

## Monitoring

### 1. Function Logs

**Monitor logs via Netlify CLI:**
```bash
netlify functions:log mcp --follow
```

**Or in Netlify Dashboard:**
- Site → Functions → mcp → Logs

**Look for:**
- [ ] Repeated 403s from same origin
- [ ] Missing headers patterns
- [ ] Path normalization issues
- [ ] Rate limiting hits

### 2. Structured Logging

**Verify logs include:**
- Timestamp
- Method
- Path (normalized)
- Origin
- Result (allowed/forbidden/discovery/preflight)
- IP address

### 3. Metrics Endpoint

**Check metrics:**
```bash
curl -i -H 'Origin: https://chatgpt.com' \
  'https://zingy-profiterole-f31cb8.netlify.app/mcp/metrics'
# Expected: 200 with metrics JSON
```

## ChatGPT Connector Setup

### 1. Add Connector

**In ChatGPT:**
- Server URL: `https://zingy-profiterole-f31cb8.netlify.app/mcp`
- Authentication: None
- Headers: (leave empty initially)

### 2. Verify Connection

- [ ] Connector validation succeeds
- [ ] No 403 errors during validation
- [ ] Tools are discovered correctly

### 3. Test Tool Calls

- [ ] Test actual MCP tool call from ChatGPT
- [ ] Verify response includes CORS headers
- [ ] Check function logs for successful requests

## Post-Deployment

### 1. Security Hardening

- [ ] Remove `MCP_DEBUG_SECRET` if used (or secure with IP allowlist)
- [ ] Verify `MCP_HTTP_REQUIRE_ORIGIN=true` is set
- [ ] Check security headers are present
- [ ] Verify rate limiting is working

### 2. Monitoring Setup

- [ ] Set up log monitoring (Netlify dashboard or external service)
- [ ] Configure alerts for repeated 403s
- [ ] Monitor rate limiting hits
- [ ] Track metrics endpoint

### 3. Documentation

- [ ] Update documentation with production URL
- [ ] Document environment variables
- [ ] Create runbook for common issues
- [ ] Document fallback procedures

## Troubleshooting

### Issue 1: Still Getting 403 on Discovery

**Check:**
- [ ] Function logs for actual path received
- [ ] Verify `normalizedPath()` is working (check logs)
- [ ] Confirm redirect rules deployed (check Netlify dashboard)
- [ ] Test with debug endpoint (if enabled)

**Solution:**
```bash
# Add logging to function
console.log("Normalized path:", normalizedPath(event));
```

### Issue 2: Wildcard Origins Not Working

**Check:**
- [ ] `minimatch` is installed (`npm list minimatch`)
- [ ] `node_modules` in deploy log
- [ ] Test with explicit origin first: `https://chatgpt.com`

**Solution:**
```bash
# Verify minimatch in production
netlify functions:log mcp | grep minimatch
```

### Issue 3: CORS Headers Missing

**Check:**
- [ ] `corsHeaders()` is called on ALL return statements
- [ ] `vary: Origin` is present even on error responses
- [ ] `base` is spread into headers: `{ ...base }`

**Solution:**
```bash
# Check headers in response
curl -i -H "Origin: https://chatgpt.com" \
  'https://zingy-profiterole-f31cb8.netlify.app/mcp' \
  | grep -i "access-control"
```

## Emergency Fallback

### If Still Getting 403 After All Fixes

**Temporary bypass (use only for registration):**

```bash
# 1. Temporarily disable origin check
netlify env:set MCP_HTTP_REQUIRE_ORIGIN false

# 2. Set expiration (1 hour from now)
netlify env:set MCP_FALLBACK_UNTIL $(date -u -d '+1 hour' +%Y-%m-%dT%H:%M:%SZ)

# 3. Deploy
netlify deploy --prod

# 4. Register connector in ChatGPT

# 5. Immediately revert
netlify env:set MCP_HTTP_REQUIRE_ORIGIN true
netlify env:unset MCP_FALLBACK_UNTIL

# 6. Redeploy
netlify deploy --prod
```

**⚠️ Security Warning:**
- Don't leave `MCP_HTTP_REQUIRE_ORIGIN=false` in production
- Use only to register the connector
- Revert immediately after registration

## Success Criteria

✅ **Discovery works** - GET `/mcp` without Origin returns 200
✅ **Health check works** - GET `/mcp/health` without Origin returns 200
✅ **CORS works** - Requests with valid Origin include CORS headers
✅ **Preflight works** - OPTIONS requests return 200 with CORS headers
✅ **Security works** - Invalid origins return 403
✅ **Rate limiting works** - Too many requests return 429
✅ **Logging works** - Structured logs appear in Netlify logs
✅ **Security headers work** - X-Content-Type-Options, X-Frame-Options present
✅ **Connector works** - ChatGPT connector validation succeeds
✅ **Tool calls work** - Actual MCP tool calls from ChatGPT succeed

## Next Steps

1. ✅ Complete all pre-deployment checks
2. ✅ Run local tests
3. ✅ Deploy to Netlify
4. ✅ Run production tests
5. ✅ Add connector in ChatGPT
6. ✅ Verify connection succeeds
7. ✅ Monitor logs for issues
8. ✅ Remove debug secret (if used)
9. ✅ Set up monitoring alerts
10. ✅ Document production setup

