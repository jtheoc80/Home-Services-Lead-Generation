# Quality Gate

This repository includes an automated quality gate workflow that runs on all pull requests to ensure code quality and consistency.

## What's Checked

### Node.js/Frontend
- **ESLint**: Code linting for JavaScript and TypeScript files
- **TypeScript**: Type checking to catch type errors
- **Tests**: Frontend test suite (when available)

### Python/Backend
- **Black**: Code formatting consistency 
- **Ruff**: Fast Python linter for code quality
- **Tests**: Python test suite using pytest

## Workflow Behavior

### Auto-Fixing
When a PR contains only formatting issues, the workflow will:
1. Create an auto-fix branch with formatting fixes applied
2. Comment on the PR with instructions to merge the fixes
3. Apply Black formatting and Ruff auto-fixes for Python
4. Apply ESLint auto-fixes for JavaScript/TypeScript

### Merge Blocking
The workflow will block PR merges when:
- **Tests fail**: Both Node.js and Python test failures block merges (configurable via `REQUIRE_TESTS` repository variable)
- **TypeScript type errors**: Type errors are considered critical and block merges
- ESLint and formatting issues are reported but don't block merges (can be auto-fixed)

### Test Execution Safety
The workflow uses a safer test execution pattern:
- **Test Detection**: Automatically detects JS/TS and Python test files before execution
- **Graceful Failures**: Tests run with `continue-on-error: true` to prevent workflow interruption
- **Flexible Test Runners**: Supports both Vitest and Jest for JavaScript tests, with automatic fallback
- **Proper Result Tracking**: Test results are captured and marked for accurate reporting

### Coverage Reports
Test coverage reports are automatically uploaded to Codecov for tracking coverage metrics.

## Local Development

To run the same checks locally:

```bash
# Node.js checks
npm run lint
npm run typecheck  
npm run test

# Python checks
black --check .
ruff check .
pytest tests/
```

## Configuration

- **ESLint**: Configured in `frontend/.eslintrc.json`
- **TypeScript**: Configured in `frontend/tsconfig.json`
- **Black/Ruff**: Configured in `pyproject.toml`
- **Pytest**: Configured in `pyproject.toml`

### Repository Variables

- **REQUIRE_TESTS**: Set to `'true'` to block merges when tests fail. When not set or `'false'`, test failures are reported but don't block merges.