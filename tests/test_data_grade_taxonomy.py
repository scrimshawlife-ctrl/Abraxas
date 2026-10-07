"""The data grade must never be inferred from absence.

`data_grade` defaulted to `"real"` in three models and was coerced with `or "real"` at seven call
sites, so a packet that declared NOTHING was read as `"real"` -- observed in the world, the strongest
grade there is. The repository's own doctrine says the producer's declaration determines evidentiary
meaning; a default cannot. These tests pin the corrected contract.
"""

from __future__ import annotations

import pytest

from abraxas.evidence.data_grade import (
    DERIVED,
    GRADES,
    REAL,
    SIMULATED,
    UNDECLARED,
    declares_observation,
    normalize_grade,
    weakest_grade,
)


class TestNormalizeGrade:
    @pytest.mark.parametrize("value", [None, "", "   "])
    def test_absence_is_undeclared_not_real(self, value) -> None:
        assert normalize_grade(value) == UNDECLARED

    @pytest.mark.parametrize("value", [REAL, DERIVED, SIMULATED, UNDECLARED])
    def test_known_grades_pass_through(self, value) -> None:
        assert normalize_grade(value) == value

    def test_known_grades_pass_through_case_insensitively(self) -> None:
        assert normalize_grade("REAL") == REAL
        assert normalize_grade("  Simulated ") == SIMULATED

    @pytest.mark.parametrize("value", ["reel", "synthetic", "fixture", 0, False])
    def test_an_unknown_value_is_undeclared_not_a_guess(self, value) -> None:
        """A typo must not silently become the strongest grade."""
        assert normalize_grade(value) == UNDECLARED

    def test_every_grade_is_covered(self) -> None:
        assert GRADES == frozenset({REAL, DERIVED, SIMULATED, UNDECLARED})


class TestWeakestGrade:
    def test_the_weakest_member_decides(self) -> None:
        assert weakest_grade([REAL, REAL, SIMULATED]) == SIMULATED

    def test_an_undeclared_member_poisons_the_aggregate(self) -> None:
        assert weakest_grade([REAL, UNDECLARED]) == UNDECLARED

    def test_a_single_real_does_not_carry_a_simulated_frame(self) -> None:
        """The trust-inflation case: one strong member among many weak ones."""
        assert weakest_grade([SIMULATED] * 20 + [REAL]) == SIMULATED

    def test_an_empty_aggregate_is_undeclared(self) -> None:
        assert weakest_grade([]) == UNDECLARED

    def test_uniform_input_is_unchanged(self) -> None:
        assert weakest_grade([REAL, REAL]) == REAL

    def test_unknown_values_are_normalized_before_ranking(self) -> None:
        assert weakest_grade(["nonsense", SIMULATED]) == UNDECLARED


class TestDeclaresObservation:
    def test_only_real_declares_an_observation(self) -> None:
        assert declares_observation(REAL) is True
        for grade in (DERIVED, SIMULATED, UNDECLARED):
            assert declares_observation(grade) is False
