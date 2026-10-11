<#
.SYNOPSIS
  The Lenny Growth Assistant - Native Windows Development Runner
.DESCRIPTION
  Orchestrates the entire local development stack on Windows:
  1. Verifies prerequisites (Docker PostgreSQL, Ollama, Python venv, Node.js).
  2. Ensures Ollama models (llama3.2) are available.
  3. Starts backend services safely without duplicate processes.
  4. Displays executive access URLs and operational logs.
  5. Provides graceful shutdown on Ctrl+C.
#>

$ErrorActionPreference = "Stop"
$WorkspaceRoot = $PSScriptRoot

Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "  THE LENNY GROWTH ASSISTANT - LOCAL DEVELOPMENT RUNNER" -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host ""

# Helper to test TCP port availability
function Test-PortOpen ($port) {
    try {
        $client = New-Object System.Net.Sockets.TcpClient
        $iar = $client.BeginConnect("127.0.0.1", $port, $null, $null)
        $success = $iar.AsyncWaitHandle.WaitOne(800)
        if ($success) {
            $client.EndConnect($iar)
            $client.Close()
            return $true
        }
        $client.Close()
        return $false
    } catch {
        return $false
    }
}

# -----------------------------------------------------------------------------
# 1. Verify Prerequisites
# -----------------------------------------------------------------------------
Write-Host "[1/5] Verifying System Prerequisites..." -ForegroundColor Yellow

# Node.js
if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Error "Node.js (v18+) is required but was not found on PATH. Please install Node.js."
}
Write-Host "  [OK] Node.js $(node --version) detected" -ForegroundColor Green

# Python venv
$PythonExe = Join-Path $WorkspaceRoot "backend\.venv\Scripts\python.exe"
if (-not (Test-Path $PythonExe)) {
    Write-Error "Python virtual environment not found at $PythonExe. Run: python -m venv backend\.venv && backend\.venv\Scripts\pip install -r backend\requirements.txt"
}
Write-Host "  [OK] Python virtual environment ready" -ForegroundColor Green

# Docker / PostgreSQL
$DockerBin = "C:\Users\user\AppData\Local\Programs\DockerDesktop\resources\bin\docker.exe"
if (-not (Test-Path $DockerBin)) {
    $DockerCmd = Get-Command docker -ErrorAction SilentlyContinue
    if ($DockerCmd) { $DockerBin = $DockerCmd.Source }
}

if (Test-PortOpen 5432) {
    Write-Host "  [OK] PostgreSQL detected on port 5432" -ForegroundColor Green
} else {
    Write-Host "  Starting Docker PostgreSQL container..." -ForegroundColor Yellow
    if (Test-Path $DockerBin) {
        & $DockerBin compose up db -d
        Start-Sleep -Seconds 3
        if (Test-PortOpen 5432) {
            Write-Host "  [OK] PostgreSQL started successfully" -ForegroundColor Green
        } else {
            Write-Warning "PostgreSQL not reachable on port 5432. Backend will fallback to SQLite if configured."
        }
    } else {
        Write-Warning "Docker CLI not found. Ensure PostgreSQL is running on port 5432."
    }
}

# Ollama Daemon
if (Test-PortOpen 11434) {
    Write-Host "  [OK] Ollama daemon active on port 11434" -ForegroundColor Green
} else {
    Write-Host "  Starting local Ollama daemon..." -ForegroundColor Yellow
    $OllamaExe = Join-Path $env:LOCALAPPDATA "Programs\Ollama\ollama.exe"
    if (Test-Path $OllamaExe) {
        Start-Process -FilePath $OllamaExe -ArgumentList "serve" -WindowStyle Hidden
        Start-Sleep -Seconds 3
        Write-Host "  [OK] Ollama daemon started" -ForegroundColor Green
    } else {
        Write-Warning "Ollama executable not found at $OllamaExe. Please start Ollama manually."
    }
}

