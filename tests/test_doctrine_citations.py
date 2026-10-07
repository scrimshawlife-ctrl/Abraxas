"""Guard: every citation in docs/DOCTRINE.md resolves.

The doctrine document is a set of checkable claims about this repository — `path:line`
references, quotations of source text, and a table of surfaces that are deliberately absent.
Verifying them by hand once proves they were right once. This makes it a permanent guard, in the
same spirit as `test_engine_manifest_agreement.py`: if the code moves or the doc drifts, the
suite says so instead of the reader discovering it.

The checks live in `_problems()` so the failure modes are themselves tested. A guard nobody has
seen fail is not known to be a guard — see `TestTheGuardCanFail` below.

Conventions this depends on, both stated in the document itself:

  * A fenced block is treated as a QUOTATION only when the prose introducing it contains the word
    "verbatim". Otherwise it is illustrative (a diagram, a schematic) and is not matched against
    source. Without this distinction the flywheel diagram would be required to appear in the code,
    which is not what it claims.
  * A row of the "Present here?" table ending in `| no |` declares its paths ABSENT. Those are
    asserted absent, so a later port that adds them fails here and forces the table to be updated.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
DOC = REPO / "docs" / "DOCTRINE.md"
INDEX = REPO / "docs" / "README.md"

#: Roots searched when looking for source text quoted by the document. Kept explicit so a quote
#: cannot be "found" inside the document itself, which would certify nothing.
SOURCE_GLOBS = ("abraxas/**/*.py", "abx/**/*.py", "docs/**/*.md", "contracts/**/*.json")

_CITE = re.compile(r"`([A-Za-z0-9_./\-]+\.(?:py|md|json|ya?ml)):(\d+)`")
_BARE = re.compile(r"`([A-Za-z0-9_./\-]+\.[A-Za-z0-9]+)`")
_QUOTE = re.compile(r'\*"([^"]+)"\*')
#: Horizontal whitespace ONLY. `\s*` here was a real bug: `\s` matches newlines, so the indent
#: group swallowed the preceding newline (`opening` became "\n"), the closing-fence search then
#: looked for a doubled newline, found nothing, and EVERY block was silently skipped -- a guard
#: reporting clean over a document it never examined.
_FENCE = re.compile(r"^([ \t]*)```[ \t]*$", re.M)
_ABSENT_ROW = re.compile(r"^\|\s*(.+?)\s*\|\s*no\s*\|\s*$", re.M)


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _source_texts() -> dict[str, str]:
    out: dict[str, str] = {}
    for pattern in SOURCE_GLOBS:
        for f in REPO.glob(pattern):
            if "__pycache__" in str(f) or f.resolve() == DOC.resolve():
                continue
            out[str(f.relative_to(REPO))] = _norm(f.read_text(errors="replace"))
    return out


def _fenced_blocks(text: str) -> list[tuple[str, bool]]:
    """Return [(block, is_quotation)] for every fenced block.

    Handles INDENTED fences: a fence inside a list item has leading whitespace, so a
    line-anchored ``` regex silently skips it and would report a clean run over a quote it
    never examined.
    """
    blocks: list[tuple[str, bool]] = []
    for m in _FENCE.finditer(text):
        opening = m.group(1)
        end = text.find("\n" + opening + "```", m.end())
        if end == -1:
            continue
        body = text[m.end():end].strip("\n")
        # Label lookup: the IMMEDIATELY PRECEDING paragraph, not a fixed character window. A
        # window missed the real document's label -- "verbatim" sat 177 chars back, but a longer
        # preceding paragraph pushed it outside 400 -- and a large window could equally pick up
        # "verbatim" from an unrelated earlier paragraph.
        preface = text[:m.start()].rstrip().rsplit("\n\n", 1)[-1]
        blocks.append((body, "verbatim" in preface.lower()))
    return blocks


def _problems(
    text: str,
    *,
    source_texts: dict[str, str] | None = None,
    index_path: Path | None = None,
) -> list[str]:
    """Every reason this document fails its own citations. Empty list means it verifies."""
    problems: list[str] = []
    sources = source_texts if source_texts is not None else _source_texts()
    index = index_path if index_path is not None else INDEX

    # 1. path:line citations must exist and be in range
    for path, lineno in sorted(set(_CITE.findall(text))):
        f = REPO / path
        if not f.is_file():
            problems.append(f"cited file does not exist: {path}:{lineno}")
            continue
        lines = f.read_text(errors="replace").split("\n")
        if int(lineno) > len(lines):
            problems.append(
                f"cited line out of range: {path}:{lineno} (file has {len(lines)} lines)"
            )
        elif not lines[int(lineno) - 1].strip():
            problems.append(f"cited line is blank: {path}:{lineno}")

    # 2. blocks the document labels VERBATIM must appear in a source file
    for body, is_quotation in _fenced_blocks(text):
        if not is_quotation:
            continue
        needle = _norm(body)
        if not any(needle in src for src in sources.values()):
            problems.append(
                "block labelled verbatim does not appear in any source file: "
                f"{needle[:70]!r}"
            )

    # 3. quoted laws must appear in a source file
    for quote in sorted(set(_QUOTE.findall(text))):
        if not any(_norm(quote) in src for src in sources.values()):
            problems.append(f"quoted text not found in any source file: {quote[:60]!r}")

    # 4. rows declared ABSENT must actually be absent
    for row in _ABSENT_ROW.findall(text):
        for path in _BARE.findall(row):
            if (REPO / path).exists():
                problems.append(
                    f"declared absent but exists: {path} -- update the table in {DOC.name}"
                )

    # 5. the document must be reachable from the docs index
    if index.is_file():
        if DOC.name not in index.read_text(errors="replace"):
            problems.append(f"{DOC.name} is not linked from {index.name}")

    return problems


