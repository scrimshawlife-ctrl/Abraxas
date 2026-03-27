from __future__ import annotations

from abx.observability.types import OperatorInsightView
from abx.operator.insightSections import build_insight_sections
from abx.operator.insightViews import list_insight_views
from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


def assemble_operator_insight_view(*, run_id: str, linkage_refs: dict[str, str]) -> OperatorInsightView:
    sections = build_insight_sections(run_id=run_id, linkage_refs=linkage_refs)
    overview = {
        "availableViews": list_insight_views(),
        "linkedSurfaceCount": len(linkage_refs),
    }
    drilldown = sections
    digest = sha256_bytes(dumps_stable({"run_id": run_id, "overview": overview, "drilldown": drilldown}).encode("utf-8"))
    return OperatorInsightView(
        view_id=f"operator-insight-{run_id}",
        run_id=run_id,
        overview=overview,
        drilldown=drilldown,
        view_hash=digest,
    )
