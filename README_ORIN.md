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

### `abx drift`
Drift detection for configuration and code changes:

```bash
# Take snapshot of current state
abx drift snapshot

# Check for drift since last snapshot
abx drift check
```

### `abx watchdog`
Health monitoring with automatic service restart:

```bash
abx watchdog \
  --ready-url http://127.0.0.1:8766/readyz \
  --unit aal-bus.service \
  --interval 5 \
  --fail-threshold 3
```

### `abx update`
Atomic update with rollback:

```bash
abx update \
  --repo-url https://github.com/your-org/abraxas.git \
  --branch main
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

## Self-Healing Layer

Orin includes production-grade self-healing capabilities to prevent devices from becoming "haunted toasters" at 2:13am.

### Drift Detection

Detect changes to code, configuration, or assets that invalidate assumptions:

```bash
# Take initial snapshot
abx drift snapshot

# Check for drift (compares against last snapshot)
abx drift check
```

Drift detection tracks:
- Git commit SHA and dirty status
- Lock file hash (dependencies)
- Config hash (environment settings)
- Assets hash (asset manifest)
- Python version
- Platform (OS + arch)

Output example:
```json
{
  "ok": false,
  "drift": {
    "git_sha": {"from": "abc1234", "to": "def5678"},
    "assets_hash": {"from": "old_hash", "to": "new_hash"}
  },
  "prev_ts": 1702800000,
  "cur_ts": 1702900000
}
```

The snapshot is stored in `.aal/state/drift.snapshot.json`.

### Watchdog

Automated health monitoring with service restart on failure:

```bash
# Run watchdog (usually via systemd)
abx watchdog \
  --ready-url http://127.0.0.1:8766/readyz \
  --unit aal-bus.service \
  --interval 5 \
  --fail-threshold 3
```

The watchdog:
- Polls the health endpoint every N seconds
- Restarts the systemd unit after N consecutive failures
- Logs all events as structured JSON for journald
- Recovers gracefully when service returns to healthy state

**Enable watchdog via systemd:**

```bash
# Copy watchdog service
sudo cp systemd/abx-watchdog.service /etc/systemd/system/

# Edit to set correct ready-url and unit name
sudo nano /etc/systemd/system/abx-watchdog.service

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable abx-watchdog
sudo systemctl start abx-watchdog

# Monitor watchdog logs
sudo journalctl -u abx-watchdog -f
```

### Atomic Updates with Rollback

Safe, reversible deployments without downtime:

```bash
# Run atomic update (pulls latest code, runs smoke test, activates)
abx update \
  --repo-url https://github.com/your-org/abraxas.git \
  --branch main
```

Update process:
1. Clone latest code to timestamped directory
2. Run smoke test (`abx smoke`) in new directory
3. If smoke test passes, atomically swap symlink
4. If smoke test fails, keep old version active
5. If activation fails, automatically rollback to previous version

**Directory layout for atomic updates:**

```
/opt/aal/
├── abraxas_releases/
│   ├── abc1234/          # Release by git SHA
│   ├── def5678/          # Another release
│   └── .tmp_12345/       # Temporary staging (cleaned up)
└── abraxas_current -> abraxas_releases/abc1234/  # Symlink to active release
```

Set via environment:
- `ABX_RELEASES=/opt/aal/abraxas_releases` - Release storage directory
- `ABX_CURRENT=/opt/aal/abraxas_current` - Symlink to active release

**Enable nightly updates via systemd timer:**

```bash
# Copy update service and timer
sudo cp systemd/abx-update.service /etc/systemd/system/
sudo cp systemd/abx-update.timer /etc/systemd/system/

# Edit service to set repo URL
sudo nano /etc/systemd/system/abx-update.service
# Replace REPLACE_ME with actual repository URL

# Enable timer (runs at 3:15am daily)
sudo systemctl daemon-reload
sudo systemctl enable abx-update.timer
sudo systemctl start abx-update.timer

# Check timer status
sudo systemctl list-timers abx-update.timer

# Manually trigger update
sudo systemctl start abx-update.service

# Check update logs
sudo journalctl -u abx-update -f
```

**Manual rollback procedure:**

If you need to rollback to a previous release:

```bash
# List available releases
ls -la /opt/aal/abraxas_releases/

# Repoint symlink to previous release
sudo ln -sfn /opt/aal/abraxas_releases/OLD_SHA /opt/aal/abraxas_current

# Restart services
sudo systemctl restart abraxas-core
sudo systemctl restart aal-bus  # if applicable

