# Quick verification script for HTTP bridge
# Run this after starting the bridge with: .\start_http_bridge.ps1

param(
    [string]$BaseUrl = "http://localhost:8001",
    [string]$Origin = "https://chatgpt.com"
)

if (-not $env:MCP_HTTP_TOKEN) {
    Write-Error "Set MCP_HTTP_TOKEN first."
    exit 1
}

$headers = @{ Origin = $Origin }

Write-Host "=== Cursor MCP HTTP Bridge Verification ===" -ForegroundColor Cyan
Write-Host ""

# 1. Health check
Write-Host "1. Checking health..." -ForegroundColor Yellow
try {
    $health = Invoke-WebRequest "$BaseUrl/mcp/health?token=$env:MCP_HTTP_TOKEN" -Headers $headers -UseBasicParsing
    Write-Host "   ✅ Health endpoint: OK" -ForegroundColor Green
    $healthJson = $health.Content | ConvertFrom-Json
    Write-Host "   Workspace: $($healthJson.workspace)" -ForegroundColor Gray
    Write-Host "   Workspace exists: $($healthJson.workspace_exists)" -ForegroundColor Gray
} catch {
    Write-Host "   ❌ Health endpoint failed: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""

# 2. Manifest
Write-Host "2. Fetching manifest..." -ForegroundColor Yellow
try {
    $manifest = Invoke-WebRequest "$BaseUrl/mcp?token=$env:MCP_HTTP_TOKEN" -Headers $headers -UseBasicParsing
    Write-Host "   ✅ Manifest endpoint: OK" -ForegroundColor Green
    $manifestJson = $manifest.Content | ConvertFrom-Json
    Write-Host "   Tools: $($manifestJson.tools.Count)" -ForegroundColor Gray
    Write-Host "   Resources: $($manifestJson.resources.Count)" -ForegroundColor Gray
    Write-Host "   Prompts: $($manifestJson.prompts.Count)" -ForegroundColor Gray
} catch {
    Write-Host "   ❌ Manifest endpoint failed: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""

# 3. Call a tool: read README.md
Write-Host "3. Calling read_file on README.md..." -ForegroundColor Yellow
try {
    $body = @{ params = @{ path = "README.md" } } | ConvertTo-Json -Depth 5
    $result = Invoke-WebRequest `
        -Method POST `
        -Uri "$BaseUrl/mcp/tool/read_file?token=$env:MCP_HTTP_TOKEN" `
        -Headers $headers `
        -ContentType "application/json" `
        -Body $body `
        -UseBasicParsing
    
    Write-Host "   ✅ Tool call: OK" -ForegroundColor Green
    $resultJson = $result.Content | ConvertFrom-Json
    Write-Host "   Response type: $($resultJson.content[0].type)" -ForegroundColor Gray
    $contentText = $resultJson.content[0].text
    if ($contentText.Length -gt 100) {
        Write-Host "   Preview: $($contentText.Substring(0, 100))..." -ForegroundColor Gray
    } else {
        Write-Host "   Content: $contentText" -ForegroundColor Gray
    }
} catch {
    Write-Host "   ❌ Tool call failed: $_" -ForegroundColor Red
    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $responseBody = $reader.ReadToEnd()
        Write-Host "   Response: $responseBody" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "=== Verification Complete ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "If all checks passed, your bridge is ready!" -ForegroundColor Green
Write-Host "Add this URL to ChatGPT Connectors:" -ForegroundColor Yellow
Write-Host "  $BaseUrl/mcp?token=$env:MCP_HTTP_TOKEN" -ForegroundColor White
