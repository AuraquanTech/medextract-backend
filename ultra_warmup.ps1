# Ultra-aggressive warmup for ChatGPT validation
# Run this for 30 seconds before trying validation

Write-Host "=== Ultra-Aggressive Function Warmup ===" -ForegroundColor Green
Write-Host "Running for 30 seconds to eliminate cold start..." -ForegroundColor Cyan
Write-Host ""

$startTime = Get-Date
$endTime = $startTime.AddSeconds(30)
$iteration = 0

while ((Get-Date) -lt $endTime) {
    $iteration++
    $elapsed = ((Get-Date) - $startTime).TotalSeconds
    
    # Warm up all endpoints
    try {
        Invoke-WebRequest -Uri 'https://zingy-profiterole-f31cb8.netlify.app/mcp' -Method GET -UseBasicParsing -TimeoutSec 5 | Out-Null
        Invoke-WebRequest -Uri 'https://zingy-profiterole-f31cb8.netlify.app/mcp/health' -Method GET -UseBasicParsing -TimeoutSec 5 | Out-Null
        
        $body = @{jsonrpc='2.0';id=1;method='tools/list';params=@{}} | ConvertTo-Json -Compress
        Invoke-WebRequest -Uri 'https://zingy-profiterole-f31cb8.netlify.app/mcp' -Method POST -Headers @{'Origin'='https://chatgpt.com';'User-Agent'='ChatGPT';'Content-Type'='application/json'} -Body $body -UseBasicParsing -TimeoutSec 5 | Out-Null
    } catch {
        # Ignore errors during warmup
    }
    
    if ($iteration % 5 -eq 0) {
        Write-Host "[$([math]::Round($elapsed, 1))s] Function warmed - iteration $iteration" -ForegroundColor Yellow
    }
    
    Start-Sleep -Milliseconds 500
}

Write-Host ""
Write-Host "✅ Function is WARM - Try validation NOW!" -ForegroundColor Green
Write-Host "Expected validation time: 10-15 seconds" -ForegroundColor Cyan
Write-Host ""

