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

# Placeholder for workspace layout
st.info("MEOW Connected Observability Workspace Initializing...")
