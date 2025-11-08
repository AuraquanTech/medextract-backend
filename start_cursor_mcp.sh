#!/usr/bin/env bash

set -euo pipefail

: "${WORKSPACE_DIR:?Set WORKSPACE_DIR to your workspace root}"

export MCP_AUDIT_LOG="${MCP_AUDIT_LOG:-$WORKSPACE_DIR/.mcp_audit.log}"

python -u cursor_mcp_server.py

