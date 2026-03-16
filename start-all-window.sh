#!/bin/bash

echo "✅ start-all-window is running"

# Function to kill background processes on exit
cleanup() {
    echo "Stopping all services..."
    kill $(jobs -p)
    exit
}

trap cleanup SIGINT SIGTERM

echo "Starting Agent Builder Platform... (windows version)"

# Function to kill process on a specific port
kill_port() {
    local port=$1
    # Find PID using netstat (Windows command)
    local pid=$(netstat -ano | grep ":$port " | grep "LISTENING" | awk '{print $5}' | head -n 1)
    if [ ! -z "$pid" ]; then
        echo "Killing process on port $port (PID: $pid)..."
        # Use //F and //PID for Git Bash compatibility with Windows taskkill
        taskkill //F //PID $pid 2>/dev/null || echo "Process $pid already terminated."
    fi
}

echo "Cleaning up ports..."
kill_port 8000
kill_port 3000
kill_port 5174
kill_port 3005

# Start API
echo "Starting API Server..."
cd apps/api
# Check if venv exists and activate
if [ -d ".venv" ]; then
    echo "Activating virtual environment (.venv)..."
    if [ -f ".venv/Scripts/activate" ]; then
        source .venv/Scripts/activate
    else
        source .venv/bin/activate
    fi
elif [ -d "venv" ]; then
    echo "Activating virtual environment (venv)..."
    if [ -f "venv/Scripts/activate" ]; then
        source venv/Scripts/activate
    else
        source venv/bin/activate
    fi
fi

# Run API
python run.py &
API_PID=$!
cd ../..

# Wait for API to initialize
sleep 5

# Start Admin
echo "Starting Admin Dashboard..."
cd apps/admin
npm start &
ADMIN_PID=$!
cd ../..

# Start Widget
echo "Starting Widget..."
cd apps/widget
npm run dev &
WIDGET_PID=$!
cd ../..

# Start Shopify MCP
echo "Starting Shopify MCP..."
cd apps/shopify-mcp
npm start &
SHOPIFY_PID=$!
cd ../..

echo "All services started!"
echo "----------------------------------------"
echo "API Server:      http://localhost:8000"
echo "Admin Dashboard: http://localhost:3000"
echo "Widget:          http://localhost:5174"
echo "Shopify MCP:     http://localhost:3005"
echo "----------------------------------------"
echo "Press Ctrl+C to stop all services."

wait
