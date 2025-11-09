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
import logging
import os
import re
import sys
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable
from collections import deque

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
    r"^git\s+status$",
    r"^git\s+diff(?:\s+--(staged|cached))?$",
    
    # Python tests & tooling
    r"^pytest(?:\s+(?:-q|-x|-s|-k\s+[\w\-\.,]+|-m\s+[\w\-\.,]+|--maxfail=\d+|[\w/\.\-]+))*$",
    r"^python(?:3)?\s+-m\s+pytest(?:\s+(?:-q|-x|-s|-k\s+[\w\-\.,]+|-m\s+[\w\-\.,]+|--maxfail=\d+|[\w/\.\-]+))*$",
    r"^python(?:3)?\s+--version$",
    r"^ruff\s+check(?:\s+[\w/\.\-]+)*$",
    r"^black\s+--check(?:\s+[\w/\.\-]+)*$",
    r"^mypy(?:\s+[\w/\.\-]+)*$",
    
    # Node/JS tests & tooling
    r"^node\s+-v$",
    r"^(?:npm|pnpm|yarn)\s+test$",
    r"^eslint\s+(?:[\w/\.\-]+|\.)+(?:\s+--max-warnings=0)?$",
    
    # Common script wrappers (only "test*" scripts)
    r"^npm\s+run\s+test(?::[\w\-]+)?$",
    r"^yarn\s+run\s+test(?::[\w\-]+)?$",
    r"^pnpm\s+run\s+test(?::[\w\-]+)?$"
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

# Audit rotation settings
_MAX_AUDIT_BYTES = int(os.environ.get("MCP_MAX_AUDIT_BYTES", 10_000_000))  # 10MB default
_MAX_AUDIT_BACKUPS = 3

# Context summarization settings
# Auto-summarize when context reaches 85% of max
CONTEXT_MAX_CHARS = int(os.environ.get("MCP_CONTEXT_MAX_CHARS", 100_000))  # ~100k chars default
CONTEXT_SUMMARY_THRESHOLD = float(os.environ.get("MCP_CONTEXT_SUMMARY_THRESHOLD", 0.85))  # 85%
CONTEXT_SUMMARY_ENABLED = os.environ.get("MCP_CONTEXT_SUMMARY_ENABLED", "true").lower() == "true"

# Watcher settings
WATCHER_ENABLED = os.environ.get("MCP_ENABLE_WATCHER", "true").lower() == "true"

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

def _rotate_audit_if_needed() -> None:
    """Rotate audit log if it exceeds size limit."""
    try:
        if AUDIT_LOG_PATH.exists() and AUDIT_LOG_PATH.stat().st_size > _MAX_AUDIT_BYTES:
            # Rotate backups: .log.3 -> .log.4 (delete), .log.2 -> .log.3, .log.1 -> .log.2, .log -> .log.1
            for i in range(_MAX_AUDIT_BACKUPS, 0, -1):
                src = AUDIT_LOG_PATH.with_suffix(AUDIT_LOG_PATH.suffix + (f".{i-1}" if i > 1 else ""))
                dst = AUDIT_LOG_PATH.with_suffix(AUDIT_LOG_PATH.suffix + f".{i}")
                if i == 1:
                    src = AUDIT_LOG_PATH
                if Path(src).exists():
                    Path(dst).unlink(missing_ok=True)
                    Path(src).replace(dst)
    except Exception:
        # Never crash due to rotation failures
        pass

def write_audit(entry: AuditEntry) -> None:
    try:
        AUDIT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        _rotate_audit_if_needed()
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
# Logging & Watcher Setup
# -----------------------------
# Configure logging to stderr so it's visible in terminal
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] [WATCHER] %(message)s',
    datefmt='%H:%M:%S',
    stream=sys.stderr
)
LOG = logging.getLogger(__name__)

