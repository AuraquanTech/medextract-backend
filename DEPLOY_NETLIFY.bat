@echo off
REM Simple Netlify deployment script - Run in a NEW terminal window
REM This script avoids pager issues by using non-interactive flags

echo === Netlify MCP Server Deployment ===
echo.

REM Check if Netlify CLI is installed
where netlify >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Netlify CLI not found
    echo.
    echo Install with:
    echo   npm install -g netlify-cli
    echo.
    echo Then login with:
    echo   netlify login
    echo.
    pause
    exit /b 1
)

echo Netlify CLI found
echo.

REM Install dependencies if needed
if not exist "node_modules" (
    echo Installing dependencies...
    call npm install --silent
    if %ERRORLEVEL% NEQ 0 (
        echo ERROR: Failed to install dependencies
        pause
        exit /b 1
    )
)

echo Deploying to Netlify (production)...
echo.

REM Deploy with non-interactive flags
netlify deploy --prod --dir . --functions netlify/functions

if %ERRORLEVEL% EQU 0 (
    echo.
    echo === Deployment successful! ===
    echo.
    echo Next steps:
    echo 1. Set environment variables in Netlify Dashboard:
    echo    - ALLOWED_ORIGINS=https://chatgpt.com,https://*.chatgpt.com,https://chat.openai.com,https://*.openai.com
    echo    - MCP_HTTP_REQUIRE_ORIGIN=true
    echo    - RATE_LIMIT_WINDOW_MS=60000
    echo    - RATE_LIMIT_MAX_REQ=300
    echo.
    echo 2. Test: curl -i https://your-site.netlify.app/mcp
    echo.
    echo 3. Connect in ChatGPT with Server URL: https://your-site.netlify.app/mcp
) else (
    echo.
    echo === Deployment failed ===
    echo Check the error messages above
)

echo.
pause

