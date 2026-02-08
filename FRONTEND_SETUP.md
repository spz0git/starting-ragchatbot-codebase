# Frontend Development Setup

Quick guide to set up frontend code quality tools.

## 5-Minute Setup

### 1. Install Node.js

Download from https://nodejs.org/ (LTS version recommended)

### 2. Install Dependencies

```bash
npm install
```

### 3. Try Formatting

```bash
npm run format
```

Done! Your frontend code is now formatted.

## Daily Development

### Before committing code:

```bash
# Auto-format and lint
npm run format

# Check quality
npm run check-quality
```

## Available Commands

| Command | Purpose |
|---------|---------|
| `npm run format` | Auto-format all frontend code |
| `npm run check-quality` | Check code quality without changes |
| `npm run lint` | Run ESLint |
| `npm run lint:fix` | Auto-fix ESLint issues |
| `npm run format:check` | Check if code needs formatting |
| `npm run format:write` | Auto-format code |

## IDE Setup (Optional but Recommended)

### VS Code

1. Install extensions:
   - "ESLint" by Dirk Bäumer
   - "Prettier - Code formatter" by Prettier

2. Create `.vscode/settings.json`:

```json
{
  "editor.defaultFormatter": "esbenp.prettier-vscode",
  "editor.formatOnSave": true,
  "[javascript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "[css]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "[html]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "eslint.validate": ["javascript"],
  "eslint.format.enable": true
}
```

This enables real-time formatting and linting as you code.

### WebStorm / PhpStorm

1. Go to Settings → Languages & Frameworks → JavaScript → Code Quality Tools → ESLint
2. Enable ESLint
3. Go to Settings → Languages & Frameworks → JavaScript → Prettier
4. Enable Prettier

## Troubleshooting

### npm install fails
```bash
npm cache clean --force
npm install
```

### Commands not found
```bash
# Use npm run instead
npm run lint    # instead of eslint
npm run format  # instead of prettier
```

### Can't find prettier/eslint
```bash
# Install locally
npm install
```

## Next Steps

- Read `FRONTEND_QUALITY_GUIDE.md` for detailed standards
- Check `CLAUDE.md` for full project setup
- Review `README.md` for project overview

## Support

Run `npm run check-quality` to identify any issues, then check the `FRONTEND_QUALITY_GUIDE.md` for solutions.
