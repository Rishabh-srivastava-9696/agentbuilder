#!/bin/bash

# Stop all Agent Builder services

echo "🛑 Stopping Agent Builder Platform..."

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

# Kill processes by PID
if [ -f logs/api.pid ]; then
    API_PID=$(cat logs/api.pid)
    kill $API_PID 2>/dev/null && echo -e "${GREEN}✓ Stopped API (PID: $API_PID)${NC}" || echo -e "${RED}✗ API not running${NC}"
    rm logs/api.pid
fi

if [ -f logs/admin.pid ]; then
    ADMIN_PID=$(cat logs/admin.pid)
    kill $ADMIN_PID 2>/dev/null && echo -e "${GREEN}✓ Stopped Admin Dashboard (PID: $ADMIN_PID)${NC}" || echo -e "${RED}✗ Admin not running${NC}"
    rm logs/admin.pid
fi

if [ -f logs/widget.pid ]; then
    WIDGET_PID=$(cat logs/widget.pid)
    kill $WIDGET_PID 2>/dev/null && echo -e "${GREEN}✓ Stopped Widget (PID: $WIDGET_PID)${NC}" || echo -e "${RED}✗ Widget not running${NC}"
    rm logs/widget.pid
fi

# Also kill by port as backup
lsof -ti:8000 | xargs kill -9 2>/dev/null || true
lsof -ti:3000 | xargs kill -9 2>/dev/null || true
lsof -ti:5173 | xargs kill -9 2>/dev/null || true

echo -e "${GREEN}All services stopped${NC}"
