# Warmup script for Netlify MCP function
# Run this before ChatGPT validation to eliminate cold starts

Write-Host "Warming up MCP function..." -ForegroundColor Cyan

# Warm up manifest endpoint
Invoke-WebRequest -Uri 'https://zingy-profiterole-f31cb8.netlify.app/mcp' -Method GET -UseBasicParsing | Out-Null
Start-Sleep -Milliseconds 500

# Warm up health endpoint
Invoke-WebRequest -Uri 'https://zingy-profiterole-f31cb8.netlify.app/mcp/health' -Method GET -UseBasicParsing | Out-Null
Start-Sleep -Milliseconds 500

# Warm up tools/list
$body = @{jsonrpc='2.0';id=1;method='tools/list';params=@{}} | ConvertTo-Json -Compress
Invoke-WebRequest -Uri 'https://zingy-profiterole-f31cb8.netlify.app/mcp' -Method POST -Headers @{'Origin'='https://chatgpt.com';'Content-Type'='application/json'} -Body $body -UseBasicParsing | Out-Null

Write-Host "Function warmed up! Wait 2 seconds, then try ChatGPT validation." -ForegroundColor Green
