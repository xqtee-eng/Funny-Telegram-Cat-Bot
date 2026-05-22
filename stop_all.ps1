$ErrorActionPreference = "SilentlyContinue"

Set-Location $PSScriptRoot

$targets = Get-CimInstance Win32_Process | Where-Object {
    ($_.CommandLine -like '*bot.py*') -or
    ($_.CommandLine -like '*http.server 8787*mini_app*') -or
    (($_.CommandLine -like '*nokey@localhost.run*') -and ($_.CommandLine -like '*8787*'))
}

if (-not $targets) {
    Write-Host "Nothing to stop."
    exit 0
}

$targets | ForEach-Object {
    Write-Host "Stopping PID $($_.ProcessId): $($_.Name)"
    Stop-Process -Id $_.ProcessId -Force
}

Write-Host "Stopped bot, Mini App server, and tunnel."
