from __future__ import annotations

from abraxas_ase.sdct.squares.grid import extract_readings_letter, fill_grid


def test_square_readings_extraction() -> None:
    chars = "abcdefghijklmnopqrstuvwxy"  # 25 letters
    grid = fill_grid(chars, 5)
    readings = extract_readings_letter(grid, include_diagonals=False)

    assert "abcde" in readings
    assert "fghij" in readings
    assert "afkpu" in readings
    assert "ejoty" in readings
    assert readings == sorted(readings)
