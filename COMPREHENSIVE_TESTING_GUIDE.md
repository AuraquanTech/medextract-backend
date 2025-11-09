# Comprehensive Testing Guide

## Pre-Deployment Checklist

### 1. Dependencies

**Install required packages:**
```bash
npm install
```

**Verify `minimatch` is installed:**
```bash
npm list minimatch
```

**Expected output:**
```
netlify-mcp-server@1.0.0
└── minimatch@10.0.0
```

### 2. TypeScript Configuration

**Verify `tsconfig.json` exists and is correct:**
```bash
cat tsconfig.json
```

**Key settings:**
- `target: "ES2020"`
- `module: "commonjs"`
- `esModuleInterop: true`
- `resolveJsonModule: true`

### 3. Netlify Configuration

**Check `netlify.toml` redirect order:**
- Most specific paths first
- Wildcard patterns last
- Exact `/mcp` path after wildcard

**Verify function bundler:**
```toml
[functions]
  node_bundler = "zisi"  # v1 (default)
```

### 4. Environment Variables

**Check current environment variables:**
```bash
# Using Netlify CLI
netlify env:list

# Or check in Netlify Dashboard
# Site settings → Environment variables
```

**Required variables:**
```
ALLOWED_ORIGINS=https://chatgpt.com,https://*.chatgpt.com,https://chat.openai.com,https://*.openai.com
MCP_HTTP_REQUIRE_ORIGIN=true
RATE_LIMIT_WINDOW_MS=60000
RATE_LIMIT_MAX_REQ=300
```

## Local Testing

### 1. Start Netlify Dev

```bash
netlify dev
```

**Expected output:**
```
◈ Netlify Dev ◈
◈ Server now ready on http://localhost:8888
```

### 2. Test Discovery (No Origin)

```bash
# Discovery endpoint (should return 200 + manifest)
curl -i http://localhost:8888/mcp

# Expected response:
# HTTP/1.1 200 OK
# content-type: application/json
# vary: Origin
# 
# {"name":"cursor-mcp-netlify","version":"1.1",...}
```

### 3. Test Health Check

```bash
# Health endpoint (should return 200)
curl -i http://localhost:8888/mcp/health

# Expected response:
# HTTP/1.1 200 OK
# content-type: application/json
# vary: Origin
# 
# {"ok":true,"status":"ok","service":"mcp"}
```

### 4. Test with Valid Origin

```bash
# With ChatGPT origin (should return 200 + CORS headers)
curl -i -H "Origin: https://chatgpt.com" \
  http://localhost:8888/mcp

# Expected headers:
# access-control-allow-origin: https://chatgpt.com
# access-control-allow-methods: GET,POST,OPTIONS
# access-control-allow-headers: content-type,authorization
# vary: Origin
```

### 5. Test with Invalid Origin

```bash
# With invalid origin (should return 403)
curl -i -H "Origin: https://evil.com" \
  http://localhost:8888/mcp

# Expected response:
# HTTP/1.1 403 Forbidden
# vary: Origin
# 
# Forbidden origin
```

### 6. Test OPTIONS Preflight

```bash
# CORS preflight (should return 200 + CORS headers)
curl -i -X OPTIONS \
  -H "Origin: https://chatgpt.com" \
  -H "Access-Control-Request-Method: POST" \
  http://localhost:8888/mcp

# Expected response:
# HTTP/1.1 200 OK
# access-control-allow-origin: https://chatgpt.com
# access-control-allow-methods: GET,POST,OPTIONS
# access-control-allow-headers: content-type,authorization
# vary: Origin
```

## Production Testing

### 1. After Deployment

**Test discovery endpoint:**
```bash
# Should return 200 + manifest (no Origin required)
curl -i https://zingy-profiterole-f31cb8.netlify.app/mcp

# Expected:
# HTTP/1.1 200 OK
# content-type: application/json
# vary: Origin
# 
# {"name":"cursor-mcp-netlify","version":"1.1",...}
```

**Test health check:**
```bash
# Should return 200 (no Origin required)
curl -i https://zingy-profiterole-f31cb8.netlify.app/mcp/health

# Expected:
# HTTP/1.1 200 OK
# content-type: application/json
# vary: Origin
# 
# {"ok":true,"status":"ok","service":"mcp"}
```

**Test with valid Origin:**
```bash
# Should return 200 + CORS headers
curl -i -H "Origin: https://chatgpt.com" \
  https://zingy-profiterole-f31cb8.netlify.app/mcp

# Expected headers:
# access-control-allow-origin: https://chatgpt.com
# access-control-allow-methods: GET,POST,OPTIONS
# access-control-allow-headers: content-type,authorization
# vary: Origin
```

