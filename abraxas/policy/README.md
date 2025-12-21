# Abraxas Non-Censorship Invariant

Abraxas MUST NEVER censor, filter, rewrite, or block user-facing outputs. Detectors and analytics may flag or log suspicious drift, but they must never alter what the user sees.

Allowed:
- Drift detection and provenance logging
- Metadata annotations that do **not** modify text

Forbidden:
- Any rewriting, redaction, sanitization, blocking, or refusal that changes the generated text before rendering
- Appending disclaimers, safety prefaces, or other post-hoc modifiers

Every rendering boundary must enforce this invariant with `assert_output_unchanged`.
