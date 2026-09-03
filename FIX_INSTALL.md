# 🔧 Fix Installation Error

## Error: pg_config executable not found

This error occurs because `psycopg2-binary` requires PostgreSQL development files, but Python 3.14 is too new and doesn't have pre-built wheels.

## ✅ Solution

I've already updated the code to use `psycopg` (the modern version) instead. Now follow these steps:

### Step 1: Remove old virtual environment
```bash
cd /Users/ramaseshu/Documents/CDA650_Project/TIDE-HF_Phase-2/backend
rm -rf venv
```

### Step 2: Create new virtual environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

This should work now! The new `psycopg` library doesn't require PostgreSQL to be installed on your system.

---

## Alternative: Use Docker

If you still have issues, use Docker instead:

```bash
cd /Users/ramaseshu/Documents/CDA650_Project/TIDE-HF_Phase-2
docker-compose up -d
```

This will start everything (database + backend + frontend) without any installation issues.

---

## Quick Test

Once installed, test the backend:

```bash
# Terminal 1 - Backend
cd backend
source venv/bin/activate
python -m uvicorn app.main:app --reload
```

Visit: http://localhost:8000/api/health

You should see: `{"status":"healthy","database":"connected","api":"operational"}`

---

## Next: Install Frontend

```bash
# Terminal 2 - Frontend
cd frontend
npm install
npm run dev
```

Visit: http://localhost:3000

---

**That's it! Your system should be running now. 🎉**
