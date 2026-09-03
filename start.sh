#!/bin/bash

# QAS AI Medical System - Quick Start Script
# This script starts both backend and frontend in separate terminals

set -e

echo "🏥 Starting QAS AI Medical System..."
echo ""

# Check if running on macOS
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS - use Terminal app
    echo "Opening backend in new terminal..."
    osascript <<EOF
tell application "Terminal"
    do script "cd '$PWD/backend' && source venv/bin/activate && python -m uvicorn app.main:app --reload"
end tell
EOF

    sleep 2

    echo "Opening frontend in new terminal..."
    osascript <<EOF
tell application "Terminal"
    do script "cd '$PWD/frontend' && npm run dev"
end tell
EOF

    echo "✅ Both servers starting in separate terminals!"
    echo ""
    echo "Frontend: http://localhost:3000"
    echo "Backend API: http://localhost:8000"
    echo "API Docs: http://localhost:8000/api/docs"

else
    # Linux/Windows - use gnome-terminal or start in background
    if command -v gnome-terminal &> /dev/null; then
        gnome-terminal -- bash -c "cd '$PWD/backend' && source venv/bin/activate && python -m uvicorn app.main:app --reload; exec bash"
        gnome-terminal -- bash -c "cd '$PWD/frontend' && npm run dev; exec bash"
        echo "✅ Both servers starting in separate terminals!"
    else
        echo "Starting backend..."
        cd backend
        source venv/bin/activate
        python -m uvicorn app.main:app --reload &
        BACKEND_PID=$!

        echo "Starting frontend..."
        cd ../frontend
        npm run dev &
        FRONTEND_PID=$!

        echo ""
        echo "✅ Servers started!"
        echo "Backend PID: $BACKEND_PID"
        echo "Frontend PID: $FRONTEND_PID"
        echo ""
        echo "To stop servers:"
        echo "  kill $BACKEND_PID $FRONTEND_PID"
    fi

    echo ""
    echo "Frontend: http://localhost:3000"
    echo "Backend API: http://localhost:8000"
    echo "API Docs: http://localhost:8000/api/docs"
fi