# -----------------------------
# Command Watcher
# -----------------------------
class CommandWatcher:
    """Monitors command execution and provides real-time status updates."""
    
    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        self.active_commands: Dict[str, Dict[str, Any]] = {}
        self.command_history: deque = deque(maxlen=50)
    
    def start_command(self, command_id: str, command: str) -> None:
        """Log command start."""
        if not self.enabled:
            return
        start_time = time.time()
        self.active_commands[command_id] = {
            "command": command,
            "start_time": start_time,
            "status": "running",
        }
        LOG.info(f"▶️  START: {command[:80]}...")
        sys.stderr.flush()  # Force flush to ensure visibility
    
    def update_command(self, command_id: str, status: str, message: str = "") -> None:
        """Update command status."""
        if not self.enabled or command_id not in self.active_commands:
            return
        self.active_commands[command_id]["status"] = status
        if message:
            LOG.info(f"🔄 {status.upper()}: {message}")
        sys.stderr.flush()
    
    def end_command(self, command_id: str, success: bool, returncode: int = 0, 
                    elapsed_ms: int = 0, output_size: int = 0) -> None:
        """Log command completion."""
        if not self.enabled or command_id not in self.active_commands:
            return
        cmd_info = self.active_commands.pop(command_id)
        elapsed = time.time() - cmd_info["start_time"]
        status_icon = "✅" if success else "❌"
        LOG.info(f"{status_icon} END: {cmd_info['command'][:60]}... (rc={returncode}, {elapsed_ms}ms, {output_size} bytes)")
        sys.stderr.flush()
        
        # Add to history
        self.command_history.append({
            "command": cmd_info["command"],
            "success": success,
            "returncode": returncode,
            "elapsed_ms": elapsed_ms,
            "timestamp": time.time(),
        })
    
    def get_status(self) -> Dict[str, Any]:
        """Get current watcher status."""
        return {
            "enabled": self.enabled,
            "active_commands": len(self.active_commands),
            "recent_commands": list(self.command_history)[-10:],
        }

# Global command watcher
_command_watcher = CommandWatcher(enabled=os.environ.get("MCP_ENABLE_WATCHER", "true").lower() == "true")

# -----------------------------
# Server
# -----------------------------
server = Server("cursor-mcp-server")

# -----------------------------
# Context Tracking & Summarization
# -----------------------------
class ContextTracker:
    """Tracks context usage and auto-summarizes when threshold is reached."""
    
    def __init__(self, max_chars: int = CONTEXT_MAX_CHARS, threshold: float = CONTEXT_SUMMARY_THRESHOLD):
        self.max_chars = max_chars
        self.threshold = threshold
        self.current_chars = 0
        self.summaries: deque = deque(maxlen=10)  # Keep last 10 summaries
        self.enabled = CONTEXT_SUMMARY_ENABLED
    
    def add(self, content: str) -> int:
        """Add content and return current usage."""
        self.current_chars += len(content)
        return self.current_chars
    
    def should_summarize(self) -> bool:
        """Check if we should summarize (at 85% threshold)."""
        if not self.enabled:
            return False
        usage_pct = self.current_chars / self.max_chars
        return usage_pct >= self.threshold
    
    def get_usage_pct(self) -> float:
        """Get current usage percentage."""
        return (self.current_chars / self.max_chars) * 100
    
    def reset(self) -> None:
        """Reset context counter."""
        self.current_chars = 0
    
    def record_summary(self, original_size: int, summary_size: int) -> None:
        """Record a summarization event."""
        self.summaries.append({
            "ts": time.time(),
            "original_chars": original_size,
            "summary_chars": summary_size,
            "compression_ratio": summary_size / original_size if original_size > 0 else 0.0,
        })

# Global context tracker
_context_tracker = ContextTracker()

