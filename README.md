# Authentication Core Sprints

Foundational backend app built with FastAPI.

## Set up the virtual environment

First, create the virtual environment:
```bash
python3 -m venv .venv
```

Next, activate the environment based on your operating system:

**Linux / macOS:**
```bash
source .venv/bin/activate
```

**Windows (Command Prompt):**
```cmd
.venv\Scripts\activate.bat
```

**Windows (PowerShell):**
```powershell
.venv\Scripts\Activate.ps1
```

## How to run the app

Make sure your virtual environment is active, install the packages, and start the server:

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

Once running, the home page is live at http://127.0.0.1:8000 and the health check endpoint is at http://127.0.0.1:8000/health

## How to run tests

To run the automated test suite in-memory:

```bash
pytest
```

## ⚠️ Integration Testing Warning
The test suite executed via `pytest` is an active integration test suite that communicates directly with the cloud database configured inside your local `.env` file. 

* Running the tests requires active internet access and valid Supabase API keys.
* The test harness executes selective target deletions against specified test accounts (e.g., `eoihd@gmai.com`) before each run. Ensure your `.env` configuration points to a dedicated testing or development database environment, **never a live production project store.**

