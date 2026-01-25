from __future__ import annotations

import hashlib
from typing import List


_LETTERS = "abcdefghijklmnopqrstuvwxyz"
_DIGITS = "0123456789"


def normalize_letters(s: str) -> str:
    return "".join(ch for ch in s.lower() if ch.isalpha())


def normalize_digits(s: str) -> str:
    return "".join(ch for ch in s if ch.isdigit())


def _expand_chars(seed: str, total: int, alphabet: str) -> str:
    base = seed or ""
    digest = hashlib.sha256(base.encode("utf-8")).digest()
    out = []
    idx = 0
    while len(out) < total:
        if idx >= len(digest):
            digest = hashlib.sha256(digest).digest()
            idx = 0
        out.append(alphabet[digest[idx] % len(alphabet)])
        idx += 1
    return "".join(out)


def fill_grid(chars: str, n: int) -> List[List[str]]:
    if n <= 0:
        raise ValueError("grid size must be positive")
    total = n * n
    alphabet = _DIGITS if chars.isdigit() else _LETTERS
    if len(chars) >= total:
        expanded = chars[:total]
    else:
        expanded = chars + _expand_chars(chars, total - len(chars), alphabet)
    grid = []
    idx = 0
    for _ in range(n):
        row = list(expanded[idx:idx + n])
        grid.append(row)
        idx += n
    return grid


def extract_readings_letter(grid: List[List[str]], include_diagonals: bool) -> List[str]:
    readings: List[str] = []
    size = len(grid)
    for row in grid:
        if len(row) != size:
            raise ValueError("grid must be square")
        readings.append("".join(row))
    for c in range(size):
        readings.append("".join(grid[r][c] for r in range(size)))
    if include_diagonals:
        readings.append("".join(grid[i][i] for i in range(size)))
        readings.append("".join(grid[i][size - 1 - i] for i in range(size)))
    readings = [r for r in readings if len(r) >= 3]
    return sorted(set(readings))


def extract_invariants_digit(grid: List[List[str]]) -> dict:
    size = len(grid)
    row_sums = []
    col_sums = []
    diag_sums = []
    for row in grid:
        if len(row) != size:
            raise ValueError("grid must be square")
        row_sums.append(sum(int(v) for v in row))
    for c in range(size):
        col_sums.append(sum(int(grid[r][c]) for r in range(size)))
    diag_sums.append(sum(int(grid[i][i]) for i in range(size)))
    diag_sums.append(sum(int(grid[i][size - 1 - i]) for i in range(size)))
    return {
        "row_sums": row_sums,
        "col_sums": col_sums,
        "diag_sums": diag_sums,
        "row_mod9": [v % 9 for v in row_sums],
        "col_mod9": [v % 9 for v in col_sums],
        "diag_mod9": [v % 9 for v in diag_sums],
    }
