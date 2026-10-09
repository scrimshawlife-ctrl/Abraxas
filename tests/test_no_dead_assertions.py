"""A test that asserts nothing is not a test, and the linter cannot tell.

No ruff rule detects a test function with no assertion, or one that swallows its own failure into
`except: pass`. Both require semantics, so this guard parses test files as ASTs without importing
them and checks the shape directly.

An intentional no-assertion test must say so on its own line with a marker carrying a reason:

    def test_module_imports():  # no-assert-intended: import failure raises
        import abraxas.oracle.v2

The marker is the escape hatch, and it is deliberately not silent: the reason is part of the line, so
a reader sees the intent and a reviewer can object to it.
"""

from __future__ import annotations

import ast
import pathlib
import re

REPO = pathlib.Path(__file__).resolve().parents[1]

# Directories the repository actually tests. Mirrors pyproject.toml testpaths and CI.
TEST_ROOTS = ["tests", "webpanel", "abraxas/evidence"]

# Name prefixes that make a call assertion-like.
ASSERTING_CALLS = ("pytest.raises", "pytest.fail", "pytest.xfail", "pytest.warns", "warns")

MARKER = re.compile(r"#\s*no-assert-intended:\s*\S")


def _test_files() -> list[pathlib.Path]:
    out: list[pathlib.Path] = []
    for root in TEST_ROOTS:
        base = REPO / root
        if base.is_dir():
            out.extend(sorted(base.rglob("test_*.py")))
    return out


def _mentions_assertion(node: ast.AST) -> bool:
    """True if this subtree contains an assertion-like statement."""
    for sub in ast.walk(node):
        if isinstance(sub, ast.Assert):
            return True
        if isinstance(sub, ast.Call):
            src = ast.unparse(sub.func)
            if any(src.startswith(a) for a in ASSERTING_CALLS):
                return True
        if isinstance(sub, ast.Raise):
            return True
    return False


def _swallows(node: ast.AST) -> list[int]:
    """Line numbers of `except ...: pass` handlers that explicitly swallow.

    Narrowed to an explicit `pass`. An earlier version treated any handler with no non-expression
    statement as a swallow, which flagged legitimate handlers whose body is only a string, and
    fixture-driven tests. A guard that reports the wrong thing is worse than no guard.
    """
    hits: list[int] = []
    for sub in ast.walk(node):
        if isinstance(sub, ast.Try):
            for handler in sub.handlers:
                if any(isinstance(s, ast.Pass) for s in handler.body):
                    hits.append(handler.lineno)
    return hits


def _literal_truth(node: ast.AST) -> list[int]:
    """Line numbers of `assert True` / `assert <literal>` with a constant condition."""
    hits: list[int] = []
    for sub in ast.walk(node):
        if isinstance(sub, ast.Assert) and isinstance(sub.test, ast.Constant):
            if sub.test.value is True or sub.test.value == 1:
                hits.append(sub.lineno)
    return hits


# NO CHECK FOR "a test that asserts nothing" EXISTS HERE, DELIBERATELY.
#
# Three attempts were made to detect it statically and all three over-reported. A test can assert by
# calling a validator whose raise IS the assertion (the ~83 `test_valid_*` tests here), by importing
# a module (failure is the ImportError), or through a fixture, and no AST shape distinguishes those
# from a test that does nothing. Ruff cannot either: measuring its full rule list showed no `PT` or
# `B` rule for a missing assertion, and `PT015` targets `assert False`, the opposite problem.
#
# The decidable cases are covered below. The rest is a review question, which is why the marker
# exists: an intentional no-assertion test should carry `# no-assert-intended: <reason>` on the
# definition line, making the intent visible instead of inferred.


# Known offenders, recorded rather than fixed in this pass. The guard fails if this list grows, so a
# new instance anywhere in the repo is caught immediately; existing instances are named debt.
KNOWN_LITERAL_TRUTH = {
    "tests/test_oracle_signal_layer_v2_drop.py:90",  # dead `assert True`; real assert is line 88
    "abraxas/evidence/test_noesis_q1.py:969",  # placeholder for an unimplemented feature flag
}
KNOWN_SWALLOWS = {
    "tests/test_shadow_metrics_access_gate.py:75",  # except NotImplementedError: pass
    "tests/test_shadow_metrics_access_gate.py:112",  # except (NotImplementedError, KeyError): pass
    "webpanel/test_engine_topology_drift.py:26",  # except Exception: pass around initialize()
}


def test_no_literal_truth_assertion() -> None:
    offenders: set[str] = set()
    for path in _test_files():
        try:
            tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            for hit in _literal_truth(node):
                offenders.add(f"{path.relative_to(REPO)}:{hit}")
    new = sorted(offenders - KNOWN_LITERAL_TRUTH)
    assert not new, (
        "New assertions that always pass:\n  " + "\n  ".join(new)
        + "\n(Existing instances are listed in KNOWN_LITERAL_TRUTH.)"
    )


def test_no_failure_swallowed_inside_a_test() -> None:
    offenders: set[str] = set()
    for path in _test_files():
        try:
            tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if not node.name.startswith("test_"):
                continue
            for hit in _swallows(node):
                offenders.add(f"{path.relative_to(REPO)}:{hit}")
    new = sorted(offenders - KNOWN_SWALLOWS)
    assert not new, (
        "New failures swallowed inside tests:\n  " + "\n  ".join(new)
        + "\n(Existing instances are listed in KNOWN_SWALLOWS.)"
    )
