# ADR-001: Four-Tier Memory and Storage Architecture

## Status
Accepted

## Context
AI-powered customer support copilot systems frequently conflate multiple distinct types of information into a single unstructured prompt context or single vector index. This causes:
1. Operational bugs where unconfirmed agent guesses are mistakenly treated as verified facts.
2. Inability to recall failures (e.g., repeating troubleshooting steps the customer already tried).
3. Conflation between static policy documents (canonical knowledge) and customer-specific preferences.
4. Absence of auditable relational history for ticket lifecycles and human review decisions.

## Decision
We decouple state into four distinct, specialized storage tiers:

1. **Relational Storage (`SQLite`)**:
   - Manages ticket lifecycles (`open`, `pending`, `resolved`) and drafts (`pending`, `accepted`, `discarded`).
   - Serves as the source of truth for all transactional entities and audit trails.

2. **Customer Memory (`Mem0`)**:
   - Stores permanent customer profile facts (e.g., enterprise integration pipelines, SLA tiers).
   - Only stores *verified* resolutions; rejected drafts are explicitly excluded from Mem0.

3. **Domain Knowledge (`ChromaDB / RAG`)**:
   - Stores immutable company manuals, standard operating procedures, and product documentation.
   - Retrieved via semantic similarity on customer issue keywords.

4. **Experiential Memory (`Hindsight`)**:
   - Stores cognitive operational outcomes categorized into:
     - `FAILURE`: Do-not-repeat warnings with agent rationale.
     - `SUCCESS`: Verified fixes that successfully resolved an issue.
     - `PREFERENCE`: Customer communication and tone preferences.
     - `PATTERN`: Recurring incident triggers.

## Consequences
- **Positive**: Strict separation of concerns prevents data pollution across memory boundaries. Failures can be retained and recalled without altering factual profile information.
- **Negative**: Requires careful coordination and orchestration across multiple storage backends.
