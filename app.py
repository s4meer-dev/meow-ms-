"""Streamlit dashboard for support agents."""

from __future__ import annotations

import os
import re
from typing import Any

import requests
import streamlit as st

from customer_support_agent.core.sanitizer import sanitize_obj_for_display
from customer_support_agent.demo.learning_scenario import (
    DEMO_CUSTOMER,
    DemoLearningController,
    DemoState,
)

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


st.set_page_config(page_title="Support Copilot", layout="wide")
st.title("Support Copilot Dashboard")


@st.cache_data(ttl=10)
def fetch_tickets() -> list[dict[str, Any]]:
    response = requests.get(f"{API_BASE_URL}/api/tickets", timeout=20)
    response.raise_for_status()
    return response.json()


def fetch_draft(ticket_id: int) -> dict[str, Any] | None:
    response = requests.get(f"{API_BASE_URL}/api/drafts/{ticket_id}", timeout=20)
    if response.status_code == 404:
        return None
    response.raise_for_status()
    return response.json()


def _extract_api_error(response: requests.Response) -> str:
    try:
        payload = response.json()
    except ValueError:
        return response.text or response.reason or "Unknown API error"

    detail = payload.get("detail")
    if isinstance(detail, list):
        parts = []
        for item in detail:
            if isinstance(item, dict):
                loc = ".".join(str(p) for p in item.get("loc", []))
                msg = item.get("msg", "validation error")
                parts.append(f"{loc}: {msg}" if loc else msg)
            else:
                parts.append(str(item))
        return "; ".join(parts)
    if detail:
        return str(detail)
    return str(payload)


def create_ticket(payload: dict[str, Any]) -> dict[str, Any]:
    response = requests.post(f"{API_BASE_URL}/api/tickets", json=payload, timeout=20)
    if response.status_code >= 400:
        raise RuntimeError(_extract_api_error(response))
    fetch_tickets.clear()
    return response.json()


def trigger_draft(ticket_id: int) -> dict[str, Any]:
    response = requests.post(
        f"{API_BASE_URL}/api/tickets/{ticket_id}/generate-draft",
        timeout=60,
    )
    if response.status_code >= 400:
        raise RuntimeError(_extract_api_error(response))
    return response.json()["draft"]


def update_draft(
    draft_id: int,
    content: str,
    status: str,
    rejection_reason: str | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {"content": content, "status": status}
    if rejection_reason:
        payload["rejection_reason"] = rejection_reason
    response = requests.patch(
        f"{API_BASE_URL}/api/drafts/{draft_id}",
        json=payload,
        timeout=20,
    )
    if response.status_code >= 400:
        raise RuntimeError(_extract_api_error(response))
    fetch_tickets.clear()
    return response.json()


def ingest_knowledge(clear_existing: bool) -> dict[str, Any]:
    response = requests.post(
        f"{API_BASE_URL}/api/knowledge/ingest",
        json={"clear_existing": clear_existing},
        timeout=60,
    )
    if response.status_code >= 400:
        raise RuntimeError(_extract_api_error(response))
    return response.json()


def search_memory(customer_id: int, query: str, limit: int = 8) -> list[dict[str, Any]]:
    response = requests.get(
        f"{API_BASE_URL}/api/customers/{customer_id}/memory-search",
        params={"query": query, "limit": limit},
        timeout=20,
    )
    if response.status_code >= 400:
        raise RuntimeError(_extract_api_error(response))
    payload = response.json()
    return payload.get("results", [])


def fetch_customer_timeline(customer_id: int) -> list[dict[str, Any]]:
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/customers/{customer_id}/timeline",
            timeout=10,
        )
        if response.status_code == 200:
            return response.json().get("timeline", [])
    except Exception:
        pass
    return []


def _clean_evidence_text(text: str) -> str:
    """Clean internal tag markers for human-readable judge UI display."""
    if not text:
        return ""
    cleaned = text.strip()
    prefixes = [
        "[SUCCESS - PROVEN FIX]",
        "[FAILED - DO NOT REPEAT]",
        "[SUCCESS]",
        "[FAILURE]",
        "[PREFERENCE]",
        "[PATTERN]",
        "[ATTEMPT]",
    ]
    for p in prefixes:
        if cleaned.startswith(p):
            cleaned = cleaned[len(p):].strip()
    return cleaned


_sanitize_obj_for_display = sanitize_obj_for_display


