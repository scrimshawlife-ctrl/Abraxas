from __future__ import annotations

import importlib
from typing import Any, Callable, Dict, Optional, Tuple

from ..core.stub_oracle_engine import _stub_engine_adapter


KERNEL_REGISTRY: Dict[str, str] = {
    "v2": "abraxas.kernel.v2.engine:run_oracle_v2",
}


def _load_runner(path: str) -> Tuple[Optional[Callable[[Any], Dict[str, Any]]], Optional[str]]:
    try:
        module_path, func_name = path.split(":", 1)
    except ValueError:
        return None, f"Invalid kernel entrypoint: {path}"
    try:
        mod = importlib.import_module(module_path)
        fn = getattr(mod, func_name, None)
        if not callable(fn):
            return None, f"Kernel entrypoint not callable: {path}"
        return fn, None
    except ModuleNotFoundError as err:
        return None, f"Kernel module not installed: {err}"
    except Exception as err:
        return None, f"Kernel import error: {err}"


def get_kernel_runner(version: str = "v2") -> Callable[[Any], Dict[str, Any]]:
    path = KERNEL_REGISTRY.get(version)
    if not path:
        return _stub_engine_adapter
    runner, err = _load_runner(path)
    if runner is None:
        return _stub_engine_adapter
    return runner
