"""
OAuth-protected HTTP MCP bridge for ChatGPT Developer Mode.

- Public HTTPS endpoint (deploy to Render/Fly/Vercel-compatible ASGI)
- Requires OAuth 2.1 Bearer token (Authorization: Bearer <JWT>)
- Validates JWT via JWKS (Auth0 / generic OpenID providers)
- Delegates to cursor_mcp_server tools/resources/prompts

ENV (set in your hosting platform):
  WORKSPACE_DIR               -> absolute path inside container (or mount)
  AUTH_ISSUER                 -> e.g. https://YOUR-TENANT.us.auth0.com/
  AUTH_AUDIENCE               -> e.g. https://cursor-mcp (API identifier)
  AUTH_JWKS_URL               -> e.g. https://YOUR-TENANT.us.auth0.com/.well-known/jwks.json
  MCP_HTTP_REQUIRE_ORIGIN     -> "true" (default) | "false"
  ALLOWED_ORIGINS             -> comma list (default: chatgpt.com, chat.openai.com)
"""
from __future__ import annotations

import os
import time
from typing import Any, Dict, Optional

import httpx
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.responses import PlainTextResponse
from jose import jwt
from pydantic import BaseModel, Field

import cursor_mcp_server as srv

app = FastAPI(title="cursor-mcp-oauth", version="1.0")

# ---- Config ----
AUTH_ISSUER = os.environ["AUTH_ISSUER"].rstrip("/") + "/"
AUTH_AUDIENCE = os.environ["AUTH_AUDIENCE"]
AUTH_JWKS_URL = os.environ.get("AUTH_JWKS_URL") or (AUTH_ISSUER + ".well-known/jwks.json")

ALLOWED_ORIGINS = set([o.strip() for o in os.environ.get(
    "ALLOWED_ORIGINS", "https://chatgpt.com,https://chat.openai.com"
).split(",") if o.strip()])

REQUIRE_ORIGIN = os.environ.get("MCP_HTTP_REQUIRE_ORIGIN", "true").lower() != "false"

# ---- JWKS cache ----
_JWKS: Optional[Dict[str, Any]] = None
_JWKS_TS: float = 0

async def _get_jwks() -> Dict[str, Any]:
    global _JWKS, _JWKS_TS
    now = time.time()
    if _JWKS and (now - _JWKS_TS) < 3600:
        return _JWKS
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(AUTH_JWKS_URL)
        r.raise_for_status()
        _JWKS = r.json()
        _JWKS_TS = now
        return _JWKS

def _ok_origin(req: Request) -> bool:
    if not REQUIRE_ORIGIN:
        return True
    origin = req.headers.get("origin") or req.headers.get("referer", "")
    return any(origin.startswith(o) for o in ALLOWED_ORIGINS)

async def require_oauth(req: Request):
    if not _ok_origin(req):
        raise HTTPException(status_code=403, detail="Forbidden origin")
    auth = req.headers.get("authorization") or req.headers.get("Authorization")
    if not auth or not auth.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = auth.split(" ", 1)[1].strip()

    jwks = await _get_jwks()
    try:
        claims = jwt.decode(
            token,
            jwks,
            algorithms=["RS256", "PS256", "ES256", "EdDSA"],
            audience=AUTH_AUDIENCE,
            issuer=AUTH_ISSUER,
            options={"verify_at_hash": False},
        )
        req.state.claims = claims
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")

class ToolCall(BaseModel):
    params: Dict[str, Any] = Field(default_factory=dict)

class ToolResult(BaseModel):
    ok: bool
    result: Optional[Any] = None
    error: Optional[str] = None
    elapsed_ms: Optional[int] = None

TOOLS = {
    "read_file": {"description": "Read a UTF-8 file", "params": {"path": "str", "allow_denied_explicit": "bool?"}},
    "list_files": {"description": "List files with glob", "params": {"base": "str?", "pattern": "str?", "max_results": "int?", "include_denied": "bool?"}},
    "write_file": {"description": "Write a file (preview by default)", "params": {"path": "str", "content": "str", "mode": "str?", "require_confirmation": "bool?", "create_dirs": "bool?"}},
    "run_command": {"description": "Run whitelisted command", "params": {"command": "str", "timeout_seconds": "int?"}},
    "get_diagnostics": {"description": "Health & limits", "params": {}},
    "search_code": {"description": "Regex search", "params": {"query": "str", "file_glob": "str?", "max_results": "int?", "context_lines": "int?"}},
    "reset_context": {"description": "Reset rate windows", "params": {}},
}
RESOURCES = {"workspace_tree": "File list", "workspace_summary": "Summary", "readme": "README"}
PROMPTS = ["code_review", "debug_assistant", "refactor_suggestion"]

@app.get("/mcp", dependencies=[Depends(require_oauth)])
async def manifest():
    return {"name": "cursor-mcp-oauth", "version": "1.0", "tools": TOOLS, "resources": RESOURCES, "prompts": PROMPTS, "workspace": str(srv.WORKSPACE_DIR)}

@app.get("/mcp/health", dependencies=[Depends(require_oauth)])
async def health():
    di = await srv.get_diagnostics()
    return {"ok": True, "diagnostics": di}

_TOOL_MAP = {
    "read_file": srv.read_file,
    "list_files": srv.list_files,
    "write_file": srv.write_file,
    "run_command": srv.run_command,
    "get_diagnostics": srv.get_diagnostics,
    "search_code": srv.search_code,
    "reset_context": srv.reset_context,
}

_METRICS = {"tool_calls_total": 0, "tool_ok_total": 0, "tool_error_total": 0, "tool_duration_ms_sum": 0}

@app.post("/mcp/tool/{name}", response_model=ToolResult, dependencies=[Depends(require_oauth)])
async def call_tool(name: str, body: ToolCall, req: Request):
    fn = _TOOL_MAP.get(name)
    if not fn:
        raise HTTPException(status_code=404, detail=f"Unknown tool: {name}")
    t0 = time.perf_counter()
    try:
        res = await fn(**body.params)
        dt = int((time.perf_counter() - t0) * 1000)
        _METRICS["tool_calls_total"] += 1
        _METRICS["tool_ok_total"] += 1
        _METRICS["tool_duration_ms_sum"] += dt
        return ToolResult(ok=True, result=res, elapsed_ms=dt)
    except Exception as e:
        dt = int((time.perf_counter() - t0) * 1000)
        _METRICS["tool_calls_total"] += 1
        _METRICS["tool_error_total"] += 1
        _METRICS["tool_duration_ms_sum"] += dt
        return ToolResult(ok=False, error=str(e), elapsed_ms=dt)

@app.get("/metrics")
async def metrics():
    text = (
        f'cursor_tool_calls_total {_METRICS["tool_calls_total"]}\n'
        f'cursor_tool_ok_total {_METRICS["tool_ok_total"]}\n'
        f'cursor_tool_error_total {_METRICS["tool_error_total"]}\n'
        f'cursor_tool_duration_ms_sum {_METRICS["tool_duration_ms_sum"]}\n'
    )
    return PlainTextResponse(text, media_type="text/plain")

