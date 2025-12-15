# abraxas/linguistic/rdv.py
# Replacement Direction Vector (RDV)

from __future__ import annotations
from typing import Dict
import math

from .tokenize import tokens

RDV_AXES = ("humor", "aggression", "authority", "intimacy", "nihilism", "irony")

# Minimal deterministic lexicons (extend over time; no placeholders in outputs—only used as weak priors)
_HUMOR = {"lol","lmao","rofl","clown","meme","goofy","silly","unhinged"}
_AGGR  = {"kill","destroy","trash","hate","stupid","idiot","wreck","smoke"}
_AUTH  = {"policy","official","expert","science","law","rules","compliance"}
_INTIM = {"feel","heart","care","safe","healing","love","friend","together"}
_NIHI  = {"nothing","pointless","doomed","dead","over","collapse","blackpill"}
_IRON  = {"sure","yeahright","asif","literally","unironically","based","cringe"}

def rdv_from_context(text: str) -> Dict[str, float]:
    """
    Replacement Direction Vector:
    deterministic shallow affect classifier using small lexicons.
    Outputs a normalized axis weight map.
    """
    ts = tokens(text)
    counts = {ax: 0.0 for ax in RDV_AXES}

    for t in ts:
        if t in _HUMOR: counts["humor"] += 1
        if t in _AGGR:  counts["aggression"] += 1
        if t in _AUTH:  counts["authority"] += 1
        if t in _INTIM: counts["intimacy"] += 1
        if t in _NIHI:  counts["nihilism"] += 1
        if t in _IRON:  counts["irony"] += 1

    # Normalize to [0,1] vector by L2 norm
    norm = math.sqrt(sum(v*v for v in counts.values())) or 1.0
    return {k: round(v / norm, 6) for k, v in counts.items()}
