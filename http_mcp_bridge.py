#!/usr/bin/env python3
"""
HTTP Bridge for Cursor MCP Server.

Exposes the MCP server over HTTP for ChatGPT Developer Mode integration.
Includes token-based authentication, origin checks, and rate limiting.

Usage:
    uvicorn http_mcp_bridge:app --host 127.0.0.1 --port 8001
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional, List

from fastapi import FastAPI, HTTPException, Request, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

# Import the MCP server and its tools/resources
from cursor_mcp_server import (
    server,
    WORKSPACE_DIR,
    AUDIT_LOG_PATH,
    write_audit,
    AuditEntry,
    rate_read,
    rate_write,
    rate_cmd,
)

# Import all the tool functions directly
from cursor_mcp_server import (
    read_file,
    list_files,
    write_file,
    run_command,
    get_diagnostics,
    search_code,
    reset_context,
)

# -----------------------------
# Configuration
# -----------------------------
MCP_HTTP_TOKEN = os.environ.get("MCP_HTTP_TOKEN", "3f7a1c2e5d8b9f0a4c7e2d1b6a5f9c8e7d0b3a6c5e1f2d4b7c9a0e3f6d1b2c4")
ALLOWED_ORIGINS = os.environ.get("MCP_ALLOWED_ORIGINS", "http://localhost:3000,https://chat.openai.com").split(",")

# -----------------------------
# Logging
# -----------------------------
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] [HTTP-BRIDGE] %(message)s',
    datefmt='%H:%M:%S',
    stream=sys.stderr
)
LOG = logging.getLogger(__name__)

# -----------------------------
# FastAPI App
# -----------------------------
app = FastAPI(
    title="Cursor MCP HTTP Bridge",
    description="HTTP bridge for Cursor MCP Server",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# Authentication & Security
# -----------------------------
def verify_token(token: Optional[str] = None) -> bool:
    """Verify the provided token matches the configured token."""
    if not token:
        return False
    return token == MCP_HTTP_TOKEN

def get_client_origin(request: Request) -> str:
    """Extract client origin from request."""
    origin = request.headers.get("origin") or request.headers.get("referer", "")
    return origin

# -----------------------------
# MCP Protocol Handler
# -----------------------------
class MCPHTTPHandler:
    """Handles MCP protocol over HTTP."""
    
    def __init__(self):
        self.server = server
    
    async def handle_request(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle an MCP request."""
        try:
            # Map HTTP method to MCP tool/resource/prompt
            if method == "tools/list":
                # Get all registered tools
                tools = []
                # Access the server's internal tool registry
                if hasattr(self.server, "_tools"):
                    for tool_name, tool_info in self.server._tools.items():
                        tools.append({
                            "name": tool_name,
                            "description": tool_info.get("description", "") or (tool_info.get("handler", {}).__doc__ or ""),
                        })
                else:
                    # Fallback: manually list known tools
                    tools = [
                        {"name": "read_file", "description": "Read a UTF-8 text file from the workspace."},
                        {"name": "list_files", "description": "List files under a base directory with glob pattern."},
                        {"name": "write_file", "description": "Write a text file."},
                        {"name": "run_command", "description": "Run a whitelisted shell command within the workspace."},
                        {"name": "get_diagnostics", "description": "Return health & security posture and a perf probe."},
                        {"name": "search_code", "description": "Regex search across text files with context."},
                        {"name": "reset_context", "description": "Reset soft state like rate windows (keeps audit log)."},
                    ]
                return {"tools": tools}
            
            elif method == "tools/call":
                tool_name = params.get("name")
                arguments = params.get("arguments", {})
                
                # Map tool name to handler
                tool_handlers = {
                    "read_file": read_file,
                    "list_files": list_files,
                    "write_file": write_file,
                    "run_command": run_command,
                    "get_diagnostics": get_diagnostics,
                    "search_code": search_code,
                    "reset_context": reset_context,
                }
                
                if tool_name not in tool_handlers:
                    raise HTTPException(status_code=404, detail=f"Tool not found: {tool_name}")
                
                tool_handler = tool_handlers[tool_name]
                result = await tool_handler(**arguments)
                
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(result) if not isinstance(result, str) else result
                        }
                    ]
                }
            
            elif method == "resources/list":
                resources = [
                    {"uri": "mcp://workspace_tree", "name": "workspace_tree", "description": "Full file tree"},
                    {"uri": "mcp://workspace_summary", "name": "workspace_summary", "description": "Workspace overview"},
                    {"uri": "mcp://readme", "name": "readme", "description": "README.md content"},
                ]
                return {"resources": resources}
            
            elif method == "resources/read":
                resource_uri = params.get("uri", "")
                resource_name = resource_uri.replace("mcp://", "")
                
                # Map resource name to handler
                resource_handlers = {
                    "workspace_tree": self._get_workspace_tree,
                    "workspace_summary": self._get_workspace_summary,
                    "readme": self._get_readme,
                }
                
                if resource_name not in resource_handlers:
                    raise HTTPException(status_code=404, detail=f"Resource not found: {resource_name}")
                
                resource_handler = resource_handlers[resource_name]
                result = await resource_handler()
                
                return {
                    "contents": [
                        {
                            "type": "text",
                            "text": result if isinstance(result, str) else json.dumps(result)
                        }
                    ]
                }
            
            elif method == "prompts/list":
                prompts = [
                    {"name": "code_review", "description": "Code review assistant"},
                    {"name": "debug_assistant", "description": "Debugging helper"},
                    {"name": "refactor_suggestion", "description": "Refactoring suggestions"},
                ]
                return {"prompts": prompts}
            
            else:
                raise HTTPException(status_code=400, detail=f"Unknown method: {method}")
        
        except Exception as e:
            LOG.error(f"Error handling MCP request: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=str(e))
    
    async def _get_workspace_tree(self) -> str:
        """Get workspace tree."""
        files = await list_files(".", "**/*", 2000)
        return "\n".join(files)
    
    async def _get_workspace_summary(self) -> str:
        """Get workspace summary."""
        parts = [f"Workspace: {WORKSPACE_DIR}"]
        readme_p = WORKSPACE_DIR / "README.md"
        if readme_p.exists():
            try:
                txt = readme_p.read_text(encoding="utf-8")
                parts.append(f"README (preview):\n{txt[:1000]}")
            except Exception:
                pass
        return "\n\n".join(parts)
    
    async def _get_readme(self) -> str:
        """Get README content."""
        readme_p = WORKSPACE_DIR / "README.md"
        if readme_p.exists():
            try:
                return readme_p.read_text(encoding="utf-8")
            except Exception:
                return "(Error reading README.md)"
        return "(No README.md found)"

# Global handler
_mcp_handler = MCPHTTPHandler()

# -----------------------------
# HTTP Endpoints
# -----------------------------
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "status": "ok",
        "service": "Cursor MCP HTTP Bridge",
        "workspace": str(WORKSPACE_DIR),
        "version": "1.0.0"
    }

