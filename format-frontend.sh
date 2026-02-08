#!/bin/bash

# Frontend Code Formatter Script
# Automatically formats JavaScript, CSS, and HTML files

set -e

echo "🎨 Frontend Code Formatter"
echo "=========================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Prettier is installed
if ! command -v prettier &> /dev/null; then
    echo -e "${YELLOW}⚠️  Prettier not found. Installing globally...${NC}"
    npm install --global prettier
fi

# Check if ESLint is installed with auto-fix capability
if command -v eslint &> /dev/null; then
    echo "📝 Auto-fixing JavaScript with ESLint..."
    eslint frontend/ --fix --format=compact || true
    echo -e "${GREEN}✓ ESLint auto-fix complete${NC}"
    echo ""
fi

# Format with Prettier
echo "✨ Formatting code with Prettier..."
prettier --write frontend/ --log-level warn

echo ""
echo -e "${GREEN}✓ Frontend code formatting complete!${NC}"
echo ""
echo "Formatted files in frontend/ directory:"
find frontend -type f \( -name "*.js" -o -name "*.css" -o -name "*.html" \) | sort