def render_memory_sources(context: dict[str, Any] | None) -> None:
    """Render visually distinct cards for the three memory sources with authority levels."""
    signals = (context or {}).get("signals") or {}
    mem0_count = signals.get("memory_hit_count", 0)
    rag_count = signals.get("knowledge_hit_count", 0)
    hindsight_count = signals.get("hindsight_hit_count", 0)

    h_status = (context or {}).get("hindsight_status") or signals.get("hindsight_status", "UNAVAILABLE")
    m_status = (context or {}).get("mem0_status") or signals.get("mem0_status", "LIVE_SUCCESS")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("**👤 Mem0**")
        st.caption("Customer facts & profile")
        st.caption("⚖️ *Authority: Authoritative Facts*")
        st.metric("Customer Facts", mem0_count)
        if m_status == "LIVE_SUCCESS":
            st.caption("🟢 Factual profile online")
        elif m_status == "DEMO_MODE":
            st.caption("🧪 Deterministic demo facts (fixture)")
        else:
            st.caption(f"⚠️ {m_status}")

    with col2:
        st.markdown("**📚 ChromaDB (RAG)**")
        st.caption("Company knowledge & technical docs")
        st.caption("⚖️ *Authority: Reference Documentation*")
        st.metric("KB Chunks", rag_count)
        sources = signals.get("knowledge_sources") or []
        if sources:
            st.caption(f"🟢 Sources: {', '.join(sources)}")
        else:
            st.caption("ℹ️ No specific KB hits")

    with col3:
        st.markdown("**🧠 Hindsight**")
        st.caption("Past outcomes & experience")
        st.caption("⚖️ *Authority: Advisory Experience*")
        st.metric("Experiences", hindsight_count)
        if h_status == "LIVE_SUCCESS":
            st.caption("🟢 Experiential recall active")
        elif h_status == "DEMO_MODE":
            st.caption("🧪 Deterministic demo memory (fixture)")
        elif h_status == "PROVIDER_QUOTA_ERROR":
            st.caption("⚠️ Provider quota exhausted — continuing with Mem0 + RAG")
        elif h_status == "DISABLED":
            st.caption("ℹ️ Disabled by config")
        else:
            st.caption("⚠️ Unavailable — continuing with Mem0 + RAG")


def render_memory_trace(ticket: dict[str, Any], context: dict[str, Any] | None) -> None:
    """Render a compact timeline of the decision pipeline for the current ticket."""
    st.markdown("##### ⏱️ Current-Ticket Memory Trace")
    signals = (context or {}).get("signals") or {}
    h_status = (context or {}).get("hindsight_status") or signals.get("hindsight_status", "UNAVAILABLE")
    injected = (context or {}).get("hindsight_context_injected", False)

    mem0_count = signals.get("memory_hit_count", 0)
    rag_count = signals.get("knowledge_hit_count", 0)
    hindsight_count = signals.get("hindsight_hit_count", 0)

    stage1 = f"**1. Current Issue:** {ticket.get('subject', 'Issue')} ({ticket.get('priority', 'medium')})"
    stage2 = f"**2. Mem0 Recall:** {mem0_count} profile fact(s)" if mem0_count > 0 else "**2. Mem0 Recall:** 0 profile facts"
    stage3 = f"**3. RAG Recall:** {rag_count} doc chunk(s)" if rag_count > 0 else "**3. RAG Recall:** 0 KB matches"

    if h_status == "DEMO_MODE":
        stage4 = f"**4. Demo Recall:** {hindsight_count} deterministic experience(s) recalled"
    elif h_status == "LIVE_SUCCESS":
        if hindsight_count > 0:
            stage4 = f"**4. Hindsight Recall:** {hindsight_count} experience(s) recalled"
        else:
            stage4 = "**4. Hindsight Recall:** 0 past experiences (novel issue pattern)"
    elif h_status == "PROVIDER_QUOTA_ERROR":
        stage4 = "**4. Hindsight Recall:** ⚠️ *Hindsight provider quota exhausted — continuing with Mem0 + RAG*"
    elif h_status == "CONFIGURATION_ERROR":
        stage4 = "**4. Hindsight Recall:** ⚠️ *Hindsight configuration error — continuing with Mem0 + RAG*"
    elif h_status == "DISABLED":
        stage4 = "**4. Hindsight Recall:** ℹ️ *Hindsight disabled by config — continuing with Mem0 + RAG*"
    else:
        stage4 = "**4. Hindsight Recall:** ⚠️ *Hindsight unavailable — continuing with Mem0 + RAG*"

    if injected:
        stage5 = "**5. AI Draft:** ✨ *Hindsight-informed draft generated*"
    else:
        stage5 = "**5. AI Draft:** 🤖 *Standard draft generated (Mem0 + RAG)*"

    trace_line = f"{stage1}  \n➔ {stage2}  \n➔ {stage3}  \n➔ {stage4}  \n➔ {stage5}"
    st.info(trace_line)


