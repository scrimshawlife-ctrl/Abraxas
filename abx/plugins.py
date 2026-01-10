"""Plugin loader for ABX CLI entry points."""

from __future__ import annotations

from dataclasses import dataclass
from importlib.metadata import entry_points
from typing import Callable, Iterable, Protocol


class PluginCallable(Protocol):
    def __call__(self, subparsers) -> None: ...


@dataclass(frozen=True)
class PluginRegistration:
    name: str
    loader: Callable[[], PluginCallable]


def load_plugins(subparsers, registrations: Iterable[PluginRegistration] | None = None) -> None:
    """Load ABX CLI plugins from entry points."""
    plugins = list(registrations) if registrations is not None else _discover_plugins()
    for plugin in sorted(plugins, key=lambda item: item.name):
        plugin.loader()(subparsers)


def _discover_plugins() -> list[PluginRegistration]:
    group = entry_points(group="abx.plugins")
    registrations: list[PluginRegistration] = []
    for ep in group:
        registrations.append(PluginRegistration(name=ep.name, loader=ep.load))
    return registrations
