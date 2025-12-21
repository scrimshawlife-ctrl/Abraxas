# Abraxas Oracle CLI & API

Deterministic oracle system for correlation analysis with CLI and FastAPI interface.

## CLI Usage

Run the oracle deterministically for a specific date:

```bash
python -m abraxas.oracle.cli \
  --date 2025-12-20 \
  --deltas ./examples/deltas.json \
  --half-life-hours 24 \
  --top-k 12
```

### CLI Arguments

- `--date` (required): Date in YYYY-MM-DD format
- `--deltas` (required): Path to JSON file with correlation deltas
- `--half-life-hours` (optional): Decay half-life in hours (default: 24.0)
- `--top-k` (optional): Number of top signals to return (default: 12)
- `--run-id` (optional): Custom run identifier (UUID generated if not provided)
- `--as-of-utc` (optional): Reference timestamp in ISO8601 Z format
- `--store` (optional): Persist to Postgres (requires DATABASE_URL env var)

### Deltas JSON Format

```json
{
  "deltas": [
    {
      "domain_a": "crypto",
      "domain_b": "social",
      "key": "bitcoin",
      "delta": 0.85,
      "observed_at_utc": "2025-12-20T10:30:00Z"
    }
  ]
}
```

## API Usage

### Start the API Server

```bash
uvicorn abraxas.api.app:app --host 0.0.0.0 --port 8000
```

### Endpoints

#### POST /api/lexicons/register

Register a lexicon pack:

```bash
curl -X POST http://localhost:8000/api/lexicons/register \
  -H "Content-Type: application/json" \
  -d '{
    "domain": "crypto",
    "version": "1.0",
    "entries": [
      {"token": "bitcoin", "weight": 0.9, "meta": {}},
      {"token": "ethereum", "weight": 0.85, "meta": {}}
    ]
  }'
```

#### POST /api/oracle/run

Run oracle for a date:

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
      "top_k": 12
    },
    "store": false
  }'
```

#### GET /api/oracle/{artifact_id}

Fetch oracle artifact by ID (requires Postgres store):

```bash
curl http://localhost:8000/api/oracle/{artifact_id}
```

#### WebSocket /ws

Connect to WebSocket for real-time event streaming:

```javascript
const ws = new WebSocket('ws://localhost:8000/ws');
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Event:', data.type, data.payload);
};
```

Event types:
- `compression`: Lexicon compression events
- `correlation`: Correlation delta events
- `oracle`: Oracle generation events
- `lexicon`: Lexicon registration events
- `error`: Error events

## PostgreSQL Support

Optional PostgreSQL persistence for oracle artifacts and lexicon packs.

### Setup

1. Install PostgreSQL support:
```bash
pip install psycopg2-binary
```

2. Set DATABASE_URL:
```bash
export DATABASE_URL="postgresql://user:pass@localhost/abraxas"
```

3. Tables are created automatically on first use.

## Architecture

- **CLI**: Deterministic oracle runner (`abraxas.oracle.cli`)
- **API**: FastAPI routes (`abraxas.api.routes`)
- **Event Bus**: Pub/sub messaging (`abraxas.events.bus`)
- **WebSocket**: Real-time event streaming (`abraxas.api.ws`)
- **Storage**: Optional Postgres persistence (`abraxas.oracle.pg_store`, `abraxas.lexicon.pg_registry`)

## Dependencies

Core:
- `pydantic>=2.0.0`

Server (optional):
- `fastapi>=0.104.0`
- `uvicorn[standard]>=0.24.0`
- `websockets>=12.0`

PostgreSQL (optional):
- `psycopg2-binary>=2.9.0`

Install with:
```bash
pip install -e ".[server,postgres]"
```