@app.get("/mcp/health")
async def health(
    request: Request,
    token: str = Query(..., description="Authentication token"),
):
    """Health check endpoint."""
    if not verify_token(token):
        raise HTTPException(status_code=401, detail="Invalid token")
    
    return {
        "status": "healthy",
        "workspace": str(WORKSPACE_DIR),
        "workspace_exists": WORKSPACE_DIR.exists(),
        "audit_log": str(AUDIT_LOG_PATH),
    }

@app.get("/mcp")
async def mcp_manifest(
    request: Request,
    token: str = Query(..., description="Authentication token"),
):
    """Get MCP manifest (tools/resources/prompts)."""
    if not verify_token(token):
        raise HTTPException(status_code=401, detail="Invalid token")
    
    # Get tools
    tools_result = await _mcp_handler.handle_request("tools/list", {})
    resources_result = await _mcp_handler.handle_request("resources/list", {})
    prompts_result = await _mcp_handler.handle_request("prompts/list", {})
    
    return JSONResponse(content={
        "tools": tools_result.get("tools", []),
        "resources": resources_result.get("resources", []),
        "prompts": prompts_result.get("prompts", []),
    })

@app.post("/mcp/tool/{tool_name}")
async def mcp_tool(
    request: Request,
    tool_name: str,
    token: str = Query(..., description="Authentication token"),
    body: Dict[str, Any] = Body(default={}),
):
    """Invoke an MCP tool."""
    if not verify_token(token):
        write_audit(AuditEntry(
            ts=asyncio.get_event_loop().time(),
            tool="http_mcp",
            args={"tool": tool_name},
            ok=False,
            meta={"error": "Invalid token", "origin": get_client_origin(request)}
        ))
        raise HTTPException(status_code=401, detail="Invalid token")
    
    # Get params from body
    params = body.get("params", {})
    arguments = params if params else body.get("arguments", {})
    
    # Log request
    write_audit(AuditEntry(
        ts=asyncio.get_event_loop().time(),
        tool="http_mcp",
        args={"tool": tool_name, "arguments": arguments},
        ok=True,
        meta={"origin": get_client_origin(request)}
    ))
    
    # Handle tool call
    result = await _mcp_handler.handle_request("tools/call", {
        "name": tool_name,
        "arguments": arguments,
    })
    return JSONResponse(content=result)

# -----------------------------
# Entry Point
# -----------------------------
def main():
    """Run the HTTP bridge server."""
    host = os.environ.get("MCP_HTTP_HOST", "127.0.0.1")
    port = int(os.environ.get("MCP_HTTP_PORT", "8001"))
    
    LOG.info(f"Starting Cursor MCP HTTP Bridge on {host}:{port}")
    LOG.info(f"Workspace: {WORKSPACE_DIR}")
    LOG.info(f"Token: {MCP_HTTP_TOKEN[:20]}...")
    LOG.info(f"Allowed origins: {ALLOWED_ORIGINS}")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )

if __name__ == "__main__":
    main()