def render_memory_intelligence_panel(context: dict[str, Any] | None) -> None:
    """Render compact cards/badges for SUCCESS, FAILURE, PREFERENCE, and PATTERN."""
    st.markdown("#### 🧠 MEOW Memory Intelligence")
    if not context:
        st.info("Draft context not available yet. Generate a draft to inspect Memory Intelligence.")
        return

    hindsight_hits = context.get("hindsight_hits") or []
    h_status = context.get("hindsight_status") or "UNAVAILABLE"
    is_demo = h_status == "DEMO_MODE"

    if h_status == "PROVIDER_QUOTA_ERROR":
        st.warning("⚠️ **Hindsight provider quota exhausted — continuing with Mem0 + RAG**")
        return
    elif h_status not in ("LIVE_SUCCESS", "DEMO_MODE") and not hindsight_hits:
        st.warning("⚠️ **Hindsight unavailable — continuing with Mem0 + RAG**")
        return

    if not hindsight_hits:
        st.caption("ℹ️ No historical Hindsight experience recalled for this ticket. Copilot operating on factual profile & documentation.")
        return

    success_items = [h for h in hindsight_hits if h.get("category") == "SUCCESS"]
    failure_items = [h for h in hindsight_hits if h.get("category") == "FAILURE"]
    preference_items = [h for h in hindsight_hits if h.get("category") == "PREFERENCE"]
    pattern_items = [h for h in hindsight_hits if h.get("category") == "PATTERN"]
    other_items = [h for h in hindsight_hits if h.get("category") not in ("SUCCESS", "FAILURE", "PREFERENCE", "PATTERN")]

    col_a, col_b = st.columns(2)
    with col_a:
        if success_items:
            st.markdown("##### 🟢 Previously successful experience (SUCCESS)")
            for item in success_items[:3]:
                score_str = ""
                if item.get("score") is not None:
                    pct = int(item["score"] * 100)
                    score_str = f" • *Deterministic demo score: {pct}%*" if is_demo else f" • *Provider relevance: {pct}%*"
                source_tag = "Demo Experience" if is_demo else "Hindsight"
                clean_text = _clean_evidence_text(item.get("text", ""))
                st.success(f"**Previously successful experience** `[{source_tag}{score_str}]`\n\n{clean_text}")

        if failure_items:
            st.markdown("##### 🔴 Previously unsuccessful approach (FAILURE)")
            for item in failure_items[:3]:
                score_str = ""
                if item.get("score") is not None:
                    pct = int(item["score"] * 100)
                    score_str = f" • *Deterministic demo score: {pct}%*" if is_demo else f" • *Provider relevance: {pct}%*"
                source_tag = "Demo Experience" if is_demo else "Hindsight"
                clean_text = _clean_evidence_text(item.get("text", ""))
                st.error(f"**Previously unsuccessful approach** `[{source_tag}{score_str}]`\n\n{clean_text}")

    with col_b:
        if preference_items:
            st.markdown("##### 🟣 Recorded customer preference (PREFERENCE)")
            for item in preference_items[:3]:
                source_tag = "Demo Experience" if is_demo else "Hindsight"
                clean_text = _clean_evidence_text(item.get("text", ""))
                st.info(f"**Recorded preference** `[{source_tag}]`\n\n{clean_text}")

        if pattern_items:
            st.markdown("##### 🔵 Historical recurring pattern (PATTERN)")
            for item in pattern_items[:3]:
                source_tag = "Demo Experience" if is_demo else "Hindsight"
                clean_text = _clean_evidence_text(item.get("text", ""))
                st.info(f"**Historical pattern** `[{source_tag}]`\n\n{clean_text}")

        if other_items and not (preference_items or pattern_items):
            st.markdown("##### ⚪ Historical support experience")
            for item in other_items[:3]:
                source_tag = "Demo Experience" if is_demo else "Hindsight"
                clean_text = _clean_evidence_text(item.get("text", ""))
                st.caption(f"• `[{source_tag}]` {clean_text}")


def render_why_meow(context: dict[str, Any] | None) -> None:
    """Render an expandable explanation of why MEOW formulated this draft."""
    with st.expander("💡 Why did MEOW recommend this?", expanded=False):
        hindsight_hits = (context or {}).get("hindsight_hits") or []
        if hindsight_hits:
            st.markdown("**MEOW recalled historical support experience:**")
            has_success = any(h.get("category") == "SUCCESS" for h in hindsight_hits)
            has_failure = any(h.get("category") == "FAILURE" for h in hindsight_hits)
            has_pref = any(h.get("category") == "PREFERENCE" for h in hindsight_hits)
            has_pattern = any(h.get("category") == "PATTERN" for h in hindsight_hits)

            if has_success:
                st.markdown("- **✓ Previously successful experience**: Recalled a historical resolution that previously resolved a similar issue for this customer.")
            if has_failure:
                st.markdown("- **✕ Previously unsuccessful approach**: Recalled an approach previously reported as unsuccessful or rejected, avoiding repeating it.")
            if has_pref:
                st.markdown("- **♥ Recorded preference**: Respected recorded customer operational and communication preferences.")
            if has_pattern:
                st.markdown("- **🔄 Historical recurring pattern**: Accounted for historical recurrence patterns on this customer account.")
        else:
            st.markdown("**MEOW synthesized this draft using standard knowledge retrieval:**")
            st.markdown("- **✓ Customer facts**: Authoritative account context from Mem0 profile.")
            st.markdown("- **✓ Technical documentation**: Verified knowledge base articles from ChromaDB.")


