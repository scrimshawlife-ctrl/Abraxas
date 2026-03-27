#!/usr/bin/env python3
from __future__ import annotations

import json

from abx.knowledge.memoryLifecycle import build_memory_lifecycle
from abx.knowledge.memoryTransitions import validate_memory_transitions
from abx.knowledge.retentionPolicy import build_retention_policy
from abx.knowledge.staleMemoryDetection import detect_stale_memory


def main() -> None:
    print(
        json.dumps(
            {
                "artifactType": "MemoryLifecycleAudit.v1",
                "artifactId": "memory-lifecycle-audit",
                "lifecycle": [x.__dict__ for x in build_memory_lifecycle()],
                "retention": [x.__dict__ for x in build_retention_policy()],
                "transitions": validate_memory_transitions(),
                "stale": detect_stale_memory(),
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
