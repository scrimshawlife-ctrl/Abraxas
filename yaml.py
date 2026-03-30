from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_VENDORED_INIT = Path(__file__).resolve().parent / "vendor" / "pyyaml" / "yaml" / "__init__.py"
_VENDORED_PACKAGE_DIR = _VENDORED_INIT.parent

if not _VENDORED_INIT.exists():
    raise ModuleNotFoundError("Vendored PyYAML is missing at vendor/pyyaml/yaml")

spec = importlib.util.spec_from_file_location(
    __name__,
    _VENDORED_INIT,
    submodule_search_locations=[str(_VENDORED_PACKAGE_DIR)],
)
if spec is None or spec.loader is None:
    raise ModuleNotFoundError("Unable to load vendored PyYAML module spec")

module = importlib.util.module_from_spec(spec)
sys.modules[__name__] = module
spec.loader.exec_module(module)
