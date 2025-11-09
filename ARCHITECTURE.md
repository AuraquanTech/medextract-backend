# Architecture Overview

## System Architecture

### Two-Layer Design

This project has **two separate components**:

1. **Netlify Function** (`netlify/functions/mcp.ts`)
   - HTTP endpoint layer
   - Handles CORS, authentication, rate limiting
   - Provides HTTP interface for ChatGPT
   - **Purpose:** Fix 403 errors, handle HTTP layer

2. **Local MCP Server** (`cursor_mcp_server.py`)
   - Actual MCP tool implementation
   - Runs locally via stdio transport
   - Implements tools (read_file, list_files, write_file, etc.)
   - **Purpose:** Provide MCP tools to Cursor AI

## Component Responsibilities

### Netlify Function (HTTP Layer)

**Responsibilities:**
- ✅ Handle HTTP requests from ChatGPT
- ✅ Fix 403 errors (path normalization, discovery exception)
- ✅ CORS handling (origin validation, headers)
- ✅ Rate limiting
- ✅ Security headers
- ✅ Structured logging
- ✅ Debug endpoint

**What it does NOT do:**
- ❌ Implement actual MCP tools (that's in the local server)
- ❌ Execute file operations (that's in the local server)
- ❌ Provide workspace access (that's in the local server)

**Current Implementation:**
- Provides discovery endpoints (`GET /mcp`, `GET /mcp/health`)
- Handles MCP JSON-RPC protocol (initialize, etc.)
- Routes to appropriate handlers
- **Note:** Actual tool implementations would be added here if you want to run tools on Netlify

### Local MCP Server (Tool Layer)

**Responsibilities:**
- ✅ Implement MCP tools (read_file, list_files, write_file, etc.)
- ✅ Provide workspace access
- ✅ Execute file operations
- ✅ Run commands (whitelisted)
- ✅ Search code
- ✅ Context summarization
- ✅ Command watching

**What it does:**
- Runs locally via stdio transport
- Connects to Cursor AI
- Provides tools to Cursor AI
- **Note:** This is separate from the Netlify function

## Connection Flow

### ChatGPT → Netlify Function

```
ChatGPT
  ↓
  HTTP Request (with Origin header)
  ↓
Netlify Function (netlify/functions/mcp.ts)
  ↓
  - Path normalization
  - Origin validation
  - CORS headers
  - Rate limiting
  ↓
  Response (with CORS headers)
  ↓
ChatGPT
```

### Cursor AI → Local MCP Server

```
Cursor AI
  ↓
  stdio transport
  ↓
Local MCP Server (cursor_mcp_server.py)
  ↓
  - Tool execution
  - File operations
  - Command execution
  ↓
  Response
  ↓
Cursor AI
```

## If You Want MCP Tools in Netlify

If you want to implement actual MCP tools in the Netlify function (instead of just the HTTP layer), you would add:

### Example: Implement `tools/list`

```typescript
if (body.method === "tools/list") {
  return {
    statusCode: 200,
    headers: { "content-type": "application/json", ...base },
    body: JSON.stringify({
      jsonrpc: "2.0",
      id: body.id,
      result: {
        tools: [
          {
            name: "read_file",
            description: "Read a file from the workspace",
            inputSchema: {
              type: "object",
              properties: {
                path: { type: "string" }
              },
              required: ["path"]
            }
          },
          // ... more tools
        ]
      }
    })
  };
}
```

### Example: Implement `tools/call`

```typescript
if (body.method === "tools/call") {
  const toolName = body.params?.name;
  const args = body.params?.arguments || {};
  
  // Execute tool
  let result;
  switch (toolName) {
    case "read_file":
      result = await readFile(args.path);
      break;
    case "list_files":
      result = await listFiles(args.base, args.pattern);
      break;
    // ... more tools
    default:
      return {
        statusCode: 200,
        headers: { "content-type": "application/json", ...base },
        body: JSON.stringify({
          jsonrpc: "2.0",
          id: body.id,
          error: { code: -32601, message: "Method not found" }
        })
      };
  }
  
  return {
    statusCode: 200,
    headers: { "content-type": "application/json", ...base },
    body: JSON.stringify({
      jsonrpc: "2.0",
      id: body.id,
      result: {
        content: [
          {
            type: "text",
            text: JSON.stringify(result, null, 2)
          }
        ]
      }
    })
  };
}
```

**However**, for the current use case (connecting Cursor AI to ChatGPT), the Netlify function is correctly focused on:
- ✅ Fixing the 403 error
- ✅ Handling CORS properly
- ✅ Providing discovery endpoints
- ✅ Security and rate limiting

The actual MCP tools are implemented in the local server (`cursor_mcp_server.py`).

## Current Implementation Status

### ✅ Complete (Netlify Function)
- Path normalization
- Discovery exception
- CORS handling
- Rate limiting
- Security headers
- Structured logging
- Debug endpoint
- Metrics tracking

### ✅ Complete (Local MCP Server)
- Tool implementation (read_file, list_files, write_file, etc.)
- Workspace access
- Command execution
- Context summarization
- Command watching

### ⏳ Optional (Netlify Function)
- Actual MCP tool implementations (if you want tools to run on Netlify)
- Resource listing
- Prompt listing

## Recommendation

**For the current use case (fixing 403 errors):**
- ✅ Keep Netlify function focused on HTTP layer (CORS, auth, routing)
- ✅ Keep local MCP server for actual tool implementation
- ✅ This separation is correct and maintainable

**If you want tools to run on Netlify:**
- Add tool implementations to `netlify/functions/mcp.ts`
- Implement `tools/list` and `tools/call` handlers
- Add actual tool execution logic
- Consider security implications (workspace access, file operations)

## Summary

**Current Architecture:**
- **Netlify Function** = HTTP layer (fixes 403, handles CORS)
- **Local MCP Server** = Tool layer (implements actual tools)

**This is correct for the current use case.**

The Netlify function is production-ready for fixing 403 errors and handling the HTTP layer. The actual MCP tools are correctly implemented in the local server.

