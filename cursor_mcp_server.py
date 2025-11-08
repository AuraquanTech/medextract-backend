#!/usr/bin/env python3
"""
Cursor MCP Server — full implementation.

Exposes a project workspace to ChatGPT Developer Mode using the official
MCP Python SDK over stdio. Includes:

- Tools: read_file, list_files, write_file (confirmable), run_command (whitelist),
         get_diagnostics, search_code

- Resources: workspace_tree, workspace_summary, readme

- Prompts: code_review, debug_assistant, refactor_suggestion

- Security: workspace sandboxing, rate limiting, audit logging, command whitelist,
            optional denylist globs for secrets

- Health: internal self-check + perf timing in diagnostics

Requires: `pip install mcp anthropic-mcp-sdk`
"""

from __future__ import annotations

import asyncio
import fnmatch
import json
import os
import re
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List

# MCP SDK
from mcp.server import Server
from mcp.types import ResourceContents
from mcp.transport import stdio_server

# -----------------------------
# Configuration
# -----------------------------
WORKSPACE_DIR = Path(os.environ.get("WORKSPACE_DIR", os.getcwd())).resolve()
AUDIT_LOG_PATH = Path(os.environ.get("MCP_AUDIT_LOG", WORKSPACE_DIR / ".mcp_audit.log"))

RATE_LIMITS = {
    "read": (100, 3600),   # 100 reads per hour
    "write": (50, 3600),   # 50 writes per hour
    "command": (20, 3600), # 20 commands per hour
}

# Add or remove commands as needed. Keep tight & anchored.
ALLOWED_COMMANDS = [
    # --- Git (read-only ops) ---
    r"^git\s+status$",
    r"^git\s+diff(?:\s+--(staged|cached))?$",
    
    # --- Python tests & tooling ---
    r"^pytest(?:\s+(?:-q|-x|-s|-k\s+[\w\-\.,]+|-m\s+[\w\-\.,]+|--maxfail=\d+|[\w/\.\-]+))*$",
    r"^python(?:3)?\s+-m\s+pytest(?:\s+(?:-q|-x|-s|-k\s+[\w\-\.,]+|-m\s+[\w\-\.,]+|--maxfail=\d+|[\w/\.\-]+))*$",
    r"^python(?:3)?\s+--version$",
    
    # --- Node / package manager tests ---
    r"^node\s+-v$",
    r"^(?:npm|pnpm|yarn)\s+test$",
    
    # --- Optional linters/formatters (safe, read-only on check) ---
    r"^ruff\s+check(?:\s+[\w/\.\-]+)*$",
    r"^black\s+--check(?:\s+[\w/\.\-]+)*$",
    r"^mypy(?:\s+[\w/\.\-]+)*$",
    r"^eslint\s+(?:[\w/\.\-]+|\.)+(?:\s+--max-warnings=0)?$",
]

# Denylist globs excluded from reads/searches unless explicitly targeted
READ_DENYLIST = [
    # VCS / vendors / envs
    "**/.git/**",
    "**/.svn/**",
    "**/.hg/**",
    "**/node_modules/**",
    "**/.venv/**",
    "**/venv/**",
    "**/.tox/**",
    "**/.cache/**",
    
    # Secrets & credentials
    "**/.env*",
    "**/*id_rsa*",
    "**/*id_dsa*",
    "**/*.pem",
    "**/*.key",
    "**/*.p12",
    "**/*.pfx",
    "**/*_cert*",
    "**/*.kdbx",
    
    # Cloud & auth config
    "**/.aws/**",
    "**/.azure/**",
    "**/.gcp/**",
    "**/.ssh/**",
    "**/.npmrc",
    "**/.pypirc",
]

# 2–4MB is a nicer default for real projects; still override via env.
MAX_FILE_BYTES = int(os.environ.get("MCP_MAX_FILE_BYTES", 2_000_000))

# -----------------------------
# Utilities: sandboxing, audit, rate-limit
# -----------------------------
def _is_relative_to(base: Path, target: Path) -> bool:
    try:
        target.resolve().relative_to(base.resolve())
        return True
    except Exception:
        return False

def in_workspace(path: Path) -> bool:
    return _is_relative_to(WORKSPACE_DIR, path)

def safe_join(*parts: str | Path) -> Path:
    p = (WORKSPACE_DIR.joinpath(*map(str, parts))).resolve()
    if not in_workspace(p):
        raise PermissionError(f"Path escapes workspace: {p}")
    return p

@dataclass
class AuditEntry:
    ts: float
    tool: str
    args: Dict[str, Any]
    ok: bool
    meta: Dict[str, Any]

