# Non-interactive Netlify deployment script
# Disables all pagers and interactive prompts

# Disable all pagers and interactive prompts
$env:GIT_PAGER = "cat"
$env:PAGER = "cat"
$env:GIT_TERMINAL_PROMPT = "0"
$env:GIT_ASKPASS = ""
$env:GCM_INTERACTIVE = "never"

Write-Host "=== Netlify MCP Server Deployment ===" -ForegroundColor Green
Write-Host ""

# Check if Netlify CLI is installed
$netlify = Get-Command netlify -ErrorAction SilentlyContinue
if (-not $netlify) {
    Write-Host "❌ Netlify CLI not found" -ForegroundColor Red
    Write-Host ""
    Write-Host "Install with:" -ForegroundColor Yellow
    Write-Host "  npm install -g netlify-cli" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Then login with:" -ForegroundColor Yellow
    Write-Host "  netlify login" -ForegroundColor Cyan
    exit 1
}

Write-Host "✅ Netlify CLI found" -ForegroundColor Green
Write-Host ""

# Install dependencies if needed
if (-not (Test-Path "node_modules")) {
    Write-Host "Installing dependencies..." -ForegroundColor Cyan
    npm install --silent
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Failed to install dependencies" -ForegroundColor Red
        exit 1
    }
}

# Deploy with non-interactive flags
Write-Host "Deploying to Netlify (production)..." -ForegroundColor Cyan
Write-Host ""

# Use --json to avoid interactive prompts and capture output
$deployOutput = netlify deploy --prod --dir . --functions netlify/functions --json 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ Deployment successful!" -ForegroundColor Green
    Write-Host ""
    
    # Try to extract URL from JSON output
    try {
        $json = $deployOutput | ConvertFrom-Json
        if ($json.url) {
            Write-Host "Deployed URL: $($json.url)" -ForegroundColor Cyan
            Write-Host "MCP Endpoint: $($json.url)/mcp" -ForegroundColor Cyan
        }
    } catch {
        # If JSON parsing fails, just show success
    }
    
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "1. Set environment variables in Netlify Dashboard:" -ForegroundColor Cyan
    Write-Host "   - ALLOWED_ORIGINS=https://chatgpt.com,https://*.chatgpt.com,https://chat.openai.com,https://*.openai.com"
    Write-Host "   - MCP_HTTP_REQUIRE_ORIGIN=true"
    Write-Host "   - RATE_LIMIT_WINDOW_MS=60000"
    Write-Host "   - RATE_LIMIT_MAX_REQ=300"
    Write-Host ""
    Write-Host "2. Test the endpoint:" -ForegroundColor Cyan
    Write-Host "   curl -i 'https://your-site.netlify.app/mcp'"
    Write-Host ""
    Write-Host "3. Connect in ChatGPT:" -ForegroundColor Cyan
    Write-Host "   Server URL: https://your-site.netlify.app/mcp"
    Write-Host "   Authentication: None"
} else {
    Write-Host "❌ Deployment failed" -ForegroundColor Red
    Write-Host ""
    Write-Host "Error output:" -ForegroundColor Yellow
    Write-Host $deployOutput
    exit 1
}