class TestTheDocumentVerifies:
    def test_every_citation_resolves(self) -> None:
        assert DOC.is_file(), "docs/DOCTRINE.md is missing"
        problems = _problems(DOC.read_text())
        assert not problems, "DOCTRINE.md cites things that do not resolve:\n  - " + "\n  - ".join(
            problems
        )

    def test_it_actually_found_something_to_check(self) -> None:
        """A guard over an empty set passes trivially. Assert the doc has content to verify."""
        text = DOC.read_text()
        assert len(set(_CITE.findall(text))) >= 4, "too few path:line citations to be meaningful"
        assert any(q for _, q in _fenced_blocks(text)), "no verbatim block found"
        assert _ABSENT_ROW.search(text), "no absence table found"


class TestTheGuardCanFail:
    """Each failure mode, driven with synthetic text so the guard is known to be able to fail."""

    def test_detects_a_citation_to_a_missing_file(self) -> None:
        problems = _problems("see `abraxas/does_not_exist.py:3` for details")
        assert any("does not exist" in p for p in problems)

    def test_detects_a_line_beyond_the_end_of_the_file(self) -> None:
        problems = _problems("see `abraxas/runes/models.py:99999`")
        assert any("out of range" in p for p in problems)

    def test_detects_a_citation_to_a_blank_line(self) -> None:
        """Citing a blank line means citing nothing. The line is located, not hardcoded -- an
        earlier version of this test pinned line 22, which is not blank."""
        lines = (REPO / "abraxas/runes/models.py").read_text().split("\n")
        blank = next(n for n, l in enumerate(lines, 1) if not l.strip())

        problems = _problems(f"see `abraxas/runes/models.py:{blank}`")
        assert any("blank" in p for p in problems), problems

    def test_detects_a_REFORMATTED_quotation(self) -> None:
        """The exact defect this guard was built from: a quotation that was rewritten.

        The source says ``planned`` with DOUBLED backticks. Quoting it with single backticks is a
        paraphrase wearing quotation marks, and must fail.
        """
        reformatted = (
            "The invariant verbatim:\n\n"
            "```\n"
            "A `planned` engine must never be presented as available.\n"
            "```\n"
        )
        problems = _problems(reformatted)
        assert any("verbatim" in p for p in problems), problems

    def test_accepts_the_verbatim_form_of_the_same_quote(self) -> None:
        """Counterfactual to the above: the exact wording passes."""
        exact = (
            "The invariant verbatim:\n\n"
            "```\n"
            "A ``planned`` engine must never be presented as available.\n"
            "```\n"
        )
        problems = [p for p in _problems(exact) if "verbatim" in p]
        assert not problems, problems

    def test_ignores_an_illustrative_fence(self) -> None:
        """A diagram must NOT be required to appear in the source."""
        diagram = "The flywheel:\n\n```\nFIELD -> hypothesis -> LAB\n```\n"
        problems = [p for p in _problems(diagram) if "verbatim" in p]
        assert not problems, problems

    def test_detects_an_indented_fence(self) -> None:
        """An indented (list-item) fence must still be checked, or the guard silently skips it."""
        indented = (
            "2. Some invariant.\n\n"
            "   The invariant verbatim:\n\n"
            "   ```\n"
            "   A completely invented sentence that is nowhere in the source.\n"
            "   ```\n"
        )
        problems = _problems(indented)
        assert any("verbatim" in p for p in problems), (
            "indented fenced block was not examined at all"
        )

    def test_detects_an_absence_that_reappeared(self) -> None:
        """If a declared-absent surface is added, the table is stale and this must fire."""
        text = "| `abraxas/metric_extractors/base.py` | no |"
        problems = _problems(text)
        assert any("declared absent but exists" in p for p in problems), problems

    def test_detects_an_unlinked_document(self, tmp_path: Path) -> None:
        """A doc nobody links to is undiscoverable."""
        orphan_index = tmp_path / "README.md"
        orphan_index.write_text("# Index\n\n- something else entirely\n")

        problems = _problems("nothing cited here", source_texts={}, index_path=orphan_index)
        assert any("not linked from" in p for p in problems), problems

    def test_accepts_a_linked_document(self, tmp_path: Path) -> None:
        """Counterfactual: the same document passes when the index does link it."""
        good_index = tmp_path / "README.md"
        good_index.write_text(f"# Index\n\n- [{DOC.name}]({DOC.name})\n")

        problems = _problems("nothing cited here", source_texts={}, index_path=good_index)
        assert not any("not linked from" in p for p in problems), problems

    def test_ignores_a_missing_index(self, tmp_path: Path) -> None:
        """No index at all is not a citation defect; do not manufacture one."""
        problems = _problems(
            "nothing cited here", source_texts={}, index_path=tmp_path / "nope.md"
        )
        assert not any("not linked from" in p for p in problems), problems
