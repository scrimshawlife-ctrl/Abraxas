/**
 * Vitest Configuration for Abraxas Golden Tests
 */

import { defineConfig } from 'vitest/config';
import path from 'path';

export default defineConfig({
  test: {
    globals: true,
    environment: 'node',
    include: ['server/abraxas/tests/**/*.test.ts'],
    setupFiles: ['server/abraxas/tests/setup.ts'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      include: [
        'server/abraxas/core/**/*.ts',
        'server/abraxas/pipelines/**/*.ts',
        'server/abraxas/integrations/**/*.ts',
        'server/abraxas/models/**/*.ts',
      ],
      exclude: [
        '**/*.test.ts',
        '**/fixtures.ts',
      ],
    },
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './'),
      '@shared': path.resolve(__dirname, './shared'),
    },
  },
});
