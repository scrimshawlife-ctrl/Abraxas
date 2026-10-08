"""The README's test counts must not go stale. They did, twice.

README.md claimed "3,548 passing, 3,559 collected" on 2026-10-08 while the suite collected 3,806,
and the sentence itself carried a note that an earlier figure had been "stale by more than an
order of magnitude". A number with a documented history of going stale needs a comparator, not
another careful edit.

The floor used here is the LOCAL one (scripts/test_ratchet.sh, 3,779). The README reports what a
local run collects. CI collects more because it installs the server and postgres extras, so CI's
floor (3,850) is a different measurement and must not be compared against this sentence.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
README = REPO_ROOT / "README.md"

#: Local ratified floor from scripts/test_ratchet.sh. Raise both together.
LOCAL_COLLECTED_FLOOR = 3779


def _claimed_collected() -> int:
    text = README.read_text(encoding="utf-8")
    match = re.search(r"([0-9][0-9,]*)\s+collected", text)
    assert match, (
        "README no longer states a collected count. If the status section changed shape, update "
        "this pattern rather than deleting the check."
    )
    return int(match.group(1).replace(",", ""))


def test_readme_collected_count_is_above_the_ratcheted_floor() -> None:
    claimed = _claimed_collected()
    assert claimed >= LOCAL_COLLECTED_FLOOR, (
        f"README claims {claimed} collected, below the local ratcheted floor of "
        f"{LOCAL_COLLECTED_FLOOR}. Either the suite shrank (investigate, do not edit this test) or "
        f"the README was not updated after a change (fix the README)."
    )
