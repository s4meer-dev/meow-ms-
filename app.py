"""
MEOW: Memory-Enhanced Operations & Workflow
"Support that remembers."

Connected Observable System Experience — Real Activity, Deltas & State Visibility
"""

from __future__ import annotations

import os
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

# ---------------------------------------------------------------------------
# Streamlit Page Config & Minimal Clean Design
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="MEOW — Support That Remembers",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    /* ==========================================================================
       MEOW Connected Design System: Modern AI Observability Architecture
       Linear/Apple-level clarity, deep slate theme, restrained colors
       ========================================================================== */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

    html, body, [class*="css"], .stApp {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }

    /* Container Spacing */
    .main .block-container {
        padding-top: 1.0rem;
        padding-bottom: 2.0rem;
        max-width: 1140px;
    }

    /* Top Brand Navigation */
    .meow-brand-title {
        font-size: 1.85rem;
        font-weight: 800;
        letter-spacing: -0.04em;
        line-height: 1.1;
        color: #ffffff;
    }
    .meow-brand-tagline {
        font-size: 0.92rem;
        color: #94a3b8;
        font-style: italic;
        margin-top: 2px;
    }
    .meow-badge-demo {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: rgba(16, 185, 129, 0.12);
        color: #34d399;
        border: 1px solid rgba(16, 185, 129, 0.3);
        padding: 4px 11px;
        border-radius: 9999px;
        font-weight: 700;
        font-size: 0.76rem;
        letter-spacing: 0.04em;
        text-transform: uppercase;
    }
    .meow-badge-live {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: rgba(239, 68, 68, 0.12);
        color: #f87171;
        border: 1px solid rgba(239, 68, 68, 0.3);
        padding: 4px 11px;
        border-radius: 9999px;
        font-weight: 700;
        font-size: 0.76rem;
        letter-spacing: 0.04em;
        text-transform: uppercase;
    }

    /* Persistent "NOW" What Is Happening Banner */
    .meow-now-bar {
        display: flex;
        align-items: center;
        gap: 12px;
        background: #111827;
        border: 1px solid rgba(255, 255, 255, 0.09);
        border-radius: 10px;
        padding: 10px 16px;
        margin-bottom: 14px;
        font-size: 0.88rem;
    }
    .meow-now-tag {
        background: #2563eb;
        color: #ffffff;
        font-weight: 800;
        font-size: 0.72rem;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        padding: 3px 8px;
        border-radius: 6px;
    }
    .meow-now-desc {
        color: #e2e8f0;
        font-weight: 500;
        line-height: 1.4;
    }

    /* Compact 6-Step Story Progress Tracker */
    .meow-stepper {
        display: flex;
        align-items: center;
        justify-content: space-between;
        background: #0d131f;
        border: 1px solid rgba(255, 255, 255, 0.07);
        border-radius: 10px;
        padding: 8px 14px;
        margin-top: 14px;
        margin-bottom: 14px;
    }
    .meow-step-item {
        font-size: 0.8rem;
        font-weight: 500;
        color: #64748b;
        padding: 4px 10px;
        border-radius: 6px;
        transition: all 0.15s ease-in-out;
    }
    .meow-step-item.active {
        color: #38bdf8;
        background: rgba(56, 189, 248, 0.12);
        font-weight: 700;
        border: 1px solid rgba(56, 189, 248, 0.3);
    }
    .meow-step-arrow {
        color: #334155;
        font-size: 0.75rem;
    }

    /* Base Story Card */
    .meow-card {
        background: #111827;
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 16px 20px;
        margin-bottom: 14px;
    }
    .meow-card-header {
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #38bdf8;
        margin-bottom: 6px;
    }
    .meow-card-title {
        font-size: 1.22rem;
        font-weight: 700;
        color: #ffffff;
        margin-bottom: 6px;
        letter-spacing: -0.02em;
    }

    /* Live Activity Stream Styling */
    .meow-activity-panel {
        background: #0d131f;
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 10px;
        padding: 12px 14px;
        margin-bottom: 12px;
    }
    .meow-activity-title {
        font-size: 0.75rem;
        font-weight: 800;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #94a3b8;
        margin-bottom: 10px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .meow-event-item {
        display: flex;
        align-items: flex-start;
        gap: 8px;
        padding: 6px 0;
        border-bottom: 1px solid rgba(255, 255, 255, 0.04);
        font-size: 0.8rem;
    }
    .meow-event-item:last-child {
        border-bottom: none;
    }
    .meow-event-time {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.72rem;
        color: #64748b;
        white-space: nowrap;
        margin-top: 1px;
    }
    .meow-comp-badge {
        font-size: 0.68rem;
        font-weight: 700;
        text-transform: uppercase;
        padding: 2px 6px;
        border-radius: 4px;
        white-space: nowrap;
    }
    .badge-sqlite { background: rgba(148, 163, 184, 0.15); color: #cbd5e1; border: 1px solid rgba(148, 163, 184, 0.3); }
    .badge-mem0 { background: rgba(45, 212, 191, 0.15); color: #2dd4bf; border: 1px solid rgba(45, 212, 191, 0.3); }
    .badge-rag { background: rgba(56, 189, 248, 0.15); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.3); }
    .badge-hindsight { background: rgba(192, 132, 252, 0.15); color: #c084fc; border: 1px solid rgba(192, 132, 252, 0.3); }
    .badge-groq { background: rgba(251, 146, 60, 0.15); color: #fb923c; border: 1px solid rgba(251, 146, 60, 0.3); }
    .badge-system { background: rgba(59, 130, 246, 0.15); color: #60a5fa; border: 1px solid rgba(59, 130, 246, 0.3); }
    .meow-event-desc {
        color: #e2e8f0;
        line-height: 1.35;
        flex: 1;
    }

    /* What Changed (Delta) Panel */
    .meow-delta-panel {
        background: #0d131f;
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 10px;
        padding: 12px 14px;
        margin-bottom: 12px;
    }
    .meow-delta-title {
        font-size: 0.75rem;
        font-weight: 800;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #38bdf8;
        margin-bottom: 8px;
    }
    .meow-delta-row {
        margin-bottom: 8px;
        padding: 6px 8px;
        border-radius: 6px;
        background: rgba(15, 23, 42, 0.7);
        font-size: 0.8rem;
    }
    .meow-delta-label {
        font-size: 0.7rem;
        font-weight: 700;
        text-transform: uppercase;
        color: #94a3b8;
        margin-bottom: 2px;
    }
    .meow-delta-val {
        color: #ffffff;
        font-weight: 500;
    }

    /* Memory Cards */
    .mem-card-success {
        background: rgba(16, 185, 129, 0.08);
        border: 1px solid rgba(16, 185, 129, 0.28);
        border-radius: 8px;
        padding: 10px 14px;
        margin-bottom: 8px;
    }
    .mem-card-failure {
        background: rgba(239, 68, 68, 0.08);
        border: 1px solid rgba(239, 68, 68, 0.28);
        border-radius: 8px;
        padding: 10px 14px;
        margin-bottom: 8px;
    }
    .mem-card-preference {
        background: rgba(168, 85, 247, 0.08);
        border: 1px solid rgba(168, 85, 247, 0.28);
        border-radius: 8px;
        padding: 10px 14px;
        margin-bottom: 8px;
    }
    .mem-card-pattern {
        background: rgba(59, 130, 246, 0.08);
        border: 1px solid rgba(59, 130, 246, 0.28);
        border-radius: 8px;
        padding: 10px 14px;
        margin-bottom: 8px;
    }
    .mem-card-tag {
        font-size: 0.7rem;
        font-weight: 800;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        margin-bottom: 4px;
    }
    .mem-tag-success { color: #34d399; }
    .mem-tag-failure { color: #f87171; }
    .mem-tag-preference { color: #c084fc; }
    .mem-tag-pattern { color: #60a5fa; }
    .mem-card-content {
        font-size: 0.88rem;
        color: #f1f5f9;
        line-height: 1.4;
    }

    /* Buttons */
    .stButton button {
        border-radius: 8px !important;
        font-weight: 600 !important;
        font-size: 0.92rem !important;
        padding: 0.5rem 1.2rem !important;
        letter-spacing: -0.01em !important;
        transition: all 0.15s ease !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Backend API & Health Probing
# ---------------------------------------------------------------------------
def fetch_system_health() -> dict[str, Any]:
    health = {
        "fastapi": "Offline",
        "sqlite": "Offline",
        "mem0": "Offline",
        "chromadb": "Offline",
        "hindsight": "Offline",
        "llm": "Configured",
    }
    try:
        r = requests.get(f"{API_BASE_URL}/debug/memory-flow", timeout=2)
        if r.status_code == 200:
            flow = r.json()
            health["fastapi"] = "Connected"
            health["sqlite"] = "Connected" if flow.get("database_available") else "Offline"
            health["mem0"] = "Connected" if flow.get("mem0_available") else "Unavailable"
            health["chromadb"] = "Connected" if flow.get("chromadb_available") else "Unavailable"
            try:
                hr = requests.get(f"{API_BASE_URL}/health/hindsight", timeout=2)
                if hr.status_code == 200:
                    h_res = hr.json()
                    if h_res.get("available"):
                        health["hindsight"] = "Connected"
                    else:
                        err = str(h_res.get("error", "")).lower()
                        if "quota" in err or "429" in err:
                            health["hindsight"] = "Provider Quota Exhausted"
                        else:
                            health["hindsight"] = "Unavailable"
                else:
                    health["hindsight"] = "Unavailable"
            except Exception:
                health["hindsight"] = "Unavailable"
    except Exception:
        pass
    return health


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


def create_ticket(payload: dict[str, Any]) -> dict[str, Any]:
    response = requests.post(f"{API_BASE_URL}/api/tickets", json=payload, timeout=20)
    response.raise_for_status()
    fetch_tickets.clear()
    return response.json()


def trigger_draft(ticket_id: int) -> dict[str, Any]:
    response = requests.post(f"{API_BASE_URL}/api/tickets/{ticket_id}/generate-draft", timeout=60)
    response.raise_for_status()
    return response.json()["draft"]


def update_draft(draft_id: int, content: str, status: str, rejection_reason: str | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {"content": content, "status": status}
    if rejection_reason:
        payload["rejection_reason"] = rejection_reason
    response = requests.patch(f"{API_BASE_URL}/api/drafts/{draft_id}", json=payload, timeout=20)
    response.raise_for_status()
    fetch_tickets.clear()
    return response.json()


# ---------------------------------------------------------------------------
# Sidebar Mode Switcher
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### MEOW Control")
    app_mode = st.radio(
        "Mode:",
        ["🧪 DEMO MODE", "🔴 LIVE PRODUCTION"],
        index=0,
        help="Switch between the connected observable demo walkthrough and live connected production backend.",
    )
    st.divider()
    if app_mode == "🧪 DEMO MODE":
        st.caption("ℹ️ Demo mode runs with isolated demo customers while executing real state changes, live activity logging, and delta tracking.")
        if st.button("🔄 Reset Demo to Start", use_container_width=True):
            if "demo_controller" in st.session_state:
                st.session_state.demo_controller.reset()
            st.session_state.demo_step = "START"
            st.rerun()
    else:
        st.caption("ℹ️ Live Production connects to local SQLite, ChromaDB, Mem0, and live LLM/Hindsight services.")
        st.code(API_BASE_URL)


# ---------------------------------------------------------------------------
# Top Header Bar
# ---------------------------------------------------------------------------
nav_left, nav_right = st.columns([3, 1])
with nav_left:
    st.markdown(
        """
        <div>
            <div class="meow-brand-title">MEOW</div>
            <div class="meow-brand-tagline">Support that remembers.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with nav_right:
    st.write("")
    if app_mode == "🧪 DEMO MODE":
        st.markdown('<div style="text-align: right;"><span class="meow-badge-demo">DEMO MODE ●</span></div>', unsafe_allow_html=True)
    else:
        st.markdown('<div style="text-align: right;"><span class="meow-badge-live">LIVE PRODUCTION ●</span></div>', unsafe_allow_html=True)


# ===========================================================================
# DEMO MODE: Connected Observable System Walkthrough
# ===========================================================================
if app_mode == "🧪 DEMO MODE":
    if "demo_controller" not in st.session_state:
        st.session_state.demo_controller = DemoLearningController()
    if "demo_step" not in st.session_state:
        st.session_state.demo_step = "START"

    controller: DemoLearningController = st.session_state.demo_controller
    state = controller.state
    step = st.session_state.demo_step

    # Synchronize step if controller was reset or changed
    if state == DemoState.NEW_CUSTOMER and step != "START":
        st.session_state.demo_step = "START"
        step = "START"
    elif state == DemoState.FIRST_TICKET and step not in ("STEP_1_PROBLEM", "STEP_2_MEMORY", "STEP_3_RECOMMENDATION"):
        st.session_state.demo_step = "STEP_1_PROBLEM"
        step = "STEP_1_PROBLEM"
    elif state == DemoState.REJECTED_FAILURE and step != "STEP_4_FEEDBACK":
        st.session_state.demo_step = "STEP_4_FEEDBACK"
        step = "STEP_4_FEEDBACK"
    elif state == DemoState.SECOND_TICKET and step != "STEP_5_RETURNS":
        st.session_state.demo_step = "STEP_5_RETURNS"
        step = "STEP_5_RETURNS"
    elif state == DemoState.ACCEPTED_SUCCESS and step != "STEP_6_SUCCESS":
        st.session_state.demo_step = "STEP_6_SUCCESS"
        step = "STEP_6_SUCCESS"
    elif state in (DemoState.THIRD_TICKET, DemoState.LEARNED_STATE) and step != "STEP_7_FULL_RECALL":
        st.session_state.demo_step = "STEP_7_FULL_RECALL"
        step = "STEP_7_FULL_RECALL"

    payload = controller.get_current_payload()
    system_state = controller.get_system_state()
    deltas = controller.get_deltas()
    recent_events = controller.get_events(limit=8)

    # Multi-screen connected views
    tab_demo, tab_mem, tab_rag, tab_sys, tab_activity = st.tabs([
        "🎬 DEMO WORKSPACE",
        "🧠 MEMORY (Mem0 & Hindsight)",
        "📚 KNOWLEDGE (RAG)",
        "⚙ SYSTEM (SQLite & APIs)",
        "🕒 LIVE ACTIVITY LOG",
    ])


    # -----------------------------------------------------------------------
    # TAB 1: DEMO WORKSPACE (4 Visual Zones)
    # -----------------------------------------------------------------------
    with tab_demo:

        # ZONE 1: TOP (Now Banner & Stage Heading)
        now_messages = {
            "START": "Alex Rivera has submitted a novel support issue.",
            "STEP_1_PROBLEM": "Alex has reported a novel timeout error MEOW has never seen before.",
            "STEP_2_MEMORY": "MEOW is searching customer facts, company documentation, and historical experience.",
            "STEP_3_RECOMMENDATION": "MEOW generated an initial standard resolution based only on documentation.",
            "STEP_4_FEEDBACK": "Human agent rejected draft — MEOW is recording failure into Hindsight experience.",
            "STEP_5_RETURNS": "Alex returns with the same issue — MEOW recalls the failure and proposes a new fix.",
            "STEP_6_SUCCESS": "Human agent accepted draft — MEOW retains proven fix into Hindsight & Mem0.",
            "STEP_7_FULL_RECALL": "Alex returns for month-end export — MEOW recalls full history for optimal response.",
        }
        now_text = now_messages.get(step, "Active Demonstration")

        st.markdown(
            f"""
            <div class="meow-now-bar">
                <span class="meow-now-tag">NOW</span>
                <span class="meow-now-desc">{now_text}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # 4 VISUAL ZONES LAYOUT: Main Action (Left 3 cols), Live Activity & What Changed (Right 2 cols)
        col_main, col_side = st.columns([3, 2])

        with col_main:
            # ---------------------------------------------------------------
            # ZONE 2: CENTER ACTION (Current Primary Story Card)
            # ---------------------------------------------------------------
            if step == "START":
                st.markdown(
                    f"""
                    <div class="meow-card" style="text-align: center; padding: 28px 24px;">
                        <div style="font-size: 1.6rem; font-weight: 800; color: #ffffff; margin-bottom: 4px;">Welcome to MEOW</div>
                        <div style="font-size: 0.95rem; color: #38bdf8; font-style: italic; margin-bottom: 12px;">Support that remembers.</div>
                        <div style="font-size: 0.88rem; color: #cbd5e1; max-width: 500px; margin: 0 auto 20px auto; line-height: 1.5;">
                            An AI support agent that learns from every customer outcome.
                            Watch as MEOW queries Mem0, RAG, and Hindsight, absorbs human feedback, and prevents repeated mistakes.
                        </div>
                        <div style="background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 8px; padding: 12px 16px; max-width: 440px; margin: 0 auto 20px auto; text-align: left;">
                            <div style="font-size: 0.7rem; font-weight: 700; color: #38bdf8; text-transform: uppercase;">CUSTOMER PROFILE</div>
                            <div style="font-size: 1.05rem; font-weight: 700; color: #ffffff;">{DEMO_CUSTOMER['name']} <span style="font-size: 0.8rem; color: #94a3b8; font-weight: 500;">({DEMO_CUSTOMER['company']})</span></div>
                            <div style="font-size: 0.8rem; color: #94a3b8; margin-top: 2px;">Reported Problem: <strong>Large batch export timeout</strong></div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                if st.button("🚀 START DEMO →", type="primary", use_container_width=True):
                    controller.advance_to_ticket_1()
                    st.session_state.demo_step = "STEP_1_PROBLEM"
                    st.rerun()

            elif step == "STEP_1_PROBLEM":
                st.markdown(
                    f"""
                    <div class="meow-card">
                        <div class="meow-card-header">STEP 01 / NEW CUSTOMER</div>
                        <div class="meow-card-title">Alex has reported a problem MEOW has never seen before.</div>
                        <div style="display: grid; grid-template-columns: 1fr 2fr; gap: 14px; margin-top: 10px;">
                            <div>
                                <div style="font-size: 0.7rem; color: #94a3b8; font-weight: 700; text-transform: uppercase;">CUSTOMER</div>
                                <div style="font-size: 1.0rem; font-weight: 700; color: #ffffff;">{payload['customer']['name']}</div>
                                <div style="font-size: 0.8rem; color: #94a3b8;">{payload['customer']['company']}</div>
                            </div>
                            <div>
                                <div style="font-size: 0.7rem; color: #94a3b8; font-weight: 700; text-transform: uppercase;">ISSUE & DETAIL</div>
                                <div style="font-size: 1.0rem; font-weight: 700; color: #f87171;">🔴 API 504 Gateway Timeout</div>
                                <div style="font-size: 0.82rem; color: #cbd5e1; margin-top: 2px;">Large batch export is timing out after 60s.</div>
                            </div>
                        </div>
                        <div style="margin-top: 14px; padding-top: 10px; border-top: 1px solid rgba(255, 255, 255, 0.08); font-size: 0.8rem; color: #94a3b8;">
                            Past experience: <strong style="color: #ffffff;">0 matches</strong> &nbsp;•&nbsp; <em>Clean slate for this issue</em>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                if st.button("CHECK WHAT MEOW KNOWS (MEM0 + RAG + HINDSIGHT) →", type="primary", use_container_width=True):
                    st.session_state.demo_step = "STEP_2_MEMORY"
                    st.rerun()

            elif step == "STEP_2_MEMORY":
                st.markdown(
                    """
                    <div class="meow-card">
                        <div class="meow-card-header">STEP 02 / MEMORY CHECK</div>
                        <div class="meow-card-title">MEOW checks what it already knows.</div>
                        <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; margin-top: 10px;">
                            <div style="background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 8px; padding: 10px 12px;">
                                <div style="font-size: 0.7rem; font-weight: 700; color: #38bdf8; text-transform: uppercase;">CUSTOMER (Mem0)</div>
                                <div style="font-size: 0.82rem; color: #34d399; font-weight: 600;">🟢 1 fact found</div>
                                <div style="font-size: 0.74rem; color: #cbd5e1;">Enterprise custom export pipeline</div>
                            </div>
                            <div style="background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 8px; padding: 10px 12px;">
                                <div style="font-size: 0.7rem; font-weight: 700; color: #38bdf8; text-transform: uppercase;">COMPANY (RAG)</div>
                                <div style="font-size: 0.82rem; color: #34d399; font-weight: 600;">🟢 1 doc matched</div>
                                <div style="font-size: 0.74rem; color: #cbd5e1;">API timeout configuration guidelines</div>
                            </div>
                            <div style="background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 8px; padding: 10px 12px;">
                                <div style="font-size: 0.7rem; font-weight: 700; color: #38bdf8; text-transform: uppercase;">EXPERIENCE (Hindsight)</div>
                                <div style="font-size: 0.82rem; color: #94a3b8; font-weight: 600;">⚪ 0 experiences</div>
                                <div style="font-size: 0.74rem; color: #64748b;">No prior history for this problem</div>
                            </div>
                        </div>
                        <div style="margin-top: 14px; padding: 10px 12px; background: rgba(59, 130, 246, 0.06); border-radius: 8px; font-size: 0.82rem; color: #cbd5e1;">
                            💡 <strong>Summary:</strong> No previous experience found. This is a new problem for MEOW.
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                if st.button("GENERATE FIRST RESPONSE →", type="primary", use_container_width=True):
                    st.session_state.demo_step = "STEP_3_RECOMMENDATION"
                    st.rerun()

            elif step == "STEP_3_RECOMMENDATION":
                st.markdown(
                    """
                    <div class="meow-card">
                        <div class="meow-card-header">STEP 03 / AI RESPONSE</div>
                        <div class="meow-card-title">What is MEOW recommending?</div>
                        <div style="background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 8px; padding: 12px 16px; margin-bottom: 12px;">
                            <div style="font-size: 0.7rem; font-weight: 700; color: #38bdf8; text-transform: uppercase; margin-bottom: 4px;">PROPOSED DRAFT</div>
                            <div style="font-size: 0.9rem; color: #ffffff; line-height: 1.45;">
                                "Hi Alex,<br><br>
                                Thank you for reaching out. For large report export timeouts, please try <strong>clearing your local browser and proxy cache</strong>, then retry generating the ledger report.<br><br>
                                Let us know if the issue persists."
                            </div>
                        </div>
                        <div style="font-size: 0.78rem; color: #94a3b8;">
                            <strong>Why?</strong> Standard documentation troubleshooting for this type of timeout.
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                st.markdown('<div style="font-size: 0.74rem; font-weight: 700; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 4px;">HUMAN DECISION</div>', unsafe_allow_html=True)
                col_r1, col_r2 = st.columns([3, 2])
                with col_r1:
                    rejection_reason = st.selectbox(
                        "Rejection Reason:",
                        [
                            "Already tried clearing cache without effect",
                            "Incorrect solution for 504 timeout",
                            "Customer uses custom API pipeline",
                        ],
                        label_visibility="collapsed",
                    )
                with col_r2:
                    if st.button("❌ REJECT — TEACH MEOW", type="primary", use_container_width=True):
                        controller.reject_ticket_1(rejection_reason)
                        st.session_state.demo_step = "STEP_4_FEEDBACK"
                        st.rerun()

            elif step == "STEP_4_FEEDBACK":
                st.markdown(
                    f"""
                    <div class="meow-card">
                        <div class="meow-card-header">STEP 04 / HUMAN FEEDBACK</div>
                        <div class="meow-card-title">You rejected the response.</div>
                        <div style="font-size: 0.82rem; color: #94a3b8; margin-bottom: 12px;">
                            Reason provided: <em>"{controller.rejection_reason or 'Already tried clearing cache without effect'}"</em>
                        </div>
                        <div class="mem-card-failure">
                            <div class="mem-card-tag mem-tag-failure">🧠 MEOW LEARNED &nbsp;•&nbsp; 🔴 DO NOT REPEAT</div>
                            <div class="mem-card-content" style="font-size: 0.95rem; font-weight: 600;">
                                "Clearing the cache did not solve this customer's problem."
                            </div>
                            <div style="font-size: 0.74rem; color: #f87171; margin-top: 4px;">
                                Stored into Hindsight experience bank <code>customer_bank_alex_rivera</code>.
                            </div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                if st.button("CONTINUE TO TICKET 2 (SAME CUSTOMER RETURNS) →", type="primary", use_container_width=True):
                    controller.advance_to_ticket_2()
                    st.session_state.demo_step = "STEP_5_RETURNS"
                    st.rerun()

            elif step == "STEP_5_RETURNS":
                st.markdown(
                    """
                    <div class="meow-card">
                        <div class="meow-card-header">STEP 05 / CUSTOMER RETURNS</div>
                        <div class="meow-card-title">Alex has the same problem again.</div>
                        <div class="mem-card-failure" style="padding: 8px 12px; margin-bottom: 12px;">
                            <div class="mem-card-tag mem-tag-failure">🔴 RECALLED FAILED ATTEMPT — AVOIDED REPEATING</div>
                            <div style="font-size: 0.82rem; color: #ffffff;">Cache clearing failed: Already tried without effect</div>
                        </div>
                        <div style="background: rgba(15, 23, 42, 0.8); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 8px; padding: 12px 16px; margin-bottom: 12px;">
                            <div style="font-size: 0.7rem; font-weight: 700; color: #38bdf8; text-transform: uppercase; margin-bottom: 4px;">NEW PROPOSED RECOMMENDATION</div>
                            <div style="font-size: 0.9rem; color: #ffffff; line-height: 1.45;">
                                "Hi Alex,<br><br>
                                We note that clearing cache was previously unsuccessful for this issue.
                                For large batch exports, please <strong>increase your API client timeout from 30 to 90 seconds</strong> in your export configuration (<code>timeout: 90s</code>).<br><br>
                                This provides sufficient window for the ledger compilation worker to complete."
                            </div>
                        </div>
                        <div style="font-size: 0.78rem; color: #94a3b8;">
                            <strong>Why?</strong> ✓ Avoided failure (did not repeat cache clearing) &nbsp;•&nbsp; ✓ Raised client timeout to 90s.
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                st.markdown('<div style="font-size: 0.74rem; font-weight: 700; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 4px;">HUMAN DECISION</div>', unsafe_allow_html=True)
                if st.button("✅ ACCEPT — TEACH MEOW (This Fixed The Issue)", type="primary", use_container_width=True):
                    controller.accept_ticket_2()
                    st.session_state.demo_step = "STEP_6_SUCCESS"
                    st.rerun()

            elif step == "STEP_6_SUCCESS":
                st.markdown(
                    """
                    <div class="meow-card">
                        <div class="meow-card-header">STEP 06 / MEOW LEARNS</div>
                        <div class="meow-card-title">Resolution accepted — MEOW retains proven fix.</div>
                        <div class="mem-card-success">
                            <div class="mem-card-tag mem-tag-success">🧠 MEOW LEARNED &nbsp;•&nbsp; 🟢 PROVEN FIX</div>
                            <div class="mem-card-content" style="font-size: 0.95rem; font-weight: 600;">
                                "Increase API timeout from 30s → 90s."
                            </div>
                            <div style="font-size: 0.74rem; color: #34d399; margin-top: 4px;">
                                Stored into Hindsight experience bank & verified in Mem0 customer facts.
                            </div>
                        </div>
                        <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 8px; margin-top: 10px;">
                            <div style="background: rgba(15, 23, 42, 0.6); border-radius: 6px; padding: 6px 10px; font-size: 0.78rem;">
                                Outcome: <strong style="color: #34d399;">Accepted ✓</strong>
                            </div>
                            <div style="background: rgba(15, 23, 42, 0.6); border-radius: 6px; padding: 6px 10px; font-size: 0.78rem;">
                                Hindsight: <strong style="color: #38bdf8;">Retained ✓</strong>
                            </div>
                            <div style="background: rgba(15, 23, 42, 0.6); border-radius: 6px; padding: 6px 10px; font-size: 0.78rem;">
                                SQLite: <strong style="color: #34d399;">Resolved ✓</strong>
                            </div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                if st.button("SEE WHAT HAPPENS NEXT (FINAL PAYOFF) →", type="primary", use_container_width=True):
                    controller.advance_to_ticket_3()
                    st.session_state.demo_step = "STEP_7_FULL_RECALL"
                    st.rerun()

            elif step == "STEP_7_FULL_RECALL":
                st.markdown(
                    """
                    <div class="meow-card">
                        <div class="meow-card-header">STEP 07 / FULL RECALL</div>
                        <div class="meow-card-title">Alex returns again (End-of-Month Batch Export).</div>
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 12px;">
                            <div class="mem-card-success" style="margin: 0; padding: 8px 10px;">
                                <div class="mem-card-tag mem-tag-success">🟢 PROVEN FIX</div>
                                <div class="mem-card-content" style="font-size: 0.8rem;">Increase timeout 30s → 90s</div>
                            </div>
                            <div class="mem-card-failure" style="margin: 0; padding: 8px 10px;">
                                <div class="mem-card-tag mem-tag-failure">🔴 DO NOT REPEAT</div>
                                <div class="mem-card-content" style="font-size: 0.8rem;">Cache clearing failed without effect</div>
                            </div>
                            <div class="mem-card-preference" style="margin: 0; padding: 8px 10px;">
                                <div class="mem-card-tag mem-tag-preference">🟣 PREFERENCE</div>
                                <div class="mem-card-content" style="font-size: 0.8rem;">Concise technical instructions</div>
                            </div>
                            <div class="mem-card-pattern" style="margin: 0; padding: 8px 10px;">
                                <div class="mem-card-tag mem-tag-pattern">🔵 PATTERN</div>
                                <div class="mem-card-content" style="font-size: 0.8rem;">End-of-month batch export recurrence</div>
                            </div>
                        </div>
                        <div style="background: rgba(15, 23, 42, 0.85); border: 1px solid rgba(56, 189, 248, 0.25); border-radius: 8px; padding: 12px 16px; margin-bottom: 10px;">
                            <div style="font-family: 'JetBrains Mono', monospace; font-size: 0.88rem; color: #ffffff; line-height: 1.45;">
                                Alex:<br><br>
                                Set <code>export_timeout: 90s</code> in export config.<br><br>
                                <span style="color: #94a3b8; font-size: 0.78rem;">(Per account history: Cache clearing does not resolve this timeout; increasing client timeout to 90s is the verified fix for end-of-month batch runs).</span>
                            </div>
                        </div>
                        <div style="font-size: 0.78rem; color: #34d399;">
                            ✓ MEOW combined all 4 dimensions of history for the optimal answer.
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                if st.button("🔄 RESTART DEMO", type="primary", use_container_width=True):
                    controller.reset()
                    st.session_state.demo_step = "START"
                    st.rerun()

        with col_side:
            # ---------------------------------------------------------------
            # ZONE 3 & 4: WHAT CHANGED? & LIVE SYSTEM ACTIVITY (Secondary)
            # ---------------------------------------------------------------
            # WHAT CHANGED? PANEL (Phase 8)
            st.markdown(
                f"""
                <div class="meow-delta-panel">
                    <div class="meow-delta-title">⚡ WHAT CHANGED? (Data Deltas)</div>
                    <div class="meow-delta-row">
                        <div class="meow-delta-label">HINDSIGHT EXPERIENCE BANK</div>
                        <div class="meow-delta-val">{deltas.get('hindsight', 'Unchanged')}</div>
                    </div>
                    <div class="meow-delta-row">
                        <div class="meow-delta-label">MEM0 CUSTOMER FACTS</div>
                        <div class="meow-delta-val">{deltas.get('mem0', 'Unchanged')}</div>
                    </div>
                    <div class="meow-delta-row" style="margin-bottom:0;">
                        <div class="meow-delta-label">SQLITE REPOSITORY</div>
                        <div class="meow-delta-val">{deltas.get('sqlite', 'Unchanged')}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # LIVE SYSTEM ACTIVITY PANEL (Phase 7)
            events_html = ""
            for ev in recent_events:
                comp = ev["component"]
                badge_class = f"badge-{comp.lower()}"
                events_html += f"""
                <div class="meow-event-item">
                    <span class="meow-event-time">{ev['timestamp']}</span>
                    <span class="meow-comp-badge {badge_class}">{comp}</span>
                    <span class="meow-event-desc">{ev['description']}</span>
                </div>
                """

            st.markdown('<div class="meow-activity-panel"><div class="meow-card-header">Live System Activity</div><div style="font-size:0.85rem;color:#94a3b8;">Streaming real-time component telemetry...</div></div>', unsafe_allow_html=True)

    with tab_mem:
        st.info("Customer Memory Architecture (Mem0 + Hindsight)")
    with tab_rag:
        st.info("Company Knowledge Base (ChromaDB / RAG)")
    with tab_sys:
        st.info("System Architecture & SQLite Repository")
    with tab_activity:
        st.info("Full Chronological Event Stream")
