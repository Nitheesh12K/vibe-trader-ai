# Windows PowerShell Setup Guide — Vibe Trader AI

Follow these exact steps to run **Vibe Trader AI** on Windows.

## Prerequisites
- **Python 3.10+** (Tested on Python 3.12)
- **Node.js 18+** (Tested on Node v24.11 / npm 11.6)
- **PowerShell 5.1+ or PowerShell 7+**

---

## 1. Backend Setup & Startup

Open a PowerShell terminal in the project root:

```powershell
# Navigate to the backend folder
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# If PowerShell script execution policy blocks activation, run:
# Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Upgrade pip & install dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt

# Start the FastAPI server
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

The backend will be running at:
- **Root**: `http://127.0.0.1:8000/`
- **Health Check**: `http://127.0.0.1:8000/api/health`
- **Demo Market Data**: `http://127.0.0.1:8000/api/market/demo`
- **Interactive OpenAPI Docs**: `http://127.0.0.1:8000/docs`

---

## 2. Frontend Setup & Startup

Open a second PowerShell terminal in the project root:

```powershell
# Navigate to the frontend folder
cd frontend

# Install node dependencies
npm install

# Start Vite development server
npm run dev
```

The frontend dashboard will be running at:
- **Terminal URL**: `http://localhost:5173/`

---

## 3. Running Automated Tests

### Backend Tests (Pytest)
```powershell
cd vibe-trader-ai
.\backend\venv\Scripts\pytest tests/backend/test_api.py -v
```

### Frontend Tests (Vitest)
```powershell
cd vibe-trader-ai\frontend
npm test -- --run
```

---

## 4. Troubleshooting

- **Port Conflict**: If port 8000 is occupied, adjust `PORT` in `.env` and `VITE_API_BASE_URL` in `frontend/.env`.
- **Database Location**: SQLite database is automatically created and stored in `data/vibe_trader.db`.
