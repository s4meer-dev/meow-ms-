# ADR-003: Deterministic Demo Isolation and Production Segregation

## Status
Accepted

## Context
During presentations, hackathons, and offline reviews, third-party network APIs or quota limits (e.g., LLM provider rate limits, live memory server cold starts) can introduce latency or downtime.
Conversely, running synthetic demo fixtures directly against live production databases risks data pollution and corrupted production customer memory banks.

## Decision
We enforce strict architectural segregation between **Live Production Mode** and **Demo Mode**:

1. **Deterministic Scenario Controller (`DemoLearningController`)**:
   - Manages a self-contained, offline-capable 3-ticket state machine for customer Alex Rivera.
   - Operates in dedicated in-memory projections completely segregated from SQLite production tables.
   - Provider quota limits or external API outages never impact the demonstration narrative.

2. **Zero Fixture Leakage**:
   - Demo customer IDs and bank namespaces (`customer_bank_alex_rivera`) are isolated from real customer accounts.
   - Demo reset completely cleans demo fixture state without touching persistent production SQLite records or live Mem0 indices.

3. **Quota & Measurement Honesty**:
   - Demo mock scores and relevance weights are never presented as real live provider latency measurements.
   - Live Production Mode transparently reports actual connection status and honest error codes.

## Consequences
- **Positive**: 100% reproducible demonstrations and offline presentations with zero risk to production data integrity.
- **Negative**: Requires maintaining synchronized state projections for demo presentations.
