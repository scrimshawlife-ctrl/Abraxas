"""Metric extractors for SourcePacket ingestion."""

from .base import MetricExtractor, MetricPoint
from .astronomy import AstronomyExtractor
from .geomagnetic import GeomagneticExtractor
from .governance import GovernanceExtractor
from .meteorology import MeteorologyExtractor
from .schumann import SchumannExtractor
from .temporal import TemporalExtractor
from .linguistics import LinguisticsExtractor
from .economics import EconomicsExtractor

EXTRACTORS = [
    MeteorologyExtractor(),
    GeomagneticExtractor(),
    AstronomyExtractor(),
    SchumannExtractor(),
    TemporalExtractor(),
    LinguisticsExtractor(),
    GovernanceExtractor(),
    EconomicsExtractor(),
]

__all__ = [
    "MetricExtractor",
    "MetricPoint",
    "AstronomyExtractor",
    "GeomagneticExtractor",
    "MeteorologyExtractor",
    "SchumannExtractor",
    "TemporalExtractor",
    "LinguisticsExtractor",
    "GovernanceExtractor",
    "EconomicsExtractor",
    "EXTRACTORS",
]
