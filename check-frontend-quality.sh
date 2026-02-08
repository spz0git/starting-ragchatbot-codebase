#!/bin/bash

# Frontend Quality Check Script
# Runs linting and formatting checks on frontend code

set -e

echo "🔍 Frontend Code Quality Checker"
echo "================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

FAILED=0

# Check if Node.js and npm are installed
if ! command -v node &> /dev/null; then
    echo -e "${YELLOW}⚠️  Node.js is not installed. Some checks will be skipped.${NC}"
    echo "   Install Node.js from https://nodejs.org/"
    echo ""
fi

# Check if ESLint is installed
if command -v npx &> /dev/null && command -v eslint &> /dev/null; then
    echo "📋 Running ESLint..."
    if eslint frontend/ --format=compact || eslint frontend/ --fix --format=compact; then
        echo -e "${GREEN}✓ ESLint passed${NC}"
    else
        echo -e "${RED}✗ ESLint found issues (some auto-fixed)${NC}"
        FAILED=$((FAILED + 1))
    fi
    echo ""
else
    echo -e "${YELLOW}⚠️  ESLint not found. Install with: npm install --global eslint${NC}"
    echo ""
fi

# Check if Prettier is installed
if command -v prettier &> /dev/null; then
    echo "🎨 Checking code formatting with Prettier..."
    if prettier --check frontend/ 2>/dev/null; then
        echo -e "${GREEN}✓ Prettier formatting check passed${NC}"
    else
        echo -e "${YELLOW}⚠️  Prettier found formatting issues${NC}"
        echo "   Run 'prettier --write frontend/' to auto-fix"
        FAILED=$((FAILED + 1))
    fi
    echo ""
else
    echo -e "${YELLOW}⚠️  Prettier not found. Install with: npm install --global prettier${NC}"
    echo ""
fi

# Check CSS with stylelint if available
if command -v stylelint &> /dev/null; then
    echo "🎨 Checking CSS with stylelint..."
    if stylelint 'frontend/**/*.css' --fix; then
        echo -e "${GREEN}✓ Stylelint passed${NC}"
    else
        echo -e "${YELLOW}⚠️  Stylelint found CSS issues${NC}"
        FAILED=$((FAILED + 1))
    fi
    echo ""
else
    echo -e "${YELLOW}⚠️  stylelint not found. Install with: npm install --global stylelint stylelint-config-standard${NC}"
    echo ""
fi

# Summary
echo "================================"
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All frontend quality checks passed!${NC}"
    exit 0
else
    echo -e "${RED}✗ $FAILED quality check(s) failed or had warnings${NC}"
    exit 1
fi
