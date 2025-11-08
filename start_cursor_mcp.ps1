param(
  [Parameter(Mandatory=$true)][string]$WorkspaceDir
)

$env:WORKSPACE_DIR = (Resolve-Path $WorkspaceDir).Path

if (-not $env:MCP_AUDIT_LOG) { $env:MCP_AUDIT_LOG = Join-Path $env:WORKSPACE_DIR ".mcp_audit.log" }

python -u cursor_mcp_server.py

