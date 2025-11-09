param(
    [Parameter(Mandatory=$false)][string]$WorkspaceDir = "",
    [Parameter(Mandatory=$false)][string]$Token = "",
    [Parameter(Mandatory=$false)][int]$Port = 8001
)

# Set workspace directory
if ($WorkspaceDir) {
    $env:WORKSPACE_DIR = (Resolve-Path $WorkspaceDir).Path
} elseif (-not $env:WORKSPACE_DIR) {
    Write-Host "Error: WORKSPACE_DIR not set. Please provide -WorkspaceDir or set $env:WORKSPACE_DIR" -ForegroundColor Red
    exit 1
}

# Set token
if ($Token) {
    $env:MCP_HTTP_TOKEN = $Token
} elseif (-not $env:MCP_HTTP_TOKEN) {
    $env:MCP_HTTP_TOKEN = "3f7a1c2e5d8b9f0a4c7e2d1b6a5f9c8e7d0b3a6c5e1f2d4b7c9a0e3f6d1b2c4"
    Write-Host "Using default token. Set MCP_HTTP_TOKEN env var or use -Token for custom token." -ForegroundColor Yellow
}

# Set port
$env:MCP_HTTP_PORT = $Port

# Set audit log
if (-not $env:MCP_AUDIT_LOG) {
    $env:MCP_AUDIT_LOG = Join-Path $env:WORKSPACE_DIR ".mcp_audit.log"
}

Write-Host "Starting Cursor MCP HTTP Bridge..." -ForegroundColor Green
Write-Host "Workspace: $env:WORKSPACE_DIR" -ForegroundColor Cyan
Write-Host "Port: $env:MCP_HTTP_PORT" -ForegroundColor Cyan
Write-Host "Token: $($env:MCP_HTTP_TOKEN.Substring(0, 20))..." -ForegroundColor Cyan
Write-Host ""
Write-Host "Server URL: http://localhost:$env:MCP_HTTP_PORT/mcp?token=$env:MCP_HTTP_TOKEN" -ForegroundColor Yellow
Write-Host ""

# Run the HTTP bridge
uvicorn http_mcp_bridge:app --host 127.0.0.1 --port $env:MCP_HTTP_PORT