**Test with invalid Origin:**
```bash
# Should return 403
curl -i -H "Origin: https://evil.com" \
  https://zingy-profiterole-f31cb8.netlify.app/mcp

# Expected:
# HTTP/1.1 403 Forbidden
# vary: Origin
# 
# Forbidden origin
```

**Test OPTIONS preflight:**
```bash
# Should return 200 + CORS headers
curl -i -X OPTIONS \
  -H "Origin: https://chatgpt.com" \
  -H "Access-Control-Request-Method: POST" \
  https://zingy-profiterole-f31cb8.netlify.app/mcp

# Expected:
# HTTP/1.1 200 OK
# access-control-allow-origin: https://chatgpt.com
# access-control-allow-methods: GET,POST,OPTIONS
# access-control-allow-headers: content-type,authorization
# vary: Origin
```

### 2. Verify Headers

**Check for required CORS headers:**
```bash
curl -i -H "Origin: https://chatgpt.com" \
  https://zingy-profiterole-f31cb8.netlify.app/mcp \
  | grep -i "access-control"

# Expected:
# access-control-allow-origin: https://chatgpt.com
# access-control-allow-methods: GET,POST,OPTIONS
# access-control-allow-headers: content-type,authorization
# vary: Origin
```

### 3. Test Metrics Endpoint

```bash
# Metrics endpoint (optional)
curl -i -H "Origin: https://chatgpt.com" \
  https://zingy-profiterole-f31cb8.netlify.app/mcp/metrics

# Expected:
# HTTP/1.1 200 OK
# content-type: application/json
# 
# {"totalRequests":...,"lastError":null,...}
```

### 4. Test Debug Endpoint (if enabled)

```bash
# Debug endpoint (requires MCP_DEBUG_SECRET)
curl -i "https://zingy-profiterole-f31cb8.netlify.app/mcp/debug?token=<your-secret>"

# Expected:
# HTTP/1.1 200 OK
# content-type: application/json
# 
# {"ok":true,"headers":{...}}
```

## Troubleshooting

### Issue: Still Getting 403

**Check 1: Verify minimatch is installed**
```bash
npm list minimatch
```

**Check 2: Verify environment variables**
```bash
netlify env:list
```

**Check 3: Check Netlify function logs**
```bash
# In Netlify Dashboard
# Site → Functions → mcp → Logs
```

**Check 4: Test with debug endpoint**
```bash
# If MCP_DEBUG_SECRET is set
curl "https://zingy-profiterole-f31cb8.netlify.app/mcp/debug?token=<secret>"
```

**Check 5: Temporarily disable origin check**
```bash
# Emergency bypass
netlify env:set MCP_HTTP_REQUIRE_ORIGIN false

# Deploy, test, then revert:
netlify env:set MCP_HTTP_REQUIRE_ORIGIN true
```

### Issue: CORS Errors in Browser

**Check 1: Verify CORS headers are present**
```bash
curl -i -H "Origin: https://chatgpt.com" \
  https://zingy-profiterole-f31cb8.netlify.app/mcp \
  | grep -i "access-control"
```

**Check 2: Verify Origin is in ALLOWED_ORIGINS**
```bash
netlify env:get ALLOWED_ORIGINS
```

**Check 3: Check browser console for CORS errors**
- Open browser DevTools
- Check Console tab
- Look for CORS-related errors

### Issue: TypeScript Compilation Errors

**Check 1: Verify tsconfig.json**
```bash
cat tsconfig.json
```

**Check 2: Try building locally**
```bash
npm run build
```

**Check 3: Check Netlify build logs**
```bash
# In Netlify Dashboard
# Site → Deploys → Latest → Build log
```

### Issue: Redirect Not Working

**Check 1: Verify redirect order in netlify.toml**
- Most specific paths first
- Wildcard patterns last
- Exact `/mcp` path after wildcard

**Check 2: Test redirect directly**
```bash
# Should redirect to function
curl -i -L https://zingy-profiterole-f31cb8.netlify.app/mcp
```

**Check 3: Check Netlify redirect logs**
```bash
# In Netlify Dashboard
# Site → Redirects → Test redirect
```

## Success Criteria

✅ **Discovery works** - GET `/mcp` without Origin returns 200
✅ **Health check works** - GET `/mcp/health` without Origin returns 200
✅ **CORS works** - Requests with valid Origin include CORS headers
✅ **Preflight works** - OPTIONS requests return 200 with CORS headers
✅ **Security works** - Invalid origins return 403
✅ **Rate limiting works** - Too many requests return 429

## Next Steps

1. ✅ Complete all local tests
2. ✅ Deploy to Netlify
3. ✅ Complete all production tests
4. ✅ Add connector in ChatGPT
5. ✅ Verify connection succeeds
6. ✅ Monitor metrics endpoint
7. ✅ Remove debug secret (if used)