def render_customer_timeline(
    customer_id: int,
    context: dict[str, Any] | None,
    timeline_items: list[dict[str, Any]] | None = None,
) -> None:
    """Render a chronological memory view for the selected customer."""
    st.markdown("#### 📜 Customer Memory Timeline")
    if timeline_items is None:
        timeline_items = fetch_customer_timeline(customer_id)

    if not timeline_items and context:
        for h in context.get("hindsight_hits") or []:
            meta = h.get("metadata") or {}
            timeline_items.append({
                "source": "hindsight",
                "category": h.get("category", "OTHER"),
                "text": h.get("text", ""),
                "timestamp": meta.get("timestamp") or meta.get("created_at"),
            })
        for m in context.get("memory_hits") or []:
            meta = m.get("metadata") or {}
            timeline_items.append({
                "source": "mem0",
                "category": "FACT",
                "text": m.get("memory", ""),
                "timestamp": meta.get("created_at") or meta.get("timestamp"),
            })

    if not timeline_items:
        st.caption("ℹ️ No historical timeline records found for this customer yet.")
        return

    for item in timeline_items[:8]:
        cat = item.get("category", "OTHER")
        source = item.get("source", "memory")
        text = _clean_evidence_text(item.get("text", ""))
        ts = item.get("timestamp")
        date_str = str(ts)[:10] if ts else "Recent Record"

        if cat == "SUCCESS":
            icon = "🟢"
            badge = "PREVIOUS SUCCESS"
        elif cat == "FAILURE":
            icon = "🔴"
            badge = "PREVIOUS FAILURE"
        elif cat == "PREFERENCE":
            icon = "🟣"
            badge = "RECORDED PREFERENCE"
        elif cat == "PATTERN":
            icon = "🔵"
            badge = "HISTORICAL PATTERN"
        else:
            icon = "👤"
            badge = "CUSTOMER FACT" if source == "mem0" else "EXPERIENCE"

        st.markdown(f"**{date_str}** &nbsp; {icon} `{badge}` `[{source.upper()}]`")
        st.caption(text)


def render_technical_details(context: dict[str, Any] | None) -> None:
    """Keep deep developer and evaluation inspection data cleanly expandable."""
    if not context:
        return

    with st.expander("🛠️ Deep Technical Details & Tool Calls", expanded=False):
        tool_calls = context.get("tool_calls") or []
        memory_hits = context.get("memory_hits") or []
        hindsight_hits = context.get("hindsight_hits") or []
        knowledge_hits = context.get("knowledge_hits") or []
        mem_eval = context.get("memory_evaluation")
        errors = context.get("errors") or []

        if tool_calls:
            st.markdown("**Tool Calls**")
            rows = [
                {
                    "Tool": call.get("tool_name", "unknown"),
                    "Status": call.get("status", "unknown"),
                    "Summary": call.get("summary") or call.get("output_text", ""),
                }
                for call in tool_calls
            ]
            st.dataframe(rows, use_container_width=True, hide_index=True)

        if mem_eval:
            st.markdown("**Memory Overlap Analysis**")
            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric("Common Facts", len(mem_eval.get("common_facts", [])))
            with c2:
                st.metric("Mem0 Only", len(mem_eval.get("mem0_only_facts", [])))
            with c3:
                st.metric("Hindsight Only", len(mem_eval.get("hindsight_only_facts", [])))

        t1, t2, t3 = st.tabs(["Mem0 Hits", "Hindsight Hits", "KB Hits"])
        with t1:
            st.json(_sanitize_obj_for_display(memory_hits))
        with t2:
            st.json(_sanitize_obj_for_display(hindsight_hits))
        with t3:
            st.json(_sanitize_obj_for_display(knowledge_hits))

        if errors:
            st.markdown("**Context Warnings/Errors**")
            for err in errors:
                st.caption(f"• {_sanitize_obj_for_display(err)}")


def render_context(context: dict[str, Any] | None) -> None:
    """Backwards-compatible wrapper coordinating memory intelligence and technical details."""
    render_memory_sources(context)
    render_memory_intelligence_panel(context)
    render_why_meow(context)
    render_technical_details(context)


