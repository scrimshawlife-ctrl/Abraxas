from __future__ import annotations

from abraxas_ase.sdct.squares.grid import fill_grid, normalize_digits, normalize_letters


def test_square_grid_determinism() -> None:
    text = "Alpha 123 beta 456"
    letters = normalize_letters(text)
    digits = normalize_digits(text)
    letter_grid_a = fill_grid(letters, 5)
    letter_grid_b = fill_grid(letters, 5)
    digit_grid_a = fill_grid(digits, 3)
    digit_grid_b = fill_grid(digits, 3)

    assert letter_grid_a == letter_grid_b
    assert digit_grid_a == digit_grid_b
