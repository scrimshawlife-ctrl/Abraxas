# Abraxas API & CLI Quick Start

This guide shows you how to run Abraxas end-to-end without UI, using the deterministic CLI and minimal FastAPI routes.

## Installation

### Core + CLI (no server)

```bash
pip install -e .
```

### With FastAPI Server

```bash
pip install -e ".[server]"
```

### With PostgreSQL Support

```bash
pip install -e ".[server,postgres]"
export DATABASE_URL="postgresql://user:pass@localhost/abraxas"
```

## CLI Usage

Run the oracle deterministically for a specific date:

```bash
python -m abraxas.oracle.cli \
  --date 2025-12-20 \
  --deltas ./examples/deltas.json \
  --half-life-hours 24 \
  --top-k 12
```

With Postgres persistence:

```bash
python -m abraxas.oracle.cli \
  --date 2025-12-20 \
  --deltas ./examples/deltas.json \
  --store
```

## API Server

Start the FastAPI server:

```bash
uvicorn abraxas.api.app:app --host 0.0.0.0 --port 8000
```

Or with auto-reload for development:

```bash
uvicorn abraxas.api.app:app --reload
```

### Test the API

**Health check:**
```bash
curl http://localhost:8000/health
```

**Register a lexicon:**
```bash
curl -X POST http://localhost:8000/api/lexicons/register \
  -H "Content-Type: application/json" \
  -d '{
    "domain": "crypto",
    "version": "1.0",
    "entries": [
      {"token": "bitcoin", "weight": 0.9, "meta": {"source": "manual"}},
      {"token": "ethereum", "weight": 0.85, "meta": {"source": "manual"}}
    ]
  }'
```

**Run oracle:**
```bash
curl -X POST http://localhost:8000/api/oracle/run \
  -H "Content-Type: application/json" \
  -d @examples/deltas.json
```

Or with inline data:
```bash
curl -X POST http://localhost:8000/api/oracle/run \
  -H "Content-Type: application/json" \
  -d '{
    "date": "2025-12-20",
    "deltas": [
      {
        "domain_a": "crypto",
        "domain_b": "social",
        "key": "bitcoin",
        "delta": 0.85,
        "observed_at_utc": "2025-12-20T10:30:00Z"
      }
    ],
    "config": {
      "half_life_hours": 24.0,
      "top_k": 5
    }
  }'
```

## WebSocket Event Streaming

Connect to real-time events:

```javascript
const ws = new WebSocket('ws://localhost:8000/ws');

ws.onopen = () => {
  console.log('Connected to Abraxas event stream');
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(`Event [${data.type}]:`, data.payload);
};
```

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      Abraxas System                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  CLI                    API                 WebSocket        │
│  ┌──────────┐          ┌──────────┐        ┌──────────┐    │
│  │ oracle   │          │ /lexicon │        │   /ws    │    │
│  │   cli    │          │ /oracle  │        │  events  │    │
│  └────┬─────┘          └────┬─────┘        └────┬─────┘    │
│       │                     │                   │           │
│       └──────────┬──────────┘                   │           │
│                  │                              │           │
│         ┌────────▼────────┐          ┌─────────▼────────┐  │
│         │ Oracle Runner   │          │   Event Bus      │  │
│         │  (Deterministic)│◄─────────┤   (Pub/Sub)      │  │
│         └────────┬────────┘          └──────────────────┘  │
│                  │                                          │
│         ┌────────▼────────┐                                 │
│         │ Lexicon Engine  │                                 │
│         │  (Compression)  │                                 │
│         └────────┬────────┘                                 │
│                  │                                          │
│         ┌────────▼────────┐                                 │
│         │   PostgreSQL    │  (optional)                     │
│         │  - Artifacts    │                                 │
│         │  - Lexicons     │                                 │
│         └─────────────────┘                                 │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Key Features

✅ **Deterministic Oracle**: Same inputs → same outputs → same signature
✅ **Minimal API**: 3 core endpoints (register lexicon, run oracle, fetch oracle)
✅ **Real-time Events**: WebSocket bridge from event bus
✅ **Optional Postgres**: Falls back to in-memory if DB not available
✅ **CLI First**: Run daily without server

## Next Steps

Once you have CLI and API working:

1. **Event Store Logging**: Add Postgres event logger with replay endpoint
2. **Daily Scheduler**: Create systemd timer or cron job for daily runs
3. **UI Dashboard**: Build thin client that consumes the API (not hijacks roadmap!)

See `abraxas/oracle/README.md` for detailed API documentation.

## Example Workflow

```bash
# 1. Run oracle via CLI (deterministic daily run)
python -m abraxas.oracle.cli \
  --date $(date +%Y-%m-%d) \
  --deltas ./data/today_deltas.json \
  --store

# 2. Query result via API
ARTIFACT_ID=$(python -m abraxas.oracle.cli --date $(date +%Y-%m-%d) --deltas ./data/today_deltas.json | jq -r '.id')
curl http://localhost:8000/api/oracle/$ARTIFACT_ID

# 3. Monitor live events via WebSocket
wscat -c ws://localhost:8000/ws
```

## Troubleshooting

**Import errors for fastapi/uvicorn:**
```bash
pip install -e ".[server]"
```

**Postgres connection errors:**
```bash
export DATABASE_URL="postgresql://localhost/abraxas"
# Or run without --store flag to use in-memory only
```

**Module not found: abraxas.oracle:**
```bash
pip install -e .
```
