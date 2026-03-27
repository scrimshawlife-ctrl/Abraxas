from __future__ import annotations

from dataclasses import dataclass

from abx.util.hashutil import sha256_bytes
from abx.util.jsonutil import dumps_stable


@dataclass(frozen=True)
class ArtifactScope:
    run_id: str
    local_artifact_id: str
    global_artifact_id: str
    visibility: str


def scope_artifact(run_id: str, artifact_id: str, visibility: str = "RUN_LOCAL") -> ArtifactScope:
    run_id_norm = str(run_id).strip()
    local_id = str(artifact_id).strip()
    if not run_id_norm:
        raise ValueError("run_id_required")
    if not local_id:
        raise ValueError("artifact_id_required")
    global_id = f"{run_id_norm}:{local_id}"
    return ArtifactScope(run_id=run_id_norm, local_artifact_id=local_id, global_artifact_id=global_id, visibility=visibility)


def build_scoped_registry(run_artifacts: dict[str, list[str]]) -> dict[str, object]:
    scoped: list[ArtifactScope] = []
    collisions: list[str] = []
    seen_global: set[str] = set()

    for run_id in sorted(run_artifacts):
        for artifact_id in sorted(run_artifacts[run_id]):
            scope = scope_artifact(run_id, artifact_id)
            scoped.append(scope)
            if scope.global_artifact_id in seen_global:
                collisions.append(scope.global_artifact_id)
            seen_global.add(scope.global_artifact_id)

    payload = [x.__dict__ for x in scoped]
    registry_hash = sha256_bytes(dumps_stable(payload).encode("utf-8"))
    return {
        "artifactType": "ArtifactScopeRegistry.v1",
        "artifactId": "artifact-scope-registry",
        "scoped": payload,
        "collisions": sorted(set(collisions)),
        "registryHash": registry_hash,
    }
