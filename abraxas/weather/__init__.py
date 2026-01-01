"""Memetic Weather System: Environmental classification for symbolic dynamics."""

from abraxas.weather.registry import WeatherType, WEATHER_REGISTRY
from abraxas.weather.affinity import compute_affinity, AffinityScore

__all__ = ["WeatherType", "WEATHER_REGISTRY", "compute_affinity", "AffinityScore"]