def write_audit(entry: AuditEntry) -> None:
    try:
        AUDIT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with AUDIT_LOG_PATH.open("a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(entry), ensure_ascii=False) + "\n")
    except Exception:
        # Never crash the tool path due to audit failures
        pass

class FixedWindowRateLimiter:
    def __init__(self, max_ops: int, window_seconds: int):
        self.max_ops = max_ops
        self.window = window_seconds
        self.events: List[float] = []

    def allow(self) -> bool:
        now = time.time()
        self.events = [t for t in self.events if now - t < self.window]
        if len(self.events) >= self.max_ops:
            return False
        self.events.append(now)
        return True

rate_read = FixedWindowRateLimiter(*RATE_LIMITS["read"])
rate_write = FixedWindowRateLimiter(*RATE_LIMITS["write"])
rate_cmd = FixedWindowRateLimiter(*RATE_LIMITS["command"])

# -----------------------------
# Server
# -----------------------------
server = Server("cursor-mcp-server")

# -----------------------------
# Helpers
# -----------------------------
def _denylisted(rel_posix: str) -> bool:
    return any(fnmatch.fnmatch(rel_posix, pat) for pat in READ_DENYLIST)

def _read_text_guarded(p: Path) -> str:
    data = p.read_bytes()
    if len(data) > MAX_FILE_BYTES:
        raise ValueError(f"File exceeds byte limit: {p} ({len(data)} bytes > {MAX_FILE_BYTES})")
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return data.decode("utf-8", errors="replace")

# -----------------------------
# Command validation helpers
# -----------------------------
# Reject obvious shell chaining/redirection. We keep Windows & POSIX symbols.
_DANGEROUS_CHARS = re.compile(r"[;&|><`$]")

_ALLOWED_PATTERNS = [re.compile(p) for p in ALLOWED_COMMANDS]

def is_allowed_command(cmd: str) -> bool:
    """Check if command is allowed (no shell chaining, strict full-match)."""
    # No chaining / redirection
    if _DANGEROUS_CHARS.search(cmd):
        return False
    # Strict full-match against anchored patterns
    return any(p.fullmatch(cmd) for p in _ALLOWED_PATTERNS)

# -----------------------------
# Tools — full
# -----------------------------
@server.tool()
async def read_file(path: str) -> str:
    """Read a UTF-8 text file from the workspace."""
    if not rate_read.allow():
        raise RuntimeError("Rate limit exceeded for reads")
    abs_path = safe_join(path)
    if not abs_path.is_file():
        raise FileNotFoundError(f"Not a file: {path}")
    rel = abs_path.relative_to(WORKSPACE_DIR).as_posix()
    if _denylisted(rel):
        raise PermissionError("Path is denylisted for reads")
    try:
        text = _read_text_guarded(abs_path)
        write_audit(AuditEntry(time.time(), "read_file", {"path": path}, True, {"size": len(text)}))
        return text
    except Exception as e:
        write_audit(AuditEntry(time.time(), "read_file", {"path": path}, False, {"error": str(e)}))
        raise

@server.tool()
async def list_files(base: str = ".", pattern: str = "**/*", max_results: int = 2000, include_denied: bool = False) -> List[str]:
    """List files under a base directory with glob pattern."""
    if not rate_read.allow():
        raise RuntimeError("Rate limit exceeded for reads")
    base_abs = safe_join(base)
    if not base_abs.exists():
        raise FileNotFoundError(f"Base not found: {base}")
    results: List[str] = []
    for p in base_abs.rglob("*"):
        if not p.is_file():
            continue
        rel = p.relative_to(WORKSPACE_DIR).as_posix()
        if not fnmatch.fnmatch(rel, pattern):
            continue
        if not include_denied and _denylisted(rel):
            continue
        results.append(rel)
        if len(results) >= max_results:
            break
    write_audit(AuditEntry(time.time(), "list_files", {"base": base, "pattern": pattern}, True, {"count": len(results)}))
    return results

@server.tool()
async def write_file(path: str, content: str, mode: str = "replace", require_confirmation: bool = True, create_dirs: bool = True) -> str:
    """Write a text file.
    mode: "replace" | "append" | "create" (fail if exists)
    require_confirmation: when True, returns a preview plan; call again with False to apply.
    """
    if not rate_write.allow():
        raise RuntimeError("Rate limit exceeded for writes")
    abs_path = safe_join(path)
    rel = abs_path.relative_to(WORKSPACE_DIR).as_posix()
    if require_confirmation:
        plan = {
            "action": "WRITE_PREVIEW",
            "path": rel,
            "bytes": len(content),
            "mode": mode,
            "note": "Resend with require_confirmation=false to apply",
        }
        write_audit(AuditEntry(time.time(), "write_file", {"path": path, "mode": mode}, True, {"preview": True}))
        return json.dumps(plan)
    abs_path.parent.mkdir(parents=True, exist_ok=create_dirs)
    exists = abs_path.exists()
    if mode == "create" and exists:
        raise FileExistsError("File already exists (mode=create)")
    if mode == "append" and exists:
        with abs_path.open("a", encoding="utf-8") as f:
            f.write(content)
    else:
        with abs_path.open("w", encoding="utf-8") as f:
            f.write(content)
    write_audit(AuditEntry(time.time(), "write_file", {"path": path, "mode": mode}, True, {"applied": True, "bytes": len(content)}))
    return "OK"

@server.tool()
async def run_command(command: str, timeout_seconds: int = 60) -> Dict[str, Any]:
    """Run a whitelisted shell command within the workspace."""
    if not rate_cmd.allow():
        raise RuntimeError("Rate limit exceeded for commands")
    
    if not is_allowed_command(command):
        raise PermissionError("Command not allowed by whitelist")
    proc = await asyncio.create_subprocess_shell(
        command,
        cwd=str(WORKSPACE_DIR),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        t0 = time.perf_counter()
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout_seconds)
        dt = time.perf_counter() - t0
    except asyncio.TimeoutError:
        proc.kill()
        write_audit(AuditEntry(time.time(), "run_command", {"command": command}, False, {"timeout": timeout_seconds}))
        raise TimeoutError("Command timed out")
    write_audit(AuditEntry(time.time(), "run_command", {"command": command}, True, {"rc": proc.returncode, "ms": int(dt*1000)}))
    return {
        "returncode": proc.returncode,
        "stdout": stdout.decode("utf-8", errors="replace"),
        "stderr": stderr.decode("utf-8", errors="replace"),
        "elapsed_ms": int(dt * 1000),
    }

@server.tool()
async def get_diagnostics() -> Dict[str, Any]:
    """Return health & security posture and a perf probe."""
    t0 = time.perf_counter()
    _ = list((WORKSPACE_DIR).iterdir()) if WORKSPACE_DIR.exists() else []
    elapsed_ms = int((time.perf_counter() - t0) * 1000)
    return {
        "workspace": str(WORKSPACE_DIR),
        "audit_log": str(AUDIT_LOG_PATH),
        "limits": RATE_LIMITS,
        "allowed_commands": ALLOWED_COMMANDS,
        "denylist": READ_DENYLIST,
        "max_file_bytes": MAX_FILE_BYTES,
        "perf_probe_ms": elapsed_ms,
    }

@server.tool()
async def search_code(query: str, file_glob: str = "**/*", max_results: int = 200, context_lines: int = 1) -> List[Dict[str, Any]]:
    """Regex search across text files with context."""
    if not rate_read.allow():
        raise RuntimeError("Rate limit exceeded for reads")
    try:
        pattern = re.compile(query, re.MULTILINE)
    except re.error as e:
        raise ValueError(f"Invalid regex: {e}")
    hits: List[Dict[str, Any]] = []
    for path in WORKSPACE_DIR.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(WORKSPACE_DIR).as_posix()
        if _denylisted(rel):
            continue
        if not fnmatch.fnmatch(rel, file_glob):
            continue
        try:
            text = _read_text_guarded(path)
        except Exception:
            continue
        for m in pattern.finditer(text):
            lines = text.splitlines()
            line_no = text.count("\n", 0, m.start()) + 1
            lo = max(1, line_no - context_lines)
            hi = min(len(lines), line_no + context_lines)
            snippet = "\n".join(lines[lo-1:hi])
            hits.append({
                "file": rel,
                "line": line_no,
                "match": m.group(0),
                "context": snippet,
            })
            if len(hits) >= max_results:
                break
        if len(hits) >= max_results:
            break
    write_audit(AuditEntry(time.time(), "search_code", {"query": query}, True, {"count": len(hits)}))
    return hits

# -----------------------------
# Resources
# -----------------------------
@server.resource()
async def workspace_tree() -> ResourceContents:
    items = await list_files(".", "**/*", 2000)
    return ResourceContents(text="\n".join(items))

@server.resource()
async def workspace_summary() -> ResourceContents:
    parts = [f"Workspace: {WORKSPACE_DIR}"]
    readme_p = safe_join("README.md")
    if readme_p.exists():
        txt = _read_text_guarded(readme_p)
        parts.append("README (first 300 chars):\n" + txt[:300])
    try:
        pkg = safe_join("package.json")
        if pkg.exists():
            parts.append("package.json present")
    except Exception:
        pass
    return ResourceContents(text="\n\n".join(parts))

@server.resource()
async def readme() -> ResourceContents:
    p = safe_join("README.md")
    if p.exists():
        return ResourceContents(text=_read_text_guarded(p))
    return ResourceContents(text="(No README.md found)")

# -----------------------------
# Prompts
# -----------------------------
@server.prompt("code_review")
async def code_review() -> str:
    return (
        "You are a meticulous code reviewer. Focus on correctness, security, performance, and readability."
    )

@server.prompt("debug_assistant")
async def debug_assistant() -> str:
    return (
        "You are a debugging assistant. Form hypotheses, request minimal repros, and suggest instrumented fixes."
    )

@server.prompt("refactor_suggestion")
async def refactor_suggestion() -> str:
    return (
        "You propose safe refactors with tests. Prefer small, mechanical changes and explain trade-offs."
    )

# -----------------------------
# Entry
# -----------------------------
async def amain() -> None:
    WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)
    await stdio_server.run(server)

def main() -> None:
    try:
        asyncio.run(amain())
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()

