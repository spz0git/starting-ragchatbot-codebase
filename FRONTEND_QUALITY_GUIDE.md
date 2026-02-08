# Frontend Code Quality Guide

This document describes the code quality tools and standards for frontend development in this project.

## Overview

The frontend code quality workflow includes:
- **ESLint** - JavaScript linting and code quality
- **Prettier** - Automatic code formatting for JavaScript, CSS, and HTML
- **Stylelint** - CSS linting and consistency
- **Quality check scripts** - Automated quality assurance

## Setup

### Prerequisites

Ensure you have Node.js and npm installed:

```bash
# Check Node.js installation
node --version
npm --version
```

Install from https://nodejs.org/ if needed.

### Installation

Install frontend development dependencies:

```bash
npm install
```

This installs ESLint, Prettier, and Stylelint based on `package.json`.

## Available Commands

### Format Code

Automatically format all frontend code:

```bash
npm run format
# or
./format-frontend.sh
```

This runs:
- ESLint auto-fix on JavaScript files
- Prettier formatting on JS, CSS, and HTML files

### Check Code Quality

Run quality checks without modifying files:

```bash
npm run check-quality
# or
./check-frontend-quality.sh
```

This runs:
- ESLint linting
- Prettier formatting check
- Stylelint CSS validation

### Individual Commands

```bash
# JavaScript linting
npm run lint

# Auto-fix JavaScript issues
npm run lint:fix

# Check formatting
npm run format:check

# Auto-format code
npm run format:write

# Check CSS
npm run stylelint
```

## Configuration Files

### `.prettierrc.json`
Prettier configuration for consistent formatting:
- Print width: 100 characters
- Tab width: 2 spaces
- Single quotes
- Trailing commas in ES5
- Line feed endings

### `.eslintrc.json`
ESLint configuration for JavaScript quality:
- Browser environment with ES2021 features
- ESLint recommended rules
- Custom rules for consistency:
  - Prefer `const` and `let` over `var`
  - Strict equality (`===`)
  - 2-space indentation
  - Semicolons required
  - Single quotes

### `.stylelintrc.json`
Stylelint configuration for CSS quality:
- Standard rules extended
- Consistent formatting
- Vendor prefix validation

### `.prettierignore` and `.eslintignore`
Files and directories to exclude from formatting and linting:
- Backend Python files
- Node modules
- Virtual environments
- Git directories

## Code Style Standards

### JavaScript

1. **Use `const` and `let`**
   ```javascript
   // ✅ Good
   const API_URL = '/api';
   let sessionId = null;

   // ❌ Avoid
   var API_URL = '/api';
   ```

2. **Use strict equality**
   ```javascript
   // ✅ Good
   if (value === null) { }

   // ❌ Avoid
   if (value == null) { }
   ```

3. **Use single quotes**
   ```javascript
   // ✅ Good
   const message = 'Hello, World!';

   // ❌ Avoid
   const message = "Hello, World!";
   ```

4. **Meaningful variable names**
   ```javascript
   // ✅ Good
   const chatMessages = document.getElementById('chatMessages');

   // ❌ Avoid
   const c = document.getElementById('chatMessages');
   ```

5. **Add semicolons**
   ```javascript
   // ✅ Good
   const x = 5;

   // ❌ Avoid
   const x = 5
   ```

### CSS

1. **Use 2-space indentation**
   ```css
   /* ✅ Good */
   .button {
     padding: 10px;
     background: blue;
   }

   /* ❌ Avoid */
   .button {
       padding: 10px;
       background: blue;
   }
   ```

2. **Consistent formatting**
   - Spaces around property values
   - Proper selector spacing
   - Empty lines between rule sets

3. **CSS Variables for theming**
   ```css
   :root {
     --primary-color: #2563eb;
     --text-primary: #f1f5f9;
   }

   .button {
     background: var(--primary-color);
     color: var(--text-primary);
   }
   ```

### HTML

1. **Consistent indentation** (2 spaces)
2. **Proper semantic HTML**
3. **Accessible attributes** (alt, aria-labels, etc.)

## Pre-commit Workflow

### Manual Check Before Commit

```bash
# 1. Format your code
npm run format

# 2. Check quality
npm run check-quality

# 3. If issues found, review and fix
npm run lint:fix    # Auto-fix JavaScript
npm run format:write # Auto-format code

# 4. Commit when all checks pass
git add .
git commit -m "Your message"
```

### GitHub Actions Integration (Optional)

You can add a GitHub Actions workflow to automatically check code quality on pull requests:

```yaml
name: Frontend Quality Checks

on: [pull_request]

jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: npm install
      - run: npm run quality
```

## Common Issues and Fixes

### Issue: ESLint errors on console usage

**Solution**: Use only allowed console methods or add comment:
```javascript
// ✅ Allowed
console.error('Error message');
console.warn('Warning message');
console.log('Debug:', value); // Remove before commit

// ❌ Disallowed (unless documented)
console.info('Info');

// To disable for a line:
// eslint-disable-next-line no-console
console.debug('Debug info');
```

### Issue: Prettier formatting differs from IDE

**Solution**: Ensure your IDE uses the same Prettier config:
- VS Code: Install "Prettier - Code formatter" extension
- Use `.prettierrc.json` from project
- Enable "Format on Save" in settings

### Issue: Unused variables causing lint errors

**Solution**: Use underscore prefix for intentional unused params:
```javascript
// ✅ Good
document.addEventListener('click', (_event) => {
  // event intentionally unused
});

// Auto-prefixed variables are allowed
const _tempVar = someValue; // Underscore indicates it's intentional
```

### Issue: Scripts not executable

**Solution**: Make scripts executable:
```bash
chmod +x format-frontend.sh check-frontend-quality.sh
```

## Integration with Development Workflow

### Update run.sh (Optional)

Add quality check to development startup:

```bash
#!/bin/bash

# ... existing code ...

echo "Checking frontend quality..."
./check-frontend-quality.sh

echo "Starting Course Materials RAG System..."
cd backend && uv run uvicorn app:app --reload --port 8000
```

### Pre-commit Hook (Optional)

Create `.git/hooks/pre-commit`:

```bash
#!/bin/bash
npm run quality
if [ $? -ne 0 ]; then
  echo "Quality checks failed. Commit aborted."
  exit 1
fi
```

Make executable:
```bash
chmod +x .git/hooks/pre-commit
```

## Troubleshooting

### npm install fails

```bash
# Clear npm cache
npm cache clean --force

# Try installing again
npm install
```

### ESLint/Prettier not found in PATH

```bash
# Install locally instead of globally
npm install --save-dev eslint prettier stylelint

# Run through npm
npm run lint
npm run format
```

### Permission denied on shell scripts

```bash
chmod +x format-frontend.sh check-frontend-quality.sh
```

## Best Practices

1. **Format before committing**
   ```bash
   npm run format
   npm run check-quality
   ```

2. **Address linting warnings**, not just errors

3. **Keep formatting consistent** across the team

4. **Review formatting changes** in code reviews

5. **Use IDE integration** for real-time feedback

6. **Document any style exceptions** with comments

## Resources

- [ESLint Documentation](https://eslint.org/docs/)
- [Prettier Documentation](https://prettier.io/docs/)
- [Stylelint Documentation](https://stylelint.io/user-guide/)
- [JavaScript Style Guide](https://google.github.io/styleguide/jsguide.html)

## Questions?

Refer to the main `CLAUDE.md` for project architecture and development setup.
