# Abraxas Operational Runbook

## Overview
This runbook provides procedures for common operational tasks in Abraxas deployment and maintenance.

## Table of Contents
1. [System Health Checks](#system-health-checks)
2. [Starting and Stopping Services](#starting-and-stopping-services)
3. [Memory Layer Maintenance](#memory-layer-maintenance)
4. [Streaming Processor Operations](#streaming-processor-operations)
5. [Backup and Recovery](#backup-and-recovery)
6. [Log Management](#log-management)
7. [Performance Tuning](#performance-tuning)
8. [Troubleshooting Common Issues](#troubleshooting-common-issues)
9. [Updating Abraxas](#updating-abraxas)
10. [Security Procedures](#security-procedures)

## System Health Checks

### Basic Health Check
```bash
# Check if the Abraxas service is responding
curl http://localhost:8000/health
# Expected response: {"status": "healthy", "timestamp": "2026-10-04T10:30:00Z"}
```

### Detailed System Status
```bash
# Using the Abraxas CLI (if available)
abraxas status
# Or via Python
python -c "
from abraxas.governance.production import ProductionOrchestrator
orchestrator = ProductionOrchestrator()
orchestrator.initialize()
status = orchestrator.get_system_status()
print('System Status:', status)
orchestrator.shutdown()
"
```

### Component-Specific Checks

#### Memory Layer Health
```bash
python -c "
from abraxas.yggdrasil.memory import CypherMemoryLayer
memory = CypherMemoryLayer()
memory.initialize()
status = memory.get_status()
print('Memory Layer Status:', status)
memory.shutdown()
"
```

#### Orchestrator Health
```bash
python -c "
from abraxas.governance.production import ProductionOrchestrator
orchestrator = ProductionOrchestrator()
orchestrator.initialize()
status = orchestrator.get_system_status()
print('Orchestrator Status:')
print(f'  Initialized: {status.get(\"initialized\", False)}')
print(f'  Engines: {status.get(\"engines\", {})}')
print(f'  Streaming: {status.get(\"streaming\", {})}')
orchestrator.shutdown()
"
```

## Starting and Stopping Services

### Starting Abraxas Orchestrator
```bash
# Method 1: Using Python directly
python -m abraxas.governance.production

# Method 2: Using the CLI (if installed)
abraxas start

# Method 3: As a background service
nohup python -m abraxas.governance.production > abraxas.log 2>&1 &
echo $! > abraxas.pid
```

### Stopping Abraxas Orchestrator
```bash
# Method 1: Using CLI
abraxas stop

# Method 2: Using PID file
if [ -f abraxas.pid ]; then
    kill $(cat abraxas.pid)
    rm abraxas.pid
fi

# Method 3: Using pkill
pkill -f "abraxas.governance.production"
```

### Graceful Shutdown Procedure
1. Stop accepting new requests
2. Wait for ongoing processes to complete (or timeout)
3. Shutdown streaming processor
4. Shutdown memory layer
5. Shutdown engine registry
6. Exit

## Memory Layer Maintenance

### Checking Memory Layer Status
```bash
python -c "
from abraxas.yggdrasil.memory import CypherMemoryLayer
memory = CypherMemoryLayer()
memory.initialize()
status = memory.get_status()
print(f'Initialized: {status.get(\"initialized\", False)}')
print(f'Total Records: {status.get(\"total_records\", 0)}')
print(f'Evidence Records: {status.get(\"evidence_records\", 0)}')
print(f'Decision Records: {status.get(\"decision_records\", 0)}')
print(f'Storage Path: {status.get(\"storage_path\", \"unknown\")}')
print(f'Timechain Enabled: {status.get(\"timechain_enabled\", False)}')
memory.shutdown()
"
```

### Manual Memory Layer Backup
```bash
# Backup the memory storage directory
STORAGE_PATH=$(python -c "
from abraxas.yggdrasil.memory import CypherMemoryLayer
memory = CypherMemoryLayer()
memory.initialize()
print(memory.storage_path)
memory.shutdown()
")

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/abraxas_memory_${TIMESTAMP}"
mkdir -p "${BACKUP_DIR}"
cp -r "${STORAGE_PATH}"/* "${BACKUP_DIR}/"
echo "Memory layer backed up to ${BACKUP_DIR}"
```

### Manual Memory Layer Restore
```bash
# Stop Abraxas first
abraxas stop

# Restore from backup
STORAGE_PATH=$(python -c "
from abraxas.yggdrasil.memory import CypherMemoryLayer
memory = CypherMemoryLayer()
memory.initialize()
print(memory.storage_path)
memory.shutdown()
")

BACKUP_DIR="/path/to/backup/directory"  # Change this to your backup
cp -r "${BACKUP_DIR}"/* "${STORAGE_PATH}/"
echo "Memory layer restored from ${BACKUP_DIR}"

# Start Abraxas
abraxas start
```

### Memory Layer Cleanup
```bash
# Clean old records (beyond retention period)
python -c "
from abraxas.yggdrasil.memory import CypherMemoryLayer
import time
memory = CypherMemoryLayer()
memory.initialize()

# Remove records older than 30 days
cutoff_time = time.time() - (30 * 24 * 60 * 60)
cleaned = memory.cleanup_old_records(cutoff_time)
print(f'Cleaned {cleaned} old records')

memory.shutdown()
"
```

## Streaming Processor Operations

### Starting Streaming Processor
```bash
python -c "
from abraxas.governance.production import ProductionOrchestrator
orchestrator = ProductionOrchestrator()
orchestrator.initialize()
orchestrator.start_streaming_processor(num_workers=4)
print('Streaming processor started with 4 workers')
# Keep running... (in practice, this would be part of a service)
orchestrator.shutdown()
"
```

### Checking Streaming Processor Status
```bash
python -c "
from abraxas.governance.production import ProductionOrchestrator
orchestrator = ProductionOrchestrator()
orchestrator.initialize()
status = orchestrator.get_system_status()
streaming_info = status.get('streaming', {})
print(f'Streaming Active: {streaming_info.get(\"active\", False)}')
print(f'Worker Count: {streaming_info.get(\"worker_count\", 0)}')
print(f'Queue Size: {streaming_info.get(\"queue_size\", 0)}')
print(f'Processed Count: {streaming_info.get(\"processed_count\", 0)}'
print(f'Failed Count: {streaming_info.get(\"failed_count\", 0)}')
orchestrator.shutdown()
"
```

### Stopping Streaming Processor
```bash
python -c "
from abraxas.governance.production import ProductionOrchestrator
orchestrator = ProductionOrchestrator()
orchestrator.initialize()
orchestrator.stop_streaming_processor()
print('Streaming processor stopped')
orchestrator.shutdown()
"
```

### Submitting Evidence for Streaming
```bash
python -c "
from abraxas.governance.production import ProductionOrchestrator
import time
orchestrator = ProductionOrchestrator()
orchestrator.initialize()
orchestrator.start_streaming_processor()

# Submit evidence for processing
stream_id = orchestrator.submit_evidence_stream(
    'test-evidence-001',
    'What is the capital of Japan?',
    {'domain': 'geography', 'priority': 'high'}
)
print(f'Submitted evidence with stream ID: {stream_id}')

# Wait a bit for processing
time.sleep(2)

# Retrieve result
result = orchestrator.get_stream_result(stream_id, timeout=5.0)
print(f'Stream result: {result}')

orchestrator.stop_streaming_processor()
orchestrator.shutdown()
"
```

## Backup and Recovery

### Full System Backup
```bash
#!/bin/bash
# Abraxas full system backup script

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/abraxas_full_${TIMESTAMP}"
mkdir -p "${BACKUP_DIR}"

# 1. Backup configuration
cp -r ./config "${BACKUP_DIR}/" 2>/dev/null || echo "No config directory to backup"

# 2. Backup memory layer
python -c "
from abraxas.yggdrasil.memory import CypherMemoryLayer
memory = CypherMemoryLayer()
memory.initialize()
import shutil
import os
shutil.copytree(memory.storage_path, '${BACKUP_DIR}/memory')
memory.shutdown()
"

# 3. Backup logs (if applicable)
cp -r ./logs "${BACKUP_DIR}/" 2>/dev/null || echo "No logs directory to backup"

# 4. Create backup manifest
cat > "${BACKUP_DIR}/MANIFEST" << EOF
Abraxas Backup Manifest
======================
Timestamp: $(date)
Version: $(python -c "import abraxas; print(abraxas.__version__)" 2>/dev/null || echo "unknown")
Components:
- Configuration: $(ls -la "${BACKUP_DIR}/config/" 2>/dev/null | wc -l) items
- Memory Layer: $(du -sh "${BACKUP_DIR}/memory/" 2>/dev/null | cut -f1)
- Logs: $(du -sh "${BACKUP_DIR}/logs/" 2>/dev/null | cut -f1)
EOF

echo "Full backup completed: ${BACKUP_DIR}"
```

### Restore from Backup
```bash
#!/bin/bash
# Abraxas restore from backup script

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <backup_directory>"
    exit 1
fi

BACKUP_DIR="$1"

if [ ! -d "${BACKUP_DIR}" ]; then
    echo "Backup directory not found: ${BACKUP_DIR}"
    exit 1
fi

echo "Restoring Abraxas from backup: ${BACKUP_DIR}"

# 1. Stop Abraxas
abraxas stop

# 2. Restore configuration
if [ -d "${BACKUP_DIR}/config" ]; then
    cp -r "${BACKUP_DIR}/config"/* ./config/ 2>/dev/null || echo "No config to restore"
fi

# 3. Restore memory layer
if [ -d "${BACKUP_DIR}/memory" ]; then
    python -c "
from abraxas.yggdrasil.memory import CypherMemoryLayer
import shutil
import os
memory = CypherMemoryLayer()
memory.initialize()
# Clear existing storage
if os.path.exists(memory.storage_path):
    shutil.rmtree(memory.storage_path)
os.makedirs(memory.storage_path, exist_ok=True)
# Copy backup
shutil.copytree('${BACKUP_DIR}/memory', os.path.join(memory.storage_path, 'backup'))
# Move contents up
for item in os.listdir(os.path.join(memory.storage_path, 'backup')):
    shutil.move(os.path.join(memory.storage_path, 'backup', item), os.path.join(memory.storage_path, item))
os.rmdir(os.path.join(memory.storage_path, 'backup'))
memory.shutdown()
"
fi

# 4. Restore logs (if applicable)
if [ -d "${BACKUP_DIR}/logs" ]; then
    cp -r "${BACKUP_DIR}/logs"/* ./logs/ 2>/dev/null || echo "No logs to restore"
fi

# 5. Start Abraxas
abraxas start

echo "Restore completed from ${BACKUP_DIR}"
```

## Log Management

### Log Rotation Setup
```bash
# Using logrotate (example configuration)
cat > /etc/logrotate.d/abraxas << EOF
/var/log/abraxas/*.log {
    daily
    rotate 14
    compress
    delaycompress
    missingok
    notifempty
    create 644 abraxas abraxas
    sharedscripts
    postrotate
        # Restart Abraxas service if needed
        systemctl restart abraxas-service >/dev/null 2>&1 || true
    endscript
}
EOF
```

### Viewing Recent Logs
```bash
# Tail the main Abraxas log
tail -f ./logs/abraxas.log

# View logs with timestamps
grep "ERROR" ./logs/abraxas.log | tail -20

# Get log statistics
python -c "
import collections
import re
with open('./logs/abraxas.log', 'r') as f:
    logs = f.readlines()

levels = collections.Counter()
for line in logs:
    if 'ERROR' in line:
        levels['ERROR'] += 1
    elif 'WARN' in line:
        levels['WARN'] += 1
    elif 'INFO' in line:
        levels['INFO'] += 1
    elif 'DEBUG' in line:
        levels['DEBUG'] += 1

print('Log Levels:')
for level, count in levels.items():
    print(f'  {level}: {count}')
"
```

### Structured Logging Configuration
```bash
# Configure Abraxas for JSON logging (if supported)
cat > ./config/logging.json << EOF
{
  "version": 1,
  "disable_existing_loggers": false,
  "formatters": {
    "json": {
      "class": "pythonjsonlogger.json.JsonFormatter",
      "format": "%(asctime)s %(name)s %(levelname)s %(message)s %(pathname)s %(lineno)d"
    }
  },
  "handlers": {
    "file": {
      "class": "logging.handlers.RotatingFileHandler",
      "level": "INFO",
      "formatter": "json",
      "filename": "./logs/abraxas.json.log",
      "maxBytes": 10485760,
      "backupCount": 5
    },
    "console": {
      "class": "logging.StreamHandler",
      "level": "INFO",
      "formatter": "json",
      "stream": "ext://sys.stdout"
    }
  },
  "root": {
    "level": "INFO",
    "handlers": ["file", "console"]
  }
}
EOF
```

## Performance Tuning

### Memory Layer Tuning
```bash
# Adjust memory layer parameters for better performance
# Edit the CypherMemoryLayer constructor parameters:
# - storage_path: Use SSD for better I/O performance
# - Enable Timechain only if needed (adds overhead)
# - Consider increasing cache sizes if applicable

# Example optimization for high-write scenarios
python -c "
from abraxas.yggdrasil.memory import CypherMemoryLayer
# Use buffered writes and larger cache
memory = CypherMemoryLayer(
    storage_path='/ssd/abraxas_memory',  # Fast storage
    # Other performance-related parameters would go here
)
memory.initialize()
# ... use memory ...
memory.shutdown()
"
```

### Orchestrator Tuning
```bash
# Adjust orchestrator parameters
python -c "
from abraxas.governance.production import ProductionOrchestrator
orchestrator = ProductionOrchestrator(
    # Tune engine initialization timeout
    engine_init_timeout=30.0,
    # Tune arbitration timeout
    arbitration_timeout=10.0,
    # Tune governance check strictness
    governance_strictness=0.8
)
orchestrator.initialize()
# ... use orchestrator ...
orchestrator.shutdown()
"
```

### Streaming Processor Tuning
```bash
# Tune streaming processor for your workload
python -c "
from abraxas.governance.production import ProductionOrchestrator
orchestrator = ProductionOrchestrator()
orchestrator.initialize()

# Start with optimal worker count based on CPU cores
import os
cpu_count = os.cpu_count() or 4
optimal_workers = min(cpu_count * 2, 16)  # Cap at 16 workers

orchestrator.start_streaming_processor(num_workers=optimal_workers)
print(f'Started streaming processor with {optimal_workers} workers')

# Adjust queue size based on expected burst traffic
# (This would be configured in the ProductionOrchestrator constructor)

orchestrator.shutdown()
"
```

### Verifier Performance Tuning
```bash
# The SignRelationVerifier already uses LRU caching
# To adjust cache size:
python -c "
from abraxas.evidence.verifiers.sign import SignRelationVerifier
from functools import lru_cache

# To change cache size, you would modify the decorator:
# @lru_cache(maxsize=256)  # Instead of 128
# This requires modifying the source code

verifier = SignRelationVerifier()
print('SignRelationVerifier uses LRU caching with maxsize=128')
print('To change cache size, edit abraxas/evidence/verifiers/sign.py')
"
```

## Troubleshooting Common Issues

### Issue: Import Errors
**Symptoms**: `ModuleNotFoundError: No module named 'abraxas'`
**Solution**:
```bash
# Ensure you're in the correct directory
cd /path/to/abraxas

# Install in development mode
pip install -e .

# Verify installation
python -c "import abraxas; print('Abraxas version:', abraxas.__version__)"
```

### Issue: Memory Layer Storage Errors
**Symptoms**: Permission errors, disk full errors, storage corruption
**Solution**:
```bash
# Check storage path permissions
python -c "
from abraxas.yggdrasil.memory import CypherMemoryLayer
memory = CypherMemoryLayer()
memory.initialize()
print('Storage path:', memory.storage_path)
import os
print('Path exists:', os.path.exists(memory.storage_path))
print('Path writable:', os.access(memory.storage_path, os.W_OK))
memory.shutdown()
"

# Check disk space
df -h $(python -c "
from abraxas.yggdrasil.memory import CypherMemoryLayer
memory = CypherMemoryLayer()
memory.initialize()
print(memory.storage_path)
memory.shutdown()
")

# Clear old records if needed
python -c "
from abraxas.yggdrasil.memory import CypherMemoryLayer
import time
memory = CypherMemoryLayer()
memory.initialize()
# Clean records older than 7 days
cleaned = memory.cleanup_old_records(time.time() - (7 * 24 * 60 * 60))
print(f'Cleaned {cleaned} old records')
memory.shutdown()
"
```

### Issue: Streaming Processor Backup
**Symptoms**: Queue backup, increasing latency, worker starvation
**Solution**:
```bash
# Check streaming status
python -c "
from abraxas.governance.production import ProductionOrchestrator
orchestrator = ProductionOrchestrator()
orchestrator.initialize()
status = orchestrator.get_system_status()
streaming = status.get('streaming', {})
print('Streaming Active:', streaming.get('active', False))
print('Queue Size:', streaming.get('queue_size', 0))
print('Worker Count:', streaming.get('worker_count', 0))
print('Processed Count:', streaming.get('processed_count', 0))
print('Failed Count:', streaming.get('failed_count', 0))
orchestrator.shutdown()
"

# If queue is backing up:
# 1. Increase worker count
# 2. Check if workers are stuck (look at logs)
# 3. Consider reducing submission rate
# 4. Check if external dependencies are slow

# Restart streaming processor if needed
python -c "
from abraxas.governance.production import ProductionOrchestrator
orchestrator = ProductionOrchestrator()
orchestrator.initialize()
orchestrator.stop_streaming_processor()
orchestrator.start_streaming_processor(num_workers=8)  # Increase workers
orchestrator.shutdown()
"
```

### Issue: Slow Arbitration Performance
**Symptoms**: High latency in evidence arbitration, low throughput
**Solution**:
```bash
# Profile arbitration performance
python -c "
import time
from abraxas.governance.production import ProductionOrchestrator
from abraxas.evidence.contract import EvidenceEnvelope, EvidenceType, CandidateOutput, RelationStep

orchestrator = ProductionOrchestrator()
orchestrator.initialize()

# Create test envelope
envelope = EvidenceEnvelope(
    engine='test',
    engine_version='1.0',
    model_identity='test_model',
    request_id='perf-test-001',
    claim='Performance test claim',
    candidate_outputs=[CandidateOutput(
        answer='Test answer',
        confidence=0.8,
        reasoning_trace='Test reasoning',
        relation_steps=[RelationStep(
            relation='test',
            subject='test',
            object='test',
            result='test',
            confidence=0.8
        ) for _ in range(5)]  # Vary this to test complexity
    )],
    evidence_type=EvidenceType.RELATIONAL_REASONING,
    confidence=0.8,
    uncertainty=0.2,
    provenance={'test': True}
)

# Time arbitration
start = time.time()
for i in range(100):
    result = orchestrator.arbitrate_pipeline(envelope.claim)
end = time.time()

avg_time = (end - start) / 100
print(f'Average arbitration time: {avg_time*1000:.2f}ms')
print(f'Throughput: {1/avg_time:.0f} arbitrations/second')

orchestrator.shutdown()
"

# If slow:
# 1. Check if engines are initializing slowly
# 2. Profile individual engine performance
# 3. Consider caching frequently used results
# 4. Check if governance checks are too strict
# 5. Optimize evidence creation complexity
```

### Issue: High Memory Usage
**Symptoms**: Increasing memory consumption over time, eventual OOM kills
**Solution**:
```bash
# Check memory layer for record accumulation
python -c "
from abraxas.yggdrasil.memory import CypherMemoryLayer
memory = CypherMemoryLayer()
memory.initialize()
status = memory.get_status()
print('Total Records:', status.get('total_records', 0))
print('Evidence Records:', status.get('evidence_records', 0))
print('Decision Records:', status.get('decision_records', 0))
memory.shutdown()
"

# If records are accumulating:
# 1. Implement regular cleanup
# 2. Check if streaming results are not being cleaned up
# 3. Verify that temporary objects are being released
# 4. Consider implementing record TTL (time-to-live)

# Check for streaming result accumulation
python -c "
from abraxas.governance.production import ProductionOrchestrator
orchestrator = ProductionOrchestrator()
orchestrator.initialize()
status = orchestrator.get_system_status()
streaming = status.get('streaming', {})
print('Streaming Results Count:', streaming.get('results_count', 'not_available'))
orchestrator.shutdown()
"
```

## Updating Abraxas

### Checking Current Version
```bash
python -c "import abraxas; print(abraxas.__version__)"
```

### Updating via Pip
```bash
# Check for updates
pip list --outdated | grep abraxas

# Update to latest version
pip install --upgrade abraxas-framework

# Or update from source
cd /path/to/abraxas
git pull origin main
pip install -e .
```

### Update Procedure
```bash
#!/bin/bash
# Abraxas update procedure

echo "Starting Abraxas update..."

# 1. Stop Abraxas
abraxas stop

# 2. Backup current state (optional but recommended)
./backup_script.sh  # Refer to backup section above

# 3. Pull latest code
cd /path/to/abraxas
git fetch origin
git reset --hard origin/main

# 4. Reinstall dependencies
pip install -e .[dev]

# 5. Run database migrations if any
# python -m abraxas.migrate  # If migration system exists

# 6. Start Abraxas
abraxas start

# 7. Verify update
python -c "import abraxas; print('Updated to version:', abraxas.__version__)"

echo "Abraxas update completed"
```

### Rollback Procedure
```bash
#!/bin/bash
# Abraxas rollback procedure

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <backup_directory>"
    exit 1
fi

BACKUP_DIR="$1"

echo "Rolling back Abraxas from backup: ${BACKUP_DIR}"

# 1. Stop Abraxas
abraxas stop

# 2. Restore from backup (refer to backup section)
./restore_script.sh "${BACKUP_DIR}"

# 3. Verify rollback
python -c "import abraxas; print('Rolled back to version:', abraxas.__version__)"

echo "Abraxas rollback completed"
```

## Security Procedures

### Checking for Vulnerabilities
```bash
# Check dependencies for known vulnerabilities
pip list --outdated
pip-audit  # If installed
safety check  # If safety is installed

# Or use GitHub's dependabot alerts
```

### Rotating Secrets
```bash
# If using external services (API keys, database passwords, etc.)
# 1. Generate new secrets
# 2. Update configuration files or environment variables
# 3. Restart Abraxas to pick up new secrets
# 4. Verify functionality
# 5. Remove old secrets from storage

# Example for Timechain configuration (if used)
# Update TimechainConfig with new credentials and restart memory layer
```

### Security Scan Procedure
```bash
#!/bin/bash
# Basic security scan for Abraxas deployment

echo "Starting Abraxas security scan..."

# 1. Check file permissions
echo "Checking file permissions..."
find . -type f -name "*.py" -perm /022 | head -10
find . -type f -name "*.yaml" -o -name "*.yml" -o -name "*.json" -perm /022 | head -10

# 2. Check for hardcoded secrets (basic patterns)
echo "Checking for potential hardcoded secrets..."
grep -r "password\|secret\|key\|token" . --include="*.py" --include="*.yaml" --include="*.yml" --include="*.json" | grep -v "__pycache__" | head -10

# 3. Check dependencies
echo "Checking dependency versions..."
pip list --outdated | head -10

# 4. Check configuration exposure
echo "Checking for exposed configuration..."
find . -name "config*" -o -name "*.env" -o -name "settings*" | head -10

echo "Security scan completed. Review output above for potential issues."
```

### Incident Response Procedure
1. **Identify**: Determine the nature and scope of the security incident
2. **Contain**: Isolate affected systems to prevent further damage
3. **Eradicate**: Remove the threat and restore systems to known good state
4. **Recover**: Return systems to normal operation and verify functionality
5. **Learn**: Document the incident and update procedures to prevent recurrence

### Emergency Shutdown Procedure
```bash
# In case of suspected compromise or emergency
abraxas stop

# Or force kill
pkill -9 -f "abraxas"

# Isolate network
# Depending on your infrastructure, you may want to:
# 1. Disconnect from network
# 2. Block incoming/outgoing traffic on Abraxas ports
# 3. Take snapshots for forensic analysis

# Contact security team
# Follow your organization's incident response plan
```

## Appendix: Useful Commands

### Quick Diagnostics
```bash
# One-liner to check overall system health
python -c "
try:
    from abraxas.governance.production import ProductionOrchestrator
    from abraxas.yggdrasil.memory import CypherMemoryLayer
    
    # Check orchestrator
    orchestrator = ProductionOrchestrator()
    orchestrator.initialize()
    orch_status = orchestrator.get_system_status()
    orchestrator.shutdown()
    
    # Check memory layer
    memory = CypherMemoryLayer()
    memory.initialize()
    mem_status = memory.get_status()
    memory.shutdown()
    
    print('=== Abraxas Health Check ===')
    print(f'Orchestrator Initialized: {orch_status.get(\"initialized\", False)}')
    print(f'Memory Layer Initialized: {mem_status.get(\"initialized\", False)}')
    print(f'Total Memory Records: {mem_status.get(\"total_records\", 0)}')
    print('System Status: HEALTHY' if orch_status.get(\"initialized\", False) and mem_status.get(\"initialized\", False) else 'System Status: DEGRADED')
    
except Exception as e:
    print(f'System Status: UNHEALTHY - Error: {e}')
"
```

### Performance Baseline
```bash
# Establish performance baseline
python benchmarks/benchmark_suite.py 2>&1 | tee baseline_$(date +%Y%m%d_%H%M%S).log
```

### Configuration Validation
```bash
# Validate configuration files
python -c "
import yaml
import json
import os

config_files = [
    './config/settings.yaml',
    './config/logging.yaml',
    './config/production.yaml'
]

for config_file in config_files:
    if os.path.exists(config_file):
        try:
            if config_file.endswith('.yaml') or config_file.endswith('.yml'):
                with open(config_file, 'r') as f:
                    yaml.safe_load(f)
                print(f'✓ {config_file}: Valid YAML')
            elif config_file.endswith('.json'):
                with open(config_file, 'r') as f:
                    json.load(f)
                print(f'✓ {config_file}: Valid JSON')
            else:
                print(f'? {config_file}: Unknown format')
        except Exception as e:
            print(f'✗ {config_file}: Invalid - {e}')
    else:
        print(f'- {config_file}: Not found')
"
```