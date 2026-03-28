param(
    [switch]$SkipOllama
)

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$FrontendDir = Join-Path $RepoRoot "frontend"
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
if (Test-PortListening 8000) {
    Write-Host "Backend already appears to be running on port 8000." -ForegroundColor Yellow
} else {
    $backendScript = @"
Set-Location '$RepoRoot'
\$env:PYTHONPATH = '$VendorPath'
Write-Host 'Starting TrustSphere backend on $BackendUrl' -ForegroundColor Cyan
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
"@
    Start-NewPowerShellWindow "Backend" $backendScript
    Start-Sleep -Seconds 3
}

Write-Step "Starting frontend app"
if (Test-PortListening 3000) {
    Write-Host "Frontend already appears to be running on port 3000." -ForegroundColor Yellow
} else {
    $frontendScript = @"
Set-Location '$FrontendDir'
\$env:TRUSTSPHERE_BACKEND_URL = '$BackendUrl'
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
Write-Host "If playbook generation needs the configured local model, make sure this succeeds at least once:" -ForegroundColor Yellow
Write-Host "ollama pull tinyllama:latest" -ForegroundColor Yellow
