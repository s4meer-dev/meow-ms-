# MEOW: Connected Observable AI Support System
## Judge-Facing Demonstration & Architecture Guide

> **Core Thesis:** Generic AI support copilots repeat past mistakes because they rely solely on static documentation. MEOW introduces closed-loop experiential learning: capturing failure attempts, retaining verified fixes, and adapting future drafts based on what actually worked.

---

## 1. System Architecture & Connected Storage Tiers

MEOW coordinates four distinct storage and reasoning layers in real time:

```
                      ┌──────────────────────────────────────┐
                      │          Support Copilot (LLM)       │
                      │     (Groq / Llama 3.3 70B Versatile)  │
                      └──────────────────┬───────────────────┘
                                         │
       ┌──────────────────┬──────────────┴─────┬──────────────────┐
       │                  │                    │                  │
       ▼                  ▼                    ▼                  ▼
┌──────────────┐   ┌──────────────┐    ┌──────────────┐   ┌──────────────┐
│ SQLite DB    │   │ Mem0         │    │ ChromaDB     │   │ Hindsight    │
│ (Relational) │   │ (Facts)      │    │ (Knowledge)  │   │ (Experience) │
├──────────────┤   ├──────────────┤    ├──────────────┤   ├──────────────┤
│ • Tickets    │   │ • Customer   │    │ • Static     │   │ • Successes  │
│ • Drafts     │   │   profile    │    │   manuals    │   │ • Failures   │
│ • Customer   │   │ • Verified   │    │ • API guides │   │ • User prefs │
│   records    │   │   facts      │    │ • Semantic   │   │ • Recurring  │
│ • Decisions  │   │ • Preferences│    │   search     │   │   patterns   │
└──────────────┘   └──────────────┘    └──────────────┘   └──────────────┘
```

### The 4 Connected Layers:

1. **Relational Storage (`SQLite`)**:
   - Manages ticket lifecycles (`open`, `pending`, `resolved`) and response drafts (`pending`, `accepted`, `discarded`).
   - Ensures deterministic audit trails and state integrity.

2. **Customer Memory (`Mem0`)**:
   - Stores confirmed factual profile traits (e.g., *"Customer uses custom enterprise export pipeline"*).
   - Only stores *verified* resolutions; rejected drafts are never committed as facts.

3. **Domain Knowledge (`ChromaDB / RAG`)**:
   - Stores canonical product documentation, technical guides, and standard operating procedures.
   - Provides semantic search context based on issue keywords.

4. **Experiential Memory (`Hindsight`)**:
   - Captures real operational outcomes:
     - 🔴 **FAILURES**: Do-not-repeat warnings with agent rejection rationale.
     - 🟢 **SUCCESSES**: Proven fixes that successfully solved customer problems.
     - 🟡 **PREFERENCES**: Implicit and explicit communication style preferences.
     - 🟣 **PATTERNS**: Recurring system behaviors across recurring incidents.

---

## 2. The 4 Visual Zones in the MEOW Workspace

The UI is divided into 4 primary visual zones designed for immediate clarity:

### Zone 1: Persistent "NOW" Activity Banner
- Displays what MEOW is doing at this exact millisecond.
- Shows active component badge (`SQLite`, `Mem0`, `RAG`, `Hindsight`, `Groq`), current story step, and execution status (`PROCESSING`, `WAITING ON AGENT`, `RESOLVED`).

### Zone 2: Central Primary Story Action Card
- The focal point for the user/judge.
- Single clean container focusing on the immediate decision or discovery.
- Transitions sequentially through the 7-step learning narrative:
  1. `START`: Clean-slate initialization for customer Alex Rivera.
  2. `STEP_1_PROBLEM`: Ticket #1 intake (Large report export 504 timeout).
  3. `STEP_2_MEMORY`: Memory check shows 0 prior experiences.
  4. `STEP_3_DRAFT`: AI suggests standard documentation fix (Clear cache).
  5. `STEP_4_HUMAN`: Human agent rejects draft (*"Already cleared cache without effect"*).
  6. `STEP_5_FEEDBACK`: Failure experience retained in Hindsight; Mem0 bypassed.
  7. `STEP_6_RECALL`: Ticket #2 recurrence; MEOW recalls failure and avoids cache wipe.
  8. `STEP_7_BETTER`: Human accepts 90s timeout fix; retained as proven success.
  9. `DONE`: Ticket #3 arrives; MEOW synthesizes all 4 memory types (Fix + Failure + Preference + Pattern).

