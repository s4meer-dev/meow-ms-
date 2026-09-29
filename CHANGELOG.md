# Changelog

All notable changes to the **MEOW (Memory-Enhanced Operations & Workflow)** project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.1.0] - 2026-09-29

### Added
- **Closed-Loop Experiential Learning (Phase 7–9)**:
  - Integration of Hindsight experiential memory alongside Mem0 customer memory and ChromaDB knowledge base.
  - Causal categorization: `SUCCESS`, `FAILURE`, `PREFERENCE`, and `PATTERN`.
  - Closed-loop human agent feedback: rejected drafts record do-not-repeat failure patterns; accepted drafts commit verified solutions.
- **Connected Observability Dashboard**:
  - Zone 1: Persistent real-time "NOW" activity banner showing active component and execution status.
  - Zone 2: Step-by-step primary story action card tracking the 3-ticket learning progression.
  - Zone 3: "WHAT CHANGED?" data delta panel showing concrete before/after state diffs across Hindsight, Mem0, and SQLite.
  - Zone 4: "LIVE SYSTEM ACTIVITY" telemetry stream with real-time component execution badges (`SQLite`, `Mem0`, `RAG`, `Hindsight`, `Groq`).
  - Zone 5: Compact 6-step journey stepper and customer history timeline.
  - Deep inspection tabs for Customer Memory, Company Knowledge (RAG), System Architecture (SQLite), and Full Event Log.
- **Automated Verification & Tooling**:
  - 60-test automated verification suite covering shadow mode, dual-memory evaluation, isolation, and observability.
  - End-to-end demo lifecycle verification script (`scripts/verify_demo.py`).
  - Interactive terminal walkthrough runner for headless presentations (`scripts/demo_cli.py`).
  - Unified development and demonstration startup runner (`scripts/run_all.py`).
  - Subsystem latency benchmark tool (`scripts/benchmark_health.py`).
  - GitHub Actions CI workflow running full test suite on push to `main`.
- **Architectural Documentation**:
  - Architecture Decision Records (`ADR-001`, `ADR-002`, `ADR-003`).
  - Presenter guide and 90-second demo script (`docs/CONNECTED_DEMO_GUIDE.md`).
  - REST API endpoint reference (`docs/API_REFERENCE.md`).
  - Security policy and contributing guidelines.

### Security
- Automated secret and token sanitization (`customer_support_agent.core.sanitizer`).
- Zero secret leakage in API health diagnostic endpoints.
- Strict isolation between demo fixture state and live production customer banks.
