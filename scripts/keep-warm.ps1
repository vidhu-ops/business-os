# Local keep-warm loop for https://iidatech.biz (or KEEP_WARM_URL).
# Run while developing so Render does not sleep between requests:
#   powershell -File scripts/keep-warm.ps1
# Stop with Ctrl+C.

param(
  [string]$Url = $env:KEEP_WARM_URL,
  [int]$IntervalSeconds = 300
)

if (-not $Url) { $Url = "https://iidatech.biz" }
$Url = $Url.TrimEnd("/")

Write-Host "Keep-warm: pinging $Url/api/health every $IntervalSeconds s (Ctrl+C to stop)"
Write-Host "Note: GitHub cron alone is unreliable — use UptimeRobot (5 min) or upgrade Render to Starter."
while ($true) {
  $sw = [System.Diagnostics.Stopwatch]::StartNew()
  $health = "$Url/api/health?warm=1&t=$([DateTimeOffset]::UtcNow.ToUnixTimeSeconds())"
  try {
    $resp = Invoke-WebRequest -Uri $health -Method GET -TimeoutSec 100 -UseBasicParsing -Headers @{ "Cache-Control" = "no-cache" }
    $sw.Stop()
    Write-Host ("[{0:HH:mm:ss}] HTTP {1} in {2}ms" -f (Get-Date), [int]$resp.StatusCode, $sw.ElapsedMilliseconds)
  } catch {
    $sw.Stop()
    Write-Host ("[{0:HH:mm:ss}] FAIL after {1}ms — {2}" -f (Get-Date), $sw.ElapsedMilliseconds, $_.Exception.Message)
  }
  Start-Sleep -Seconds $IntervalSeconds
}