def render_learning_demo_ui() -> None:
    """Render the deterministic Phase 7/8 end-to-end Hindsight learning demonstration."""
    if "demo_controller" not in st.session_state:
        st.session_state.demo_controller = DemoLearningController()

    controller: DemoLearningController = st.session_state.demo_controller
    payload = controller.get_current_payload()

    st.markdown("## 🧪 DEMO MODE")
    st.markdown("**Using isolated deterministic demo memory — no production customer data.**")
    st.caption("Demonstrates MEOW's closed-loop experiential learning workflow on deterministic fixtures without affecting real customer records.")

    st.subheader(f"🎓 {payload['stage_label']}")

    c1, c2, c3 = st.columns([1, 1, 1])
    with c1:
        st.markdown("**Demo Customer**")
        st.write(f"**Name:** {payload['customer']['name']}")
        st.write(f"**Email:** `{payload['customer']['email']}`")
        st.write(f"**Company:** {payload['customer']['company']}")
    with c2:
        st.markdown("**Customer Preference Profile**")
        st.info(f"💡 {payload['customer']['preference']}")
    with c3:
        st.markdown("**Current Demo State**")
        st.code(payload["state"])

    # 6 Scenario Step Navigation Controls
    st.markdown("##### 🕹️ Scenario Step Navigation")
    b1, b2, b3, b4, b5, b6 = st.columns(6)
    with b1:
        if st.button("1. Ticket 1", use_container_width=True, disabled=(controller.state not in (DemoState.NEW_CUSTOMER, DemoState.FIRST_TICKET))):
            controller.advance_to_ticket_1()
            st.rerun()
    with b2:
        if st.button("2. Reject (Fail)", use_container_width=True, disabled=(controller.state != DemoState.FIRST_TICKET)):
            controller.reject_ticket_1()
            st.rerun()
    with b3:
        if st.button("3. Ticket 2", use_container_width=True, disabled=(controller.state != DemoState.REJECTED_FAILURE)):
            controller.advance_to_ticket_2()
            st.rerun()
    with b4:
        if st.button("4. Accept (Win)", use_container_width=True, disabled=(controller.state != DemoState.SECOND_TICKET)):
            controller.accept_ticket_2()
            st.rerun()
    with b5:
        if st.button("5. Ticket 3", use_container_width=True, disabled=(controller.state not in (DemoState.ACCEPTED_SUCCESS, DemoState.THIRD_TICKET, DemoState.LEARNED_STATE))):
            controller.advance_to_ticket_3()
            st.rerun()
    with b6:
        if st.button("🔄 RESET DEMO", use_container_width=True):
            controller.reset()
            st.rerun()

    # Welcome Card for Stage 0 (Clean Slate)
    if controller.state == DemoState.NEW_CUSTOMER:
        st.divider()
        st.info(
            "👋 **Welcome to the MEOW Learning Demonstration!**\n\n"
            "This interactive scenario proves MEOW's closed-loop experiential support memory:\n\n"
            "1. **Ticket #1 (Novel Issue):** Customer reports a 504 gateway timeout. With no prior history, the AI proposes clearing browser cache. The human agent rejects this because cache was already cleared.\n"
            "2. **Learning from Failure:** MEOW retains the failed approach in Hindsight as `[FAILURE] (Do not repeat)`.\n"
            "3. **Ticket #2 (Recurrence & Avoidance):** Customer reports the issue again. MEOW recalls the failure, avoids proposing cache clearing, and instead suggests increasing the client timeout to 90s. The human agent accepts.\n"
            "4. **Learning from Success:** MEOW retains the resolution in Hindsight as `[SUCCESS] (Proven fix)`.\n"
            "5. **Ticket #3 (Full Historical Recall):** When the issue recurs at month-end, MEOW recalls both the proven fix, the failed attempt, customer communication preferences, and recurrence patterns to generate an optimal response."
        )
        if st.button("🚀 Begin Demo: Load Ticket #1 (Novel Issue)", type="primary", use_container_width=True):
            controller.advance_to_ticket_1()
            st.rerun()

    # Prominent MEOW LEARNED box if available
    learned = payload.get("learned_card")
    if learned:
        st.divider()
        if learned["type"] == "FAILURE":
            st.error(
                f"### 🧠 MEOW LEARNED: UNSUCCESSFUL APPROACH RECORDED\n\n"
                f"• **Action Attempted:** `{learned['action']}`\n\n"
                f"• **Outcome Classification:** `FAILURE` (Previously unsuccessful approach)\n\n"
                f"• **Rejection Reason:** *\"{learned['reason']}\"*\n\n"
                f"• **System Impact:** {learned['note']}\n\n"
                f"• **Storage Bank:** Retained in `{payload['customer']['email']}` deterministic demo bank"
            )
        elif learned["type"] == "SUCCESS":
            st.success(
                f"### 🧠 MEOW LEARNED: SUCCESSFUL RESOLUTION RECORDED\n\n"
                f"• **Resolution Applied:** `{learned['action']}`\n\n"
                f"• **Outcome Classification:** `SUCCESS` (Previously successful experience)\n\n"
                f"• **Verification:** {learned['reason']}\n\n"
                f"• **System Impact:** {learned['note']}\n\n"
                f"• **Storage Bank:** Retained in `{payload['customer']['email']}` deterministic demo bank"
            )

    ticket = payload.get("ticket")
    draft = payload.get("draft")
    context = payload.get("context_used")

    if ticket:
        st.divider()
        st.markdown(f"#### 🎫 Ticket #{ticket['id']}: {ticket['subject']}")
        col_t1, col_t2 = st.columns([1, 2])
        with col_t1:
            st.write(f"**Priority:** `{ticket['priority'].upper()}`")
            st.write(f"**Status:** `{ticket['status']}`")
        with col_t2:
            st.write(f"**Description:** {ticket['description']}")

    if draft:
        # 1. Memory Sources Separation (Mem0, ChromaDB, Hindsight)
        render_memory_sources(context)

        # 2. Memory Trace
        render_memory_trace(ticket, context)

        # 3. Memory Intelligence Panel (SUCCESS / FAILURE / PREFERENCE / PATTERN)
        render_memory_intelligence_panel(context)

        # 4. "Why MEOW?"
        render_why_meow(context)

        st.divider()

        # 5. Current Support Draft
        st.markdown("#### 📝 Current Support Draft")
        st.text_area(
            "Draft Content generated by SupportCopilot:",
            value=draft["content"],
            height=160,
            key=f"demo_draft_view_{payload['state']}",
            disabled=True,
        )

        # Interactive Step Action
        if controller.state == DemoState.FIRST_TICKET:
            st.markdown("##### 👤 Human Agent Decision on Novel Draft")
            st.caption("The proposed solution (`Clear cache`) is unhelpful because the customer already tried it.")
            col_act1, col_act2 = st.columns([2, 1])
            with col_act1:
                rejection_reason = st.selectbox(
                    "Rejection Reason",
                    [
                        "Already tried clearing cache without effect",
                        "Incorrect solution for 504 timeout",
                        "Customer uses custom API pipeline",
                    ],
                    key="demo_rej_reason",
                )
            with col_act2:
                st.write("")
                st.write("")
                if st.button("❌ Discard Draft (Record Failure)", use_container_width=True):
                    controller.reject_ticket_1(rejection_reason)
                    st.rerun()

        elif controller.state == DemoState.REJECTED_FAILURE:
            st.caption("Draft was discarded and failure retained. Next, simulate customer returning with the same issue.")
            if st.button("⏩ Advance to Ticket 2 (See Failure Recalled & Avoided)", use_container_width=True):
                controller.advance_to_ticket_2()
                st.rerun()

        elif controller.state == DemoState.SECOND_TICKET:
            st.markdown("##### 👤 Human Agent Decision on Informed Draft")
            st.caption("Notice how MEOW explicitly recalled the failed cache attempt and recommended increasing timeout to 90s.")
            if st.button("✅ Accept Draft (Record Proven Fix in Hindsight)", use_container_width=True):
                controller.accept_ticket_2()
                st.rerun()

        elif controller.state == DemoState.ACCEPTED_SUCCESS:
            st.caption("Draft was accepted and proven fix retained. Next, simulate a third ticket to verify full historical recall.")
            if st.button("⏩ Advance to Ticket 3 (Full Historical Experience)", use_container_width=True):
                controller.advance_to_ticket_3()
                st.rerun()

        elif controller.state in (DemoState.THIRD_TICKET, DemoState.LEARNED_STATE):
            st.success("🎉 **Full Closed-Loop Learning Scenario Complete!** MEOW demonstrated memory retention, failure avoidance, preference adherence, and pattern recognition.")
            if st.button("🔄 Reset Demo Scenario", use_container_width=True):
                controller.reset()
                st.rerun()

        st.divider()

        # 6. Customer Timeline
        render_customer_timeline(payload["customer"]["id"], context, timeline_items=payload.get("timeline"))

        # 7. Technical Details
        render_technical_details(context)


