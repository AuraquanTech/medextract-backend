# Critical Implementation Notes

## ⚠️ Important: Must-Have Dependencies

### 1. minimatch Package

**Installation Required:**
```bash
npm install minimatch
```

**Why it's critical:**
- Wildcard origin matching (`https://*.chatgpt.com`) requires `minimatch`
- Without it, wildcard patterns will fail silently
- You'll get 403 errors from subdomain requests

**Verify installation:**
```bash
npm list minimatch
```

**Expected:**
```
netlify-mcp-server@1.0.0
└── minimatch@10.0.0
```

## 🔧 TypeScript Configuration

### Required tsconfig.json Settings

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "module": "commonjs",
    "esModuleInterop": true,
    "resolveJsonModule": true
  }
}
```

**Why these matter:**
- `target: "ES2020"` - Ensures modern JavaScript features work
- `module: "commonjs"` - Required for Netlify Functions v1
- `esModuleInterop: true` - Allows importing CommonJS modules
- `resolveJsonModule: true` - Allows importing JSON files

**Build script in package.json:**
```json
{
  "scripts": {
    "build": "tsc"
  }
}
```

## 📦 Netlify Functions v1 vs v2

### Current Implementation: v1

**Function signature:**
```typescript
import { Handler } from "@netlify/functions";

export const handler: Handler = async (event) => {
  // v1 signature
};
```

**netlify.toml configuration:**
```toml
[functions]
  node_bundler = "zisi"  # v1 (default)
```

### If Upgrading to v2

**Function signature changes:**
```typescript
// v2 signature
export default async (req: Request) => {
  return new Response(body, { status: 200, headers });
};
```

**netlify.toml configuration:**
```toml
[functions]
  node_bundler = "esbuild"  # v2
```

**⚠️ Important:** The current code uses v1. If you upgrade to v2, you'll need to rewrite the handler.

## 🔀 Redirect Order Matters

### Correct Order (Most Specific First)

```toml
# Health check (most specific)
[[redirects]]
  from = "/mcp/health"
  to = "/.netlify/functions/mcp"
  status = 200

# Tool endpoints (specific pattern)
[[redirects]]
  from = "/mcp/tool/*"
  to = "/.netlify/functions/mcp/:splat"
  status = 200

# Metrics endpoint
[[redirects]]
  from = "/mcp/metrics"
  to = "/.netlify/functions/mcp"
  status = 200

# Wildcard for all other /mcp/* paths
[[redirects]]
  from = "/mcp/*"
  to = "/.netlify/functions/mcp/:splat"
  status = 200

# Exact /mcp path (must come after wildcard)
[[redirects]]
  from = "/mcp"
  to = "/.netlify/functions/mcp"
  status = 200
