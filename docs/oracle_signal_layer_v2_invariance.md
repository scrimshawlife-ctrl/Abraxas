# Oracle Signal Layer v2 Invariance

## Strategy
- Canonicalize hashable input core only.
- Canonicalize authority payload separately from full output envelope.
- Compare digest triplet first across repeated runs.
- Emit mismatch payload only when digest instability is detected.

## Stability gates
- Identical canonical input must yield identical `input_hash`.
- Advisory/display metadata must not destabilize `authority_hash`.
- Full envelope digest includes advisory attachments and should remain deterministic when inputs are fixed.

- Mismatch report now includes canonical authority/full envelope blobs only when digest drift is detected.
