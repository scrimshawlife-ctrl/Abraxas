"""Lexicon Engine v1 + Domain Compression Engine v2 + Integrated Pipeline

v1: Domain-scoped, versioned token-weight mapping
v2: Lifecycle-aware, lineage-tracked compression operators
v3: DCE ↔ SCO/STI/RDV integration pipeline
"""

from .engine import (
    CompressionResult,
    InMemoryLexiconRegistry,
    LexiconEngine,
    LexiconEntry,
    LexiconPack,
    LexiconRegistry,
)
from .dce import (
    DCECompressionResult,
    DCEEntry,
    DCEPack,
    DCERegistry,
    DomainCompressionEngine,
    EvolutionEvent,
    EvolutionReason,
    LexiconLineage,
    LifecycleState,
)
from .operators import (
    ConspiracyOperator,
    DomainOperatorRegistry,
    DomainSignal,
    FinanceOperator,
    MediaOperator,
    PoliticsOperator,
)
from .pipeline import (
    DCEFeedbackLoop,
    DCEFeedbackProcessor,
    DCELinguisticPipeline,
    DCEPipelineInput,
    DCEPipelineOutput,
    create_integrated_pipeline,
    process_tokens_with_dce,
)

__all__ = [
    # v1 - Lexicon Engine
    "LexiconEntry",
    "LexiconPack",
    "LexiconRegistry",
    "InMemoryLexiconRegistry",
    "LexiconEngine",
    "CompressionResult",
    # v2 - Domain Compression Engine
    "DCEEntry",
    "DCEPack",
    "DCERegistry",
    "DomainCompressionEngine",
    "DCECompressionResult",
    "LexiconLineage",
    "EvolutionEvent",
    "EvolutionReason",
    "LifecycleState",
    # v2.1 - Domain Operators
    "DomainSignal",
    "DomainOperatorRegistry",
    "PoliticsOperator",
    "MediaOperator",
    "FinanceOperator",
    "ConspiracyOperator",
    # v3 - Integrated Pipeline
    "DCELinguisticPipeline",
    "DCEPipelineInput",
    "DCEPipelineOutput",
    "DCEFeedbackLoop",
    "DCEFeedbackProcessor",
    "create_integrated_pipeline",
    "process_tokens_with_dce",
]
