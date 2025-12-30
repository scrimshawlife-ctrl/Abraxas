# Oracle Daily Run - Systemd Service

Automated daily Oracle v2 pipeline execution for historical data collection.

## Purpose

This service runs the Oracle v2 pipeline daily at 00:00 UTC to:
- Build historical τ (tau) measurements for stabilization gate validation
- Generate weather intel for memetic tracking
- Create forecast accuracy baseline data
- Enable 30-day stabilization window analysis

## Installation

### 1. Install Service Files

```bash
sudo cp systemd/abraxas-oracle-daily.service /etc/systemd/system/
sudo cp systemd/abraxas-oracle-daily.timer /etc/systemd/system/
sudo systemctl daemon-reload
```

### 2. Create Required Directories

```bash
sudo mkdir -p /var/lib/abraxas/{oracle_history,intel,reports}
sudo mkdir -p /var/log/abraxas
sudo chown -R abraxas:abraxas /var/lib/abraxas
sudo chown -R abraxas:abraxas /var/log/abraxas
```

### 3. Install Configuration

```bash
sudo cp config/oracle_daily.json /opt/abraxas/config/
```

### 4. Enable and Start Timer

```bash
sudo systemctl enable abraxas-oracle-daily.timer
sudo systemctl start abraxas-oracle-daily.timer
```

## Usage

### Check Timer Status

```bash
systemctl status abraxas-oracle-daily.timer
```

### View Upcoming Runs

```bash
systemctl list-timers abraxas-oracle-daily.timer
```

### Manually Trigger Run

```bash
sudo systemctl start abraxas-oracle-daily.service
```

### View Logs

```bash
# Service logs
sudo journalctl -u abraxas-oracle-daily.service

# Today's logs
sudo journalctl -u abraxas-oracle-daily.service --since today

# Follow logs
sudo journalctl -u abraxas-oracle-daily.service -f

# Log file
tail -f /var/log/abraxas/oracle_daily.log
```

## Output Structure

```
/var/lib/abraxas/
├── oracle_history/           # Historical Oracle runs
│   ├── oracle_runs_2025-12-29.jsonl
│   ├── oracle_runs_2025-12-30.jsonl
│   └── ...
├── intel/                    # Latest weather intel artifacts
│   ├── symbolic_pressure.json
│   ├── trust_index.json
│   └── semantic_drift_signal.json
└── reports/                  # Daily weather reports
    ├── weather_report_2025-12-29.json
    ├── weather_report_2025-12-30.json
    └── ...
```

## Configuration

Edit `/opt/abraxas/config/oracle_daily.json` to customize:
- **enabled_domains**: Which domains to process
- **sources**: Data sources (RSS, APIs, Decodo)
- **pipeline_config**: Oracle pipeline settings
- **output_config**: Output and retention settings

## Monitoring

### Health Checks

```bash
# Check if service ran today
ls -l /var/lib/abraxas/oracle_history/oracle_runs_$(date +%Y-%m-%d).jsonl

# Count historical runs
ls -1 /var/lib/abraxas/oracle_history/ | wc -l

# View latest weather report
cat /var/lib/abraxas/reports/weather_report_$(date +%Y-%m-%d).json | jq .
```

### Alert on Failure

```bash
# Add to systemd service file [Service] section:
OnFailure=abraxas-oracle-failure-alert@%n.service
```

## Historical Data Analysis

After 30 days of collection, run stabilization gate validation:

```bash
python -m abraxas.metrics.evaluate \
    --metric ORACLE_V2 \
    --gate stabilization \
    --window-days 30 \
    --data /var/lib/abraxas/oracle_history/
```

## Troubleshooting

### Service Not Running

```bash
# Check timer status
systemctl status abraxas-oracle-daily.timer

# Check service status
systemctl status abraxas-oracle-daily.service

# View recent errors
journalctl -u abraxas-oracle-daily.service -n 50
```

### Disk Space Issues

```bash
# Check disk usage
du -sh /var/lib/abraxas/oracle_history/

# Clean old runs (keep last 90 days)
find /var/lib/abraxas/oracle_history/ -name "*.jsonl" -mtime +90 -delete
```

### Configuration Validation

```bash
# Test configuration
python -m abraxas.cli.oracle_daily_run \
    --config /opt/abraxas/config/oracle_daily.json \
    --verbose
```

## Integration with Stabilization Gate

The daily runs enable 6-gate governance validation:

```
Day 1-29:  Building historical data (INCOMPLETE)
Day 30:    Stabilization gate validation (READY)
Day 30+:   Full 6-gate promotion eligible
```

**Stabilization criteria**:
- Consistent performance over 30-day window
- No catastrophic failures
- Forecast accuracy within expected variance
- Provenance chain integrity maintained

## Backup and Recovery

### Backup Historical Data

```bash
tar -czf oracle_history_backup_$(date +%Y%m%d).tar.gz \
    /var/lib/abraxas/oracle_history/
```

### Restore from Backup

```bash
tar -xzf oracle_history_backup_YYYYMMDD.tar.gz -C /
sudo chown -R abraxas:abraxas /var/lib/abraxas/oracle_history/
```

## See Also

- `abraxas/cli/oracle_daily_run.py` - CLI implementation
- `config/oracle_daily.json` - Configuration file
- `docs/specs/metric_governance.md` - 6-gate governance system
- `abraxas/oracle/v2/pipeline.py` - Oracle v2 pipeline
