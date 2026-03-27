from __future__ import annotations

from abx.meta.types import CanonSurfaceRecord


def build_canon_surface_inventory() -> list[CanonSurfaceRecord]:
    return [
        CanonSurfaceRecord(
            canon_id="canon-governance-manifest",
            surface_ref="abx/governance/canonical_manifest.py",
            canon_class="authoritative-canon",
            domain_refs=["governance", "deployment", "security"],
            interpretation_boundary="canon",
            owner="canon-steward",
        ),
        CanonSurfaceRecord(
            canon_id="canon-change-control",
            surface_ref="abx/governance/change_control.py",
            canon_class="governed-derived-reference",
            domain_refs=["governance"],
            interpretation_boundary="implementation",
            owner="change-control-steward",
        ),
        CanonSurfaceRecord(
            canon_id="canon-wave-note-shadow",
            surface_ref="docs/governance_notes_shadow.md",
            canon_class="shadow-candidate",
            domain_refs=["documentation"],
            interpretation_boundary="interpretation",
            owner="documentation-steward",
        ),
        CanonSurfaceRecord(
            canon_id="canon-legacy-rules-v0",
            surface_ref="abx/governance/frozen/waivers_v1.json",
            canon_class="superseded-canon",
            domain_refs=["governance"],
            interpretation_boundary="historical-residue",
            owner="canon-steward",
        ),
    ]
