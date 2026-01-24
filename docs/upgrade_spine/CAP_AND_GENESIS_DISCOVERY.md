Upgrade Spine v1 CLI is implemented in tools/run_upgrade_spine.py with collect/apply/promote flows, and tests live in tests/upgrade_spine/test_upgrade_spine.py.  
Docs-only candidates are not emitted by default adapters (evogate/shadow/rent/drift), so a safe docs-only candidate must be seeded manually into the candidate ledger for Genesis Proof.  
Artifact bundles are written under .aal/artifacts/upgrade_spine/<YYYY-MM-DD>/<candidate_id>/ with patch.diff, provenance.json, gate_report.json, and inputs_manifest.json.
