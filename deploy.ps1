# Non-interactive deployment script for Netlify MCP Server
# Run: .\deploy.ps1

Write-Host "=== Netlify MCP Server Deployment ===" -ForegroundColor Green
Write-Host ""

# Step 1: Verify dependencies
Write-Host "Step 1: Verifying dependencies..." -ForegroundColor Cyan
if (-not (Test-Path "node_modules")) {
    Write-Host "Installing dependencies..." -ForegroundColor Yellow
    npm install --silent
} else {
    Write-Host "Dependencies already installed" -ForegroundColor Green
}

# Verify minimatch
$minimatch = npm list minimatch 2>&1 | Select-String "minimatch"
if ($minimatch) {
    Write-Host "✅ minimatch found: $minimatch" -ForegroundColor Green
} else {
    Write-Host "⚠️  minimatch not found, installing..." -ForegroundColor Yellow
    npm install minimatch --silent
}

# Step 2: Build TypeScript
Write-Host ""
Write-Host "Step 2: Building TypeScript..." -ForegroundColor Cyan
if (Test-Path "tsconfig.json") {
    npm run build 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ TypeScript build successful" -ForegroundColor Green
    } else {
        Write-Host "❌ TypeScript build failed" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "⚠️  tsconfig.json not found, skipping build" -ForegroundColor Yellow
}

# Step 3: Check environment variables
Write-Host ""
Write-Host "Step 3: Checking environment variables..." -ForegroundColor Cyan
Write-Host "⚠️  IMPORTANT: Set these in Netlify Dashboard → Site settings → Environment:" -ForegroundColor Yellow
Write-Host "   ALLOWED_ORIGINS=https://chatgpt.com,https://*.chatgpt.com,https://chat.openai.com,https://*.openai.com"
Write-Host "   MCP_HTTP_REQUIRE_ORIGIN=true"
Write-Host "   RATE_LIMIT_WINDOW_MS=60000"
Write-Host "   RATE_LIMIT_MAX_REQ=300"
Write-Host ""

# Step 4: Deploy
Write-Host "Step 4: Deploying to Netlify..." -ForegroundColor Cyan
Write-Host "⚠️  Note: This requires Netlify CLI to be installed and authenticated" -ForegroundColor Yellow
Write-Host "   Install: npm install -g netlify-cli" -ForegroundColor Yellow
Write-Host "   Login: netlify login" -ForegroundColor Yellow
Write-Host ""

# Check if netlify CLI is available
$netlify = Get-Command netlify -ErrorAction SilentlyContinue
if ($netlify) {
    Write-Host "✅ Netlify CLI found" -ForegroundColor Green
    Write-Host "Deploying..." -ForegroundColor Cyan
    netlify deploy --prod --dir . --functions netlify/functions
    if ($LASTEXITCODE -eq 0) {
        Write-Host ""
        Write-Host "✅ Deployment successful!" -ForegroundColor Green
        Write-Host ""
        Write-Host "Next steps:" -ForegroundColor Cyan
        Write-Host "1. Test: curl -i 'https://your-site.netlify.app/mcp'" -ForegroundColor Yellow
        Write-Host "2. Connect in ChatGPT with Server URL: https://your-site.netlify.app/mcp" -ForegroundColor Yellow
    } else {
        Write-Host "❌ Deployment failed" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "⚠️  Netlify CLI not found" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "To deploy manually:" -ForegroundColor Cyan
    Write-Host "1. Install Netlify CLI: npm install -g netlify-cli" -ForegroundColor Yellow
    Write-Host "2. Login: netlify login" -ForegroundColor Yellow
    Write-Host "3. Deploy: netlify deploy --prod" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Or push to GitHub if auto-deploy is enabled" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=== Deployment Script Complete ===" -ForegroundColor Green

