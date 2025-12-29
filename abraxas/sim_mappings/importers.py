"""CSV importer for simulation mapping scaffolds.

Imports parameter mappings from CSV rows without running full mapping logic.
Useful for batch scaffolding from paper_mapping_table.csv.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from abraxas.sim_mappings.registry import get_paper_ref
from abraxas.sim_mappings.types import (
    KnobVector,
    MappingResult,
    ModelFamily,
    ModelParam,
    PaperRef,
)


def parse_param_list(param_string: str) -> List[str]:
    """Parse semicolon-delimited parameter list.

    Args:
        param_string: Semicolon-delimited parameter names (e.g., "beta; gamma; c2")

    Returns:
        List of parameter names (whitespace stripped)

    Examples:
        >>> parse_param_list("beta; gamma; c2")
        ['beta', 'gamma', 'c2']

        >>> parse_param_list("")
        []

        >>> parse_param_list("  alpha  ")
        ['alpha']
    """
    if not param_string or not param_string.strip():
        return []

    # Split on semicolon and strip whitespace
    params = [p.strip() for p in param_string.split(";")]

    # Filter out empty strings
    return [p for p in params if p]


def import_mapping_from_csv_row(row_dict: Dict[str, str]) -> MappingResult:
    """Import mapping scaffold from CSV row.

    This function creates a MappingResult from a CSV row without running
    the full mapping logic. It's useful for batch scaffolding parameter
    mappings from paper_mapping_table.csv.

    The returned MappingResult has:
    - Paper reference (from registry if available)
    - Model family
    - Input parameters (names only, no values)
    - Stub KnobVector with LOW confidence and all values set to 0.0
    - Explanation indicating this is a CSV scaffold

    Args:
        row_dict: Dictionary with keys:
            - paper_id: Paper identifier
            - model_family: Model family (e.g., "DIFFUSION_SIR")
            - mri_params: Semicolon-delimited MRI parameter names
            - iri_params: Semicolon-delimited IRI parameter names
            - tau_params: Semicolon-delimited tau parameter names
            - notes: Optional notes about the mapping

    Returns:
        MappingResult with stub KnobVector (confidence='LOW', all values=0.0)

    Raises:
        ValueError: If paper_id or model_family is missing
        ValueError: If model_family is not a valid ModelFamily value

    Examples:
        >>> row = {
        ...     "paper_id": "PMC12281847",
        ...     "model_family": "DIFFUSION_SIR",
        ...     "mri_params": "beta; c2",
        ...     "iri_params": "gamma",
        ...     "tau_params": "delay",
        ...     "notes": "SIR with media impact"
        ... }
        >>> result = import_mapping_from_csv_row(row)
        >>> result.paper.paper_id
        'PMC12281847'
        >>> result.family
        ModelFamily.DIFFUSION_SIR
        >>> len(result.input_params)
        4
        >>> result.mapped.confidence
        'LOW'
    """
    # Validate required fields
    paper_id = row_dict.get("paper_id", "").strip()
    if not paper_id:
        raise ValueError("Missing required field: paper_id")

    family_str = row_dict.get("model_family", "").strip()
    if not family_str:
        raise ValueError("Missing required field: model_family")

    # Parse model family
    try:
        family = ModelFamily(family_str)
    except ValueError:
        raise ValueError(f"Invalid model_family: {family_str}")

    # Get or create paper reference
    paper = get_paper_ref(paper_id)
    if not paper:
        # Create stub paper ref if not in registry
        paper = PaperRef(
            paper_id=paper_id,
            title=f"Paper {paper_id}",
            url=f"https://example.com/{paper_id}",
            year=None,
        )

    # Parse parameter lists
    mri_param_names = parse_param_list(row_dict.get("mri_params", ""))
    iri_param_names = parse_param_list(row_dict.get("iri_params", ""))
    tau_param_names = parse_param_list(row_dict.get("tau_params", ""))

    # Create ModelParam objects (no values, just names)
    params: List[ModelParam] = []

    for name in mri_param_names:
        params.append(ModelParam(
            name=name,
            value=None,
            description=f"MRI parameter (from CSV scaffold)"
        ))

    for name in iri_param_names:
        params.append(ModelParam(
            name=name,
            value=None,
            description=f"IRI parameter (from CSV scaffold)"
        ))

    for name in tau_param_names:
        params.append(ModelParam(
            name=name,
            value=None,
            description=f"Tau parameter (from CSV scaffold)"
        ))

    # Create stub KnobVector
    stub_knobs = KnobVector(
        mri=0.0,
        iri=0.0,
        tau_latency=0.0,
        tau_memory=0.0,
        confidence="LOW",
        explanation=(
            f"Imported from CSV scaffold for {paper_id}. "
            f"No numeric mapping performed. "
            f"MRI params: {', '.join(mri_param_names) if mri_param_names else 'none'}. "
            f"IRI params: {', '.join(iri_param_names) if iri_param_names else 'none'}. "
            f"Tau params: {', '.join(tau_param_names) if tau_param_names else 'none'}."
        )
    )

    # Get notes
    notes = row_dict.get("notes", "")

    # Create MappingResult
    return MappingResult(
        paper=paper,
        family=family,
        input_params=params,
        mapped=stub_knobs,
        notes=notes,
    )


def import_mappings_from_csv(csv_path: str) -> List[MappingResult]:
    """Import all mapping scaffolds from CSV file.

    Args:
        csv_path: Path to paper_mapping_table.csv

    Returns:
        List of MappingResult objects

    Raises:
        FileNotFoundError: If CSV file doesn't exist
        ValueError: If CSV has invalid format or missing required columns

    Examples:
        >>> results = import_mappings_from_csv("data/sim_sources/paper_mapping_table.csv")
        >>> len(results) > 0
        True
    """
    import csv
    from pathlib import Path

    csv_file = Path(csv_path)
    if not csv_file.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    results: List[MappingResult] = []

    with open(csv_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        # Validate required columns
        required_cols = {"paper_id", "model_family", "mri_params", "iri_params", "tau_params"}
        if reader.fieldnames is None:
            raise ValueError("CSV file has no header row")

        missing_cols = required_cols - set(reader.fieldnames)
        if missing_cols:
            raise ValueError(f"CSV missing required columns: {missing_cols}")

        for row in reader:
            result = import_mapping_from_csv_row(row)
            results.append(result)

    return results


__all__ = [
    "parse_param_list",
    "import_mapping_from_csv_row",
    "import_mappings_from_csv",
]
