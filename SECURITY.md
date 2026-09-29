# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

---

## 1. Secret Protection & Sanitization

MEOW strictly enforces automated credential protection across all tiers:
- **Zero Secrets in State / Logs**: API keys (`gsk_`, `sk-`, `AIza`, `Bearer`) are stripped and redacted via `customer_support_agent.core.sanitizer.sanitize_obj_for_display` before rendering to UI or outputting to telemetry.
- **Environment Isolation**: Live provider secrets reside solely in `.env` and are never serialized into SQLite databases, ChromaDB embeddings, or Mem0 user facts.
- **Diagnostic Endpoint Privacy**: The `/api/health` diagnostic endpoint reports subsystem connectivity status without returning tokens, credentials, or internal configuration values.

---

## 2. Reporting a Vulnerability

If you discover a security vulnerability within MEOW, please do not disclose it publicly in an issue.

Instead, please send an advisory email directly to:
- **Contact**: `sameer3sn7@gmail.com`
- **GitHub**: [@s4meer-dev](https://github.com/s4meer-dev)

Please include:
1. Description of the vulnerability.
2. Steps to reproduce or proof-of-concept payload.
3. Potential operational or privacy impact.

We will acknowledge receipt within 48 hours and work with you on a resolution.
