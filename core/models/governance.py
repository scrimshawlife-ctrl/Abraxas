from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Optional


class Authority(BaseModel):
    authority_id: str
    actor: str
    locked: bool = False
    scope: str = ""

    def is_locked(self) -> bool:
        return self.locked
