@echo off
REM Non-interactive deployment script for Netlify MCP Server
REM Run: deploy.bat

echo === Netlify MCP Server Deployment ===
echo.

REM Step 1: Verify dependencies
echo Step 1: Verifying dependencies...
if not exist "node_modules" (
    echo Installing dependencies...
    call npm install --silent
) else (
    echo Dependencies already installed
)

REM Verify minimatch
call npm list minimatch >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo minimatch found
) else (
    echo minimatch not found, installing...
    call npm install minimatch --silent
)

REM Step 2: Build TypeScript
echo.
echo Step 2: Building TypeScript...
if exist "tsconfig.json" (
    call npm run build >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        echo TypeScript build successful
    ) else (
        echo TypeScript build failed
        exit /b 1
    )
) else (
    echo tsconfig.json not found, skipping build
)

REM Step 3: Check environment variables
echo.
echo Step 3: Checking environment variables...
echo IMPORTANT: Set these in Netlify Dashboard - Site settings - Environment:
echo    ALLOWED_ORIGINS=https://chatgpt.com,https://*.chatgpt.com,https://chat.openai.com,https://*.openai.com
echo    MCP_HTTP_REQUIRE_ORIGIN=true
echo    RATE_LIMIT_WINDOW_MS=60000
echo    RATE_LIMIT_MAX_REQ=300
echo.

REM Step 4: Deploy
echo Step 4: Deploying to Netlify...
echo Note: This requires Netlify CLI to be installed and authenticated
echo    Install: npm install -g netlify-cli
echo    Login: netlify login
echo.

REM Check if netlify CLI is available
where netlify >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo Netlify CLI found
    echo Deploying...
    call netlify deploy --prod --dir . --functions netlify/functions
    if %ERRORLEVEL% EQU 0 (
        echo.
        echo Deployment successful!
        echo.
        echo Next steps:
        echo 1. Test: curl -i "https://your-site.netlify.app/mcp"
        echo 2. Connect in ChatGPT with Server URL: https://your-site.netlify.app/mcp
    ) else (
        echo Deployment failed
        exit /b 1
    )
) else (
    echo Netlify CLI not found
    echo.
    echo To deploy manually:
    echo 1. Install Netlify CLI: npm install -g netlify-cli
    echo 2. Login: netlify login
    echo 3. Deploy: netlify deploy --prod
    echo.
    echo Or push to GitHub if auto-deploy is enabled
)

echo.
echo === Deployment Script Complete ===

