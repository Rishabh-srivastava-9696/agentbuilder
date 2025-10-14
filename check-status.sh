#!/bin/bash

# Agent Builder Platform - System Status Check

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}   Agent Builder Platform - Status${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Check API Server (Port 8000)
if lsof -i :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${GREEN}✓ API Server${NC} - Running on http://localhost:8000"
    echo -e "  📡 API Docs: http://localhost:8000/docs"
    echo -e "  📊 Health: http://localhost:8000/health"
else
    echo -e "${RED}✗ API Server${NC} - Not running"
    echo -e "  Start with: ${YELLOW}cd apps/api && ./start.sh${NC}"
fi

echo ""

# Check Admin Dashboard (Port 3000)
if lsof -i :3000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${GREEN}✓ Admin Dashboard${NC} - Running on http://localhost:3000"
else
    echo -e "${RED}✗ Admin Dashboard${NC} - Not running"
    echo -e "  Start with: ${YELLOW}cd apps/admin && npm start${NC}"
fi

echo ""

# Check Widget (Port 5173)
if lsof -i :5173 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "${GREEN}✓ Widget Server${NC} - Running on http://localhost:5173"
else
    echo -e "${RED}✗ Widget Server${NC} - Not running"
    echo -e "  Start with: ${YELLOW}cd apps/widget && ./start.sh${NC}"
fi

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
