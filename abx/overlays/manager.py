"""Overlay lifecycle manager."""

from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Any, List
import os
import subprocess
import sys
import time

from abx.util.jsonutil import load_file, dump_file
from abx.overlays.schema import OverlayManifest, OverlayState

STATE_FILE = "overlay.state.json"
MANIFEST_FILE = "manifest.json"

@dataclass
class OverlayRuntime:
    """Runtime state of an overlay."""
    manifest: OverlayManifest
    path: Path
    state: OverlayState = "stopped"
    pid: Optional[int] = None
    last_error: Optional[str] = None

class OverlayManager:
    """Manager for overlay installation and lifecycle."""

    def __init__(self, overlays_dir: Path, state_dir: Path):
        self.overlays_dir = overlays_dir
        self.state_dir = state_dir
        self.overlays_dir.mkdir(parents=True, exist_ok=True)
        self.state_dir.mkdir(parents=True, exist_ok=True)

    def _overlay_path(self, name: str) -> Path:
        """Get overlay installation path."""
        return (self.overlays_dir / name).resolve()

    def _state_path(self, name: str) -> Path:
        """Get overlay state file path."""
        return (self.state_dir / f"{name}.{STATE_FILE}").resolve()

    def load_manifest(self, name: str) -> OverlayManifest:
        """Load overlay manifest."""
        mp = self._overlay_path(name) / MANIFEST_FILE
        if not mp.exists():
            raise FileNotFoundError(f"Missing overlay manifest: {mp}")
        d = load_file(str(mp))
        return OverlayManifest.from_dict(d)

    def list_overlays(self) -> List[str]:
        """List all installed overlays."""
        if not self.overlays_dir.exists():
            return []
        names = [p.name for p in self.overlays_dir.iterdir() if p.is_dir()]
        names.sort()
        return names

    def status(self, name: str) -> Dict[str, Any]:
        """Get overlay status."""
        stp = self._state_path(name)
        if stp.exists():
            return load_file(str(stp))
        m = self.load_manifest(name)
        return {"name": m.name, "state": "stopped", "pid": None, "last_error": None}

    def _write_status(self, name: str, obj: Dict[str, Any]) -> None:
        """Write overlay status to state file."""
        dump_file(str(self._state_path(name)), obj)

    def install(self, name: str, manifest: Dict[str, Any]) -> Path:
        """Install overlay from manifest."""
        op = self._overlay_path(name)
        op.mkdir(parents=True, exist_ok=True)
        dump_file(str(op / MANIFEST_FILE), manifest)
        self._write_status(name, {"name": name, "state": "stopped", "pid": None, "last_error": None})
        return op

    def start(self, name: str) -> Dict[str, Any]:
        """Start overlay process."""
        m = self.load_manifest(name)
        # Run overlay as separate process: python -c shim entrypoint
        # The shim imports the entrypoint and runs it
        shim = (
            "import importlib\n"
            "import sys\n"
            "mod, fn = sys.argv[1].split(':', 1)\n"
            "m = importlib.import_module(mod)\n"
            "getattr(m, fn)()\n"
        )
        cmd = [sys.executable, "-c", shim, m.entrypoint]
        try:
            p = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, close_fds=True)
            time.sleep(0.2)
            status = {"name": m.name, "state": "running", "pid": p.pid, "last_error": None}
            self._write_status(name, status)
            return status
        except Exception as e:
            status = {"name": m.name, "state": "error", "pid": None, "last_error": str(e)}
            self._write_status(name, status)
            return status

    def stop(self, name: str) -> Dict[str, Any]:
        """Stop overlay process."""
        st = self.status(name)
        pid = st.get("pid")
        if pid:
            try:
                os.kill(int(pid), 15)  # SIGTERM
            except Exception as e:
                st["last_error"] = str(e)
        st["state"] = "stopped"
        st["pid"] = None
        self._write_status(name, st)
        return st
