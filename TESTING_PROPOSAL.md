# Testing Strategy Proposal

## Executive Summary

This document proposes a comprehensive testing strategy for the E-Ink Sports Scores project. Currently, the project has **0% test coverage** across ~3,225 lines of Python code and 17 JavaScript files. This proposal outlines an industry-standard testing approach that is scalable, maintainable, and aligned with best practices.

## Current State

### Codebase Analysis

- **Python Backend**: ~3,225 lines

  - Flask API endpoints (MLB/NFL scores, screensaver)
  - Display controllers (screenshot, refresh, game checking)
  - External API integrations (MLB Stats API, ESPN API)
  - Services and utilities

- **JavaScript Frontend**: 17 ES modules

  - Game rendering logic
  - Diamond/base display
  - Theme management
  - Data fetching and state management

- **External Dependencies**:
  - MLB Stats API (`statsapi.mlb.com`)
  - ESPN NFL API (`site.api.espn.com`)
  - Playwright for screenshots
  - RSS feed parsing

### Risk Assessment

**High-Risk Areas** (no tests, frequent changes):

1. API integrations with external services
2. Screenshot capture and display refresh logic
3. Game status checking and caching
4. Screensaver eligibility logic

**Medium-Risk Areas**:

1. JavaScript rendering logic
2. Configuration management
3. Error handling and retries

## Proposed Testing Strategy

### Testing Pyramid

```text
           /\
          /  \        E2E Tests (5%)
         /    \       - Critical user flows
        /------\      - Smoke tests
       /        \
      /          \    Integration Tests (25%)
     /            \   - API endpoints
    /--------------\  - External API mocking
   /                \
  /                  \ Unit Tests (70%)
 /____________________\ - Business logic
                        - Utilities
                        - Pure functions
```

### Test Types by Component

| Component            | Unit | Integration | E2E | Priority     |
| -------------------- | ---- | ----------- | --- | ------------ |
| API Endpoints        | ✓    | ✓           | ✓   | **Critical** |
| External API Clients | ✓    | ✓           | -   | **Critical** |
| Game Checker         | ✓    | ✓           | -   | **High**     |
| Display Controllers  | ✓    | -           | ✓   | **High**     |
| Screensaver Service  | ✓    | ✓           | -   | **Medium**   |
| JavaScript Renderers | ✓    | -           | -   | **Medium**   |
| Utilities/Helpers    | ✓    | -           | -   | **Low**      |

## Technology Stack

### Python Testing (Backend)

**Framework**: **pytest** (industry standard)

**Why pytest?**

- Most popular Python testing framework (50M+ downloads/month)
- Simple, pythonic syntax
- Powerful fixtures and parametrization
- Extensive plugin ecosystem
- Used by: Django, Flask, FastAPI, pandas, numpy

**Key Libraries**:

```text
pytest              - Core testing framework
pytest-flask        - Flask app testing utilities
pytest-cov          - Coverage reporting
pytest-mock         - Mocking utilities
requests-mock       - HTTP request mocking
pytest-asyncio      - Async test support
freezegun           - Time mocking (for game schedules)
```

**Example Test Structure**:

```python
# tests/api/test_scores_api.py
import pytest
from unittest.mock import patch
import requests_mock

def test_fetch_mlb_games_success(requests_mock):
    """Test MLB API returns games correctly"""
    requests_mock.get(
        'https://statsapi.mlb.com/api/v1/schedule/games/',
        json={'games': [{'id': 1, 'status': 'Live'}]}
    )

    games = fetch_mlb_games()
    assert len(games) == 1
    assert games[0]['status'] == 'Live'

def test_fetch_mlb_games_api_failure(requests_mock):
    """Test MLB API failure handling"""
    requests_mock.get(
        'https://statsapi.mlb.com/api/v1/schedule/games/',
        status_code=500
    )

    games = fetch_mlb_games()
    assert games == []  # Graceful degradation
```

### JavaScript Testing (Frontend)

**Framework**: **Vitest** (modern, fast, ESM-native)

**Why Vitest over Jest?**

- **Native ES modules support** (your code uses `type: "module"`)
- **10x faster** than Jest for ESM projects
- **Compatible API** with Jest (easy migration path)
- **Built-in coverage** with c8
- **Vite-powered** (instant HMR, no config needed)

**Alternative**: Jest with transform config (slower, more complex)

**Key Libraries**:

```text
vitest              - Testing framework
@vitest/ui          - Web UI for tests
jsdom               - DOM simulation
@testing-library/dom - DOM testing utilities
```

**Example Test Structure**:

```javascript
// tests/js/diamond.test.js
import { describe, it, expect } from 'vitest';
import { drawDiamond, isBaseOccupied } from '../../src/static/js/diamond.js';

describe('Diamond rendering', () => {
  it('should draw bases correctly', () => {
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');

    drawDiamond(ctx, { first: true, second: false, third: true });

    // Assert canvas state or mock calls
  });

  it('should detect occupied bases', () => {
    expect(isBaseOccupied({ first: true }, 'first')).toBe(true);
    expect(isBaseOccupied({ first: false }, 'first')).toBe(false);
  });
});
```

