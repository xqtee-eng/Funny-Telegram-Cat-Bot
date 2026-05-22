$ErrorActionPreference = "Stop"

Set-Location $PSScriptRoot

$Port = 8787
$HostAddress = "127.0.0.1"
$SiteUrl = "http://${HostAddress}:${Port}/"
$ServerOut = Join-Path $PSScriptRoot "mini_app_server.out.log"
$ServerErr = Join-Path $PSScriptRoot "mini_app_server.err.log"
$TunnelOut = Join-Path $PSScriptRoot "localhostrun.out.log"
$TunnelErr = Join-Path $PSScriptRoot "localhostrun.err.log"

function Resolve-PythonCommand {
    if (Get-Command "python" -ErrorAction SilentlyContinue) {
        return "python"
    }
    if (Get-Command "py" -ErrorAction SilentlyContinue) {
        return "py -3"
    }

    $fallback = Join-Path $env:LOCALAPPDATA "Programs\Python\Python311\python.exe"
    if (Test-Path $fallback) {
        return $fallback
    }

    throw "Python was not found. Install Python 3.11+ or add it to PATH."
}

$Python = Resolve-PythonCommand

function Invoke-Python {
    param([string[]] $Arguments)

    if ($Python -eq "py -3") {
        & py -3 @Arguments
    }
    else {
        & $Python @Arguments
    }
}

function Test-HttpOk {
    param([string] $Url)

    try {
        $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 5
        return $response.StatusCode -eq 200
    }
    catch {
        return $false
    }
}

function Wait-ForFileUrl {
    param(
        [string] $Path,
        [int] $TimeoutSeconds = 45
    )

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        if (Test-Path $Path) {
            $content = Get-Content $Path -Raw -ErrorAction SilentlyContinue
            if (-not [string]::IsNullOrWhiteSpace($content)) {
                $matches = [regex]::Matches($content, "https://[a-z0-9-]+\.lhr\.life")
                if ($matches.Count -gt 0) {
                    return $matches[$matches.Count - 1].Value
                }
            }
        }
        Start-Sleep -Seconds 1
    }

    throw "Tunnel URL was not found in $Path after $TimeoutSeconds seconds."
}

function Wait-ForHttpOk {
    param(
        [string] $Url,
        [int] $TimeoutSeconds = 45
    )

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    while ((Get-Date) -lt $deadline) {
        if (Test-HttpOk $Url) {
            return
        }
        Start-Sleep -Seconds 1
    }

    throw "$Url did not return HTTP 200 after $TimeoutSeconds seconds."
}

function Stop-ExistingHelpers {
    $targets = Get-CimInstance Win32_Process | Where-Object {
        ($_.CommandLine -like '*http.server 8787*mini_app*') -or
        (($_.CommandLine -like '*nokey@localhost.run*') -and ($_.CommandLine -like '*8787*'))
    }

    foreach ($target in $targets) {
        Write-Host "Stopping old helper PID $($target.ProcessId): $($target.Name)"
        Stop-Process -Id $target.ProcessId -Force
    }
}

Stop-ExistingHelpers

Write-Host "Starting Mini App server on $SiteUrl"
if (-not (Test-HttpOk $SiteUrl)) {
    $serverFile = $Python
    $serverArgs = @("-m", "http.server", "$Port", "--directory", "mini_app")
    if ($Python -eq "py -3") {
        $serverFile = "py"
        $serverArgs = @("-3") + $serverArgs
    }

    Start-Process -FilePath $serverFile `
        -ArgumentList $serverArgs `
        -RedirectStandardOutput $ServerOut `
        -RedirectStandardError $ServerErr `
        -WindowStyle Hidden

    $serverReady = $false
    for ($i = 0; $i -lt 20; $i++) {
        Start-Sleep -Milliseconds 500
        if (Test-HttpOk $SiteUrl) {
            $serverReady = $true
            break
        }
    }

    if (-not $serverReady) {
        throw "Mini App server did not start. Check $ServerErr."
    }
}
else {
    Write-Host "Mini App server is already running."
}

Write-Host "Starting localhost.run tunnel..."
Remove-Item $TunnelOut, $TunnelErr -Force -ErrorAction SilentlyContinue
Start-Process -FilePath "ssh.exe" `
    -ArgumentList @(
        "-o", "StrictHostKeyChecking=no",
        "-o", "UserKnownHostsFile=localhostrun_known_hosts",
        "-o", "ServerAliveInterval=30",
        "-R", "80:${HostAddress}:${Port}",
        "nokey@localhost.run"
    ) `
    -RedirectStandardOutput $TunnelOut `
    -RedirectStandardError $TunnelErr `
    -WindowStyle Hidden

$TunnelUrl = Wait-ForFileUrl -Path $TunnelOut
Write-Host "Tunnel URL: $TunnelUrl"
Wait-ForHttpOk -Url $TunnelUrl

Write-Host "Syncing Telegram Mini App button..."
Invoke-Python @("sync_tunnel_url.py", $TunnelUrl)

Write-Host ""
Write-Host "Bot is starting. Keep this window open."
Write-Host "Press Ctrl+C to stop the bot. Use .\stop_all.ps1 to stop the site/tunnel too."
Write-Host ""
Invoke-Python @("bot.py")