# Verify rollback
abx smoke
```

### Production Deployment Checklist

For appliance-grade reliability:

1. **Set up release directory structure:**
   ```bash
   sudo mkdir -p /opt/aal/abraxas_releases
   sudo chown -R orin:orin /opt/aal
   ```

2. **Install initial release:**
   ```bash
   cd /opt/aal/abraxas_releases
   git clone https://github.com/your-org/abraxas.git initial
   cd initial && python -m abx.cli smoke  # Verify
   ln -s /opt/aal/abraxas_releases/initial /opt/aal/abraxas_current
   ```

3. **Enable watchdog:**
   ```bash
   sudo cp /opt/aal/abraxas_current/systemd/abx-watchdog.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable abx-watchdog
   sudo systemctl start abx-watchdog
   ```

4. **Enable nightly updates:**
   ```bash
   sudo cp /opt/aal/abraxas_current/systemd/abx-update.* /etc/systemd/system/
   # Edit abx-update.service to set repo URL
   sudo systemctl enable abx-update.timer
   sudo systemctl start abx-update.timer
   ```

5. **Set up drift monitoring:**
   ```bash
   abx drift snapshot  # Take initial snapshot
   # Add to cron or systemd timer to check drift periodically
   ```

6. **Configure structured logging:**
   All self-healing components emit journald-friendly JSON logs:
   ```bash
   sudo journalctl -u abx-watchdog -o json-pretty
   sudo journalctl -u abx-update -o json-pretty
   ```

## Always-On Abraxas Daemon

Abraxas runs as an always-on daemon with continuous data ingestion via Decodo and a chat-like UI for interaction.

### Architecture

The always-on stack consists of three layers:

1. **Ingestion Layer** (`abx ingest`) - Continuously fetches data via Decodo API
2. **Storage Layer** (SQLite) - Stores ingested documents with provenance
3. **UI Layer** (`abx ui`) - Chat-like HTTP interface with admin handshake

### Data Ingestion with Decodo

Abraxas uses the [Decodo Web Scraping API](https://decodo.com) for managed data acquisition.

**Security Note:** Only use Decodo for publicly accessible data. Respect website terms of service and applicable laws.

#### Configure Decodo Credentials

Create a secure environment file for Decodo credentials:

```bash
sudo mkdir -p /etc/abraxas
sudo touch /etc/abraxas/decodo.env
sudo chmod 600 /etc/abraxas/decodo.env
```

Add credentials to `/etc/abraxas/decodo.env`:

```bash
# Base64-encoded Basic Auth (user:password)
DECODO_AUTH_B64=your_base64_encoded_credentials_here

# Mode: realtime or tasks
DECODO_MODE=realtime

# Endpoint (default shown)
DECODO_ENDPOINT=https://scraper-api.decodo.com/v2/scrape
```

To generate `DECODO_AUTH_B64`:

```bash
echo -n "username:password" | base64
```

#### Configure Ingestion Jobs

Edit `.aal/jobs/ingest.jobs.json` to define scraping jobs:

```json
{
  "jobs": [
    {
      "name": "ip_check",
      "kind": "url",
      "url": "https://ip.decodo.com",
      "every_s": 3600,
      "enabled": true,
      "target": "universal",
      "headless": "html"
    }
  ]
}
```

Job parameters:
- `name` - Unique job identifier
- `url` - Target URL to scrape
- `every_s` - Frequency in seconds
- `enabled` - true/false to enable/disable
- `target` - Decodo target type (default: "universal")
- `headless` - Output format ("html", "json", "markdown" depending on plan)
- `locale` - Locale for rendering (default: "en-us")
- `device_type` - Device type (default: "desktop")

#### Run Ingestion Service

**Manual mode:**

```bash
# Set environment variables
export DECODO_AUTH_B64="your_credentials"
export ABX_INGEST_JOBS="/opt/aal/abraxas/.aal/jobs/ingest.jobs.json"
export ABX_INGEST_INTERVAL=60

# Run ingestion
abx ingest
```

**Production mode (systemd):**

```bash
# Copy service file
sudo cp systemd/abx-ingest.service /etc/systemd/system/

# Configure Decodo credentials in /etc/abraxas/decodo.env

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable abx-ingest
sudo systemctl start abx-ingest

# Monitor logs
sudo journalctl -u abx-ingest -f
```

Ingested documents are stored in SQLite at `/opt/aal/abraxas/.aal/state/abx.sqlite` with:
- Document ID (job_name:sha256_prefix)
- Source (decodo:job_name)
- URL
- Fetch timestamp
- Content type
- Full payload JSON
- SHA256 hash

### Chat-like UI

The UI provides an LLM-like chat interface with admin handshake for module discovery.

#### Start UI Server

**Manual mode:**

```bash
export ABX_UI_PORT=8780
abx ui
```

**Production mode (systemd):**

```bash
# Copy service file
sudo cp systemd/abx-ui.service /etc/systemd/system/

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable abx-ui
sudo systemctl start abx-ui

