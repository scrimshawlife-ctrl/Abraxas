"""Evidence-Grade Artifact Packaging

Packages narratives with complete provenance chains for external consumption.

Design:
- Every artifact includes full provenance chain
- SHA-256 verification for all referenced evidence
- Structured JSON + human-readable markdown
- Ready for export, archival, or stakeholder distribution
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from abraxas.core.provenance import Provenance
from abraxas.core.canonical import sha256_hex, canonical_json


@dataclass(frozen=True)
class EvidenceArtifact:
    """Evidence-grade packaged artifact.

    Bundles narrative + provenance + evidence chain for external consumption.
    """

    artifact_id: str
    artifact_type: str  # "phase_transition", "resonance_spike", "cascade_trajectory", "comprehensive_report"
    narrative_content: str  # Human-readable narrative (markdown)
    narrative_metadata: Dict  # Narrative generation metadata
    evidence_chain: List[str]  # SHA-256 hashes of evidence bundles
    provenance_chain: List[Dict]  # Full provenance objects
    generated_at_utc: str
    package_version: str = "1.0.0"
    package_hash: str = ""  # SHA-256 of entire package

    def __post_init__(self):
        # Compute package hash if not provided
        if not self.package_hash:
            package_data = {
                "artifact_id": self.artifact_id,
                "artifact_type": self.artifact_type,
                "narrative_content": self.narrative_content,
                "narrative_metadata": self.narrative_metadata,
                "evidence_chain": self.evidence_chain,
                "provenance_chain": self.provenance_chain,
                "generated_at_utc": self.generated_at_utc,
                "package_version": self.package_version,
            }
            object.__setattr__(self, "package_hash", sha256_hex(canonical_json(package_data)))

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "artifact_id": self.artifact_id,
            "artifact_type": self.artifact_type,
            "narrative_content": self.narrative_content,
            "narrative_metadata": self.narrative_metadata,
            "evidence_chain": self.evidence_chain,
            "provenance_chain": self.provenance_chain,
            "generated_at_utc": self.generated_at_utc,
            "package_version": self.package_version,
            "package_hash": self.package_hash,
        }

    def to_json(self, indent: int = 2) -> str:
        """Export as JSON."""
        return json.dumps(self.to_dict(), indent=indent, sort_keys=True)

    def to_markdown(self) -> str:
        """Export as markdown with metadata header."""
        lines = []
        lines.append("---")
        lines.append(f"artifact_id: {self.artifact_id}")
        lines.append(f"artifact_type: {self.artifact_type}")
        lines.append(f"generated_at_utc: {self.generated_at_utc}")
        lines.append(f"package_version: {self.package_version}")
        lines.append(f"package_hash: {self.package_hash}")
        lines.append(f"evidence_chain_length: {len(self.evidence_chain)}")
        lines.append("---")
        lines.append("")
        lines.append(self.narrative_content)
        lines.append("")
        lines.append("## Provenance")
        lines.append("")
        lines.append(f"**Package Hash:** `{self.package_hash}`")
        lines.append(f"**Evidence Bundles:** {len(self.evidence_chain)}")
        lines.append("")
        for i, evidence_hash in enumerate(self.evidence_chain, 1):
            lines.append(f"{i}. `{evidence_hash[:16]}...`")
        lines.append("")
        return "\n".join(lines)


class ArtifactPackager:
    """
    Packages narratives with provenance for external consumption.

    Creates evidence-grade artifacts ready for:
    - Export to stakeholders
    - Archival storage
    - Audit trails
    - External analysis
    """

    def __init__(self, package_version: str = "1.0.0") -> None:
        """Initialize artifact packager.

        Args:
            package_version: Package format version (default "1.0.0")
        """
        self._package_version = package_version

    def package_narrative(
        self,
        narrative: any,  # GeneratedNarrative
        additional_evidence: Optional[List[str]] = None,
        additional_provenance: Optional[List[Provenance]] = None,
    ) -> EvidenceArtifact:
        """Package a generated narrative as evidence-grade artifact.

        Args:
            narrative: GeneratedNarrative object
            additional_evidence: Additional evidence hashes to include
            additional_provenance: Additional provenance objects to include

        Returns:
            EvidenceArtifact ready for export
        """
        # Build evidence chain
        evidence_chain = list(narrative.evidence_hashes)
        if additional_evidence:
            evidence_chain.extend(additional_evidence)

        # Build provenance chain
        provenance_chain = []
        if narrative.provenance:
            provenance_chain.append(narrative.provenance.__dict__)
        if additional_provenance:
            provenance_chain.extend([p.__dict__ for p in additional_provenance])

        # Narrative metadata
        metadata = {
            "narrative_id": narrative.narrative_id,
            "narrative_type": narrative.narrative_type,
            "template_version": narrative.template_version,
            "generated_at_utc": narrative.generated_at_utc,
        }

        artifact = EvidenceArtifact(
            artifact_id=f"ARTIFACT-{narrative.narrative_id}",
            artifact_type=narrative.narrative_type,
            narrative_content=narrative.content,
            narrative_metadata=metadata,
            evidence_chain=evidence_chain,
            provenance_chain=provenance_chain,
            generated_at_utc=narrative.generated_at_utc,
            package_version=self._package_version,
        )

        return artifact

    def package_comprehensive_report(
        self,
        report_content: str,
        narratives: List[any],  # List of GeneratedNarrative
        run_id: str,
    ) -> EvidenceArtifact:
        """Package comprehensive report as evidence-grade artifact.

        Args:
            report_content: Markdown report content
            narratives: List of GeneratedNarrative objects included
            run_id: Report run identifier

        Returns:
            EvidenceArtifact with complete report
        """
        timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

        # Aggregate evidence chains
        evidence_chain = []
        provenance_chain = []

        for narrative in narratives:
            evidence_chain.extend(narrative.evidence_hashes)
            if narrative.provenance:
                provenance_chain.append(narrative.provenance.__dict__)

        # Remove duplicates while preserving order
        seen = set()
        evidence_chain = [x for x in evidence_chain if not (x in seen or seen.add(x))]

        # Metadata
        metadata = {
            "run_id": run_id,
            "narrative_count": len(narratives),
            "narrative_types": list(set(n.narrative_type for n in narratives)),
            "generated_at_utc": timestamp,
        }

        artifact = EvidenceArtifact(
            artifact_id=f"ARTIFACT-REPORT-{run_id}",
            artifact_type="comprehensive_report",
            narrative_content=report_content,
            narrative_metadata=metadata,
            evidence_chain=evidence_chain,
            provenance_chain=provenance_chain,
            generated_at_utc=timestamp,
            package_version=self._package_version,
        )

        return artifact

    def export_artifact(
        self,
        artifact: EvidenceArtifact,
        output_dir: Path,
        formats: List[str] = ["json", "md"],
    ) -> Dict[str, Path]:
        """Export artifact to files.

        Args:
            artifact: EvidenceArtifact to export
            output_dir: Directory to write files
            formats: List of formats to export ("json", "md")

        Returns:
            Dict mapping format → file path
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        exported = {}

        # Export JSON
        if "json" in formats:
            json_path = output_dir / f"{artifact.artifact_id}.json"
            json_path.write_text(artifact.to_json(), encoding="utf-8")
            exported["json"] = json_path

        # Export Markdown
        if "md" in formats:
            md_path = output_dir / f"{artifact.artifact_id}.md"
            md_path.write_text(artifact.to_markdown(), encoding="utf-8")
            exported["md"] = md_path

        return exported


def create_artifact_packager(package_version: str = "1.0.0") -> ArtifactPackager:
    """Create artifact packager with default configuration.

    Args:
        package_version: Package format version (default "1.0.0")

    Returns:
        Configured ArtifactPackager
    """
    return ArtifactPackager(package_version=package_version)
