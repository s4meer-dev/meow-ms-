# ADR-002: Closed-Loop Human Feedback and Retention Boundaries

## Status
Accepted

## Context
Autonomous AI systems that directly learn from their own generated drafts suffer from hallucination drift and compounding error loops:
- An incorrect or unvalidated suggestion can be re-ingested as ground truth.
- Without human oversight, dangerous troubleshooting steps (e.g., destructive cache wipes or premature database drops) can propagate across customer sessions.

## Decision
We enforce a mandatory human-in-the-loop review boundary before any operational outcome is committed to long-term memory:

1. **AI Output Is Always a Proposal (`status: pending`)**:
   - The LLM drafts a candidate reply based on retrieved context.
   - The reply is never transmitted directly to the customer or saved into memory banks at creation time.

2. **Explicit Human Decisions**:
   - **Acceptance (`status: accepted`)**:
     - Verified response is sent to customer.
     - Confirmed resolution is recorded in `Hindsight` as a `SUCCESS` experience.
     - Key operational facts are committed to `Mem0`.
   - **Rejection (`status: discarded`)**:
     - Draft is discarded in `SQLite`.
     - `Mem0` is explicitly bypassed (unverified suggestions are never saved as customer facts).
     - The failed attempt and human agent's rationale are recorded in `Hindsight` as a `FAILURE` experience (`[DO NOT REPEAT]`).

## Consequences
- **Positive**: Eliminates hallucination loops and guarantees experiential memory only reflects human-verified reality.
- **Negative**: Requires human agent participation during initial ticket handling.
