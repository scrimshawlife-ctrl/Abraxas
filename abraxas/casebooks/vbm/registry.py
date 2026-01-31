"""VBM casebook registry with caching."""

from __future__ import annotations

from pathlib import Path

from abraxas.casebooks.vbm.comparator import score_against_vbm
from abraxas.casebooks.vbm.corpus import load_episodes_from_fixtures, build_casebook
from abraxas.casebooks.vbm.models import VBMCasebook, VBMDriftScore, VBMPhase
from abraxas.casebooks.vbm.phase import classify_phase, compute_phase_curve
from abraxas.core.provenance import hash_string


class VBMCasebookRegistry:
    """
    Singleton registry for VBM casebook with caching.

    Loads casebook once and caches drift score results by text hash.
    """

    _instance: VBMCasebookRegistry | None = None
    _casebook: VBMCasebook | None = None
    _score_cache: dict[str, VBMDriftScore] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self) -> None:
        """Initialize casebook (called once)."""
        self._score_cache = {}
        self._casebook = None

    def load_casebook(self, fixtures_dir: str | Path = "tests/fixtures/vbm") -> VBMCasebook:
        """
        Load VBM casebook from fixtures.

        Returns cached casebook if already loaded.
        """
        if self._casebook is not None:
            return self._casebook

        # Load episodes
        episodes = load_episodes_from_fixtures(fixtures_dir)

        # Compute phase curve
        phase_curve = compute_phase_curve(episodes)

        # Build casebook
        self._casebook = build_casebook(episodes, phase_curve)

        return self._casebook

    def get_casebook(self) -> VBMCasebook | None:
        """Get loaded casebook (or None if not loaded)."""
        return self._casebook

    def score_text(
        self, text: str, operator_hits: list[str] | None = None, use_cache: bool = True
    ) -> VBMDriftScore:
        """
        Score text against VBM casebook.

        Args:
            text: Text to score
            operator_hits: Optional operator IDs detected
            use_cache: Whether to use cache (default True)

        Returns:
            VBMDriftScore
        """
        # Compute cache key
        cache_key = hash_string(text)
        if operator_hits:
            cache_key += "_" + "_".join(sorted(operator_hits))

        # Check cache
        if use_cache and cache_key in self._score_cache:
            return self._score_cache[cache_key]

        # Compute score
        score = score_against_vbm(text, operator_hits)

        # Cache result
        if use_cache:
            self._score_cache[cache_key] = score

        return score

    def phase_text(self, text: str) -> tuple[VBMPhase, float]:
        """
        Classify text into VBM phase.

        Args:
            text: Text to classify

        Returns:
            (phase, confidence) tuple
        """
        return classify_phase(text)

    def clear_cache(self) -> None:
        """Clear score cache."""
        self._score_cache.clear()

    def get_cache_stats(self) -> dict[str, int]:
        """Get cache statistics."""
        return {
            "cache_size": len(self._score_cache),
            "episodes_loaded": len(self._casebook.episodes) if self._casebook else 0,
        }


# Singleton instance accessor
def get_vbm_registry() -> VBMCasebookRegistry:
    """Get VBM registry singleton."""
    return VBMCasebookRegistry()
