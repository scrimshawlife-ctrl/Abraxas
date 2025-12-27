from __future__ import annotations

from typing import Any, Dict

from abraxas.disinfo.metrics import (
    narrative_manipulation_pressure,
    provenance_integrity,
    synthetic_media_likelihood,
)


def apply_disinfo_metrics(item: Dict[str, Any]) -> Dict[str, Any]:
    """
    Adds:
      item["disinfo"] = { PI, SML, NMP }
      item["pi"] = PI (for SML reuse)
    """
    if not isinstance(item, dict):
        return item

    pi = provenance_integrity(item).to_dict()
    item["pi"] = pi
    sml = synthetic_media_likelihood(item).to_dict()
    nmp = narrative_manipulation_pressure(item).to_dict()

    item["disinfo"] = {"PI": pi, "SML": sml, "NMP": nmp}
    return item
