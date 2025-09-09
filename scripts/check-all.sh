#!/bin/bash

echo "Running all checks..."

black --check . && \
ruff check . && \
npx prettier --check . && \
npx eslint .

if [ $? -eq 0 ]; then
    echo "✅ All checks passed!"
else
    echo "❌ Some checks failed. Fix issues before committing."
    exit 1
fi