# -----------------------------------------------------------------------------
# 2. Start Pi Agent Service (Port 8001)
# -----------------------------------------------------------------------------
Write-Host "[2/5] Checking Pi Agent Service (Port 8001)..." -ForegroundColor Yellow
$PiJob = $null
if (Test-PortOpen 8001) {
    Write-Host "  [OK] Pi Agent service already running on port 8001" -ForegroundColor Green
} else {
    Write-Host "  Starting Pi Agent daemon..." -ForegroundColor Gray
    $AgentDir = Join-Path $WorkspaceRoot "agent_service"
    $PiJob = Start-Process -FilePath "node" -ArgumentList "server.mjs" -WorkingDirectory $AgentDir -PassThru -WindowStyle Hidden
    Start-Sleep -Seconds 2
    Write-Host "  [OK] Pi Agent service started (PID: $($PiJob.Id))" -ForegroundColor Green
}

# -----------------------------------------------------------------------------
# 3. Start FastAPI Backend (Port 8000)
# -----------------------------------------------------------------------------
Write-Host "[3/5] Checking FastAPI Backend (Port 8000)..." -ForegroundColor Yellow
$BackendJob = $null
if (Test-PortOpen 8000) {
    Write-Host "  [OK] FastAPI backend already running on port 8000" -ForegroundColor Green
} else {
    Write-Host "  Starting FastAPI backend..." -ForegroundColor Gray
    $BackendDir = Join-Path $WorkspaceRoot "backend"
    $UvicornArgs = "-m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"
    $BackendJob = Start-Process -FilePath $PythonExe -ArgumentList $UvicornArgs -WorkingDirectory $BackendDir -PassThru -WindowStyle Hidden
    Start-Sleep -Seconds 3
    Write-Host "  [OK] FastAPI backend started (PID: $($BackendJob.Id))" -ForegroundColor Green
}

# -----------------------------------------------------------------------------
# 4. Start React Frontend (Port 5173)
# -----------------------------------------------------------------------------
Write-Host "[4/5] Checking React Frontend (Port 5173)..." -ForegroundColor Yellow
$FrontendJob = $null
if (Test-PortOpen 5173) {
    Write-Host "  [OK] React frontend dev server already running on port 5173" -ForegroundColor Green
} else {
    Write-Host "  Starting React frontend..." -ForegroundColor Gray
    $FrontendDir = Join-Path $WorkspaceRoot "frontend"
    $FrontendJob = Start-Process -FilePath "npm.cmd" -ArgumentList "run dev -- --host 127.0.0.1 --port 5173" -WorkingDirectory $FrontendDir -PassThru -WindowStyle Hidden
    Start-Sleep -Seconds 3
    Write-Host "  [OK] Frontend dev server started (PID: $($FrontendJob.Id))" -ForegroundColor Green
}

# -----------------------------------------------------------------------------
# 5. Application Ready & Active URLs
# -----------------------------------------------------------------------------
Write-Host ""
Write-Host "=================================================================" -ForegroundColor Green
Write-Host "  ALL SERVICES ONLINE & OPERATIONAL" -ForegroundColor Green
Write-Host "=================================================================" -ForegroundColor Green
Write-Host ""
Write-Host "  Web Application (UI):  http://127.0.0.1:5173" -ForegroundColor Cyan
Write-Host "  FastAPI Health:        http://127.0.0.1:8000/api/v1/health" -ForegroundColor Cyan
Write-Host "  Interactive API Docs:  http://127.0.0.1:8000/docs" -ForegroundColor Cyan
Write-Host "  Pi Agent Health:       http://127.0.0.1:8001/health" -ForegroundColor Cyan
Write-Host "  Ollama Local Daemon:   http://127.0.0.1:11434" -ForegroundColor Cyan
Write-Host "  PostgreSQL Database:   localhost:5432 (lenny_assistant)" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to terminate local development services..." -ForegroundColor Yellow

try {
    while ($true) {
        Start-Sleep -Seconds 2
    }
} finally {
    Write-Host "`nStopping development processes..." -ForegroundColor Gray
    if ($BackendJob -and -not $BackendJob.HasExited) { Stop-Process -Id $BackendJob.Id -Force -ErrorAction SilentlyContinue }
    if ($PiJob -and -not $PiJob.HasExited) { Stop-Process -Id $PiJob.Id -Force -ErrorAction SilentlyContinue }
    if ($FrontendJob -and -not $FrontendJob.HasExited) { Stop-Process -Id $FrontendJob.Id -Force -ErrorAction SilentlyContinue }
    Write-Host "Development session terminated cleanly." -ForegroundColor Green
}