with st.sidebar:
    app_mode = st.radio(
        "Application Mode",
        ["🎓 MEOW Learning Demo", "Live Production"],
        index=0,
        help="Switch between the deterministic learning scenario walkthrough and the live production support copilot.",
    )
    if app_mode == "Live Production":
        st.sidebar.success("🟢 **LIVE PRODUCTION**\n\nUsing real customer data and live memory providers.")
        st.divider()
        st.subheader("API Settings")
        st.code(API_BASE_URL)

        if st.button("Ingest Knowledge Base", use_container_width=True):
            try:
                result = ingest_knowledge(clear_existing=False)
                st.success(
                    f"Indexed {result['files_indexed']} files / {result['chunks_indexed']} chunks"
                )
            except Exception as exc:
                st.error(f"Knowledge ingest failed: {exc}")
    else:
        st.sidebar.info("🧪 **DEMO MODE**\n\nUsing isolated deterministic demo memory — no production customer data.")
        st.divider()
        st.caption("ℹ️ Demo Mode runs entirely self-contained with zero external API dependencies.")
        if st.button("🔄 Reset Demo Scenario", use_container_width=True):
            if "demo_controller" in st.session_state:
                st.session_state.demo_controller.reset()
                st.rerun()


def render_production_ui() -> None:
    st.markdown("## 🟢 LIVE PRODUCTION")
    st.markdown("**Using real customer data and live memory providers.**")
    st.caption("Interacting with live SQLite database, real Mem0 profiles, and production knowledge base.")
    st.divider()

    st.subheader("Create Ticket")
    with st.form("create_ticket_form"):
        col1, col2 = st.columns(2)
        with col1:
            customer_email = st.text_input("Customer Email", placeholder="alex@acme.io")
            customer_name = st.text_input("Customer Name", placeholder="Alex Rivera")
        with col2:
            customer_company = st.text_input("Company", placeholder="Acme Labs")
            priority = st.selectbox("Priority", ["low", "medium", "high", "urgent"], index=1)

        subject = st.text_input("Subject")
        description = st.text_area("Description", height=120)
        auto_generate = st.checkbox("Auto-generate draft", value=True)

        submitted = st.form_submit_button("Create Ticket")
        if submitted:
            if not customer_email or not subject or not description:
                st.warning("Email, subject, and description are required.")
            elif len(subject.strip()) < 3:
                st.warning("Subject must be at least 3 characters.")
            elif len(description.strip()) < 10:
                st.warning("Description must be at least 10 characters.")
            else:
                try:
                    created = create_ticket(
                        {
                            "customer_email": customer_email,
                            "customer_name": customer_name or None,
                            "customer_company": customer_company or None,
                            "subject": subject,
                            "description": description,
                            "priority": priority,
                            "auto_generate": auto_generate,
                        }
                    )
                    st.success(f"Ticket #{created['id']} created")
                except Exception as exc:
                    st.error(f"Ticket creation failed: {exc}")

    st.divider()
    st.subheader("Tickets")

    try:
        tickets = fetch_tickets()
    except requests.exceptions.ConnectionError:
        tickets = []
        st.warning(
            "⚠️ **Live Production API is offline** (cannot connect to http://localhost:8000).\n\n"
            "To use Live Production Mode:\n"
            "1. Start the API backend: `python main.py` (or `docker compose up -d`)\n"
            "2. For a standalone demonstration without backend dependencies, switch to **🎓 MEOW Learning Demo** in the sidebar."
        )
    except Exception as exc:
        tickets = []
        st.error(f"Could not load tickets: {exc}")

    if not tickets:
        st.info("No tickets yet. Create one above or run seed_data.py")
    else:
        labels = [
            f"#{t['id']} | {t['status']} | {t['customer_email']} | {t['subject']}"
            for t in tickets
        ]
        selected_label = st.selectbox("Select ticket", labels)
        selected_ticket = tickets[labels.index(selected_label)]

        c1, c2 = st.columns([1, 1])
        with c1:
            st.markdown("**Customer**")
            st.write(selected_ticket["customer_email"])
            st.write(selected_ticket.get("customer_name") or "-")
            st.write(selected_ticket.get("customer_company") or "-")

        with c2:
            st.markdown("**Ticket**")
            st.write(f"Priority: {selected_ticket['priority']}")
            st.write(f"Status: {selected_ticket['status']}")
            st.write(selected_ticket["description"])

        if st.button("Generate Draft", use_container_width=True):
            try:
                new_draft = trigger_draft(selected_ticket["id"])
                st.session_state[f"draft_{selected_ticket['id']}"] = new_draft
                st.success("Draft generated")
            except Exception as exc:
                st.error(f"Draft generation failed: {exc}")

        draft_data = st.session_state.get(f"draft_{selected_ticket['id']}") or fetch_draft(selected_ticket["id"])

        if draft_data:
            context = draft_data.get("context_used")

            # 1. Memory Sources Separation (Mem0, ChromaDB, Hindsight)
            render_memory_sources(context)

            # 2. Current-Ticket Memory Trace (Issue -> Mem0 -> RAG -> Hindsight -> Draft)
            render_memory_trace(selected_ticket, context)

            # 3. Memory Intelligence Panel (SUCCESS / FAILURE / PREFERENCE / PATTERN)
            render_memory_intelligence_panel(context)

            # 4. "Why MEOW?" Explainability
            render_why_meow(context)

            st.divider()

            # 5. Current Support Draft
            if draft_data.get("status") == "failed":
                st.warning(
                    "Latest draft attempt failed. Check API key configuration and retry generation."
                )

            st.markdown("#### 📝 Current Support Draft")
            edited_content = st.text_area(
                "Review and edit draft reply before sending to customer:",
                value=draft_data["content"],
                height=200,
                key=f"draft_content_{draft_data['id']}",
            )

            # Rejection / Discard feedback
            rejection_reason = st.selectbox(
                "Rejection / Discard Reason (optional)",
                options=[
                    "",
                    "Incorrect solution",
                    "Already tried",
                    "Not relevant",
                    "Customer-specific issue",
                    "Other",
                ],
                key=f"rejection_reason_{draft_data['id']}",
                help="If discarding, selecting a reason helps MEOW learn to avoid this approach in future tickets.",
            )
            custom_reason = ""
            if rejection_reason == "Other":
                custom_reason = st.text_input(
                    "Specify custom reason",
                    key=f"custom_reason_{draft_data['id']}",
                    placeholder="Why is this draft being discarded?",
                )

            effective_reason = (custom_reason.strip() or rejection_reason) if rejection_reason else None

            c3, c4 = st.columns(2)
            with c3:
                if st.button("Accept Draft", use_container_width=True):
                    try:
                        updated = update_draft(draft_data["id"], edited_content, "accepted")
                        st.session_state[f"draft_{selected_ticket['id']}"] = updated
                        fb = updated.get("learning_feedback") or {}
                        h_saved = fb.get("hindsight_saved", False)
                        h_err = fb.get("hindsight_error")

                        if h_saved:
                            st.success(
                                "✓ **MEOW learned: previously successful experience recorded**\n\n"
                                "• Outcome: `SUCCESS` (Previously successful experience)\n"
                                "• Retained into customer's Hindsight experiential memory\n"
                                "• Future tickets for this customer will recall this historical experience"
                            )
                        elif h_err and ("quota" in h_err.lower() or "429" in h_err or "500" in h_err):
                            st.warning(
                                "⚠️ **Draft accepted, but Hindsight provider quota exhausted**\n\n"
                                "• Factual profile updated in Mem0\n"
                                "• Experiential retention skipped due to upstream provider quota\n"
                                "• Continuing with Mem0 + RAG"
                            )
                        else:
                            st.info(
                                "✓ **Draft accepted & resolved**\n\n"
                                "• Factual profile updated in Mem0\n"
                                f"• Hindsight status: {h_err or 'Continuing with Mem0 + RAG'}"
                            )
                    except Exception as exc:
                        st.error(f"Failed to accept draft: {exc}")

            with c4:
                if st.button("Discard Draft", use_container_width=True):
                    try:
                        updated = update_draft(
                            draft_data["id"],
                            edited_content,
                            "discarded",
                            rejection_reason=effective_reason,
                        )
                        st.session_state[f"draft_{selected_ticket['id']}"] = updated
                        fb = updated.get("learning_feedback") or {}
                        h_saved = fb.get("hindsight_saved", False)
                        h_err = fb.get("hindsight_error")
                        reason_msg = f": *{effective_reason}*" if effective_reason else ""

                        if h_saved:
                            st.info(
                                f"✕ **MEOW learned: previously unsuccessful approach recorded**{reason_msg}\n\n"
                                f"• Outcome: `FAILURE` (Previously unsuccessful approach)\n"
                                f"• Recorded in Hindsight to avoid repeating in future drafts\n"
                                f"• Mem0 factual profile kept clean"
                            )
                        elif h_err and ("quota" in h_err.lower() or "429" in h_err or "500" in h_err):
                            st.warning(
                                f"⚠️ **Draft discarded{reason_msg}, but Hindsight provider quota exhausted**\n\n"
                                f"• Unsuccessful attempt could not be retained in Hindsight due to upstream provider quota\n"
                                f"• Mem0 factual profile kept clean"
                            )
                        else:
                            st.info(
                                f"✕ **Draft discarded{reason_msg}**\n\n"
                                f"• Mem0 factual profile kept clean\n"
                                f"• Hindsight retention: {h_err or 'offline'}"
                            )
                    except Exception as exc:
                        st.error(f"Failed to discard draft: {exc}")

            st.divider()

            # 6. Customer Memory Timeline
            render_customer_timeline(selected_ticket["customer_id"], context)

            # 7. Deep Technical Details
            render_technical_details(context)

        st.markdown("**Memory Probe**")
        probe_query = st.text_input(
            "Search customer memory by entities/issues",
            value=f"{selected_ticket['subject']} {selected_ticket['priority']}",
            key=f"memory_probe_{selected_ticket['id']}",
        )
        if st.button("Run Memory Probe", use_container_width=True):
            try:
                hits = search_memory(selected_ticket["customer_id"], probe_query)
                if not hits:
                    st.info("No memory hits for this query yet.")
                else:
                    st.success(f"Found {len(hits)} memory hit(s).")
                    for idx, hit in enumerate(hits, start=1):
                        with st.expander(f"Memory hit {idx}"):
                            st.write(hit.get("memory", ""))
                            metadata = hit.get("metadata") or {}
                            if metadata:
                                st.caption("Metadata")
                                st.json(metadata)
            except Exception as exc:
                st.error(f"Memory probe failed: {exc}")


if app_mode == "🎓 MEOW Learning Demo":
    render_learning_demo_ui()
else:
    render_production_ui()
