"""Guards the rune-id wiring in abx/kernel.py against registry drift.

WHY THIS EXISTS
    A refactor renamed the 62 dotted `capability_id` literals to the `RUNE.<PATH>` convention.
    It was applied atomically, and its own verification reported "leftovers: 0 (verified -- no
    old literal survives in any target)". But the kernel routes on a RUNE id, which lives in
    registry/abx_rune_registry.json under a `rune_id` key -- outside that scan's scope. So the
    rename changed the dispatch guard to the CAPABILITY id, which matches no rune:

        invoke("compression.detect")        -> fell through to the else: branch, returning
                                               not_computable/kernel_route_missing
        invoke("RUNE.COMPRESSION.DETECT")   -> ValueError: Unknown rune_id, so the
                                               `abx compress` command could not run at all

    Nothing caught it: the suite was green and no test referenced the rune. These two checks are
    the missing instrument -- one static (every dispatch guard must name a registered rune), one
    behavioural (a registered rune must actually be routed, not silently fall through).
"""

from __future__ import annotations

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
KERNEL = REPO_ROOT / "abx" / "kernel.py"
RUNE_REGISTRY = REPO_ROOT / "registry" / "abx_rune_registry.json"


def _dispatch_guard_ids() -> set[str]:
    """Every rune id abx/kernel.py compares against."""
    source = KERNEL.read_text(encoding="utf-8")
    return set(re.findall(r'rune_id == "([^"]+)"', source))


def _registered_rune_ids() -> set[str]:
    data = json.loads(RUNE_REGISTRY.read_text(encoding="utf-8"))
    return {rune["rune_id"] for rune in data["runes"]}


def test_every_dispatch_guard_names_a_registered_rune() -> None:
    """A guard naming an unregistered rune is unreachable by construction.

    This is the check whose absence let the rename break compression.detect: the guard read
    RUNE.COMPRESSION.DETECT while the registry declared compression.detect.
    """
    guards = _dispatch_guard_ids()
    registered = _registered_rune_ids()

    assert guards, "no dispatch guards found -- the extraction pattern has drifted from kernel.py"

    unregistered = sorted(guards - registered)
    assert not unregistered, (
        "abx/kernel.py dispatches on rune id(s) that registry/abx_rune_registry.json does not "
        f"declare, so the branch can never be reached: {unregistered}. Registered ids: "
        f"{sorted(registered)}"
    )


def test_the_compression_rune_is_routed_not_silently_unrouted() -> None:
    """A registered rune must reach its handler.

    invoke()'s else: branch returns a well-formed not_computable envelope rather than raising,
    so an unrouted rune is indistinguishable from a legitimate result unless asserted on. This
    drives the rune and fails on exactly that envelope.
    """
    from abx.kernel import invoke

    result = invoke(
        "compression.detect",
        {"text_event": "the establishment is cooking the books", "lexicon": [], "config": {}},
        context={},
    )

    not_computable = result.get("not_computable")
    if isinstance(not_computable, dict):
        assert not_computable.get("reason_code") != "kernel_route_missing", (
            "compression.detect is registered but reaches no handler -- invoke() fell through to "
            "the kernel_route_missing branch. Check that abx/kernel.py routes on the RUNE id "
            f"('compression.detect'), not the capability id. Got: {not_computable}"
        )
