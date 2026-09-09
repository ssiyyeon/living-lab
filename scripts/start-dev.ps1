$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$frontendRoot = Join-Path $repoRoot "frontend"
$logRoot = Join-Path $repoRoot "tmp"
$backendPython = Join-Path $repoRoot ".venv-api\Scripts\python.exe"
$viteEntry = Join-Path $frontendRoot "node_modules\vite\bin\vite.js"
$frontendEnv = Join-Path $frontendRoot ".env.local"

New-Item -ItemType Directory -Force -Path $logRoot | Out-Null

if (-not (Test-Path -LiteralPath $backendPython)) {
    throw "Backend Python not found: $backendPython"
}

if (-not (Test-Path -LiteralPath $viteEntry)) {
    throw "Frontend dependencies are missing. Run pnpm install in the frontend directory first."
}

$apiBaseUrl = "http://localhost:8000"
if (Test-Path -LiteralPath $frontendEnv) {
    $configuredUrl = Get-Content -LiteralPath $frontendEnv |
        Where-Object { $_ -match '^VITE_API_BASE_URL=' } |
        Select-Object -First 1

    if ($configuredUrl) {
        $apiBaseUrl = ($configuredUrl -split '=', 2)[1].Trim()
    }
}

$apiPort = ([Uri]$apiBaseUrl).Port
$frontendPort = 5173

function Test-ListeningPort([int]$Port) {
    $client = [System.Net.Sockets.TcpClient]::new()
    try {
        $connectTask = $client.ConnectAsync("127.0.0.1", $Port)
        return $connectTask.Wait(500) -and $client.Connected
    }
    catch {
        return $false
    }
    finally {
        $client.Dispose()
    }
}

if (Test-ListeningPort $apiPort) {
    Write-Output "Backend is already running on port $apiPort."
}
else {
    $backendProcess = Start-Process `
        -FilePath $backendPython `
        -ArgumentList @("-m", "uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", "$apiPort") `
        -WorkingDirectory $repoRoot `
        -WindowStyle Hidden `
        -RedirectStandardOutput (Join-Path $logRoot "backend-$apiPort.stdout.log") `
        -RedirectStandardError (Join-Path $logRoot "backend-$apiPort.stderr.log") `
        -PassThru

    Write-Output "Started backend on port $apiPort (PID $($backendProcess.Id))."
}

if (Test-ListeningPort $frontendPort) {
    Write-Output "Frontend is already running on port $frontendPort."
}
else {
    $nodeCommand = Get-Command node -ErrorAction SilentlyContinue
    $nodePath = if ($nodeCommand) {
        $nodeCommand.Source
    }
    else {
        Join-Path $env:USERPROFILE ".cache\codex-runtimes\codex-primary-runtime\dependencies\node\bin\node.exe"
    }

    if (-not (Test-Path -LiteralPath $nodePath)) {
        throw "Node.js was not found. Install Node.js or add it to PATH."
    }

    $frontendProcess = Start-Process `
        -FilePath $nodePath `
        -ArgumentList @($viteEntry, "--host", "127.0.0.1", "--port", "$frontendPort", "--strictPort") `
        -WorkingDirectory $frontendRoot `
        -WindowStyle Hidden `
        -RedirectStandardOutput (Join-Path $logRoot "frontend-$frontendPort.stdout.log") `
        -RedirectStandardError (Join-Path $logRoot "frontend-$frontendPort.stderr.log") `
        -PassThru

    Write-Output "Started frontend on port $frontendPort (PID $($frontendProcess.Id))."
}

Write-Output "Open http://localhost:$frontendPort"