# Monitor logs
sudo journalctl -u abx-ui -f
```

UI runs on `http://0.0.0.0:8780` by default (configure with `ABX_UI_PORT`).

#### UI Endpoints

**Admin Handshake** - Discover modules and overlays:

```bash
curl http://localhost:8780/admin/handshake
```

Returns:
```json
{
  "type": "admin_handshake",
  "message": "Admin mode: modules detected. Choose interaction mode.",
  "modes": [
    {"id": "chat", "label": "Just interact with Abraxas (chat)"},
    {"id": "chat+modules", "label": "Chat + explicitly select modules/overlays"}
  ],
  "detected": {
    "built_in_modules": ["oracle", "rack", "weather", "semiotic"],
    "overlays": []
  }
}
```

**Chat Interaction** - Send messages:

```bash
curl -X POST http://localhost:8780/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "Hello Abraxas"}
    ],
    "selected_modules": []
  }'
```

Returns:
```json
{
  "assistant": {
    "role": "assistant",
    "content": "[stub] Processed: Hello Abraxas",
    "meta": {"frame_id": "frame_1234_abcd", "modules": []}
  },
  "frame": {
    "meta": {"frame_id": "frame_1234_abcd", "ts": 1766012345, "intent": "chat"},
    "input": {...},
    "output": {...}
  }
}
```

**Data Inspection** - View ingested data:

```bash
curl "http://localhost:8780/data/latest?source=decodo:ip_check&limit=10"
```

Returns latest documents from specified source.

#### Admin Handshake Flow

1. Client calls `GET /admin/handshake` to discover capabilities
2. Server returns list of built-in modules and installed overlays
3. User selects interaction mode:
   - **chat** - General interaction without module constraints
   - **chat+modules** - Explicitly select which modules/overlays to use
4. Client sends messages to `POST /chat` with optional `selected_modules` array

### CLI Commands

```bash
# Run ingestion scheduler (continuous)
abx ingest

# Start UI server
abx ui

# Print admin handshake JSON (for headless setup)
abx admin
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DECODO_AUTH_B64` | (required) | Base64-encoded credentials |
| `DECODO_MODE` | `realtime` | API mode (realtime/tasks) |
| `DECODO_ENDPOINT` | `https://scraper-api.decodo.com/v2/scrape` | Decodo API endpoint |
| `ABX_DB` | `/opt/aal/abraxas/.aal/state/abx.sqlite` | SQLite database path |
| `ABX_INGEST_INTERVAL` | `60` | Ingestion loop interval (seconds) |
| `ABX_INGEST_JOBS` | `/opt/aal/abraxas/.aal/jobs/ingest.jobs.json` | Jobs configuration file |
| `ABX_UI_PORT` | `8780` | UI server port |

### Full Stack Deployment

To run all components together:

```bash
# 1. Enable ingestion
sudo systemctl enable abx-ingest
sudo systemctl start abx-ingest

# 2. Enable UI
sudo systemctl enable abx-ui
sudo systemctl start abx-ui

# 3. Enable watchdog (from self-healing layer)
sudo systemctl enable abx-watchdog
sudo systemctl start abx-watchdog

# 4. Enable nightly updates (from self-healing layer)
sudo systemctl enable abx-update.timer
sudo systemctl start abx-update.timer

# Monitor all services
sudo systemctl status abx-ingest abx-ui abx-watchdog
```

### Next Steps: Real LLM Integration

The current chat implementation is a deterministic stub. Replace it with a real LLM:

**Option 1: Local model on Orin** (e.g., quantized Llama):
- Update `abx/ui/chat_engine.py` to call local inference
- Maintain same `/chat` contract for UI compatibility

**Option 2: Remote LLM** (e.g., Claude, GPT):
- Update `abx/ui/chat_engine.py` to call remote API
- Add caching and rate limiting
- Keep same `/chat` contract

The UI never changes—only the brain behind `chat_engine.py`.

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
│   ├── hashutil.py         # Deterministic hashing
│   └── logging.py          # Journald-friendly structured logging
├── runtime/
│   ├── config.py           # Runtime configuration
│   ├── provenance.py       # Provenance stamping
│   ├── drift.py            # Drift detection and snapshots
│   ├── watchdog.py         # Health monitoring with auto-restart
│   └── updater.py          # Atomic updates with rollback
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
