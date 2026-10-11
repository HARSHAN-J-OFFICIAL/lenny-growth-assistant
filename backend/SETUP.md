# Backend Setup & Execution Guide (Windows PowerShell)

This document provides the exact, canonical Windows PowerShell commands for creating the Python 3.12 virtual environment, installing dependencies, executing the test suite, and launching the development server.

All backend commands must be run from the `backend/` directory so that Python recognizes `app` as the top-level application package.

---

## Prerequisites
- **Python 3.12 (64-bit)** (executable via `py -3.12` or `python`)
- Windows PowerShell 5.1+ or PowerShell 7+

---

## 1. Navigate to the Backend Directory
Open Windows PowerShell and ensure your working directory is `backend/`:

```powershell
Set-Location -Path "backend"
```

---

## 2. Create the Python 3.12 Virtual Environment
Provision an isolated `.venv` directory inside `backend/`:

```powershell
py -3.12 -m venv .venv
```

---

## 3. Activate the Virtual Environment
Activate the newly created virtual environment:

```powershell
.\.venv\Scripts\Activate.ps1
```

*(If PowerShell displays an `ExecutionPolicy` error, run: `Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned` and re-run the activation command).*

---

## 4. Upgrade Pip and Install Pinned Dependencies
Install all pinned dependencies:

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

---

## 5. Configure Environment Variables
Copy `.env.example` to create your active `.env`:

```powershell
Copy-Item .env.example .env
```

---

## 6. Run the Automated Test Suite
From the `backend/` directory, run the canonical pytest module invocation:

```powershell
python -m pytest -v
```

Expected output:
```text
tests/test_health.py::test_health_endpoint_success PASSED
tests/test_health.py::test_root_ping_endpoint PASSED
tests/test_errors.py::test_404_not_found_structured_format PASSED
tests/test_errors.py::test_405_method_not_allowed_format PASSED
==== 4 passed in 0.xx s ====
```

---

## 7. Start the FastAPI Development Server
From the `backend/` directory, launch Uvicorn using Python's module runner:

```powershell
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

---

## 8. Verification & Interactive Documentation
Once the server is running, open a browser or another PowerShell window to verify:

- **Interactive Swagger Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc Documentation**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- **Health Check Probe**:
  ```powershell
  Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/health"
  ```
  Expected JSON:
  ```json
  {
    "status": "ok",
    "version": "0.1.0",
    "timestamp": "2026-10-10T16:35:00.000000+00:00",
    "environment": "development"
  }
  ```
