# Detector Purity Guard (v0.1) — deny side effects for detector runes
# Canon: detectors annotate/log only.

from __future__ import annotations

import os
from contextlib import contextmanager


@contextmanager
def detector_purity_guard(enabled: bool = True):
    """
    Soft sandbox (v0.1):
    - Blocks common env toggles for network/proxy use (best-effort)
    - Provides an explicit switch you can harden later (seccomp, syscall filters, etc.)
    """
    if not enabled:
        yield
        return

    old_env = dict(os.environ)
    for key in list(os.environ.keys()):
        if key.lower() in {"http_proxy", "https_proxy", "all_proxy", "no_proxy"}:
            os.environ.pop(key, None)

    try:
        yield
    finally:
        os.environ.clear()
        os.environ.update(old_env)
