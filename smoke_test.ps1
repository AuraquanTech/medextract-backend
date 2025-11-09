# Smoke tests for MCP server
# All four must return 200 quickly

Write-Host "=== MCP Server Smoke Tests ===" -ForegroundColor Green
Write-Host ""

$baseUrl = "https://zingy-profiterole-f31cb8.netlify.app/mcp"
$results = @()

# Test 1: Manifest (no Origin)
Write-Host "1. Testing GET /mcp (manifest)..." -ForegroundColor Cyan
try {
    $measure = Measure-Command {
        $response = Invoke-WebRequest -Uri $baseUrl -Method GET -UseBasicParsing -TimeoutSec 5
    }
    $json = $response.Content | ConvertFrom-Json
    $results += [PSCustomObject]@{Test='GET /mcp';Status=$response.StatusCode;Time=[math]::Round($measure.TotalSeconds, 3);Result='✅ PASS'}
    Write-Host "   ✅ Status: $($response.StatusCode) | Time: $([math]::Round($measure.TotalSeconds, 3))s | Name: $($json.name)" -ForegroundColor Green
} catch {
    $results += [PSCustomObject]@{Test='GET /mcp';Status='ERROR';Time=0;Result='❌ FAIL'}
    Write-Host "   ❌ Error: $_" -ForegroundColor Red
}

Start-Sleep -Milliseconds 200

# Test 2: Health (no Origin)
Write-Host "2. Testing GET /mcp/health..." -ForegroundColor Cyan
try {
    $measure = Measure-Command {
        $response = Invoke-WebRequest -Uri "$baseUrl/health" -Method GET -UseBasicParsing -TimeoutSec 5
    }
    $json = $response.Content | ConvertFrom-Json
    $results += [PSCustomObject]@{Test='GET /mcp/health';Status=$response.StatusCode;Time=[math]::Round($measure.TotalSeconds, 3);Result='✅ PASS'}
    Write-Host "   ✅ Status: $($response.StatusCode) | Time: $([math]::Round($measure.TotalSeconds, 3))s | OK: $($json.ok)" -ForegroundColor Green
} catch {
    $results += [PSCustomObject]@{Test='GET /mcp/health';Status='ERROR';Time=0;Result='❌ FAIL'}
    Write-Host "   ❌ Error: $_" -ForegroundColor Red
}

Start-Sleep -Milliseconds 200

# Test 3: tools/list (with Origin)
Write-Host "3. Testing POST /mcp (tools/list)..." -ForegroundColor Cyan
try {
    $body = @{jsonrpc='2.0';id=1;method='tools/list';params=@{}} | ConvertTo-Json -Compress
    $measure = Measure-Command {
        $response = Invoke-WebRequest -Uri $baseUrl -Method POST -Headers @{'Origin'='https://chatgpt.com';'Content-Type'='application/json'} -Body $body -UseBasicParsing -TimeoutSec 5
    }
    $json = $response.Content | ConvertFrom-Json
    $toolCount = $json.result.tools.Count
    $results += [PSCustomObject]@{Test='POST tools/list';Status=$response.StatusCode;Time=[math]::Round($measure.TotalSeconds, 3);Result='✅ PASS'}
    Write-Host "   ✅ Status: $($response.StatusCode) | Time: $([math]::Round($measure.TotalSeconds, 3))s | Tools: $toolCount" -ForegroundColor Green
} catch {
    $results += [PSCustomObject]@{Test='POST tools/list';Status='ERROR';Time=0;Result='❌ FAIL'}
    Write-Host "   ❌ Error: $_" -ForegroundColor Red
}

Start-Sleep -Milliseconds 200

# Test 4: get_diagnostics (with Origin)
Write-Host "4. Testing POST /mcp (tools/call - get_diagnostics)..." -ForegroundColor Cyan
try {
    $body = @{jsonrpc='2.0';id=1;method='tools/call';params=@{name='get_diagnostics';arguments=@{}}} | ConvertTo-Json -Compress
    $measure = Measure-Command {
        $response = Invoke-WebRequest -Uri $baseUrl -Method POST -Headers @{'Origin'='https://chatgpt.com';'Content-Type'='application/json'} -Body $body -UseBasicParsing -TimeoutSec 5
    }
    $json = $response.Content | ConvertFrom-Json
    $hasResult = $json.result -ne $null
    $results += [PSCustomObject]@{Test='POST tools/call (get_diagnostics)';Status=$response.StatusCode;Time=[math]::Round($measure.TotalSeconds, 3);Result='✅ PASS'}
    Write-Host "   ✅ Status: $($response.StatusCode) | Time: $([math]::Round($measure.TotalSeconds, 3))s | Has result: $hasResult" -ForegroundColor Green
} catch {
    $results += [PSCustomObject]@{Test='POST tools/call (get_diagnostics)';Status='ERROR';Time=0;Result='❌ FAIL'}
    Write-Host "   ❌ Error: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "=== Test Summary ===" -ForegroundColor Green
$results | Format-Table -AutoSize
$passed = ($results | Where-Object { $_.Result -eq '✅ PASS' }).Count
$total = $results.Count
Write-Host ""
Write-Host "Results: $passed / $total tests passed" -ForegroundColor $(if ($passed -eq $total) { 'Green' } else { 'Red' })
if ($passed -eq $total) {
    Write-Host "✅ All tests passed! Ready for ChatGPT validation." -ForegroundColor Green
} else {
    Write-Host "❌ Some tests failed. Check the errors above." -ForegroundColor Red
}

