# Expanded Test Suite

## Complete Test Coverage

### Test 1: Discovery without any headers (ChatGPT initial probe)

```bash
curl -i 'https://zingy-profiterole-f31cb8.netlify.app/mcp'
```

**Expected Response:**
```
HTTP/2 200
content-type: application/json
vary: Origin

{"name":"cursor-mcp-netlify","version":"1.1",...}
```

**Why this matters:** ChatGPT's initial discovery probe often arrives without Origin header. This must succeed.

---

### Test 2: Discovery with Referer instead of Origin

```bash
curl -i -H 'Referer: https://chatgpt.com/g/xyz' \
  'https://zingy-profiterole-f31cb8.netlify.app/mcp'
```

**Expected Response:**
```
HTTP/2 200
content-type: application/json
vary: Origin

{"name":"cursor-mcp-netlify","version":"1.1",...}
```

**Why this matters:** Some clients send `Referer` instead of `Origin`. The `candidateOrigin()` function handles this.

---

### Test 3: POST without Origin (should fail)

```bash
curl -i -X POST \
  -H 'Content-Type: application/json' \
  -d '{"method":"tools/list"}' \
  'https://zingy-profiterole-f31cb8.netlify.app/mcp'
```

**Expected Response:**
```
HTTP/2 403
vary: Origin

Forbidden origin
```

**Why this matters:** POST requests must have valid Origin for security. Discovery exception only applies to GET/HEAD.

---

### Test 4: POST with valid Origin (should succeed)

```bash
curl -i -X POST \
  -H 'Origin: https://chatgpt.com' \
  -H 'Content-Type: application/json' \
  -d '{"method":"tools/list"}' \
  'https://zingy-profiterole-f31cb8.netlify.app/mcp'
```

**Expected Response:**
```
HTTP/2 200
access-control-allow-origin: https://chatgpt.com
access-control-allow-methods: GET,POST,OPTIONS
access-control-allow-headers: content-type,authorization
vary: Origin
content-type: application/json

{"jsonrpc":"2.0",...}
```

**Why this matters:** Valid POST requests must succeed with proper CORS headers.

---

### Test 5: Preflight with wildcard subdomain

```bash
curl -i -X OPTIONS \
  -H 'Origin: https://random.chatgpt.com' \
  -H 'Access-Control-Request-Method: POST' \
  'https://zingy-profiterole-f31cb8.netlify.app/mcp'
```

**Expected Response:**
```
HTTP/2 200
access-control-allow-origin: https://random.chatgpt.com
access-control-allow-methods: GET,POST,OPTIONS
access-control-allow-headers: content-type,authorization
vary: Origin
```

**Why this matters:** Tests `minimatch` wildcard matching (`https://*.chatgpt.com`).

---

### Test 6: Invalid subdomain (should fail)

```bash
curl -i -H 'Origin: https://evil.com' \
  'https://zingy-profiterole-f31cb8.netlify.app/mcp/tool/something'
```

**Expected Response:**
```
HTTP/2 403
vary: Origin

Forbidden origin
```

**Why this matters:** Invalid origins must be rejected.

---

### Test 7: Health check without Origin

```bash
curl -i 'https://zingy-profiterole-f31cb8.netlify.app/mcp/health'
```

**Expected Response:**
```
HTTP/2 200
content-type: application/json
vary: Origin

{"ok":true,"status":"ok","service":"mcp"}
```

**Why this matters:** Health checks should work without Origin (discovery exception).

---

### Test 8: Health check with Origin

```bash
curl -i -H 'Origin: https://chatgpt.com' \
  'https://zingy-profiterole-f31cb8.netlify.app/mcp/health'
```

**Expected Response:**
```
HTTP/2 200
access-control-allow-origin: https://chatgpt.com
access-control-allow-methods: GET,POST,OPTIONS
access-control-allow-headers: content-type,authorization
vary: Origin
content-type: application/json

{"ok":true,"status":"ok","service":"mcp"}
```

**Why this matters:** Health checks with Origin should include CORS headers.

---

### Test 9: Metrics endpoint

```bash
curl -i -H 'Origin: https://chatgpt.com' \
  'https://zingy-profiterole-f31cb8.netlify.app/mcp/metrics'
```

**Expected Response:**
```
HTTP/2 200
access-control-allow-origin: https://chatgpt.com
content-type: application/json

{"totalRequests":...,"lastError":null,...}
```

