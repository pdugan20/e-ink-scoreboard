#!/bin/bash

echo "Setting up git hooks..."

# Configure git to use .githooks directory
git config core.hooksPath .githooks

echo "✅ Git hooks configured! Hooks will run from .githooks/"
echo "Pre-commit hook will run automatically before each commit."
echo ""
echo "To disable hooks temporarily, run: git config --unset core.hooksPath"
echo "To re-enable, run this script again."