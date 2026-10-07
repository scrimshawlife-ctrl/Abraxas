"""A frame's grade must be the WEAKEST member, not the strongest.

`_select_data_grade` ranked grades and kept the highest, so one `real` point among twenty
`simulated` ones labelled the whole frame `real`. An aggregate is only as strong as its weakest
member.
"""

from __future__ import annotations

from abraxas.evidence.data_grade import DERIVED, REAL, SIMULATED, UNDECLARED
from abraxas.metric_extractors.base import MetricPoint
from abraxas.tvm.frame import _select_data_grade


def _point(grade: str, n: int) -> MetricPoint:
    return MetricPoint(
        metric_id=f"m{n}",
        value=1.0,
        ts_utc="2026-01-01T00:00:00Z",
        window_start_utc=None,
        window_end_utc=None,
        source_id=f"s{n}",
        data_grade=grade,
    )


def test_one_real_among_many_simulated_does_not_carry_the_frame() -> None:
    points = [_point(SIMULATED, i) for i in range(20)] + [_point(REAL, 99)]
    assert _select_data_grade(points) == SIMULATED


def test_uniform_real_stays_real() -> None:
    assert _select_data_grade([_point(REAL, 0), _point(REAL, 1)]) == REAL


def test_undeclared_poisons_the_aggregate() -> None:
    assert _select_data_grade([_point(REAL, 0), _point(UNDECLARED, 1)]) == UNDECLARED


def test_derived_is_weaker_than_real() -> None:
    assert _select_data_grade([_point(REAL, 0), _point(DERIVED, 1)]) == DERIVED


def test_empty_input_is_undeclared() -> None:
    assert _select_data_grade([]) == UNDECLARED
