# Contributing

## The rules that matter here

- **Never loosen a governance scan to make a test pass.** A pattern that fires incorrectly is redesigned for
  its intent, or the exemption is made precise enough to test. Deleting a check is not a fix.
- **Never `git add -A`.** `out/`, `data/`, `.abraxas/` and `.aal/` are tracked but rewritten by every test
  run, so a blanket add stages noise across hundreds of files. Stage explicit paths.
- **Every guard must be seen to fail.** A check nobody has watched reject the thing it guards is not known to
  be a guard. Drive it to failure before trusting it, and keep the counterfactual as a test.
- **A number in a document is an assertion.** Counts, test totals and coverage claims get computed, then
  verified against the thing they describe.
- **Label blockers honestly.** `NOT_COMPUTABLE` is a valid and expected answer.

## Running things

```bash
python -m pytest tests/          # the suite
bash scripts/test_ratchet.sh     # the ratchet: failures may only fall, collected may only rise
```

See [docs/ENGINE_TOPOLOGY.md](docs/ENGINE_TOPOLOGY.md) before changing engine wiring.