### End-to-End Testing

**Framework**: **Playwright** (already installed!)

**Scope**: Critical user flows only

1. Display loads successfully
2. MLB scores render correctly
3. Screensaver activates when no games
4. Display refresh works

## Test Organization

### Directory Structure

```text
sports-scores-plugin/
├── src/
│   ├── api/
│   ├── display/
│   ├── services/
│   └── static/js/
├── tests/
│   ├── __init__.py
│   ├── conftest.py                 # Shared pytest fixtures
│   ├── unit/
│   │   ├── api/
│   │   │   ├── test_scores_api.py
│   │   │   └── test_screensaver_api.py
│   │   ├── display/
│   │   │   ├── test_game_checker.py
│   │   │   ├── test_refresh_controller.py
│   │   │   └── test_screenshot_controller.py
│   │   └── services/
│   │       └── test_screensaver_service.py
│   ├── integration/
│   │   ├── test_api_endpoints.py   # Flask endpoint tests
│   │   └── test_external_apis.py   # External API integration
│   ├── e2e/
│   │   ├── test_display_flow.py    # Playwright E2E tests
│   │   └── fixtures/               # Test HTML fixtures
│   └── js/
│       ├── diamond.test.js
│       ├── renderer.test.js
│       └── data.test.js
├── vitest.config.js
└── pytest.ini
```

### Configuration Files

**pytest.ini**:

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    --strict-markers
    --cov=src
    --cov-report=term-missing
    --cov-report=html
    --cov-report=xml
    --cov-fail-under=80
markers =
    unit: Unit tests
    integration: Integration tests
    e2e: End-to-end tests
    slow: Slow running tests
```

**vitest.config.js**:

```javascript
import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    globals: true,
    environment: 'jsdom',
    coverage: {
      provider: 'c8',
      reporter: ['text', 'html', 'lcov'],
      exclude: ['tests/**', 'node_modules/**'],
      lines: 80,
      functions: 80,
      branches: 80,
      statements: 80,
    },
  },
});
```

## Coverage Goals

### Phase 1: Foundation (Weeks 1-2)

**Target**: 40% overall coverage

- **Critical paths**: API endpoints, external API clients
- **Priority**: High-risk areas first
- **Deliverable**: 20-30 unit tests, 5-10 integration tests

### Phase 2: Core Logic (Weeks 3-4)

**Target**: 70% overall coverage

- **Expand**: Game checker, display controllers
- **Add**: JavaScript unit tests
- **Deliverable**: 50+ unit tests, 15+ integration tests

### Phase 3: Complete (Weeks 5-6)

**Target**: 80%+ overall coverage

- **Complete**: All business logic
- **Add**: E2E tests for critical flows
- **Polish**: Edge cases, error scenarios

### Coverage Thresholds

```yaml
Minimum Required:
  Overall: 80%
  Unit tests: 85%
  Integration tests: 75%

Branch Coverage:
  Overall: 70%
  Critical paths: 90%
```

## CI/CD Integration

### GitHub Actions Workflow

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test-python:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r requirements-dev.txt
      - run: pytest --cov --cov-report=xml
      - uses: codecov/codecov-action@v3

  test-javascript:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: '18'
      - run: npm ci
      - run: npm run test
      - run: npm run test:coverage
```

### Pre-commit Hook Integration

Add to `.pre-commit-config.yaml`:

```yaml
# Run fast unit tests before commit
- repo: local
  hooks:
    - id: pytest-fast
      name: pytest (fast tests only)
      entry: pytest -m "not slow" --maxfail=1
      language: system
      pass_filenames: false
      always_run: true
```

## Implementation Plan

### Week 1: Setup & Infrastructure

**Tasks**:

1. Install testing dependencies
2. Create test directory structure
3. Write shared fixtures (`conftest.py`)
4. Configure pytest and vitest
5. Set up coverage reporting

**Deliverable**: Testing infrastructure ready

### Week 2: Critical API Tests

**Tasks**:

1. Test API endpoints (Flask routes)
2. Mock external APIs (MLB, ESPN)
3. Test error handling and retries
4. Test API response formats

**Deliverable**: 15-20 tests, API endpoints covered

### Week 3: Display Logic Tests

**Tasks**:

1. Test `GameChecker` class
2. Test `RefreshController`
3. Test `ScreenshotController`
4. Mock Playwright interactions

**Deliverable**: 20-25 tests, display logic covered

### Week 4: JavaScript Tests

**Tasks**:

1. Test rendering functions
2. Test diamond/base logic
3. Test data transformations
4. Test utility functions

**Deliverable**: 15-20 JS tests

### Week 5: Integration & E2E

**Tasks**:

1. Integration tests for full API flows
2. E2E tests with Playwright
3. Test screensaver activation
4. Test display refresh cycle

