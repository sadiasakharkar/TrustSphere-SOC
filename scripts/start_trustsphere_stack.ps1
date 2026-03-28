param(
    [switch]$SkipOllama
)

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$FrontendDir = Join-Path $RepoRoot "frontend"
$NextCacheDir = Join-Path $FrontendDir ".next"
$VendorPath = Join-Path $RepoRoot ".vendor"
$BackendUrl = "http://127.0.0.1:8000"
$OllamaUrl = "http://127.0.0.1:11434"

function Write-Step($Message) {
    Write-Host ""
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Test-PortListening($Port) {
    try {
        $connection = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction Stop | Select-Object -First 1
        return $null -ne $connection
    } catch {
        return $false
    }
}

function Test-HttpOk($Url) {
    try {
        $response = Invoke-WebRequest -UseBasicParsing -Uri $Url -TimeoutSec 5 -ErrorAction Stop
        return $response.StatusCode -ge 200 -and $response.StatusCode -lt 400
    } catch {
        return $false
    }
}

function Wait-ForHttpOk($Url, $Label, $Attempts = 10, $DelaySeconds = 2) {
    for ($attempt = 1; $attempt -le $Attempts; $attempt++) {
        if (Test-HttpOk $Url) {
            Write-Host "$Label is healthy at $Url" -ForegroundColor Green
            return $true
        }
        Start-Sleep -Seconds $DelaySeconds
    }
    Write-Host "$Label did not become healthy in time at $Url" -ForegroundColor Yellow
    return $false
}

function Test-OllamaModelInstalled($ModelName) {
    $ollamaCommand = Get-Command ollama -ErrorAction SilentlyContinue
    if ($null -eq $ollamaCommand) {
        return $false
    }

    try {
        $models = & ollama list 2>$null
        return $models -match [regex]::Escape($ModelName)
    } catch {
        return $false
    }
}

function Start-NewPowerShellWindow($Title, $Command) {
    $encodedCommand = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($Command))
    Start-Process powershell -ArgumentList @(
        "-NoExit",
        "-EncodedCommand",
        $encodedCommand
    ) | Out-Null
    Write-Host "Started $Title" -ForegroundColor Green
}

function Ensure-PathExists($PathToCheck, $Label) {
    if (-not (Test-Path $PathToCheck)) {
        throw "$Label not found at: $PathToCheck"
    }
}

Write-Step "Preparing TrustSphere stack launcher"
Ensure-PathExists $RepoRoot "Repo root"
Ensure-PathExists $FrontendDir "Frontend directory"
Ensure-PathExists $VendorPath "Local Python dependency folder (.vendor)"

if (-not $SkipOllama) {
    Write-Step "Checking Ollama"
    if (Test-PortListening 11434) {
        Write-Host "Ollama already appears to be running on port 11434." -ForegroundColor Yellow
    } else {
        $ollamaCommand = Get-Command ollama -ErrorAction SilentlyContinue
        if ($null -eq $ollamaCommand) {
            Write-Host "Ollama CLI not found. Backend and frontend will still start, but playbook generation may use fallback output." -ForegroundColor Yellow
            Write-Host "Install Ollama from https://ollama.com/download and pull the configured model with: ollama pull tinyllama:latest" -ForegroundColor Yellow
        } else {
            $ollamaScript = @"
Set-Location '$RepoRoot'
Write-Host 'Starting Ollama server on $OllamaUrl' -ForegroundColor Cyan
ollama serve
"@
            Start-NewPowerShellWindow "Ollama" $ollamaScript
            Start-Sleep -Seconds 3
        }
    }
}

Write-Step "Starting backend API"
if (Test-HttpOk "$BackendUrl/health") {
    Write-Host "Backend is already healthy on port 8000." -ForegroundColor Yellow
} elseif (Test-PortListening 8000) {
    Write-Host "Backend port 8000 is busy, waiting for health check..." -ForegroundColor Yellow
    Wait-ForHttpOk "$BackendUrl/health" "Backend" | Out-Null
} else {
    $backendScript = @"
Set-Location '$RepoRoot'
\$env:PYTHONPATH = '$VendorPath'
Write-Host 'Starting TrustSphere backend on $BackendUrl' -ForegroundColor Cyan
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
"@
    Start-NewPowerShellWindow "Backend" $backendScript
    Wait-ForHttpOk "$BackendUrl/health" "Backend" | Out-Null
}

Write-Step "Starting frontend app"
if (Test-HttpOk "http://127.0.0.1:3000") {
    Write-Host "Frontend is already responding on port 3000." -ForegroundColor Yellow
} elseif (Test-PortListening 3000) {
    Write-Host "Frontend port 3000 is busy, waiting for HTTP response..." -ForegroundColor Yellow
    Wait-ForHttpOk "http://127.0.0.1:3000" "Frontend" | Out-Null
} else {
    $frontendScript = @"
Set-Location '$FrontendDir'
\$env:TRUSTSPHERE_BACKEND_URL = '$BackendUrl'
if (-not (Test-Path 'node_modules')) {
    Write-Host 'Installing frontend dependencies...' -ForegroundColor Cyan
    npm install
}
if (Test-Path '$NextCacheDir') {
    Write-Host 'Clearing stale Next.js cache...' -ForegroundColor DarkCyan
    Remove-Item -LiteralPath '$NextCacheDir' -Recurse -Force -ErrorAction SilentlyContinue
}
Write-Host 'Starting TrustSphere frontend on http://127.0.0.1:3000' -ForegroundColor Cyan
npm run dev
"@
    Start-NewPowerShellWindow "Frontend" $frontendScript
}

Write-Step "Run summary"
Write-Host "Frontend: http://127.0.0.1:3000" -ForegroundColor Green
Write-Host "Backend health: $BackendUrl/health" -ForegroundColor Green
Write-Host "Ollama endpoint: $OllamaUrl" -ForegroundColor Green
Write-Host ""
if (-not $SkipOllama) {
    if (Test-OllamaModelInstalled "tinyllama:latest") {
        Write-Host "Ollama model ready: tinyllama:latest" -ForegroundColor Green
    } else {
        Write-Host "If playbook generation needs the configured local model, run this once:" -ForegroundColor Yellow
        Write-Host "ollama pull tinyllama:latest" -ForegroundColor Yellow
    }
}
