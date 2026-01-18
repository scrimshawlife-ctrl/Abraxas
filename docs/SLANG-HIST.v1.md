# SLANG-HIST.v1 (Historical Seed Corpus)

**Artifact:** SLANG-HIST.v1 (Historical Seed Corpus)

**Unit:** SlangPacket.v1 + SlangMetrics.v1

**Metrics:** STI, CP, IPS, SDR, NMC, ARF, SDI, IV, CLS, SSF

**Method:** seed_heuristic_rules.v1

**Constraint:** observation-only; may observe, never govern

**Evidence:** none (no frequency series yet)

## Seed heuristic rules (v1)

ARF mapping:
- slow = 30
- fast = 65
- viral = 90

SDI mapping:
- fade = 70
- volatile = 85
- flip = 75
- revive = 55
- institutionalize = 20

NMC mapping:
- oral = 10
- print = 20
- broadcast = 40
- internet = 80

SSF baseline:
- oral/print/broadcast: 5–15 (default 5)
- internet: 10–35 (default 10)
- moderation/euphemism pattern: 85–95 (unalive = 95)

CLS guidance:
- institutionalize: 80–95
- revive: 55–70
- fade: 15–35
- volatile: 25–55

IPS/IV guidance:
- boost when polarity in {ironic, fluid} and/or decay_pattern = flip
- taboo_level boosts moderately

CP guidance:
- role/job/tool/stance terms score higher (70–90)
- generic praise/insult lower (30–55)

## Observation-only contract

SLANG-HIST.v1 is observation-only. It may be attached as a signal payload,
but must never govern or alter prediction weights.