**Deliverable**: 10+ integration/E2E tests

### Week 6: Polish & Documentation

**Tasks**:

1. Reach 80% coverage
2. Test edge cases
3. Document testing patterns
4. Train team on testing

**Deliverable**: Complete test suite

## Development Workflow

### Writing Tests (TDD Approach)

1. **Red**: Write failing test first
2. **Green**: Implement minimal code to pass
3. **Refactor**: Clean up implementation

### Running Tests

```bash
# Python tests
pytest                              # Run all tests
pytest tests/unit/                  # Run unit tests only
pytest -m integration               # Run integration tests
pytest -k "test_mlb"                # Run tests matching pattern
pytest --cov --cov-report=html      # Generate coverage report

# JavaScript tests
npm run test                        # Run all JS tests
npm run test:watch                  # Watch mode
npm run test:ui                     # Web UI
npm run test:coverage               # With coverage

# Quick checks
make test                           # Run all tests
make test-fast                      # Skip slow tests
```

### Test Quality Standards

**Good Test Characteristics**:

- ✅ **Fast**: Unit tests < 100ms, integration < 1s
- ✅ **Isolated**: No dependencies on other tests
- ✅ **Repeatable**: Same result every time
- ✅ **Readable**: Clear test name and structure
- ✅ **Maintainable**: Easy to update when code changes

**Test Naming Convention**:

```python
def test_<component>_<scenario>_<expected_result>():
    """Test that <component> <expected_result> when <scenario>"""

# Examples:
def test_fetch_mlb_games_returns_empty_list_when_api_fails():
def test_game_checker_enables_screensaver_when_no_games_scheduled():
```

## Cost-Benefit Analysis

### Benefits

**Short-term** (Weeks 1-6):

- Catch bugs before production
- Safe refactoring
- Faster debugging

**Long-term** (6+ months):

- Reduced maintenance cost
- Faster feature development
- Confident deployments
- Better documentation (tests as specs)

### Costs

**Time Investment**:

- Initial setup: 4-8 hours
- Test writing: ~1.5x development time initially
- Maintenance: ~10% ongoing time

**ROI**: Positive after 3-6 months based on:

- Bugs caught in CI vs production
- Time saved debugging
- Reduced regression issues

## Risks & Mitigation

### Risk 1: Team Resistance

**Mitigation**:

- Start with high-value tests (APIs)
- Show quick wins (bugs caught)
- Pair programming for test writing

### Risk 2: Slow Test Suite

**Mitigation**:

- Keep unit tests fast (<1s total)
- Parallel test execution
- Mark slow tests with `@pytest.mark.slow`

### Risk 3: Flaky Tests

**Mitigation**:

- Mock external dependencies
- Use `freezegun` for time-based tests
- Avoid sleep/waits in tests

## Success Metrics

### KPIs

1. **Coverage**: 80%+ overall, 90%+ critical paths
2. **Speed**: Unit tests < 2s, full suite < 30s
3. **Reliability**: <1% flaky test rate
4. **Adoption**: 100% PRs include tests

### Review Milestones

- **Week 2**: Review API test coverage
- **Week 4**: Review overall strategy effectiveness
- **Week 6**: Final assessment and adjustments

## Next Steps

1. **Review & Approval**: Stakeholder sign-off on approach
2. **Dependency Installation**: Add testing packages
3. **Infrastructure Setup**: Create test directories and config
4. **Training**: Team workshop on testing practices
5. **Implementation**: Begin Week 1 tasks

## Appendix: Tool Comparison

### Python Testing Frameworks

| Framework  | Pros                                     | Cons              | Verdict            |
| ---------- | ---------------------------------------- | ----------------- | ------------------ |
| **pytest** | Industry standard, great plugins, simple | None significant  | ✅ **Recommended** |
| unittest   | Built-in, no deps                        | Verbose, outdated | ❌ Skip            |
| nose2      | Similar to pytest                        | Less maintained   | ❌ Skip            |

### JavaScript Testing Frameworks

| Framework  | Pros                     | Cons                          | Verdict            |
| ---------- | ------------------------ | ----------------------------- | ------------------ |
| **Vitest** | Fast, ESM-native, modern | Newer (but stable)            | ✅ **Recommended** |
| Jest       | Most popular, mature     | Slow with ESM, complex config | ⚠️ Alternative     |
| Mocha      | Flexible, minimalist     | Requires many plugins         | ❌ Skip            |

## Questions & Answers

**Q: Why 80% coverage, not 100%?**
A: 80% is industry standard sweet spot. Diminishing returns above 80%, and some code (like CLI scripts) is hard to test meaningfully.

**Q: Should we test private functions?**
A: No. Test behavior through public APIs. Refactoring should not break tests.

**Q: How do we test Playwright screenshots?**
A: Mock the Playwright browser in unit tests. E2E tests verify actual screenshots.

**Q: What about load/performance testing?**
A: Out of scope for initial implementation. Consider after 80% coverage achieved.
