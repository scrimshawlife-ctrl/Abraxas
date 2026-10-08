"""The KANBAN engine table must match what the survey script measures.

WHY THIS EXISTS
    The table showed `86% (6/7)` integration for all five live engines while the script
    corroborated all seven criteria. The row was internally consistent (combined 93% really is
    mean(86, 100)), so no arithmetic self-check could have caught it. Only a comparison against
    the measurement can, which is what this does.

    A status table that drifts one stage behind is the same defect class as a stale test count or
    a README claiming production: an instrument reporting something the code contradicts.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
KANBAN = REPO_ROOT / "KANBAN.md"
SURVEY = REPO_ROOT / "scripts" / "survey_engine_settlements.py"

_ROW = re.compile(r"^\|\s*`([a-z]+)`\s*\|\s*(live|planned)\s*\|(.*)\|\s*$")


def _table_rows() -> dict[str, tuple[str, int]]:
    """{engine: (status, integration numerator out of 7)} from the KANBAN table."""
    found: dict[str, tuple[str, int]] = {}
    for line in KANBAN.read_text(encoding="utf-8").splitlines():
        match = _ROW.match(line)
        if not match:
            continue
        engine, status, rest = match.group(1), match.group(2), match.group(3)
        cells = [cell.strip() for cell in rest.split("|")]
        integration = next((c for c in cells if re.match(r"\d+% \(\d+/7\)", c)), None)
        if integration is None:
            continue
        numerator = int(re.search(r"\((\d+)/7\)", integration).group(1))
        found[engine] = (status, numerator)
    return found


def _surveyed() -> dict[str, tuple[str, int, int]]:
    """{engine: (status, count 'yes', count '?')} from the survey script.

    The script prints the JSON array and then a human summary line
    ("engines declaring technical settlement and corroborated: [...]"), so `json.loads` on the
    whole stdout raises "Extra data". `raw_decode` reads the first JSON value and ignores the
    trailing line, which is what we want here.

    The '?' count is returned because a '?' means NOT MEASURABLE (run-required criteria that need
    a real execution comparison), not zero. An engine with '?' cannot be compared against the
    table, and asserting on it would be this guard claiming more than its measurement supports.
    """
    proc = subprocess.run(
        [sys.executable, str(SURVEY), "--json"],
        cwd=REPO_ROOT, capture_output=True, text=True, timeout=300,
    )
    assert proc.returncode == 0, (
        f"survey script failed (exit {proc.returncode}):\n{proc.stderr[-2000:]}"
    )
    try:
        rows, _ = json.JSONDecoder().raw_decode(proc.stdout)
    except json.JSONDecodeError as exc:
        raise AssertionError(
            f"could not parse the survey's JSON output ({exc}).\n"
            f"stdout head: {proc.stdout[:400]!r}"
        ) from exc
    out: dict[str, tuple[str, int, int]] = {}
    for row in rows:
        values = list(row["criteria"].values())
        out[row["engine"]] = (
            row["status"],
            sum(1 for value in values if value == "yes"),
            sum(1 for value in values if value == "?"),
        )
    return out


def test_the_engine_table_matches_the_survey() -> None:
    table = _table_rows()
    surveyed = _surveyed()

    assert table, "no engine rows parsed from KANBAN.md -- the table may have moved"
    assert surveyed, "survey script returned no engines"

    missing = sorted(set(table) - set(surveyed))
    assert not missing, f"engines in the KANBAN table but not in the survey: {missing}"
    absent = sorted(set(surveyed) - set(table))
    assert not absent, (
        f"engines the survey measures but the KANBAN table omits: {absent}"
    )

    problems: list[str] = []
    compared = 0
    for engine in sorted(table):
        t_status, t_integration = table[engine]
        s_status, s_yes, s_unmeasurable = surveyed[engine]
        if t_status != s_status:
            problems.append(
                f"{engine}: table says status={t_status!r}, survey says {s_status!r}"
            )
        # Only compare the integration numerator where the survey could actually measure every
        # criterion. A '?' is not a zero, so comparing it would make this guard assert something
        # its own measurement does not support.
        if s_unmeasurable:
            continue
        compared += 1
        if t_integration != s_yes:
            problems.append(
                f"{engine}: table says integration {t_integration}/7, survey measures {s_yes}/7"
            )

    assert compared, (
        "the survey reported no fully measurable engine, so this guard asserted nothing. "
        "Investigate before trusting it."
    )
    assert not problems, (
        "the KANBAN engine table disagrees with scripts/survey_engine_settlements.py:\n  "
        + "\n  ".join(problems)
        + "\n\nRe-run the survey and update the table. Do not edit this test to agree with the "
        "table; the survey measures, the table asserts."
    )
