from __future__ import annotations
from typing import FrozenSet


def require_admin(perms: FrozenSet[str]) -> None:
    if "admin" not in perms:
        raise PermissionError("Admin permission required.")
