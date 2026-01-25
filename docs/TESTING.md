# Testing Guide

Comprehensive testing guide for the E-Ink Sports Scores project.

## Quick Start

Get your test suite up and running in 15 minutes.

### 1. Install Dependencies

```bash
# Install Python and JavaScript test dependencies
make install

# Or manually:
pip install -r requirements-test.txt
npm install
```

### 2. Run Tests

```bash
# Run all tests (Python + JavaScript)
make test

# Run Python tests only
make test-python

# Run JavaScript tests only
make test-js

# Run with coverage reports
make test-coverage
```

### 3. Verify Installation

```bash
# Check pytest
pytest --version

# Check vitest
npm run test -- --version
```

## Current Test Status

### Overall Metrics

- **Total Tests**: 110 tests (90 Python + 20 JavaScript)
- **Pass Rate**: 100%
- **Execution Time**: < 2 seconds (all tests)
- **Coverage**: ~70% overall

### Component Coverage

| Component                  | Tests | Coverage | Status   |
| -------------------------- | ----- | -------- | -------- |
| **MLB Standings API**      | 4     | 100%     | Complete |
| **MLB Games API**          | 5     | 99%      | Complete |
| **NFL Games API**          | 6     | 99%      | Complete |
| **Screensaver Config**     | 7     | 93%      | Complete |
| **GameChecker**            | 29    | ~90%     | Complete |
| **RefreshController**      | 17    | ~85%     | Complete |
| **ScreenshotController**   | 13    | ~70%     | Complete |
| **Diamond Rendering (JS)** | 20    | ~95%     | Complete |
| **Flask Endpoints**        | 9     | 100%     | Complete |

## Running Tests

### Common Commands

```bash
# Run all tests
make test

# Run Python tests only
make test-python

# Run JavaScript tests only
make test-js

# Run fast tests (skip slow/e2e)
make test-fast

# Generate coverage reports
make test-coverage

# Clean test artifacts
make clean
```

### Detailed Python Commands

```bash
# Activate virtual environment
source venv/bin/activate

# Run all tests with verbose output
pytest -v

# Run specific test file
pytest tests/unit/api/test_scores_api.py -v

# Run specific test class
pytest tests/unit/api/test_scores_api.py::TestMLBGames -v

# Run specific test
pytest tests/unit/api/test_scores_api.py::TestMLBGames::test_fetch_mlb_games_live_game -v

# Run tests by marker
pytest -m unit              # Only unit tests
pytest -m integration       # Only integration tests

# Run tests matching pattern
pytest -k "test_mlb"        # All tests with "mlb" in name

# Show print statements
pytest -s

# Stop at first failure
pytest -x

# Drop into debugger on failure
pytest --pdb

# Run last failed tests
pytest --lf

# Show slowest tests
pytest --durations=10

# Coverage for specific module
pytest tests/unit/api/ --cov=src/api --cov-report=html
open htmlcov/index.html
```

### Detailed JavaScript Commands

```bash
# Run all JavaScript tests
npm run test

# Run with coverage
npm run test:coverage
open coverage/index.html

# Run with UI debugger
npm run test:ui

# Run specific test file
npm run test tests/js/diamond.test.js

# Watch mode (re-run on changes)
npm run test:watch

# Verbose output
npm run test -- --reporter=verbose
```

## Writing Tests

### Test Structure (AAA Pattern)

All tests follow the Arrange-Act-Assert pattern:

```python
def test_component_behavior_when_condition():
    """Test that component does X when Y occurs"""
    # Arrange - Set up test data
    input_data = {"key": "value"}
    expected = "expected_result"

    # Act - Execute the code under test
    result = function_under_test(input_data)

    # Assert - Verify the result
    assert result == expected
```

### Naming Convention

```text
test_<component>_<behavior>_<condition>

Examples:
- test_fetch_mlb_games_returns_empty_list_when_api_fails
- test_game_checker_enables_screensaver_when_no_games
- test_render_diamond_highlights_occupied_bases
```

### Python Test Template

```python
"""
Tests for [module name]

[Brief description of what's being tested]
"""

import pytest
from unittest.mock import Mock, patch


@pytest.mark.unit
def test_function_success():
    """Test that [function] works correctly when [condition]"""
    # Arrange
    input_data = {"key": "value"}
    expected = "expected_result"

    # Act
    result = function_under_test(input_data)

    # Assert
    assert result == expected


@pytest.mark.unit
def test_function_error_handling():
    """Test that [function] handles errors gracefully"""
    # Arrange
    invalid_input = None

    # Act & Assert
    with pytest.raises(ValueError):
        function_under_test(invalid_input)
```

### JavaScript Test Template

```javascript
import { describe, it, expect, beforeEach, vi } from 'vitest';

describe('FunctionName', () => {
  beforeEach(() => {
    // Setup before each test
  });

  it('should do something when condition is met', () => {
    // Arrange
    const input = { key: 'value' };
    const expected = 'result';

    // Act
    const result = functionUnderTest(input);

    // Assert
    expect(result).toBe(expected);
  });

  it('should handle errors gracefully', () => {
    // Arrange
    const invalidInput = null;

    // Act & Assert
    expect(() => functionUnderTest(invalidInput)).toThrow();
  });
});
```

