# Fallback Strategy with Time-Boxed Expiration

## Emergency Fallback Procedure

### When to Use

Only use this if you still get 403 errors after:
1. ✅ All fixes are deployed
2. ✅ Environment variables are set correctly
3. ✅ All tests pass locally
4. ✅ Debug endpoint shows correct headers

### Step-by-Step Procedure

#### 1. Enable Fallback Mode

```bash
# Temporarily disable origin check
netlify env:set MCP_HTTP_REQUIRE_ORIGIN false

# Set expiration (1 hour from now)
# Windows PowerShell:
$expiry = (Get-Date).AddHours(1).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
netlify env:set MCP_FALLBACK_UNTIL $expiry

# Linux/Mac:
netlify env:set MCP_FALLBACK_UNTIL $(date -u -d '+1 hour' +%Y-%m-%dT%H:%M:%SZ)
```

#### 2. Deploy

```bash
netlify deploy --prod
```

#### 3. Register Connector

- Go to ChatGPT
- Add connector
- Server URL: `https://zingy-profiterole-f31cb8.netlify.app/mcp`
- Authentication: None
- Verify connection succeeds

#### 4. Immediately Revert

```bash
# Re-enable origin check
netlify env:set MCP_HTTP_REQUIRE_ORIGIN true

# Remove expiration
netlify env:unset MCP_FALLBACK_UNTIL

# Redeploy
netlify deploy --prod
```

#### 5. Verify Security is Restored

```bash
# Test that invalid origins are now blocked
curl -i -H 'Origin: https://evil.com' \
  'https://zingy-profiterole-f31cb8.netlify.app/mcp'
# Expected: 403 Forbidden origin
```

## Automatic Expiration (Optional)

### Add to Function

If you want automatic expiration, add this check to your function:

```typescript
// Check if fallback mode should expire
const fallbackUntil = process.env.MCP_FALLBACK_UNTIL;
if (fallbackUntil && new Date() > new Date(fallbackUntil)) {
  // Automatically re-enable origin check
  // Note: This requires redeploy to take effect
  console.warn("Fallback mode expired - origin check should be re-enabled");
}
```

**Note:** Environment variable changes require redeploy. This is mainly for logging/alerting.

## Security Warnings

### ⚠️ Critical

- **Don't leave `MCP_HTTP_REQUIRE_ORIGIN=false` in production**
- Use only to register the connector
- Revert immediately after registration
- Set expiration to prevent accidental long-term disable

### ⚠️ Monitoring

After enabling fallback:
- Monitor function logs for suspicious activity
- Set up alerts for fallback mode
- Document when fallback was used and why

## Alternative: IP Allowlist

Instead of disabling origin check entirely, consider IP allowlist:

```typescript
// Allow specific IPs without origin check
const allowedIPs = (process.env.DISCOVERY_ALLOWED_IPS || "").split(",")
  .map(s => s.trim())
  .filter(Boolean);

const ip = event.headers?.["x-forwarded-for"]?.split(",")[0].trim();
if (allowedIPs.length > 0 && allowedIPs.includes(ip)) {
  // Allow discovery from whitelisted IPs
  return null; // Skip origin check
}
```

**Set environment variable:**
```
DISCOVERY_ALLOWED_IPS=<your-ip>,<chatgpt-ip-range>
```

This is more secure than disabling origin check entirely.

## Best Practices

1. **Document fallback usage** - Keep a log of when/why fallback was used
2. **Set short expiration** - 1 hour maximum
3. **Monitor during fallback** - Watch logs for suspicious activity
4. **Revert immediately** - Don't wait for expiration
5. **Test after revert** - Verify security is restored

## Troubleshooting

### Fallback Not Working

**Check:**
- Environment variable is set correctly
- Redeploy completed successfully
- Function logs show `MCP_HTTP_REQUIRE_ORIGIN=false`

**Verify:**
```bash
netlify env:get MCP_HTTP_REQUIRE_ORIGIN
# Should return: false
```

### Can't Revert

**Check:**
- Environment variable is set correctly
- Redeploy completed successfully
- Function logs show `MCP_HTTP_REQUIRE_ORIGIN=true`

**Verify:**
```bash
netlify env:get MCP_HTTP_REQUIRE_ORIGIN
# Should return: true
```

### Expiration Not Working

**Note:** Environment variable changes require redeploy. The expiration check is mainly for logging.

**To actually expire:**
1. Set `MCP_HTTP_REQUIRE_ORIGIN=true`
2. Remove `MCP_FALLBACK_UNTIL`
3. Redeploy

