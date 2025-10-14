#!/bin/bash

# Agent Builder Platform - Widget Dev Server Startup Script
# This script ensures the widget dev server starts correctly

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}   Agent Builder Widget Server${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
WIDGET_DIR="${SCRIPT_DIR}"

# Change to widget directory
cd "${WIDGET_DIR}"

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo -e "${RED}✗ node_modules not found${NC}"
    echo -e "${YELLOW}Installing dependencies...${NC}"
    npm install
else
    echo -e "${GREEN}✓ Dependencies found${NC}"
fi

# Clean vite cache
echo -e "${YELLOW}⚙ Cleaning Vite cache...${NC}"
rm -rf node_modules/.vite

# Start the dev server
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}🚀 Starting Widget server on http://localhost:5173${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Run vite with force flag to rebuild dependencies
exec npm run dev -- --force
