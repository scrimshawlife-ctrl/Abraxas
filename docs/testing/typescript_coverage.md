# TypeScript Coverage Tracking

## Run coverage

```bash
npm run test:coverage
```

## Outputs

- HTML report: `coverage/index.html`
- JSON summary: `coverage/coverage-summary.json`
- JSON detail: `coverage/coverage-final.json`
- Text summary: printed to stdout

## Notes

- Coverage configuration is defined in `vitest.config.ts`.
- The coverage scope focuses on the TypeScript server runtime paths.
