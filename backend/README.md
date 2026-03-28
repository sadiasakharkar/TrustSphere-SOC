# TrustSphere Backend API

FastAPI backend for the TrustSphere SOC frontend and pipeline.

## What It Covers

- Demo-safe login with server-side session invalidation on logout
- Upload validation for `.json` and `.csv`
- Canonical normalization using the existing ingestion pipeline
- Rule-backed explainability labels per event
- Incident clustering and prioritization
- Explanation, terminal, monitoring summary, and playbook endpoints
- No database yet: session and upload metadata live in memory, while uploaded files are staged under `runtime/uploads`

## Run Locally

```bash
pip install -e .
uvicorn backend.main:app --reload
```

## Important Security Notes

- For local development, cookies default to non-`Secure` so the app can run on `http://localhost`
- In production, enable HTTPS/TLS and set:
  - `TRUSTSPHERE_ENFORCE_HTTPS=true`
  - `TRUSTSPHERE_SECURE_COOKIES=true`
- Logout clears the auth cookie and invalidates the session server-side
