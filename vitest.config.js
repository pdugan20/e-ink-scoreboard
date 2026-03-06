import { defineConfig } from 'vitest/config';
import path from 'path';

export default defineConfig({
  test: {
    // Enable global test APIs (describe, it, expect, etc.)
    globals: true,

    // Use jsdom for DOM simulation
    environment: 'jsdom',

    // Test file patterns
    include: ['tests/js/**/*.test.js', 'tests/js/**/*.spec.js'],

    // Coverage configuration
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html', 'lcov', 'json'],
      reportsDirectory: './coverage',

      // Files to include/exclude
      include: ['src/static/js/**/*.js'],
      exclude: [
        'node_modules/**',
        'tests/**',
        'venv/**',
        '**/*.config.js',
        '**/coverage/**',
      ],
    },

    // Setup files
    setupFiles: ['./tests/js/setup.js'],

    // Test timeout
    testTimeout: 10000,

    // Hooks timeout
    hookTimeout: 10000,
  },

  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src/static/js'),
    },
  },
});