def _summarize_text(text: str, max_chars: Optional[int] = None) -> str:
    """
    Summarize text by keeping key sections and truncating intelligently.
    
    Strategy:
    1. If under limit, return as-is
    2. Keep first 20% (intro/headers)
    3. Keep last 20% (conclusions)
    4. Summarize middle 60% (keep key patterns, remove redundancy)
    """
    if max_chars is None:
        max_chars = int(CONTEXT_MAX_CHARS * 0.3)  # Summarize to ~30% of max
    
    if len(text) <= max_chars:
        return text
    
    # Split into lines for better summarization
    lines = text.splitlines()
    total_lines = len(lines)
    
    # Keep first 20% and last 20%
    keep_start = int(total_lines * 0.2)
    keep_end = int(total_lines * 0.8)
    
    kept_start = "\n".join(lines[:keep_start])
    kept_end = "\n".join(lines[keep_end:])
    
    # Summarize middle section
    middle = lines[keep_start:keep_end]
    
    # Keep lines with key patterns (definitions, classes, important comments)
    important_patterns = [
        r"^(def|class|async def|@|import|from|# TODO|# FIXME|# NOTE)",
        r"^\s*(if|for|while|try|except|with|return|yield|raise)",
    ]
    important_lines = []
    for line in middle:
        if any(re.search(pat, line) for pat in important_patterns):
            important_lines.append(line)
    
    # Limit important lines to avoid overflow
    max_middle_lines = max_chars // 80  # ~80 chars per line estimate
    if len(important_lines) > max_middle_lines:
        # Keep evenly spaced samples
        step = len(important_lines) // max_middle_lines
        important_lines = important_lines[::max(1, step)]
    
    middle_summary = "\n".join(important_lines)
    if len(middle_summary) > max_chars * 0.6:
        # Still too long, truncate
        middle_summary = middle_summary[:int(max_chars * 0.6)]
    
    summary = f"{kept_start}\n\n[... {len(middle)} lines summarized to {len(important_lines)} key lines ...]\n\n{middle_summary}\n\n[... {len(middle)} lines summarized ...]\n\n{kept_end}"
    
    # Final truncation if still over limit
    if len(summary) > max_chars:
        summary = summary[:max_chars] + "\n[... truncated ...]"
    
    return summary

def _auto_summarize_if_needed(content: str, context_name: str = "content") -> str:
    """
    Auto-summarize content if context tracker indicates we're at threshold.
    Returns original or summarized content.
    """
    if not CONTEXT_SUMMARY_ENABLED:
        return content
    
    # Add to tracker
    _context_tracker.add(content)
    
    if _context_tracker.should_summarize():
        original_size = len(content)
        summary = _summarize_text(content)
        summary_size = len(summary)
        
        # Record the summarization
        _context_tracker.record_summary(original_size, summary_size)
        
        # Reset tracker after summarization
        _context_tracker.reset()
        _context_tracker.add(summary)  # Count the summary itself
        
        # Add metadata header
        usage_pct = _context_tracker.get_usage_pct()
        header = f"[AUTO-SUMMARIZED at {usage_pct:.1f}% context usage: {context_name}]\n"
        header += f"[Original: {original_size:,} chars → Summary: {summary_size:,} chars ({summary_size/original_size*100:.1f}%)\n\n"
        
        return header + summary
    
    return content

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
async def read_file(path: str, allow_denied_explicit: bool = False) -> str:
    """Read a UTF-8 text file from the workspace.
    
    Args:
        path: File path relative to workspace
        allow_denied_explicit: If True, allow reading denylisted paths (default: False)
    """
    if not rate_read.allow():
        raise RuntimeError("Rate limit exceeded for reads")
    abs_path = safe_join(path)
    if not abs_path.is_file():
        raise FileNotFoundError(f"Not a file: {path}")
    rel = abs_path.relative_to(WORKSPACE_DIR).as_posix()
    if _denylisted(rel) and not allow_denied_explicit:
        raise PermissionError("Path is denylisted (set allow_denied_explicit=true to override)")
    try:
        text = _read_text_guarded(abs_path)
        # Auto-summarize if context threshold reached
        text = _auto_summarize_if_needed(text, context_name=f"file:{path}")
        write_audit(AuditEntry(time.time(), "read_file", {"path": path, "allow_denied": allow_denied_explicit}, True, {"size": len(text), "context_pct": _context_tracker.get_usage_pct()}))
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
    
    # Auto-summarize file list if context threshold reached
    result_text = "\n".join(results)
    _context_tracker.add(result_text)
    if _context_tracker.should_summarize():
        # Summarize by grouping and showing counts
        file_groups: Dict[str, List[str]] = {}
        for f in results:
            ext = Path(f).suffix or "no_ext"
            if ext not in file_groups:
                file_groups[ext] = []
            file_groups[ext].append(f)
        
        summary_parts = [f"Total files: {len(results)} (summarized at {_context_tracker.get_usage_pct():.1f}% context usage)"]
        for ext, files in sorted(file_groups.items(), key=lambda x: len(x[1]), reverse=True):
            if len(files) <= 10:
                summary_parts.append(f"\n{ext or 'no_ext'}: {len(files)} files")
                summary_parts.extend(f"  - {f}" for f in files[:10])
            else:
                summary_parts.append(f"\n{ext or 'no_ext'}: {len(files)} files (showing first 10)")
                summary_parts.extend(f"  - {f}" for f in files[:10])
                summary_parts.append(f"  ... and {len(files) - 10} more")
        
        result_text = "\n".join(summary_parts)
        _context_tracker.reset()
        _context_tracker.add(result_text)
    
    write_audit(AuditEntry(time.time(), "list_files", {"base": base, "pattern": pattern}, True, {"count": len(results), "context_pct": _context_tracker.get_usage_pct()}))
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
async def reset_context() -> Dict[str, Any]:
    """Reset soft state like rate windows (keeps audit log)."""
    old_chars = _context_tracker.current_chars
    _context_tracker.reset()
    # Reset rate limiters
    rate_read.events.clear()
    rate_write.events.clear()
    rate_cmd.events.clear()
    write_audit(AuditEntry(time.time(), "reset_context", {}, True, {"reset": True}))
    return {
        "status": "reset",
        "previous_chars": old_chars,
        "current_chars": _context_tracker.current_chars,
        "rate_limiters_reset": True,
    }

