# MEOW Phase 2.5: Manual Verification Guide

**MEOW — Memory-Enhanced Operations & Workflow**  
*Support that remembers.*  
**Author:** `s4meer-dev`  
**Target Audience:** Any developer or DevOps engineer testing the system without prior knowledge of the codebase.

---

## 1. Prerequisites & Environment

1. **Python Environment**: Python 3.11 with virtual environment installed at `.venv/`.
2. **Docker**: Docker Desktop running with Compose v2.
3. **Configuration**: `.env` file present in the project root containing at minimum:
   ```env
   GROQ_API_KEY=gsk_...
   HINDSIGHT_API_URL=http://localhost:8888
   HINDSIGHT_ENABLED=true
   ```

---

## 2. Service Startup Instructions

### Step 2.1: Start the Hindsight Memory Server
In PowerShell, start the Hindsight container:
```powershell
docker compose up -d hindsight
```
Verify the container is healthy:
```powershell
docker ps --filter "name=meow-hindsight"
```
*Expected Output:* Status shows `Up ... (healthy)`.

Verify Hindsight `/health` endpoint directly:
```powershell
curl http://localhost:8888/health
```
*Expected Output:*
```json
{"status":"healthy","database":"connected",...}
```

---

### Step 2.2: Start the FastAPI Backend
Open a separate PowerShell terminal and run:
```powershell
.\.venv\Scripts\python.exe main.py
```
*Expected Output:*
```text
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

---

### Step 2.3: Start the Streamlit Dashboard
Open another PowerShell terminal and run:
```powershell
.\.venv\Scripts\streamlit.exe run app.py
```
*Expected Output:*
```text
  You can now view your Streamlit app in your browser.
  Local URL: http://localhost:8501
```

---

## 3. Automated API Diagnostic Verification

Verify the system components using the development diagnostic endpoints:

### Command 1: Base Health
```powershell
curl http://localhost:8000/health
```
*Expected Output:* `{"status":"ok"}`

### Command 2: Hindsight Subsystem Health
```powershell
curl http://localhost:8000/health/hindsight
```
*Expected Output:*
```json
{"available": true, "status": "ok", "url": "http://localhost:8888"}
```

### Command 3: Memory Pipeline & Architecture Diagnostics
```powershell
curl http://localhost:8000/debug/memory-flow
```
*Expected Output:*
```json
{
  "status": "ok",
  "database_available": true,
  "mem0_available": true,
  "chromadb_available": true,
  "hindsight_available": true,
  "active_production_flow": {
    "draft_generation": "SupportCopilot (LangChain + ChatGroq)",
    "customer_memory": "Mem0 (ChromaDB Vector Store)",
    "knowledge_rag": "ChromaDB RAG (Markdown Documents)",
    "connected": true
  },
  "shadow_experience_flow": {
    "experience_memory": "ExperienceMemoryService (Hindsight Isolated Banks)",
    "connected_to_production": false,
    "connected_to_ui": false,
    "status": "isolated_shadow"
  }
}
```

---

## 4. Manual Web UI Workflow Verification

Open your web browser and navigate to:  
**`http://localhost:8501`**

### Step 4.1: Ingest the Knowledge Base
1. Look at the left sidebar under **API Settings**.
2. Click the button: **`Ingest Knowledge Base`**.
3. **Expected Result:** A green banner appears saying:  
   `Indexed 4 files / 4 chunks` (or similar chunk count).

---

### Step 4.2: Create a Customer Support Ticket
1. In the main view under **Create Ticket**, enter:
   - **Customer Email:** `alex@acme.io`
   - **Customer Name:** `Alex Rivera`
   - **Company:** `Acme Labs`
   - **Priority:** `medium`
   - **Subject:** `Cannot withdraw cash from ATM`
   - **Description:** `My debit card transaction was declined at the ATM even though I have sufficient balance in my savings account.`
   - **Auto-generate draft:** `[x]` Checked
2. Click: **`Create Ticket`**.
3. **Expected Result:** A green banner confirms: `Ticket #1 created`.

---

### Step 4.3: Inspect & Generate Draft
1. Scroll down to the **Tickets** section.
2. In the **Select ticket** dropdown, choose:  
   `#1 | open | alex@acme.io | Cannot withdraw cash from ATM`.
3. If not generated automatically, click: **`Generate Draft`**.
4. **Expected Result:**
   - An editable text area appears containing an AI-generated draft response referencing bank withdrawal rules.
   - Click the expander **`Context used`**:
     - **Signals**: View `Memory Hits`, `KB Hits`, `Tool Calls`.
     - **Knowledge Sources**: Confirms `banking-atm-cash-withdrawal-faq.md`.

---

### Step 4.4: Accept Draft (Production Memory Retention)
1. Review the generated text in **Edit before sending**.
2. Click: **`Accept Draft`**.
3. **Expected Result:**
   - Green banner appears: `Draft accepted and memory updated`.
   - The ticket status updates to `resolved`.
   - The resolution is committed to **Mem0** (stored in `data/chroma_mem0/`).

---

### Step 4.5: Run Memory Probe
1. Scroll to the **Memory Probe** section at the bottom.
2. Enter the search query: `ATM withdrawal declined`.
3. Click: **`Run Memory Probe`**.
4. **Expected Result:**
   - Shows: `Found 1 memory hit(s)`.
   - Expanding the hit shows the accepted resolution and metadata with `scope: customer`.

---

## 5. Causal Experience Memory CLI Verification (Step 12 Demo Fixture)

To verify the **Hindsight Customer Experience Memory Layer** independently of the production UI, execute the deterministic verification script:

```powershell
.\.venv\Scripts\python.exe scripts\verify_experience_memory.py --mock
```
*(Omit `--mock` to run live against the Hindsight server when token quota is active)*

### Verifications Performed:
1. **Fixture Construction**: Builds `SupportExperience` with Problem (`Large report API timeout`), Failed Attempt (`Clear cache`), and Successful Attempt (`Increase timeout from 30 to 90 seconds`).
2. **Causal Narrative Generation**: Verifies `[FAILED - DO NOT REPEAT]` and `[SUCCESS - PROVEN FIX]` directives.
3. **Deterministic Identity**: Computes idempotent ID `meow-experience-ticket-meow-demo-001`.
4. **Experience Retention**: Retains into isolated bank `meow_customer_meow_demo_customer`.
5. **Failure-Aware Recall**:
   - Query: `"What fixed the large report API timeout?"` -> Returns 90-second timeout fix.
   - Query: `"What troubleshooting step failed?"` -> Returns failed cache clear attempt.
   - Query: `"How does this customer prefer technical support responses?"` -> Returns concise technical preference.
6. **Reflective Synthesis**:
   - Query: `"What should a support engineer know before troubleshooting this customer's report API timeout?"`
   - Returns synthesized operational directives instructing the agent never to repeat the failed cache clear step.

---

## 6. Full Automated Test Suite Execution

Run the complete regression suite:
```powershell
.\.venv\Scripts\pytest.exe -v
```

*Expected Result:*
- **31 Collected Items**
- **29 Passed**
- **2 Skipped** (Live Hindsight integration tests gracefully defer when upstream Groq free-tier daily token limits are reached)
- **0 Failed**
