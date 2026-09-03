#!/bin/bash

echo "🚀 Starting TIDE-HF Phase 2 System"
echo "===================================="
echo ""

# Check if backend dependencies are installed
if [ ! -d "backend/venv" ]; then
    echo "⚠️  Backend dependencies not found. Installing..."
    cd backend
    python3.12 -m venv venv 2>/dev/null || python3.11 -m venv venv 2>/dev/null || python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    cd ..
fi

# Check if frontend dependencies are installed
if [ ! -d "frontend/node_modules" ]; then
    echo "⚠️  Frontend dependencies not found. Installing..."
    cd frontend
    npm install
    cd ..
fi

echo ""
echo "✅ Dependencies ready"
echo ""

# Start backend
echo "🔧 Starting Backend..."
cd backend
source venv/bin/activate
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > /tmp/backend.log 2>&1 &
BACKEND_PID=$!
cd ..
echo "   Backend PID: $BACKEND_PID"
echo "   URL: http://localhost:8000"
echo "   Logs: /tmp/backend.log"

# Wait for backend to start
sleep 3

# Start frontend
echo ""
echo "🎨 Starting Frontend..."
cd frontend
npm run dev > /tmp/frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..
echo "   Frontend PID: $FRONTEND_PID"
echo "   URL: http://localhost:3000"
echo "   Logs: /tmp/frontend.log"

echo ""
echo "===================================="
echo "✅ System Started!"
echo "===================================="
echo ""
echo "🌐 Access the application:"
echo "   Frontend: http://localhost:3000"
echo "   Backend API: http://localhost:8000"
echo "   API Docs: http://localhost:8000/api/docs"
echo ""
echo "🔑 Test Account:"
echo "   Email: doctor@example.com"
echo "   Password: SecurePass123!"
echo ""
echo "📋 To stop the system:"
echo "   kill $BACKEND_PID $FRONTEND_PID"
echo ""
echo "📊 View logs:"
echo "   Backend: tail -f /tmp/backend.log"
echo "   Frontend: tail -f /tmp/frontend.log"
echo ""

# Save PIDs to file
echo "$BACKEND_PID $FRONTEND_PID" > .system_pids

