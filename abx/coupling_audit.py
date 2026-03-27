from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CouplingAuditArtifact:
    artifact_type: str
    artifact_id: str
    status: str
    coupling_map: dict[str, list[str]]
    suspect_couplings: list[str]
    prohibited_couplings: list[str]


def _module_name(repo_root: Path, file_path: Path) -> str:
    rel = file_path.relative_to(repo_root)
    return ".".join(rel.with_suffix("").parts)


def audit_coupling(*, repo_root: Path, allowlist: set[str] | None = None) -> CouplingAuditArtifact:
    allowlist = allowlist or set()
    py_files = sorted((repo_root / "abx").rglob("*.py"))

    coupling_map: dict[str, list[str]] = {}
    suspect: list[str] = []
    prohibited: list[str] = []

    for file_path in py_files:
        module = _module_name(repo_root, file_path)
        source = file_path.read_text(encoding="utf-8")
        try:
            tree = ast.parse(source)
        except SyntaxError:
            coupling_map[module] = ["<syntax-error>"]
            suspect.append(f"{module}-><syntax-error>")
            continue

        deps: set[str] = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for n in node.names:
                    if n.name.startswith("abx."):
                        deps.add(n.name)
            if isinstance(node, ast.ImportFrom):
                if node.module and node.module.startswith("abx."):
                    deps.add(node.module)

        coupling_map[module] = sorted(deps)

        for dep in deps:
            edge = f"{module}->{dep}"
            if edge in allowlist:
                continue
            # classify simple prohibited patterns
            if module.startswith("abx.operator") and dep.startswith("abx.ui"):
                prohibited.append(edge)
            elif module.startswith("abx.") and dep.startswith("abx.") and module.split(".")[1] != dep.split(".")[1]:
                suspect.append(edge)

    status = "VALID"
    if prohibited:
        status = "BROKEN"
    elif suspect:
        status = "PARTIAL"

    return CouplingAuditArtifact(
        artifact_type="CouplingAuditArtifact.v1",
        artifact_id="coupling-audit-abx",
        status=status,
        coupling_map={k: v for k, v in sorted(coupling_map.items())},
        suspect_couplings=sorted(set(suspect)),
        prohibited_couplings=sorted(set(prohibited)),
    )
