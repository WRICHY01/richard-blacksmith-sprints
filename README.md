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
