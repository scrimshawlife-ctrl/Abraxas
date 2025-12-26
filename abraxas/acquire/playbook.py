from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import yaml


def _sha(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class PlaybookRule:
    when: Dict[str, Any]
    recommend: List[Dict[str, Any]]
    rule_id: str


def load_playbook_yaml(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError("Playbook must be a YAML mapping at root.")
    return data


def validate_playbook(data: Dict[str, Any]) -> List[PlaybookRule]:
    version = data.get("version")
    if version != "0.1":
        raise ValueError(f"Unsupported playbook version: {version!r}")

    rules = data.get("rules")
    if not isinstance(rules, list) or not rules:
        raise ValueError("Playbook must contain non-empty 'rules' list.")

    parsed: List[PlaybookRule] = []
    for idx, rule in enumerate(rules):
        if not isinstance(rule, dict):
            raise ValueError(f"Rule {idx} must be a mapping.")
        when = rule.get("when")
        recommend = rule.get("recommend")
        if not isinstance(when, dict) or not isinstance(recommend, list) or not recommend:
            raise ValueError(f"Rule {idx} must have 'when' mapping and non-empty 'recommend' list.")
        rule_id = _sha(f"{version}:{idx}:{sorted(when.items())}")[:16]
        parsed.append(PlaybookRule(when=when, recommend=recommend, rule_id=rule_id))
    return parsed


def _match_scalar(expected: Any, actual: Any) -> bool:
    if expected is None:
        return True
    return expected == actual


def _match_in(expected_list: Optional[List[Any]], actual: Any) -> bool:
    if expected_list is None:
        return True
    return actual in expected_list


def rule_matches(rule: PlaybookRule, gap: Dict[str, Any]) -> bool:
    when = rule.when
    if "gap_kind" in when and not _match_scalar(when["gap_kind"], gap.get("kind")):
        return False
    if "horizon_in" in when and not _match_in(when["horizon_in"], gap.get("horizon")):
        return False
    if "domain_in" in when and not _match_in(when["domain_in"], gap.get("domain")):
        return False
    return True
