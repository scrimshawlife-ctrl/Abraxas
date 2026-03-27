from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import ast
from typing import Dict, Iterable, List, Sequence, Set, Tuple

from webpanel.models import AbraxasSignalPacket, RunState


@dataclass(frozen=True)
class MissingField:
    file: str
    line: int
    model: str
    field: str


class ContractDeltaError(RuntimeError):
    def __init__(self, missing: Sequence[MissingField]) -> None:
        details = "\n".join(
            f"missing_field:{item.model}.{item.field} ({item.file}:{item.line})" for item in missing
        )
        super().__init__(details)
        self.missing = list(missing)


def _model_fields(model) -> Set[str]:
    fields = getattr(model, "model_fields", None)
    if isinstance(fields, dict):
        return set(fields.keys())
    legacy = getattr(model, "__fields__", None)
    if isinstance(legacy, dict):
        return set(legacy.keys())
    annotations = getattr(model, "__annotations__", None)
    if isinstance(annotations, dict):
        return set(annotations.keys())
    return set()


def _iter_python_files(paths: Iterable[Path]) -> List[Path]:
    out: List[Path] = []
    for path in paths:
        if path.is_dir():
            out.extend(sorted(path.rglob("*.py")))
        elif path.is_file():
            out.append(path)
    return sorted(out)


def _collect_attr_refs(tree: ast.AST) -> List[Tuple[str, str, int]]:
    refs: List[Tuple[str, str, int]] = []
    run_vars: Set[str] = {"run"}
    packet_vars: Set[str] = {"packet"}

    class Visitor(ast.NodeVisitor):
        def visit_Assign(self, node: ast.Assign) -> None:
            if isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Name):
                func_name = node.value.func.id
                targets = [t for t in node.targets if isinstance(t, ast.Name)]
                for target in targets:
                    if func_name == "RunState":
                        run_vars.add(target.id)
                    if func_name == "AbraxasSignalPacket":
                        packet_vars.add(target.id)
            self.generic_visit(node)

        def visit_Attribute(self, node: ast.Attribute) -> None:
            if isinstance(node.value, ast.Name):
                base = node.value.id
                if base in run_vars:
                    refs.append(("RunState", node.attr, node.lineno))
                elif base in packet_vars:
                    refs.append(("AbraxasSignalPacket", node.attr, node.lineno))
            self.generic_visit(node)

        def visit_Call(self, node: ast.Call) -> None:
            if isinstance(node.func, ast.Name):
                func_name = node.func.id
                if func_name == "RunState":
                    for keyword in node.keywords:
                        if keyword.arg:
                            refs.append(("RunState", keyword.arg, node.lineno))
                if func_name == "AbraxasSignalPacket":
                    for keyword in node.keywords:
                        if keyword.arg:
                            refs.append(("AbraxasSignalPacket", keyword.arg, node.lineno))
            self.generic_visit(node)

    Visitor().visit(tree)
    return refs


def detect_contract_deltas(paths: Iterable[Path]) -> None:
    run_fields = _model_fields(RunState)
    packet_fields = _model_fields(AbraxasSignalPacket)
    missing: List[MissingField] = []

    for path in _iter_python_files(list(paths)):
        try:
            source = path.read_text(encoding="utf-8")
        except OSError:
            continue
        try:
            tree = ast.parse(source)
        except SyntaxError:
            continue
        for model, field, lineno in _collect_attr_refs(tree):
            if model == "RunState" and field not in run_fields:
                missing.append(MissingField(str(path), lineno, model, field))
            if model == "AbraxasSignalPacket" and field not in packet_fields:
                missing.append(MissingField(str(path), lineno, model, field))

    if missing:
        raise ContractDeltaError(missing)
