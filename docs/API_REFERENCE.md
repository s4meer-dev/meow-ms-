# MEOW: Backend REST API Reference

The MEOW backend is implemented with FastAPI and exposes RESTful endpoints for ticket lifecycles, draft generation, experiential learning feedback, knowledge base search, and system health diagnostics.

Base URL: `http://localhost:8000`

---

## 1. System Health & Diagnostics

### `GET /api/health`
Retrieves live operational health across all integrated subsystems without exposing sensitive credentials.

- **Response `200 OK`**:
```json
{
  "status": "ok",
  "database": "connected",
  "mem0": "ready",
  "chroma": "ready",
  "hindsight": "ready",
  "mode": "DEMO_MODE"
}
```

---

## 2. Tickets Management

### `GET /api/tickets`
Lists all customer support tickets ordered by creation date descending.

- **Query Parameters**:
  - `status` *(optional, string)*: Filter by ticket status (`open`, `pending`, `resolved`).
  - `limit` *(optional, integer, default: 50)*: Maximum number of tickets to return.

- **Response `200 OK`**:
```json
[
  {
    "id": 1001,
    "customer_id": 9999,
    "customer_email": "alex.rivera@demo.meow",
    "customer_name": "Alex Rivera",
    "customer_company": "Acme Cloud Labs",
    "subject": "Large report API timeout error 504",
    "description": "Exporting customer ledger reports with >500 rows returns 504 Gateway Timeout after 60s.",
    "priority": "high",
    "status": "open",
    "created_at": "2026-09-28T10:00:00Z"
  }
]
```

### `POST /api/tickets`
Creates a new support ticket and initiates background draft generation.

- **Request Body**:
```json
{
  "customer_email": "alex.rivera@demo.meow",
  "customer_name": "Alex Rivera",
  "customer_company": "Acme Cloud Labs",
  "subject": "Large financial report export timeout",
  "description": "End-of-month financial report export timed out with 504.",
  "priority": "high"
}
```

- **Response `201 Created`**: Returns the created ticket object with assigned `id`.

---

## 3. Drafts & Learning Loop

### `GET /api/drafts/{ticket_id}`
Fetches the AI-generated reply draft for a given ticket.

- **Path Parameters**:
  - `ticket_id` *(integer)*: ID of the ticket.

- **Response `200 OK`**:
```json
{
  "id": 5001,
  "ticket_id": 1001,
  "content": "Hi Alex, please try clearing your local browser and proxy cache...",
  "status": "pending",
  "rejection_reason": null,
  "context_used": {
    "mem0_facts": ["Customer uses custom enterprise export pipeline"],
    "rag_sources": ["kb_api_guide"],
    "hindsight_experiences": []
  }
}
```

### `POST /api/drafts/{ticket_id}/generate`
Manually triggers or regenerates an AI response draft for a ticket.

- **Response `200 OK`**: Returns the newly generated draft object.

### `PATCH /api/drafts/{draft_id}`
Updates draft status with closed-loop human feedback (`accepted` or `discarded`).

- **Request Body (Accept)**:
```json
{
  "status": "accepted",
  "content": "Hi Alex, increase API client timeout to 90s in client configuration."
}
```

- **Request Body (Reject)**:
```json
{
  "status": "discarded",
  "content": "Hi Alex, please try clearing your local browser and proxy cache...",
  "rejection_reason": "Already tried clearing cache without effect"
}
```

- **Response `200 OK`**: Returns updated draft and experiential retention feedback:
```json
{
  "draft_id": 5001,
  "status": "discarded",
  "learning_feedback": {
    "retained": true,
    "category": "FAILURE",
    "experience_id": "exp_failure_1001"
  }
}
```

---

## 4. Knowledge Base & Vector Search

### `GET /api/knowledge/search`
Queries ChromaDB knowledge base for relevant policy and documentation snippets.

- **Query Parameters**:
  - `q` *(string)*: Search query string.
  - `limit` *(optional, integer, default: 3)*: Number of document chunks to return.

- **Response `200 OK`**:
```json
[
  {
    "document": "kb_api_guide",
    "score": 0.94,
    "content": "For high-volume export requests exceeding 500 rows, default gateway timeout of 30s may be raised up to 90s via export_timeout parameter."
  }
]
```
