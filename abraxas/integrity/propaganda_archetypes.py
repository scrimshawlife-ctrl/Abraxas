"""Propaganda Archetypes: 12 canonical families with trigger signatures.

Each archetype is defined by:
- Name and description
- Trigger signatures (structured data for detection)
- Example patterns

These are reference definitions, not active detectors.
Detection logic is external (e.g., LLM-based or rule-based classifiers).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List


class PropagandaArchetype(str, Enum):
    """Canonical propaganda archetype families."""

    APPEAL_TO_AUTHORITY = "Appeal to Authority"
    BANDWAGON_EFFECT = "Bandwagon Effect"
    FEAR_THREAT_ESCALATION = "Fear/Threat Escalation"
    FALSE_DILEMMA = "False Dilemma"
    LOADED_LANGUAGE = "Loaded Language"
    NAME_CALLING_AD_HOMINEM = "Name-Calling/Ad Hominem"
    OVERSIMPLIFICATION = "Oversimplification"
    SCAPEGOATING = "Scapegoating"
    TESTIMONIAL_EXPLOITATION = "Testimonial Exploitation"
    TRANSFER_SYMBOL_HIJACKING = "Transfer (Symbol Hijacking)"
    REPETITION_SATURATION = "Repetition Saturation"
    SELECTIVE_OMISSION = "Selective Omission"


@dataclass(frozen=True)
class ArchetypeDefinition:
    """Complete definition for a propaganda archetype."""

    name: str
    description: str
    trigger_keywords: List[str]  # Example keywords that may signal this archetype
    structural_patterns: List[str]  # Structural patterns (e.g., "either...or")
    examples: List[str]


# Canonical registry of propaganda archetypes
PROPAGANDA_REGISTRY: Dict[PropagandaArchetype, ArchetypeDefinition] = {
    PropagandaArchetype.APPEAL_TO_AUTHORITY: ArchetypeDefinition(
        name="Appeal to Authority",
        description="Invokes authority figures or institutions to validate claims without evidence.",
        trigger_keywords=["expert", "scientists say", "according to", "official"],
        structural_patterns=["<authority> says <claim>", "as <expert> confirms"],
        examples=[
            "Leading scientists agree that...",
            "Experts confirm...",
            "Officials state...",
        ],
    ),
    PropagandaArchetype.BANDWAGON_EFFECT: ArchetypeDefinition(
        name="Bandwagon Effect",
        description="Encourages adoption by claiming widespread acceptance or popularity.",
        trigger_keywords=["everyone", "most people", "join the movement", "trending"],
        structural_patterns=["everyone is <action>", "most people <believe>"],
        examples=[
            "Everyone is switching to...",
            "Join millions who...",
            "The majority supports...",
        ],
    ),
    PropagandaArchetype.FEAR_THREAT_ESCALATION: ArchetypeDefinition(
        name="Fear/Threat Escalation",
        description="Amplifies fear or threat perception to motivate action or compliance.",
        trigger_keywords=["danger", "threat", "crisis", "urgent", "catastrophe"],
        structural_patterns=["if you don't <action>, <threat>", "<threat> is imminent"],
        examples=[
            "If we don't act now, disaster will strike...",
            "The threat is real and growing...",
            "Urgent action required to avoid...",
        ],
    ),
    PropagandaArchetype.FALSE_DILEMMA: ArchetypeDefinition(
        name="False Dilemma",
        description="Presents only two options when more exist, forcing binary choice.",
        trigger_keywords=["either", "or", "only two choices", "you must choose"],
        structural_patterns=["either <A> or <B>", "you're either with us or against us"],
        examples=[
            "You're either with us or against us.",
            "Either we act now or accept defeat.",
            "There are only two options...",
        ],
    ),
    PropagandaArchetype.LOADED_LANGUAGE: ArchetypeDefinition(
        name="Loaded Language",
        description="Uses emotionally charged words to influence perception.",
        trigger_keywords=["freedom", "tyranny", "patriot", "traitor", "hero", "villain"],
        structural_patterns=["<emotionally_charged_adjective> <noun>"],
        examples=[
            "Freedom-loving patriots...",
            "Tyrannical regime...",
            "Heroic resistance...",
        ],
    ),
    PropagandaArchetype.NAME_CALLING_AD_HOMINEM: ArchetypeDefinition(
        name="Name-Calling/Ad Hominem",
        description="Attacks person or group instead of addressing argument.",
        trigger_keywords=["idiot", "fool", "corrupt", "incompetent", "liar"],
        structural_patterns=["<target> is a <negative_label>"],
        examples=[
            "That politician is a corrupt liar.",
            "Only fools believe...",
            "The incompetent opposition...",
        ],
    ),
    PropagandaArchetype.OVERSIMPLIFICATION: ArchetypeDefinition(
        name="Oversimplification",
        description="Reduces complex issues to simplistic explanations or solutions.",
        trigger_keywords=["simple", "obvious", "clearly", "just", "only"],
        structural_patterns=["the solution is simple: <simplistic_action>"],
        examples=[
            "The solution is simple: just...",
            "It's obvious that...",
            "All we need to do is...",
        ],
    ),
    PropagandaArchetype.SCAPEGOATING: ArchetypeDefinition(
        name="Scapegoating",
        description="Blames a person or group for problems they did not cause.",
        trigger_keywords=["blame", "fault", "responsible for", "caused by"],
        structural_patterns=["<group> is to blame for <problem>"],
        examples=[
            "Immigrants are to blame for unemployment.",
            "The elite caused this crisis.",
            "It's their fault that...",
        ],
    ),
    PropagandaArchetype.TESTIMONIAL_EXPLOITATION: ArchetypeDefinition(
        name="Testimonial Exploitation",
        description="Uses endorsements or testimonials (real or fabricated) to validate claims.",
        trigger_keywords=["testimonial", "endorsement", "recommends", "trusts"],
        structural_patterns=["<celebrity/figure> endorses <product/idea>"],
        examples=[
            "Doctors recommend...",
            "Celebrity X endorses...",
            "I trust this brand because...",
        ],
    ),
    PropagandaArchetype.TRANSFER_SYMBOL_HIJACKING: ArchetypeDefinition(
        name="Transfer (Symbol Hijacking)",
        description="Associates idea/product with positive symbols to transfer their qualities.",
        trigger_keywords=["patriotic", "flag", "freedom", "heritage", "tradition"],
        structural_patterns=["<product> represents <positive_symbol>"],
        examples=[
            "This policy represents true patriotism.",
            "Our brand embodies freedom.",
            "Defending our heritage means...",
        ],
    ),
    PropagandaArchetype.REPETITION_SATURATION: ArchetypeDefinition(
        name="Repetition Saturation",
        description="Repeats message frequently to normalize and embed it in consciousness.",
        trigger_keywords=["again", "once more", "as I said", "repeated"],
        structural_patterns=["<message> [repeated multiple times]"],
        examples=[
            "As I've said before, and I'll say again...",
            "Let me repeat: ...",
            "[Same slogan repeated across media]",
        ],
    ),
    PropagandaArchetype.SELECTIVE_OMISSION: ArchetypeDefinition(
        name="Selective Omission",
        description="Deliberately omits context or information to shape narrative.",
        trigger_keywords=["[absence of context]", "[missing data]"],
        structural_patterns=["<claim> [without mentioning <critical_context>]"],
        examples=[
            "Crime is rising [omits: compared to all-time high last decade].",
            "Unemployment down [omits: labor force participation also down].",
            "Stock market at record highs [omits: inflation-adjusted decline].",
        ],
    ),
}


def get_archetype_definition(archetype: PropagandaArchetype) -> ArchetypeDefinition:
    """
    Get canonical definition for a propaganda archetype.

    Args:
        archetype: Propaganda archetype enum value

    Returns:
        ArchetypeDefinition
    """
    return PROPAGANDA_REGISTRY[archetype]


def list_all_archetypes() -> List[ArchetypeDefinition]:
    """
    List all propaganda archetypes.

    Returns:
        List of all ArchetypeDefinition objects
    """
    return list(PROPAGANDA_REGISTRY.values())