**Why this matters:** Metrics endpoint should be accessible for monitoring.

---

### Test 10: Debug endpoint (if enabled)

```bash
curl -i "https://zingy-profiterole-f31cb8.netlify.app/mcp/debug?token=<your-secret>"
```

**Expected Response:**
```
HTTP/2 200
content-type: application/json

{"ok":true,"normalizedPath":"/mcp","origin":"https://chatgpt.com","headers":{...}}
```

**Why this matters:** Debug endpoint helps troubleshoot header issues.

**⚠️ Security:** Only use this for debugging. Remove `MCP_DEBUG_SECRET` after debugging.

---

## Header Verification

### Required CORS Headers (for valid Origin)

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

**Why `vary: Origin` is critical:**
- Prevents cache poisoning
- Must be present even on 403 responses
- Ensures correct CORS handling

### Required Security Headers

```bash
curl -i 'https://zingy-profiterole-f31cb8.netlify.app/mcp' \
  | grep -i "x-content-type-options\|x-frame-options\|x-xss-protection"

# Expected:
# X-Content-Type-Options: nosniff
# X-Frame-Options: DENY
# X-XSS-Protection: 1; mode=block
# Referrer-Policy: strict-origin-when-cross-origin
```

**Why these matter:**
- `X-Content-Type-Options: nosniff` - Prevents MIME type sniffing
- `X-Frame-Options: DENY` - Prevents clickjacking
- `X-XSS-Protection` - XSS protection
- `Referrer-Policy` - Controls referrer information

---

## Automated Test Script

Create `test_mcp_endpoints.sh`:

```bash
#!/bin/bash

BASE_URL="https://zingy-profiterole-f31cb8.netlify.app"

echo "Testing MCP Endpoints..."
echo "========================"

# Test 1: Discovery without Origin
echo -e "\n1. Discovery without Origin:"
curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/mcp"
echo " (expected: 200)"

# Test 2: Health check
echo -e "\n2. Health check:"
curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/mcp/health"
echo " (expected: 200)"

# Test 3: With valid Origin
echo -e "\n3. With valid Origin:"
curl -s -o /dev/null -w "%{http_code}" \
  -H "Origin: https://chatgpt.com" \
  "$BASE_URL/mcp"
echo " (expected: 200)"

# Test 4: With invalid Origin
echo -e "\n4. With invalid Origin:"
curl -s -o /dev/null -w "%{http_code}" \
  -H "Origin: https://evil.com" \
  "$BASE_URL/mcp"
echo " (expected: 403)"

# Test 5: OPTIONS preflight
echo -e "\n5. OPTIONS preflight:"
curl -s -o /dev/null -w "%{http_code}" \
  -X OPTIONS \
  -H "Origin: https://chatgpt.com" \
  -H "Access-Control-Request-Method: POST" \
  "$BASE_URL/mcp"
echo " (expected: 200)"

echo -e "\n========================"
echo "Tests complete!"
```

**Run:**
```bash
chmod +x test_mcp_endpoints.sh
./test_mcp_endpoints.sh
```

---

## Expected Response Headers Summary

### Discovery (GET /mcp without Origin)
```
HTTP/2 200
content-type: application/json
vary: Origin
```

### Discovery (GET /mcp with valid Origin)
```
HTTP/2 200
access-control-allow-origin: https://chatgpt.com
access-control-allow-methods: GET,POST,OPTIONS
access-control-allow-headers: content-type,authorization
vary: Origin
content-type: application/json
```

### POST Request (with valid Origin)
```
HTTP/2 200
access-control-allow-origin: https://chatgpt.com
access-control-allow-methods: GET,POST,OPTIONS
access-control-allow-headers: content-type,authorization
vary: Origin
content-type: application/json
```

### OPTIONS Preflight
```
HTTP/2 200
access-control-allow-origin: https://chatgpt.com
access-control-allow-methods: GET,POST,OPTIONS
access-control-allow-headers: content-type,authorization
vary: Origin
```

### Error Response (403)
```
HTTP/2 403
vary: Origin

Forbidden origin
```

**Note:** Even error responses must include `vary: Origin` to prevent cache poisoning.

---

## Success Criteria

✅ All 10 tests pass
✅ CORS headers present for valid Origins
✅ Security headers present on all responses
✅ `vary: Origin` present on all responses
✅ Discovery works without Origin
✅ POST requests require valid Origin
✅ Wildcard subdomains work correctly
✅ Invalid origins are rejected

