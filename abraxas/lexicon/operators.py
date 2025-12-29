"""
Domain-Specific Compression Operators

Beyond simple weight lookup:
- Politics: Ideology mapping, rhetoric detection
- Media: Platform-specific patterns, viral mechanics
- Finance: Market sentiment, institutional signals
- Conspiracy: Narrative threads, claim chains
- Technology: AI/disruption signals, innovation patterns
- Health: Medical discourse, public health signals
- Climate: Environmental discourse, sustainability patterns
- Social: Cultural movements, identity discourse
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from abraxas.lexicon.dce import DCECompressionResult, DCEEntry, LifecycleState


@dataclass(frozen=True)
class DomainSignal:
    """Extracted signal from domain-specific compression."""

    signal_type: str  # e.g., "ideology_left", "viral_acceleration", "fear_spike"
    strength: float  # [0, 1]
    evidence_tokens: Tuple[str, ...]
    meta: Dict[str, str]


class PoliticsOperator:
    """
    Political domain compression operator.

    Extracts:
    - Ideological signals (left/right/libertarian/authoritarian)
    - Rhetoric patterns (populist/technocratic/nationalist)
    - Polarization indicators
    """

    def __init__(self) -> None:
        # Ideology markers (simplified exemplars)
        self.left_markers = {"equality", "justice", "workers", "collective", "public"}
        self.right_markers = {"freedom", "individual", "market", "tradition", "private"}
        self.populist_markers = {"elite", "establishment", "people", "corrupt", "betrayal"}

    def extract_signals(self, result: DCECompressionResult) -> List[DomainSignal]:
        """Extract political signals from compression result."""
        signals: List[DomainSignal] = []

        matched_set = set(result.matched)

        # Ideology detection
        left_count = len(matched_set & self.left_markers)
        right_count = len(matched_set & self.right_markers)

        if left_count > 0:
            strength = min(1.0, left_count / 3.0)  # Saturate at 3 markers
            signals.append(
                DomainSignal(
                    signal_type="ideology_left",
                    strength=strength,
                    evidence_tokens=tuple(matched_set & self.left_markers),
                    meta={"count": str(left_count)},
                )
            )

        if right_count > 0:
            strength = min(1.0, right_count / 3.0)
            signals.append(
                DomainSignal(
                    signal_type="ideology_right",
                    strength=strength,
                    evidence_tokens=tuple(matched_set & self.right_markers),
                    meta={"count": str(right_count)},
                )
            )

        # Populism detection
        populist_count = len(matched_set & self.populist_markers)
        if populist_count >= 2:
            strength = min(1.0, populist_count / 4.0)
            signals.append(
                DomainSignal(
                    signal_type="rhetoric_populist",
                    strength=strength,
                    evidence_tokens=tuple(matched_set & self.populist_markers),
                    meta={"count": str(populist_count)},
                )
            )

        return signals


class MediaOperator:
    """
    Media domain compression operator.

    Extracts:
    - Platform signals (twitter/reddit/tiktok patterns)
    - Viral mechanics (shares/engagement/velocity)
    - Content type (meme/thread/longform)
    """

    def __init__(self) -> None:
        self.viral_markers = {"viral", "trending", "shares", "retweet", "boost"}
        self.engagement_markers = {"like", "comment", "reply", "upvote", "award"}
        self.meme_markers = {"meme", "copypasta", "shitpost", "based", "ratio"}

    def extract_signals(self, result: DCECompressionResult) -> List[DomainSignal]:
        """Extract media signals from compression result."""
        signals: List[DomainSignal] = []

        matched_set = set(result.matched)

        # Viral detection
        viral_count = len(matched_set & self.viral_markers)
        if viral_count > 0:
            strength = min(1.0, viral_count / 2.0)
            signals.append(
                DomainSignal(
                    signal_type="viral_acceleration",
                    strength=strength,
                    evidence_tokens=tuple(matched_set & self.viral_markers),
                    meta={"count": str(viral_count)},
                )
            )

        # Engagement detection
        engagement_count = len(matched_set & self.engagement_markers)
        if engagement_count >= 2:
            strength = min(1.0, engagement_count / 3.0)
            signals.append(
                DomainSignal(
                    signal_type="high_engagement",
                    strength=strength,
                    evidence_tokens=tuple(matched_set & self.engagement_markers),
                    meta={"count": str(engagement_count)},
                )
            )

        # Meme content detection
        meme_count = len(matched_set & self.meme_markers)
        if meme_count > 0:
            strength = min(1.0, meme_count / 2.0)
            signals.append(
                DomainSignal(
                    signal_type="content_meme",
                    strength=strength,
                    evidence_tokens=tuple(matched_set & self.meme_markers),
                    meta={"count": str(meme_count)},
                )
            )

        return signals


class FinanceOperator:
    """
    Financial domain compression operator.

    Extracts:
    - Sentiment signals (bullish/bearish/neutral)
    - Institutional signals (fed/sec/institutional)
    - Market condition (boom/bust/volatility)
    """

    def __init__(self) -> None:
        self.bullish_markers = {"bull", "moon", "pump", "buy", "long", "hodl"}
        self.bearish_markers = {"bear", "crash", "dump", "sell", "short", "rekt"}
        self.institutional_markers = {"fed", "sec", "treasury", "institutional", "regulation"}
        self.volatility_markers = {"volatility", "swing", "whipsaw", "choppy", "uncertain"}

    def extract_signals(self, result: DCECompressionResult) -> List[DomainSignal]:
        """Extract financial signals from compression result."""
        signals: List[DomainSignal] = []

        matched_set = set(result.matched)

        # Sentiment detection
        bullish_count = len(matched_set & self.bullish_markers)
        bearish_count = len(matched_set & self.bearish_markers)

        if bullish_count > 0:
            strength = min(1.0, bullish_count / 3.0)
            signals.append(
                DomainSignal(
                    signal_type="sentiment_bullish",
                    strength=strength,
                    evidence_tokens=tuple(matched_set & self.bullish_markers),
                    meta={"count": str(bullish_count)},
                )
            )

        if bearish_count > 0:
            strength = min(1.0, bearish_count / 3.0)
            signals.append(
                DomainSignal(
                    signal_type="sentiment_bearish",
                    strength=strength,
                    evidence_tokens=tuple(matched_set & self.bearish_markers),
                    meta={"count": str(bearish_count)},
                )
            )

        # Institutional signals
        inst_count = len(matched_set & self.institutional_markers)
        if inst_count > 0:
            strength = min(1.0, inst_count / 2.0)
            signals.append(
                DomainSignal(
                    signal_type="institutional_signal",
                    strength=strength,
                    evidence_tokens=tuple(matched_set & self.institutional_markers),
                    meta={"count": str(inst_count)},
                )
            )

        # Volatility detection
        vol_count = len(matched_set & self.volatility_markers)
        if vol_count > 0:
            strength = min(1.0, vol_count / 2.0)
            signals.append(
                DomainSignal(
                    signal_type="market_volatility",
                    strength=strength,
                    evidence_tokens=tuple(matched_set & self.volatility_markers),
                    meta={"count": str(vol_count)},
                )
            )

        return signals


class ConspiracyOperator:
    """
    Conspiracy domain compression operator.

    Extracts:
    - Narrative threads (cabal/deepstate/agenda)
    - Claim chains (proof/evidence/source)
    - Epistemic markers (truth/fake/cover-up)
    """

    def __init__(self) -> None:
        self.narrative_markers = {"cabal", "deepstate", "agenda", "elites", "controlled"}
        self.claim_markers = {"proof", "evidence", "source", "leaked", "revealed"}
        self.epistemic_markers = {"truth", "fake", "hoax", "psyop", "coverup"}

    def extract_signals(self, result: DCECompressionResult) -> List[DomainSignal]:
        """Extract conspiracy signals from compression result."""
        signals: List[DomainSignal] = []

        matched_set = set(result.matched)

        # Narrative detection
        narrative_count = len(matched_set & self.narrative_markers)
        if narrative_count >= 2:
            strength = min(1.0, narrative_count / 3.0)
            signals.append(
                DomainSignal(
                    signal_type="narrative_conspiracy",
                    strength=strength,
                    evidence_tokens=tuple(matched_set & self.narrative_markers),
                    meta={"count": str(narrative_count)},
                )
            )

        # Claim chain detection
        claim_count = len(matched_set & self.claim_markers)
        if claim_count >= 2:
            strength = min(1.0, claim_count / 3.0)
            signals.append(
                DomainSignal(
                    signal_type="claim_chain",
                    strength=strength,
                    evidence_tokens=tuple(matched_set & self.claim_markers),
                    meta={"count": str(claim_count)},
                )
            )

        # Epistemic marker detection
        epistemic_count = len(matched_set & self.epistemic_markers)
        if epistemic_count > 0:
            strength = min(1.0, epistemic_count / 2.0)
            signals.append(
                DomainSignal(
                    signal_type="epistemic_contestation",
                    strength=strength,
                    evidence_tokens=tuple(matched_set & self.epistemic_markers),
                    meta={"count": str(epistemic_count)},
                )
            )

        return signals


class TechnologyOperator:
    """
    Technology domain compression operator.

    Extracts:
    - AI/ML signals (artificial intelligence, machine learning, automation)
    - Innovation signals (disruption, breakthrough, paradigm shift)
    - Tech skepticism (doomerism, alignment, existential risk)
    """

    def __init__(self) -> None:
        self.ai_markers = {"ai", "llm", "model", "algorithm", "neural", "gpt", "agi"}
        self.innovation_markers = {"disruption", "breakthrough", "innovation", "paradigm", "revolution"}
        self.skeptic_markers = {"doomer", "alignment", "risk", "safety", "dystopia", "terminator"}
        self.hype_markers = {"hype", "overpromise", "bubble", "vaporware", "moonshot"}

    def extract_signals(self, result: DCECompressionResult) -> List[DomainSignal]:
        """Extract technology signals from compression result."""
        signals: List[DomainSignal] = []

        matched_set = set(result.matched)

        # AI signal detection
        ai_count = len(matched_set & self.ai_markers)
        if ai_count > 0:
            strength = min(1.0, ai_count / 3.0)
            signals.append(
                DomainSignal(
                    signal_type="tech_ai_discourse",
                    strength=strength,
                    evidence_tokens=tuple(matched_set & self.ai_markers),
                    meta={"count": str(ai_count)},
                )
            )

        # Innovation signal detection
        innovation_count = len(matched_set & self.innovation_markers)
        if innovation_count > 0:
            strength = min(1.0, innovation_count / 2.0)
            signals.append(
                DomainSignal(
                    signal_type="innovation_signal",
                    strength=strength,
                    evidence_tokens=tuple(matched_set & self.innovation_markers),
                    meta={"count": str(innovation_count)},
                )
            )

        # Skepticism detection
        skeptic_count = len(matched_set & self.skeptic_markers)
        if skeptic_count >= 2:
            strength = min(1.0, skeptic_count / 3.0)
            signals.append(
                DomainSignal(
                    signal_type="tech_skepticism",
                    strength=strength,
                    evidence_tokens=tuple(matched_set & self.skeptic_markers),
                    meta={"count": str(skeptic_count)},
                )
            )

        # Hype cycle detection
        hype_count = len(matched_set & self.hype_markers)
        if hype_count > 0:
            strength = min(1.0, hype_count / 2.0)
            signals.append(
                DomainSignal(
                    signal_type="hype_cycle",
                    strength=strength,
                    evidence_tokens=tuple(matched_set & self.hype_markers),
                    meta={"count": str(hype_count)},
                )
            )

        return signals


class HealthOperator:
    """
    Health domain compression operator.

    Extracts:
    - Medical discourse (vaccine, treatment, diagnosis)
    - Public health signals (pandemic, outbreak, epidemic)
    - Wellness trends (mental health, fitness, self-care)
    """

    def __init__(self) -> None:
        self.medical_markers = {"vaccine", "treatment", "diagnosis", "clinical", "trial", "efficacy"}
        self.public_health_markers = {"pandemic", "outbreak", "epidemic", "quarantine", "lockdown"}
        self.wellness_markers = {"mental", "wellness", "therapy", "self-care", "mindfulness"}
        self.skeptic_markers = {"side-effects", "adverse", "hesitancy", "mandate", "freedom"}

    def extract_signals(self, result: DCECompressionResult) -> List[DomainSignal]:
        """Extract health signals from compression result."""
        signals: List[DomainSignal] = []

        matched_set = set(result.matched)

        # Medical discourse detection
        medical_count = len(matched_set & self.medical_markers)
        if medical_count > 0:
            strength = min(1.0, medical_count / 3.0)
            signals.append(
                DomainSignal(
                    signal_type="medical_discourse",
                    strength=strength,
                    evidence_tokens=tuple(matched_set & self.medical_markers),
                    meta={"count": str(medical_count)},
                )
            )

        # Public health signal detection
        public_health_count = len(matched_set & self.public_health_markers)
        if public_health_count > 0:
            strength = min(1.0, public_health_count / 2.0)
            signals.append(
                DomainSignal(
                    signal_type="public_health_signal",
                    strength=strength,
                    evidence_tokens=tuple(matched_set & self.public_health_markers),
                    meta={"count": str(public_health_count)},
                )
            )

        # Wellness trend detection
        wellness_count = len(matched_set & self.wellness_markers)
        if wellness_count > 0:
            strength = min(1.0, wellness_count / 2.0)
            signals.append(
                DomainSignal(
                    signal_type="wellness_trend",
                    strength=strength,
                    evidence_tokens=tuple(matched_set & self.wellness_markers),
                    meta={"count": str(wellness_count)},
                )
            )

        # Health skepticism detection
        skeptic_count = len(matched_set & self.skeptic_markers)
        if skeptic_count >= 2:
            strength = min(1.0, skeptic_count / 3.0)
            signals.append(
                DomainSignal(
                    signal_type="health_skepticism",
                    strength=strength,
                    evidence_tokens=tuple(matched_set & self.skeptic_markers),
                    meta={"count": str(skeptic_count)},
                )
            )

        return signals


class ClimateOperator:
    """
    Climate domain compression operator.

    Extracts:
    - Environmental discourse (climate, emissions, carbon)
    - Sustainability signals (renewable, green, sustainable)
    - Climate skepticism (hoax, natural cycles, alarmism)
    """

    def __init__(self) -> None:
        self.climate_markers = {"climate", "emissions", "carbon", "greenhouse", "warming"}
        self.sustainability_markers = {"renewable", "green", "sustainable", "solar", "wind"}
        self.action_markers = {"transition", "net-zero", "decarbonize", "electrify"}
        self.skeptic_markers = {"hoax", "natural", "alarmism", "exaggerate", "scam"}

    def extract_signals(self, result: DCECompressionResult) -> List[DomainSignal]:
        """Extract climate signals from compression result."""
        signals: List[DomainSignal] = []

        matched_set = set(result.matched)

        # Climate discourse detection
        climate_count = len(matched_set & self.climate_markers)
        if climate_count > 0:
            strength = min(1.0, climate_count / 3.0)
            signals.append(
                DomainSignal(
                    signal_type="climate_discourse",
                    strength=strength,
                    evidence_tokens=tuple(matched_set & self.climate_markers),
                    meta={"count": str(climate_count)},
                )
            )

        # Sustainability signal detection
        sustainability_count = len(matched_set & self.sustainability_markers)
        if sustainability_count > 0:
            strength = min(1.0, sustainability_count / 2.0)
            signals.append(
                DomainSignal(
                    signal_type="sustainability_signal",
                    strength=strength,
                    evidence_tokens=tuple(matched_set & self.sustainability_markers),
                    meta={"count": str(sustainability_count)},
                )
            )

        # Climate action detection
        action_count = len(matched_set & self.action_markers)
        if action_count > 0:
            strength = min(1.0, action_count / 2.0)
            signals.append(
                DomainSignal(
                    signal_type="climate_action",
                    strength=strength,
                    evidence_tokens=tuple(matched_set & self.action_markers),
                    meta={"count": str(action_count)},
                )
            )

        # Climate skepticism detection
        skeptic_count = len(matched_set & self.skeptic_markers)
        if skeptic_count >= 2:
            strength = min(1.0, skeptic_count / 3.0)
            signals.append(
                DomainSignal(
                    signal_type="climate_skepticism",
                    strength=strength,
                    evidence_tokens=tuple(matched_set & self.skeptic_markers),
                    meta={"count": str(skeptic_count)},
                )
            )

        return signals


class SocialOperator:
    """
    Social domain compression operator.

    Extracts:
    - Identity discourse (gender, race, class)
    - Social justice signals (equity, inclusion, representation)
    - Cultural movements (activism, awareness, solidarity)
    """

    def __init__(self) -> None:
        self.identity_markers = {"identity", "gender", "race", "class", "minority"}
        self.justice_markers = {"equity", "inclusion", "representation", "justice", "rights"}
        self.movement_markers = {"activism", "awareness", "solidarity", "movement", "protest"}
        self.backlash_markers = {"woke", "cancel", "mob", "outrage", "virtue-signal"}

    def extract_signals(self, result: DCECompressionResult) -> List[DomainSignal]:
        """Extract social signals from compression result."""
        signals: List[DomainSignal] = []

        matched_set = set(result.matched)

        # Identity discourse detection
        identity_count = len(matched_set & self.identity_markers)
        if identity_count > 0:
            strength = min(1.0, identity_count / 3.0)
            signals.append(
                DomainSignal(
                    signal_type="identity_discourse",
                    strength=strength,
                    evidence_tokens=tuple(matched_set & self.identity_markers),
                    meta={"count": str(identity_count)},
                )
            )

        # Social justice signal detection
        justice_count = len(matched_set & self.justice_markers)
        if justice_count > 0:
            strength = min(1.0, justice_count / 2.0)
            signals.append(
                DomainSignal(
                    signal_type="social_justice",
                    strength=strength,
                    evidence_tokens=tuple(matched_set & self.justice_markers),
                    meta={"count": str(justice_count)},
                )
            )

        # Movement detection
        movement_count = len(matched_set & self.movement_markers)
        if movement_count > 0:
            strength = min(1.0, movement_count / 2.0)
            signals.append(
                DomainSignal(
                    signal_type="cultural_movement",
                    strength=strength,
                    evidence_tokens=tuple(matched_set & self.movement_markers),
                    meta={"count": str(movement_count)},
                )
            )

        # Backlash detection
        backlash_count = len(matched_set & self.backlash_markers)
        if backlash_count >= 2:
            strength = min(1.0, backlash_count / 3.0)
            signals.append(
                DomainSignal(
                    signal_type="social_backlash",
                    strength=strength,
                    evidence_tokens=tuple(matched_set & self.backlash_markers),
                    meta={"count": str(backlash_count)},
                )
            )

        return signals


class DomainOperatorRegistry:
    """Registry for domain-specific compression operators."""

    def __init__(self) -> None:
        self._operators: Dict[str, object] = {
            "politics": PoliticsOperator(),
            "media": MediaOperator(),
            "finance": FinanceOperator(),
            "conspiracy": ConspiracyOperator(),
            "technology": TechnologyOperator(),
            "health": HealthOperator(),
            "climate": ClimateOperator(),
            "social": SocialOperator(),
        }

    def get_operator(self, domain: str) -> Optional[object]:
        """Get operator for domain."""
        return self._operators.get(domain)

    def extract_domain_signals(
        self, domain: str, result: DCECompressionResult
    ) -> List[DomainSignal]:
        """Extract domain-specific signals from compression result."""
        operator = self.get_operator(domain)
        if operator is None:
            return []

        # Call extract_signals method if it exists
        if hasattr(operator, "extract_signals"):
            return operator.extract_signals(result)  # type: ignore

        return []

    def register_operator(self, domain: str, operator: object) -> None:
        """Register a custom operator for a domain."""
        self._operators[domain] = operator
