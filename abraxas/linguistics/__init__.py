"""Linguistic suite v0.1."""

from .normalize import tokenize, stable_lang, shingle
from .packets import LinguisticPacket, TextItem, build_text_item
from .autopoiesis import propose_sources

__all__ = [
    "tokenize",
    "stable_lang",
    "shingle",
    "LinguisticPacket",
    "TextItem",
    "build_text_item",
    "propose_sources",
]