@server.tool()
async def run_command(command: str, timeout_seconds: int = 60) -> Dict[str, Any]:
    """Run a whitelisted shell command within the workspace."""
    if not rate_cmd.allow():
        raise RuntimeError("Rate limit exceeded for commands")
    
    if not is_allowed_command(command):
        raise PermissionError("Command not allowed by whitelist")
    
    # Generate unique command ID for tracking
    command_id = f"cmd_{int(time.time() * 1000)}"
    
    # Start watching
    _command_watcher.start_command(command_id, command)
    
    try:
        # Fix for Windows/PowerShell hanging: disable paging and ensure non-interactive
        env = os.environ.copy()
        env.update({
            "GIT_PAGER": "cat",  # Disable git pager
            "PAGER": "cat",  # Disable system pager
            "GIT_TERMINAL_PROMPT": "0",  # Disable terminal prompts
            "GIT_ASKPASS": "",  # Disable credential prompts
            "GCM_INTERACTIVE": "never",  # Disable Git Credential Manager prompts
        })
        
        # For git commands, ensure --no-pager flag if not already present
        original_command = command
        if command.strip().startswith("git ") and "--no-pager" not in command:
            # Add --no-pager after 'git' but preserve the rest
            parts = command.split(None, 1)
            if len(parts) > 1:
                command = f"{parts[0]} --no-pager {parts[1]}"
            else:
                command = f"{command} --no-pager"
            _command_watcher.update_command(command_id, "modified", f"Added --no-pager flag")
        
        _command_watcher.update_command(command_id, "spawning", f"Creating subprocess...")
        
        proc = await asyncio.create_subprocess_shell(
            command,
            cwd=str(WORKSPACE_DIR),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
            stdin=asyncio.subprocess.DEVNULL,  # Prevent waiting for input
        )
        
        _command_watcher.update_command(command_id, "executing", f"PID: {proc.pid}")
        
        t0 = time.perf_counter()
        
        # Use asyncio.wait_for with timeout
        try:
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), 
                timeout=timeout_seconds
            )
            dt = time.perf_counter() - t0
            _command_watcher.update_command(command_id, "completed", f"Finished in {int(dt*1000)}ms")
        except asyncio.TimeoutError:
            _command_watcher.update_command(command_id, "timeout", f"Exceeded {timeout_seconds}s timeout")
            proc.kill()
            await proc.wait()  # Wait for process to actually terminate
            write_audit(AuditEntry(time.time(), "run_command", {"command": original_command}, False, {"timeout": timeout_seconds}))
            _command_watcher.end_command(command_id, False, returncode=-1, elapsed_ms=int(timeout_seconds * 1000))
            raise TimeoutError(f"Command timed out after {timeout_seconds} seconds")
        
        # Decode output
        stdout_text = stdout.decode("utf-8", errors="replace")
        stderr_text = stderr.decode("utf-8", errors="replace")
        output_size = len(stdout_text) + len(stderr_text)
        
        success = proc.returncode == 0
        elapsed_ms = int(dt * 1000)
        
        # End watching
        _command_watcher.end_command(
            command_id, 
            success, 
            returncode=proc.returncode,
            elapsed_ms=elapsed_ms,
            output_size=output_size
        )
        
        write_audit(AuditEntry(time.time(), "run_command", {"command": original_command}, success, {
            "rc": proc.returncode, 
            "ms": elapsed_ms,
            "output_size": output_size
        }))
        
        return {
            "returncode": proc.returncode,
            "stdout": stdout_text,
            "stderr": stderr_text,
            "elapsed_ms": elapsed_ms,
        }
    except Exception as e:
        _command_watcher.end_command(command_id, False, returncode=-1)
        LOG.error(f"❌ ERROR: {str(e)}")
        raise

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
        "context": {
            "max_chars": CONTEXT_MAX_CHARS,
            "current_chars": _context_tracker.current_chars,
            "usage_pct": round(_context_tracker.get_usage_pct(), 2),
            "summary_threshold": CONTEXT_SUMMARY_THRESHOLD,
            "summarization_enabled": CONTEXT_SUMMARY_ENABLED,
            "recent_summaries": list(_context_tracker.summaries),
        },
        "watcher": _command_watcher.get_status(),
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
    
    # Auto-summarize search results if context threshold reached
    if _context_tracker.should_summarize() and hits:
        # Summarize by grouping by file and showing top matches
        file_groups: Dict[str, List[Dict[str, Any]]] = {}
        for hit in hits:
            f = hit["file"]
            if f not in file_groups:
                file_groups[f] = []
            file_groups[f].append(hit)
        
        # Keep top files by match count, summarize others
        sorted_files = sorted(file_groups.items(), key=lambda x: len(x[1]), reverse=True)
        top_files = sorted_files[:5]  # Top 5 files
        other_files = sorted_files[5:]
        
        summarized_hits = []
        for f, file_hits in top_files:
            # Keep all matches from top files
            summarized_hits.extend(file_hits[:10])  # Max 10 per file
        
        # Summarize other files
        if other_files:
            other_count = sum(len(hits) for _, hits in other_files)
            summarized_hits.append({
                "file": f"[{len(other_files)} other files]",
                "line": 0,
                "match": f"... {other_count} more matches in {len(other_files)} files ...",
                "context": f"Summarized: {other_count} matches across {len(other_files)} files (showing top 5 files only)",
            })
        
        hits = summarized_hits
        _context_tracker.reset()
        # Estimate size for tracking
        hits_text = json.dumps(hits)
        _context_tracker.add(hits_text)
    
    write_audit(AuditEntry(time.time(), "search_code", {"query": query}, True, {"count": len(hits), "context_pct": _context_tracker.get_usage_pct()}))
    return hits

