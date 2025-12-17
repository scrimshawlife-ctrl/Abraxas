# Abraxas Orin Boot Spine

Orin-portable scaffolding for deterministic boot, asset management, overlay lifecycle, and health monitoring.

## Quick Start

### 1. Install Python Environment

```bash
# On Jetson Orin or compatible system
python3 -m venv venv
source venv/bin/activate

# Install package in development mode
pip install -e .

# Optional: Install FastAPI for full server features
pip install fastapi uvicorn
```

### 2. Run System Check

```bash
abx doctor
```

Expected output: JSON report with system status, architecture, CUDA availability, and directory checks.

### 3. Sync Assets

```bash
# Create asset manifest from assets directory
abx assets sync
```

This generates `assets/assets.manifest.json` with deterministic hashes of all asset files.

### 4. Run Smoke Test

```bash
abx smoke
```

Executes deterministic pipeline test and writes results to `.aal/state/smoke.latest.json` with full provenance metadata.

### 5. Start Server

```bash
abx up
```

Starts HTTP server with health endpoints:
- `http://localhost:8765/healthz` - Basic liveness check
- `http://localhost:8765/readyz` - Readiness check with provenance

## CLI Commands

### `abx doctor`
System diagnostics and readiness checks. Validates:
- Architecture (aarch64/arm64 for Orin, x86_64/amd64 for dev)
- JetPack environment (if available)
- CUDA installation
- Directory creation permissions
- Port availability

### `abx up`
Start HTTP server with health endpoints. Uses FastAPI if available, otherwise falls back to minimal stdlib server.

### `abx smoke`
Run deterministic smoke test. Output includes:
- Full provenance (git SHA, lock hash, config hash, assets hash)
- Golden input vector
- Pipeline output
- Stored in `.aal/state/smoke.latest.json`

### `abx assets sync`
Generate asset manifest with SHA256 hashes for all files in assets directory.

### `abx overlay`
Manage overlay lifecycle:

```bash
# List installed overlays
abx overlay list

# Check overlay status
abx overlay status --name my-overlay

# Install overlay from manifest
abx overlay install --name my-overlay --manifest-file overlay.json

# Start overlay
abx overlay start --name my-overlay

# Stop overlay
abx overlay stop --name my-overlay
```

## Configuration

All configuration is via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `ABX_ROOT` | `/opt/aal/abraxas` | Root installation directory |
| `ABX_PROFILE` | `orin` | Runtime profile (`orin` or `dev`) |
| `ABX_ASSETS` | `$ABX_ROOT/assets` | Assets directory |
| `ABX_OVERLAYS` | `$ABX_ROOT/.aal/overlays` | Overlays directory |
| `ABX_STATE` | `$ABX_ROOT/.aal/state` | State directory |
| `ABX_HOST` | `0.0.0.0` | HTTP server host |
| `ABX_PORT` | `8765` | HTTP server port |
| `ABX_LOG` | `INFO` (orin) / `DEBUG` (dev) | Log level |
| `ABX_CONCURRENCY` | `1` (orin) / `2` (dev) | Concurrency level |

## Systemd Integration

For production deployment on Jetson Orin:

```bash
# Copy systemd units
sudo cp systemd/abraxas-core.service /etc/systemd/system/
sudo cp systemd/aal-overlay@.service /etc/systemd/system/

# Reload and enable
sudo systemctl daemon-reload
sudo systemctl enable abraxas-core
sudo systemctl start abraxas-core

# Check status
sudo systemctl status abraxas-core

# View logs
sudo journalctl -u abraxas-core -f
```

See `systemd/README.md` for detailed systemd usage.

## Overlay Manifest Format

Overlays are defined with JSON manifests:

```json
{
  "name": "my-overlay",
  "version": "1.0.0",
  "entrypoint": "my_package.module:main_function",
  "requires_gpu": true,
  "min_ram_mb": 2048,
  "ports": [8080, 8081],
  "description": "My overlay description"
}
```

## Determinism

The system enforces determinism for reproducibility:

1. **Stable JSON**: All JSON output uses sorted keys and stable separators
2. **Deterministic hashing**: Asset manifests use SHA256 with path-sorted iteration
3. **Provenance tracking**: Every run captures:
   - Git commit SHA and dirty status
   - Python version
   - Platform (OS + arch)
   - Lock file hash
   - Config hash
   - Assets hash
4. **Golden vectors**: Smoke tests use stable input vectors

## Next Steps

After scaffolding is in place, wire real Abraxas pipeline:

1. Replace stub in `abx/core/pipeline.py` with real Oracle→Rack→Weather execution
2. Ensure pipeline only reads assets via manifest'd assets directory
3. `abx smoke` becomes true canary for drift detection

## Architecture

```
abx/
├── __init__.py              # Package metadata
├── cli.py                   # CLI entry point
├── util/
│   ├── jsonutil.py         # Stable JSON serialization
│   └── hashutil.py         # Deterministic hashing
├── runtime/
│   ├── config.py           # Runtime configuration
│   └── provenance.py       # Provenance stamping
├── assets/
│   └── manifest.py         # Asset manifest generation
├── overlays/
│   ├── schema.py           # Overlay manifest schema
│   └── manager.py          # Overlay lifecycle management
├── core/
│   └── pipeline.py         # Pipeline stub (replace with real)
└── server/
    ├── app.py              # FastAPI server
    └── minhttp.py          # Minimal fallback server
```

## Testing

Run smoke test to verify determinism:

```bash
python -m pytest tests/test_smoke_determinism.py -v
```

Or run directly:
```bash
python tests/test_smoke_determinism.py
```

## Troubleshooting

### Port already in use
```bash
# Check what's using port 8765
sudo lsof -i :8765

# Change port via environment
export ABX_PORT=8766
abx up
```

### Permission denied on directories
```bash
# Ensure directories are writable
sudo chown -R $USER /opt/aal/abraxas
```

### CUDA not detected
Check `/usr/local/cuda` exists. On Jetson Orin:
```bash
echo $JETPACK_VERSION
ls /usr/local/cuda
```

## License

See main repository LICENSE file.
