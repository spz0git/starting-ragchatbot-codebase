# Quality Tools Integration Guide

This guide explains how to integrate code quality tools into your development workflow.

## Overview

The project now includes:
- **Frontend code quality tools** - ESLint, Prettier, Stylelint
- **Quality check scripts** - Automated validation
- **Development scripts** - Easy-to-use npm commands

## Quick Start

```bash
# Install once
npm install

# Before every commit
npm run format
npm run check-quality
```

## Files Added

### Configuration Files
- `.prettierrc.json` - Prettier configuration
- `.eslintrc.json` - ESLint configuration
- `.stylelintrc.json` - Stylelint configuration
- `.prettierignore` - Files to exclude from formatting
- `.eslintignore` - Files to exclude from linting

### Development Scripts
- `format-frontend.sh` - Auto-format frontend code
- `check-frontend-quality.sh` - Run quality checks
- `package.json` - NPM scripts and dependencies

### Documentation
- `FRONTEND_QUALITY_GUIDE.md` - Comprehensive quality standards
- `FRONTEND_SETUP.md` - Quick setup guide
- `QUALITY_INTEGRATION.md` - This file

## Workflow Integration

### Option 1: Manual Pre-commit Check

```bash
# Before committing
npm run format          # Auto-format code
npm run check-quality   # Verify quality

# If checks pass
git add .
git commit -m "Your message"
```

### Option 2: Enhanced run.sh (Recommended)

Update `run.sh` to check frontend quality:

```bash
#!/bin/bash

mkdir -p docs

if [ ! -d "backend" ]; then
    echo "Error: backend directory not found"
    exit 1
fi

echo "Starting Course Materials RAG System..."

# Check frontend quality (optional - remove line to skip)
echo "Checking frontend code quality..."
./check-frontend-quality.sh || echo "⚠️  Quality check had warnings (continuing)"

echo "Make sure you have set your ANTHROPIC_API_KEY in .env"

cd backend && uv run uvicorn app:app --reload --port 8000
```

### Option 3: Git Hooks (Advanced)

Create `.git/hooks/pre-commit` for automatic checks before commit:

```bash
#!/bin/bash

# Run frontend quality checks
npm run quality

if [ $? -ne 0 ]; then
  echo "❌ Quality checks failed. Commit aborted."
  echo "Run 'npm run format' to fix issues."
  exit 1
fi

exit 0
```

Enable:
```bash
chmod +x .git/hooks/pre-commit
```

### Option 4: CI/CD Integration

Add GitHub Actions workflow (`.github/workflows/frontend-quality.yml`):

```yaml
name: Frontend Quality Checks

on:
  push:
    branches: [main, quality_feature]
    paths:
      - 'frontend/**'
      - '.eslintrc.json'
      - '.prettierrc.json'
  pull_request:
    branches: [main, quality_feature]
    paths:
      - 'frontend/**'

jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - uses: actions/setup-node@v3
        with:
          node-version: '18'

      - name: Install dependencies
        run: npm install

      - name: Run ESLint
        run: npm run lint

      - name: Check Prettier formatting
        run: npm run format:check

      - name: Run Stylelint
        run: npm run stylelint
```

## Python Backend Quality Tools

For backend Python code quality (separate from frontend):

```bash
# Optional: Add to pyproject.toml for Python code
uv add --group dev black flake8 mypy

# Format Python code
uv run black backend/

# Lint Python code
uv run flake8 backend/
```

## Development Tips

### Format on Save (IDE Integration)

**VS Code:**
1. Install "Prettier - Code formatter" extension
2. Install "ESLint" extension
3. Settings → Format On Save ✓

**WebStorm/PhpStorm:**
1. Settings → Languages & Frameworks → Prettier → Enable
2. Settings → Languages & Frameworks → ESLint → Enable

### Combining Format and Check

Create a combined quality script:

```bash
#!/bin/bash
npm run format
npm run check-quality
```

### Ignore Specific Issues

To allow exceptions (use sparingly):

**ESLint:**
```javascript
// eslint-disable-next-line rule-name
const intentionallyUnused = value;
```

**Prettier:**
```html
<!-- prettier-ignore -->
<div>  weird   spacing  </div>
```

## Commands Reference

### NPM Scripts

```bash
npm run format              # Auto-format all frontend code
npm run lint                # Run ESLint
npm run lint:fix            # Auto-fix ESLint issues
npm run check-quality       # Run all quality checks
npm run format:check        # Check if formatting is needed
npm run format:write        # Write formatting changes
npm run quality             # Run lint + format:check
```

### Shell Scripts

```bash
./format-frontend.sh        # Format frontend code
./check-frontend-quality.sh # Check code quality
```

## Troubleshooting

### Node.js not installed

```bash
# Check installation
node --version

# Install from https://nodejs.org/
```

### npm install errors

```bash
npm cache clean --force
npm install
```

### Scripts not executable

```bash
chmod +x format-frontend.sh check-frontend-quality.sh
```

### ESLint/Prettier conflicts

The configurations are designed to work together. If conflicts occur:

1. Run `npm run format` first (Prettier)
2. Then `npm run lint:fix` (ESLint)

## Updating Tools

To update ESLint, Prettier, or Stylelint:

```bash
npm update eslint prettier stylelint

# Or update to latest
npm install --save-dev eslint@latest prettier@latest stylelint@latest
```

## Standards Documentation

See `FRONTEND_QUALITY_GUIDE.md` for:
- JavaScript style standards
- CSS conventions
- Code style examples
- Common issues and fixes
- Pre-commit workflow
- IDE setup instructions

## Questions?

1. Check `FRONTEND_QUALITY_GUIDE.md` for detailed standards
2. Check `FRONTEND_SETUP.md` for quick setup
3. Review tool documentation:
   - [ESLint Docs](https://eslint.org/docs/)
   - [Prettier Docs](https://prettier.io/docs/)
   - [Stylelint Docs](https://stylelint.io/)