## Mocking External Dependencies

### HTTP Requests (Python)

```python
import pytest


def test_api_call(requests_mock):
    """Test API call with mocked response"""
    requests_mock.get(
        "https://api.example.com/data",
        json={"result": "success"},
        status_code=200,
    )

    response = make_api_call()
    assert response["result"] == "success"


def test_api_timeout(requests_mock):
    """Test API timeout handling"""
    requests_mock.get(
        "https://api.example.com/data",
        exc=requests.exceptions.Timeout,
    )

    result = make_api_call()
    assert result == []  # Returns empty on timeout
```

### File System Operations (Python)

```python
from unittest.mock import mock_open, patch


def test_read_config():
    """Test reading configuration file"""
    mock_config = '{"key": "value"}'

    with patch("builtins.open", mock_open(read_data=mock_config)):
        config = load_config()
        assert config["key"] == "value"


def test_file_not_found():
    """Test handling missing file"""
    with patch("builtins.open", side_effect=FileNotFoundError()):
        config = load_config()
        assert config == {}
```

### Mock Functions (JavaScript)

```javascript
import { vi } from 'vitest';

it('should call the callback', () => {
  const callback = vi.fn();

  processData(callback);

  expect(callback).toHaveBeenCalledOnce();
  expect(callback).toHaveBeenCalledWith('data');
});
```

## Test Infrastructure

### Testing Frameworks

- **pytest** - Python test framework with fixtures and markers
- **Vitest** - Fast JavaScript testing framework
- **requests-mock** - HTTP request mocking for API tests
- **Flask test client** - Integration testing for Flask endpoints

### Configuration Files

- `pytest.ini` - pytest configuration and markers
- `vitest.config.js` - JavaScript test configuration
- `requirements-test.txt` - Python test dependencies
- `package.json` - JavaScript test dependencies and scripts
- `.github/workflows/test.yml` - CI/CD test pipeline
- `Makefile` - Common test commands

### Pre-commit Hooks

All code is automatically checked before commits:

- **Python**: Black (formatter), Ruff (linter)
- **JavaScript**: Prettier (formatter), ESLint (linter)
- **Markdown**: markdownlint

Install hooks:

```bash
make install-hooks
```

Run manually:

```bash
make check
```

### GitHub Actions CI

Two workflows run on every push and PR:

1. **Tests** (`.github/workflows/test.yml`):
   - Python tests (matrix: 3.9, 3.10, 3.11)
   - JavaScript tests
   - Integration tests
   - Coverage upload to Codecov

2. **Lint & Format** (`.github/workflows/lint-and-format.yml`):
   - Python checks (black, ruff)
   - JavaScript checks (prettier, eslint)
   - Markdown checks (markdownlint)

## Quality Standards

All tests must meet:

- **Speed**: Unit tests < 100ms each
- **Isolation**: No external dependencies (use mocks)
- **Readability**: Clear test names and structure
- **Maintainability**: Easy to update when code changes
- **Coverage**: 80%+ on new code

## Troubleshooting

### "Module not found" errors

```bash
# Python: Check PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"

# JavaScript: Check imports use correct paths
# Use relative imports: import { x } from './module.js'
```

### Tests pass locally but fail in CI

```bash
# Run tests with same Python version as CI
pyenv install 3.11
pyenv local 3.11

# Clear all caches
make clean
rm -rf .pytest_cache htmlcov coverage node_modules/.cache
```

### Slow tests

```bash
# Profile slow tests
pytest --durations=10

# Run only fast tests
pytest -m "not slow"
make test-fast
```

### Coverage not updating

```bash
# Clear coverage data
rm -rf .coverage htmlcov coverage.xml

# Run with fresh coverage
pytest --cov --cov-report=html
```

## Maintenance

### Updating Tests

When code changes:

1. Run tests: `make test`
2. Fix failing tests or update expectations
3. Ensure coverage doesn't decrease: `make test-coverage`
4. Commit changes

### Adding New Tests

1. Follow existing structure in `tests/unit/` or `tests/integration/`
2. Use same naming conventions
3. Add appropriate test markers (`@pytest.mark.unit`, `@pytest.mark.integration`)
4. Run locally before committing
5. Ensure pre-commit hooks pass

## Resources

- **pytest docs**: <https://docs.pytest.org>
- **Vitest docs**: <https://vitest.dev>
- **requests-mock docs**: <https://requests-mock.readthedocs.io>
- **Example tests**: `tests/unit/api/test_scores_api.py`
- **Contributing guide**: `CONTRIBUTING.md`

## Getting Help

- Check existing tests for examples
- Run `pytest --help` for all pytest options
- Run `npm run test -- --help` for Vitest options
- See GitHub Actions logs for CI failures
- Review pre-commit hook output for code quality issues
