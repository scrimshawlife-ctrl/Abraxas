# Abraxas Golden Test Suite
**ABX-Core v1.2 - SEED Framework Compliant**

## Overview

This test suite validates the deterministic behavior of all Abraxas oracle pipelines using golden snapshot testing. All tests verify that given identical inputs (ritual + context), the outputs are **100% reproducible**.

## Running Tests

```bash
# Install vitest if not already installed
npm install -D vitest @vitest/ui

# Run all tests
npm test

# Run tests in watch mode
npm run test:watch

# Run tests with coverage
npm run test:coverage

# View test UI
npm run test:ui
```

## Test Structure

```
tests/
├── fixtures.ts              # Deterministic test fixtures
├── kernel.test.ts           # Symbolic kernel (8 metrics)
├── daily-oracle.test.ts     # Daily oracle ciphergram generation
├── vc-analyzer.test.ts      # VC market analysis
├── social-scanner.test.ts   # Social trends scanning
├── watchlist-scorer.test.ts # Watchlist scoring
└── ers-scheduler.test.ts    # ERS task scheduling
```

## Golden Test Philosophy

**Golden tests** ensure that:
1. **Determinism:** Same input → Same output (always)
2. **Reproducibility:** Tests pass on all machines
3. **Regression Detection:** Any change to output triggers test failure
4. **Documentation:** Test snapshots serve as specification

## Test Fixtures

All tests use **fixed rituals** with deterministic seeds:

```typescript
FIXED_RITUAL = {
  date: "2025-01-15",
  seed: "test-seed-12345",
  runes: [aether, flux, nexus]
}
```

This ensures **zero randomness** in test execution.

## Snapshot Testing

Vitest snapshots capture exact output:

```typescript
expect(oracle.ciphergram).toMatchInlineSnapshot();
```

If output changes:
- Review the diff carefully
- Update snapshot if change is intentional: `npm test -- -u`
- Investigate if change is unexpected

## SEED Compliance Testing

All tests verify:
- ✓ Deterministic execution
- ✓ Provenance tracking
- ✓ Symbolic metrics in valid ranges
- ✓ Entropy bounds (Hσ < 0.8)
- ✓ Quality score aggregation

## Coverage Goals

Target: **>90% coverage** for:
- `core/` (symbolic kernel, archetypes)
- `pipelines/` (all oracle pipelines)
- `integrations/` (adapters, ERS)
- `models/` (type definitions)

## Continuous Integration

Tests run automatically on:
- Every commit
- Every pull request
- Pre-push hooks (recommended)

## Troubleshooting

**Tests fail after code changes:**
- Check if change was intentional
- Review snapshot diffs
- Update snapshots if expected: `npm test -- -u`

**Tests fail inconsistently:**
- Check for non-deterministic code (Date.now(), Math.random())
- Ensure all randomness uses ritual.seed
- Verify fixtures are unchanged

**Import errors:**
- Check TypeScript paths in vitest.config.ts
- Verify all dependencies installed

## Adding New Tests

1. Create fixture in `fixtures.ts`
2. Write test file: `<module>.test.ts`
3. Use `FIXED_RITUAL` for determinism
4. Capture golden snapshots
5. Verify reproducibility
6. Document coverage
