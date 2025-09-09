import js from '@eslint/js';

export default [
  js.configs.recommended,
  {
    ignores: [
      'node_modules/**',
      'venv/**',
      '.git/**',
      '.ruff_cache/**',
      '*.min.js',
      'dist/**',
      'build/**',
    ],
  },
  {
    files: ['src/static/js/**/*.js'],
    languageOptions: {
      ecmaVersion: 2024,
      sourceType: 'module', // Changed to module
      globals: {
        // Browser globals only - no custom globals needed with ES modules
        window: 'readonly',
        document: 'readonly',
        console: 'readonly',
        fetch: 'readonly',
        setInterval: 'readonly',
        setTimeout: 'readonly',
        Date: 'readonly',
        parseInt: 'readonly',
        Intl: 'readonly',
        getComputedStyle: 'readonly',
      },
    },
    rules: {
      'no-console': 'off',
      'prefer-const': 'warn',
    },
  },
];
