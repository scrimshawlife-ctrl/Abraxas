#!/usr/bin/env python3
from __future__ import annotations

import json

from abx.federation.semanticAlignment import build_federated_semantic_alignment


def main() -> None:
    print(json.dumps({"artifactType": "FederatedAlignmentAudit.v1", "artifactId": "federated-alignment-audit", "alignment": [x.__dict__ for x in build_federated_semantic_alignment()]}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
