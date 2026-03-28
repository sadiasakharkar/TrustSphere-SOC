# TrustSphere Run Commands

## One-step launcher

From the repo root:

```powershell
powershell -ExecutionPolicy Bypass -File .\RUN_TRUSTSPHERE.ps1
```

This starts:

- Ollama on `http://127.0.0.1:11434` if available
- Backend API on `http://127.0.0.1:8000`
- Frontend on `http://127.0.0.1:3000`

## Manual commands

### 1. Start Ollama

```powershell
ollama serve
```

If the configured model has not been downloaded yet:

```powershell
ollama pull tinyllama:latest
```

### 2. Start the backend

Run from the repo root:

```powershell
$env:PYTHONPATH="E:\Barclays\TrustSphere-SOC\.vendor"
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

### 3. Start the frontend

Run from `frontend`:

```powershell
$env:TRUSTSPHERE_BACKEND_URL="http://127.0.0.1:8000"
npm run dev
```

## Quick checks

Backend health:

```powershell
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8000/health
```

Frontend:

Open:

```text
http://127.0.0.1:3000
```
