"""No code path may eagerly default a data grade to "real".

This guard exists because the naive check for it is a false-positive generator. The obvious
verification is

    grep -rn 'or "real"' abraxas --include="*.py"

and that matches `abraxas/evidence/data_grade.py` -- not because the module contains the defect, but
because its docstring *describes* the defect, quoting the exact expression it was written to
explain. An implementer who takes that grep as the acceptance criterion has two ways to make it
quiet, and only one of them is right:

* fix the code -- correct; or
* reword the documentation until the pattern stops matching -- which destroys the explanation of
  why the module exists, and was in fact done once, as an uncommitted edit, before this guard
  replaced the grep.

So the check is structural rather than textual: parse the source and look for the *syntax* of an
eager default, which prose cannot impersonate. `x or "real"` is an `ast.BoolOp(Or)` whose right
operand is the constant `"real"`; `Field(default="real")` is a call keyword. Neither appears inside
a docstring, because a docstring is a string, not an expression.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
PACKAGE = REPO / "abraxas"


def _eager_real_sites(path: Path) -> list[str]:
    """Every place in ``path`` that eagerly produces ``"real"`` in CODE.

    Returns ``["<line>: <description>"]``. A docstring or comment mentioning ``or "real"`` is not a
    site -- it is not an expression, so the walk never sees it.
    """
    found: list[str] = []
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.BoolOp) and isinstance(node.op, ast.Or):
            for operand in node.values[1:]:
                if isinstance(operand, ast.Constant) and operand.value == "real":
                    found.append(f"{node.lineno}: `or \"real\"` -> {ast.unparse(node)[:70]}")
        if isinstance(node, ast.Call):
            for kw in node.keywords:
                if (
                    kw.arg == "default"
                    and isinstance(kw.value, ast.Constant)
                    and kw.value.value == "real"
                ):
                    found.append(
                        f"{node.lineno}: `default=\"real\"` -> {ast.unparse(node)[:70]}"
                    )
    return found


def _all_eager_real_sites() -> dict[str, list[str]]:
    sites: dict[str, list[str]] = {}
    for f in sorted(PACKAGE.rglob("*.py")):
        if "__pycache__" in str(f):
            continue
        found = _eager_real_sites(f)
        if found:
            sites[str(f.relative_to(REPO))] = found
    return sites


class TestNoEagerRealRemains:
    def test_no_eager_real_coercion_or_default_in_the_package(self) -> None:
        sites = _all_eager_real_sites()
        assert sites == {}, (
            "a data grade is still eagerly defaulted to \"real\" somewhere in code. An undeclared "
            "grade must stay undeclared -- absence is not a claim:\n"
            + "\n".join(f"  {path}: {line}" for path, lines in sites.items() for line in lines)
        )

    def test_the_module_that_documents_the_defect_has_no_code_defect(self) -> None:
        """The module whose docstring quotes the old expression must itself be clean.

        This is the specific confusion the textual grep created: the documentation carrier is
        flagged by prose, so the guard must be able to say 'that file is fine'.
        """
        assert _eager_real_sites(PACKAGE / "evidence" / "data_grade.py") == []

    def test_the_docstring_still_documents_the_defect(self) -> None:
        """And the prose must NOT have been weakened to satisfy a checker.

        The module's docstring is the explanation of why it exists. If a future implementer quiets
        a grep by rewording it, this fails and says so.
        """
        doc = (PACKAGE / "evidence" / "data_grade.py").read_text(encoding="utf-8")
        assert 'or "real"' in doc, (
            "abraxas/evidence/data_grade.py no longer quotes the expression it was written to "
            "explain. Documentation of a defect must not be weakened to make a search quiet -- "
            "fix the search, not the prose."
        )
        assert '"real"' in doc

    def test_the_three_model_defaults_are_undeclared(self) -> None:
        from abraxas.evidence.data_grade import UNDECLARED
        from abraxas.metric_extractors.base import MetricPoint
        from abraxas.sources.packets import SourcePacket

        assert MetricPoint.model_fields["data_grade"].default == UNDECLARED
        assert SourcePacket.model_fields["data_grade"].default == UNDECLARED

    def test_a_point_constructed_without_a_grade_is_undeclared(self) -> None:
        from abraxas.evidence.data_grade import UNDECLARED
        from abraxas.metric_extractors.base import MetricPoint

        point = MetricPoint(
            metric_id="m", value=1.0, ts_utc="2026-01-01T00:00:00Z",
            window_start_utc=None, window_end_utc=None, source_id="s",
        )
        assert point.data_grade == UNDECLARED

    def test_a_packet_constructed_without_a_grade_is_undeclared(self) -> None:
        from abraxas.evidence.data_grade import UNDECLARED
        from abraxas.sources.packets import SourcePacket

        packet = SourcePacket(
            source_id="s", observed_at_utc="2026-01-01T00:00:00Z",
            window_start_utc=None, window_end_utc=None, payload={},
        )
        assert packet.data_grade == UNDECLARED


class TestTheGuardCanFail:
    """A guard nobody has seen fail is not known to be a guard."""

    @pytest.mark.parametrize(
        "snippet,expected_fragment",
        [
            ('x = packet.get("data_grade") or "real"', 'or "real"'),
            ('g = str(grade) or "real"', 'or "real"'),
            ("data_grade: str = Field(default=\"real\")", 'default="real"'),
        ],
    )
    def test_it_flags_a_synthetic_violation(
        self, tmp_path: Path, snippet: str, expected_fragment: str
    ) -> None:
        f = tmp_path / "violating.py"
        f.write_text(snippet + "\n", encoding="utf-8")
        found = _eager_real_sites(f)
        assert any(expected_fragment in line for line in found), (
            f"the guard did not flag {snippet!r}; it returned {found}"
        )

    def test_it_does_NOT_flag_the_same_string_in_a_DOCSTRING(self, tmp_path: Path) -> None:
        """The counterfactual that makes this guard worth having.

        The exact text that made the naive grep useless must pass here, because it is prose.
        """
        f = tmp_path / "documenting.py"
        f.write_text(
            '"""Explains that grade was coerced with `or "real"` at seven call sites."""\n'
            "VALUE = 1\n",
            encoding="utf-8",
        )
        assert _eager_real_sites(f) == [], (
            "the guard flagged a docstring -- it is behaving like the textual grep it replaced"
        )
