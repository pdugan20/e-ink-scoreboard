# Contributing

## Development Setup

### 1. Install Dependencies

**Python dependencies:**

```bash
pip install -r requirements-dev.txt
```

**JavaScript dependencies:**

```bash
npm install
```

### 2. Install Pre-commit Hooks

Pre-commit hooks automatically format and lint your code before each commit:

```bash
pre-commit install
```

This will run automatically on every commit. To run manually on all files:

```bash
pre-commit run --all-files
```

## Code Quality Standards

### Python

- **Formatter:** Black (line length: 88)
- **Linter:** Ruff
- **Configuration:** `pyproject.toml`

Run manually:

```bash
black .
ruff check --fix .
```

### JavaScript

- **Formatter:** Prettier
- **Linter:** ESLint
- **Configuration:** `.prettierrc`, `eslint.config.js`

Run manually:

```bash
npm run format
npm run lint:fix
```

### Markdown

- **Linter:** markdownlint
- **Configuration:** `.markdownlint.json`

Run manually:

```bash
markdownlint '**/*.md' --ignore node_modules --ignore venv --fix
```

## Pre-commit Hooks

The following checks run automatically on commit:

- Trailing whitespace removal
- End-of-file fixing
- YAML/JSON validation
- Large file detection
- Merge conflict detection
- Black formatting (Python)
- Ruff linting (Python)
- Prettier formatting (JS/JSON/YAML/Markdown)
- ESLint (JavaScript)
- markdownlint (Markdown)

## CI Checks

All PRs must pass GitHub Actions CI checks:

- Python: Black --check, Ruff check
- JavaScript: Prettier --check, ESLint
- Markdown: markdownlint

## Quick Reference

```bash
# Install everything
pip install -r requirements-dev.txt
npm install
pre-commit install

# Run all checks manually
pre-commit run --all-files

# Run specific tool
black .
ruff check .
npm run lint && npm run format:check
```
