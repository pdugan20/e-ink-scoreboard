# Testing Quick Start Guide

Get your test suite up and running in 15 minutes.

## 1. Install Dependencies

```bash
# Python testing dependencies
pip install -r requirements-test.txt

# JavaScript testing dependencies
npm install
```

## 2. Verify Installation

```bash
# Check pytest is installed
pytest --version

# Check vitest is installed
npm run test -- --version
```

## 3. Run Your First Tests

```bash
# Run Python tests
pytest tests/unit/api/test_scores_api.py -v

# Run JavaScript tests
npm run test

# Run all tests
make test
```

## 4. Write Your First Test

### Python Test Example

Create `tests/unit/test_example.py`:

```python
import pytest

def add(a, b):
    return a + b

def test_addition():
    """Test that addition works"""
    assert add(2, 3) == 5
    assert add(-1, 1) == 0
    assert add(0, 0) == 0
```

Run it:

```bash
pytest tests/unit/test_example.py -v
```

### JavaScript Test Example

Create `tests/js/example.test.js`:

```javascript
import { describe, it, expect } from 'vitest';

function multiply(a, b) {
  return a * b;
}

describe('Multiplication', () => {
  it('should multiply two numbers', () => {
    expect(multiply(2, 3)).toBe(6);
    expect(multiply(-1, 5)).toBe(-5);
    expect(multiply(0, 10)).toBe(0);
  });
});
```

Run it:

```bash
npm run test
```

## 5. Generate Coverage Report

```bash
# Python coverage
pytest --cov --cov-report=html

# JavaScript coverage
npm run test:coverage

# Open reports in browser
open htmlcov/index.html          # Python
open coverage/index.html         # JavaScript
```

## 6. Common Commands

```bash
# Run tests
make test                 # All tests
make test-python          # Python only
make test-js              # JavaScript only
make test-fast            # Skip slow tests

# Watch mode (re-runs on file changes)
npm run test:watch        # JavaScript watch mode
pytest --watch            # Requires pytest-watch

# Run specific tests
pytest tests/unit/api/    # All API tests
pytest -k "test_mlb"      # Tests matching "test_mlb"
pytest -m unit            # Only unit tests

# Debugging
pytest -s                 # Show print statements
pytest --pdb              # Drop into debugger on failure
npm run test:ui           # Visual test UI
```

## 7. Test Structure Template

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
    input_data = {'key': 'value'}
    expected = 'expected_result'

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

## 8. Mocking Examples

### Mock HTTP Requests (Python)

```python
import pytest
import requests_mock

def test_api_call(requests_mock):
    """Test API call with mocked response"""
    requests_mock.get(
        'https://api.example.com/data',
        json={'result': 'success'},
        status_code=200
    )

    response = make_api_call()
    assert response['result'] == 'success'
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

## 9. Debugging Failed Tests

### Python

```bash
# Show detailed output
pytest -vv

# Stop at first failure
pytest -x

# Drop into debugger on failure
pytest --pdb

# Show print statements
pytest -s

# Run last failed tests
pytest --lf
```

### JavaScript

```bash
# Run with UI debugger
npm run test:ui

# Run specific test file
npm run test tests/js/diamond.test.js

# Show console output
npm run test -- --reporter=verbose
```

## 10. Next Steps

1. Read `TESTING_PROPOSAL.md` for full strategy
2. Implement tests for critical API endpoints
3. Add tests for your next feature
4. Aim for 80% coverage overall

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
rm -rf .pytest_cache htmlcov coverage
```

### Slow tests

```bash
# Profile slow tests
pytest --durations=10

# Run only fast tests
pytest -m "not slow"
```

## Resources

- **pytest docs**: <https://docs.pytest.org>
- **Vitest docs**: <https://vitest.dev>
- **Testing best practices**: `TESTING_PROPOSAL.md`
- **Example tests**: `tests/unit/api/test_scores_api.py`

## Getting Help

- Check existing tests for examples
- Run `pytest --help` for all options
- Run `npm run test -- --help` for Vitest options
- See `TESTING_PROPOSAL.md` for strategy details
