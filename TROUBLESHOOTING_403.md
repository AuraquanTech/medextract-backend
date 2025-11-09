# Troubleshooting 403 Forbidden Error

## Error
```
Error creating connector
Client error '403 Forbidden' for url 'https://zingy-profiterole-f31cb8.netlify.app/mcp'
```

## Common Causes

### 1. **CORS (Cross-Origin Resource Sharing) Issues**
The server may not allow requests from your origin. This is common with Netlify-hosted APIs.

**Solution:**
- Check if the server has CORS headers configured
- The server needs to allow your client's origin
- May need to configure Netlify headers

### 2. **Authentication Required**
The server may require an API key or authentication token.

**Solution:**
- Check if the server requires an `Authorization` header
- Look for API key in server documentation
- May need to register/get an API key first

### 3. **HTTP Method Not Allowed**
The endpoint may not accept the HTTP method being used (GET vs POST).

**Solution:**
- MCP servers typically use POST for tool calls
- Check what method the server expects

### 4. **Rate Limiting or IP Blocking**
The server may be blocking your IP or rate limiting requests.

**Solution:**
- Wait and retry
- Check if you need to whitelist your IP
- May need to use a different network

### 5. **Missing Required Headers**
The server may require specific headers (Content-Type, User-Agent, etc.).

**Solution:**
- Ensure proper headers are sent
- Check server documentation for required headers

## Troubleshooting Steps

### Step 1: Test the Connection
Use the test script to check if the server is accessible:

```bash
python test_mcp_connection.py
```

### Step 2: Check Server Status
Verify the server is running and accessible:

```bash
curl -v https://zingy-profiterole-f31cb8.netlify.app/mcp
```

### Step 3: Check Authentication
If the server requires authentication:

1. Check server documentation for API key requirements
2. Look for authentication endpoints
3. Register/get an API key if needed
4. Add to your MCP configuration

### Step 4: Check CORS Configuration
If connecting from a browser/client:

1. Check browser console for CORS errors
2. Verify server CORS headers
3. May need to configure Netlify headers

### Step 5: Check Netlify Configuration
For Netlify-hosted servers:

1. Check `netlify.toml` for redirects/headers
2. Verify the endpoint path is correct (`/mcp`)
3. Check if the function is deployed correctly

## MCP Configuration

If using a remote MCP server, your configuration might look like:

```json
{
  "mcpServers": {
    "remote-mcp": {
      "url": "https://zingy-profiterole-f31cb8.netlify.app/mcp",
      "headers": {
        "Authorization": "Bearer YOUR_API_KEY",
        "Content-Type": "application/json"
      }
    }
  }
}
```

## Alternative: Use Local MCP Server

If the remote server is having issues, you can use the local MCP server:

```json
{
  "mcpServers": {
    "cursor-mcp": {
      "command": "python",
      "args": ["-u", "cursor_mcp_server.py"],
      "env": {
        "WORKSPACE_DIR": "C:/path/to/your/workspace"
      }
    }
  }
}
```

## Next Steps

1. **Test the connection** using the test script
2. **Check server documentation** for authentication requirements
3. **Verify the endpoint** is correct and accessible
4. **Check Netlify logs** if you have access
5. **Contact server administrator** if issues persist