# -----------------------------
# Resources
# -----------------------------
@server.resource()
async def workspace_tree() -> ResourceContents:
    items = await list_files(".", "**/*", 2000)
    text = "\n".join(items)
    text = _auto_summarize_if_needed(text, context_name="workspace_tree")
    return ResourceContents(text=text)

@server.resource()
async def workspace_summary() -> ResourceContents:
    parts = [f"Workspace: {WORKSPACE_DIR}"]
    readme_p = safe_join("README.md")
    if readme_p.exists():
        txt = _read_text_guarded(readme_p)
        # Auto-summarize README if needed
        txt_preview = _auto_summarize_if_needed(txt[:1000], context_name="readme_preview")  # Preview first 1k
        parts.append(f"README (preview):\n{txt_preview}")
    try:
        pkg = safe_join("package.json")
        if pkg.exists():
            parts.append("package.json present")
    except Exception:
        pass
    text = "\n\n".join(parts)
    text = _auto_summarize_if_needed(text, context_name="workspace_summary")
    return ResourceContents(text=text)

@server.resource()
async def readme() -> ResourceContents:
    p = safe_join("README.md")
    if p.exists():
        text = _read_text_guarded(p)
        text = _auto_summarize_if_needed(text, context_name="readme")
        return ResourceContents(text=text)
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