### Zone 3: "WHAT CHANGED?" Data Delta Panel
- Shows the concrete state change after every action.
- Directly contrasts before-and-after values for:
  - **Hindsight Experience Bank**: e.g., `0 → 1 experience (🔴 DO NOT REPEAT: Cache clearing failed)`
  - **Mem0 Facts**: e.g., `1 → 2 facts (Added confirmed resolution: timeout raised to 90s)`
  - **SQLite Database**: e.g., `Ticket #1002: OPEN → RESOLVED, Draft #5002: PENDING → ACCEPTED`

### Zone 4: "LIVE SYSTEM ACTIVITY" Telemetry Feed
- Displays real-time chronological event traces with component badges.
- Every state change triggers observable events across all layers:
  - `[SQLite] TICKET_CREATED`
  - `[Mem0] CUSTOMER_RECALLED`
  - `[RAG] KNOWLEDGE_RETRIEVED`
  - `[Hindsight] FAILURE_RECORDED`
  - `[Groq] DRAFT_GENERATED`

---

## 3. The 90-Second Demo Presentation Script

Follow this script during hackathon presentations or demo recordings:

### Second 0–15: Introduction & Initial Ticket
- *"Notice that Alex Rivera has opened a high-priority ticket: 504 Gateway Timeout on large batch exports."*
- Click **"Step 1: Check System Memory"**.
- Point to **Zone 3 & 4**: *"MEOW queries SQLite, Mem0, and Hindsight. Mem0 knows Alex's environment, but Hindsight finds 0 prior experiences. The knowledge base suggests clearing the cache."*

### Second 16–35: The AI Draft & Human Rejection
- Click **"Step 2: Generate Initial Draft"**.
- *"The AI proposes clearing browser and proxy caches. In a standard copilot, this would be sent to the customer."*
- Click **"Step 3: Support Agent Review"** → Click **"Reject Suggestion"**.
- Type or select: *"Already tried clearing cache without effect."*
- Point to **Zone 3 (WHAT CHANGED)**: *"Notice what happens: SQLite marks the draft DISCARDED. Mem0 refuses to store the rejected guess. But Hindsight immediately commits a FAILURE experience: 'Do not recommend cache clearing for Alex Rivera'."*

### Second 36–60: Ticket #2 Recurrence & Adaptive Recall
- Click **"Step 4: Ticket #2 Arrives"**.
- Point to **Zone 1 (NOW Banner)**: *"Alex returns with the same recurring 504 error."*
- Click **"Step 5: Generate Adaptive Draft"**.
- Highlight the draft: *"Look at the draft now: 'We note that clearing cache previously failed. For large exports, increase timeout from 30s to 90s.' MEOW avoided the repeated mistake without any manual retraining!"*
- Click **"Accept & Send Resolution"**.
- Point to **Zone 3**: *"SQLite marks Ticket #1002 RESOLVED. Mem0 adds the verified fix as a permanent customer fact. Hindsight stores the SUCCESS experience."*

### Second 61–90: Ticket #3 & Full Synthesis
- Click **"Step 6: Advance to Ticket #3"**.
- Point to **Tabs (Deep Inspection)**:
  - Open **"Customer Memory"** tab: show 4 experiences (Success, Failure, Preference, Pattern).
  - Open **"System Activity"** tab: show complete real-time event trace.
- *"When Alex submits a third ticket, MEOW synthesizes all 4 memory dimensions: it recalls the proven 90s fix, avoids the cache trap, applies Alex's preference for concise technical bullet points, and recognizes the end-of-month batch pattern. That is MEOW: support that truly remembers."*

---

## 4. Verification & Testing

MEOW includes a 60-test verification suite covering unit, integration, memory isolation, and observability layers:

```bash
# Run the complete test suite:
pytest tests/test_demo_observability.py tests/test_phase3_shadow.py -v
```

All 60 tests execute offline without network dependencies and verify that:
1. Demo fixture data cannot leak into production memory.
2. Hindsight provider quotas remain honest and un-faked.
3. Event streams emit accurate timestamps and status badges.
4. Data deltas reflect real before/after states across all storage layers.