```

### Why Order Matters

- Netlify processes redirects **top to bottom**
- First match wins
- If `/mcp/*` comes before `/mcp`, the exact match won't be caught
- Most specific paths must come first

## 🔐 Environment Variable Priority

### Fallback Chain

```typescript
const RAW_ALLOWED = (
  process.env.ALLOWED_ORIGINS || 
  "https://chatgpt.com,https://*.chatgpt.com,https://chat.openai.com,https://*.openai.com"
)
```

**Important:** If `ALLOWED_ORIGINS` is already set in Netlify, the defaults won't apply.

**Check current environment variables:**
```bash
# Using Netlify CLI
netlify env:list

# Or in Netlify Dashboard
# Site settings → Environment variables
```

**If you have existing `ALLOWED_ORIGINS`:**
- The new defaults won't apply
- You need to manually update `ALLOWED_ORIGINS` to include wildcards
- Or remove `ALLOWED_ORIGINS` to use defaults

## 🧪 Testing Strategy

### 1. Local Testing First

```bash
# Start Netlify Dev
netlify dev

# Test discovery (no Origin)
curl -i http://localhost:8888/mcp

# Test with Origin
curl -i -H "Origin: https://chatgpt.com" http://localhost:8888/mcp
```

### 2. Production Testing

```bash
# Discovery (should work without Origin)
curl -i https://zingy-profiterole-f31cb8.netlify.app/mcp

# With valid Origin (should include CORS headers)
curl -i -H "Origin: https://chatgpt.com" \
  https://zingy-profiterole-f31cb8.netlify.app/mcp

# With invalid Origin (should return 403)
curl -i -H "Origin: https://evil.com" \
  https://zingy-profiterole-f31cb8.netlify.app/mcp
```

### 3. Verify CORS Headers

**Required headers for valid Origin:**
```
access-control-allow-origin: https://chatgpt.com
access-control-allow-methods: GET,POST,OPTIONS
access-control-allow-headers: content-type,authorization
vary: Origin
```

**Check headers:**
```bash
curl -i -H "Origin: https://chatgpt.com" \
  https://zingy-profiterole-f31cb8.netlify.app/mcp \
  | grep -i "access-control"
```

## 🚨 Emergency Fallback

### Temporary Bypass (Use Only for Registration)

**If you still get 403 after all fixes:**

```bash
# 1. Temporarily disable origin check
netlify env:set MCP_HTTP_REQUIRE_ORIGIN false

# 2. Deploy
netlify deploy --prod

# 3. Register connector in ChatGPT

# 4. Immediately revert
netlify env:set MCP_HTTP_REQUIRE_ORIGIN true

# 5. Redeploy
netlify deploy --prod
```

**⚠️ Security Warning:**
- **Don't leave this disabled in production**
- Use only to register the connector
- Revert immediately after registration

## 🔍 Debugging

### 1. Check Netlify Function Logs

```bash
# In Netlify Dashboard
# Site → Functions → mcp → Logs
```

**Look for:**
- Path normalization issues
- Origin validation failures
- Rate limiting hits
- Error messages

### 2. Use Debug Endpoint (if enabled)

```bash
# Set MCP_DEBUG_SECRET in Netlify
netlify env:set MCP_DEBUG_SECRET "your-random-secret"

# Test debug endpoint
curl "https://zingy-profiterole-f31cb8.netlify.app/mcp/debug?token=your-random-secret"
```

**This shows:**
- Actual path received
- Origin/Referer headers
- All request headers (redacted)

**⚠️ Remove debug secret after debugging!**

### 3. Check Build Logs

```bash
# In Netlify Dashboard
# Site → Deploys → Latest → Build log
```

**Look for:**
- TypeScript compilation errors
- Missing dependencies
- Build failures

## ✅ Success Checklist

Before connecting in ChatGPT:

- [ ] `minimatch` is installed (`npm list minimatch`)
- [ ] `tsconfig.json` has correct settings
- [ ] `netlify.toml` redirects are in correct order
- [ ] Environment variables are set correctly
- [ ] Local tests pass (discovery, health, CORS)
- [ ] Production tests pass (discovery, health, CORS)
- [ ] CORS headers are present in responses
- [ ] Debug endpoint works (if enabled)
- [ ] Netlify function logs show no errors

## 📝 Additional Hardening (After It Works)

### 1. Rate Limiting

Already implemented, but verify:
```typescript
RATE_LIMIT_WINDOW_MS=60000  // 1 minute
RATE_LIMIT_MAX_REQ=300      // 300 requests per minute
```

### 2. Request Validation

Consider adding:
```typescript
// Validate MCP protocol version
const mcpVersion = event.headers["mcp-protocol-version"];
if (mcpVersion && !["1.0", "1.1"].includes(mcpVersion)) {
  return { statusCode: 400, body: "Unsupported MCP version" };
}
```

### 3. Logging

Add structured logging:
```typescript
console.log(JSON.stringify({
  timestamp: new Date().toISOString(),
  method,
  path,
  origin,
  headers: event.headers
}));
```

## 🎯 Final Verdict

This fix **should resolve your 403 error** because it:

✅ Handles path normalization (`/.netlify/functions/mcp` → `/mcp`)
✅ Allows origin-less discovery requests
✅ Implements proper CORS with origin validation
✅ Provides required MCP manifest endpoint
✅ Handles CORS preflight correctly

**But remember:**
1. Install `minimatch` dependency
2. Verify TypeScript compilation settings
3. Confirm redirect rules are in correct order
4. Test all curl commands before registering in ChatGPT
5. Check Netlify function logs if issues persist

