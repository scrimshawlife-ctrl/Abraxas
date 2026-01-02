from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BudgetCaps:
    """
    Deterministic sandbox caps (minimal placeholder).
    Add-only as enforcement becomes real.
    """

    max_domains: int = 256
    max_subdomains: int = 2048


def enforce_caps(*, caps: BudgetCaps, domain_count: int, subdomain_count: int) -> None:
    """
    Deterministic budget enforcement (raises ValueError if exceeded).
    """
    if domain_count > caps.max_domains:
        raise ValueError("budget exceeded: domains")
    if subdomain_count > caps.max_subdomains:
        raise ValueError("budget exceeded: subdomains")

