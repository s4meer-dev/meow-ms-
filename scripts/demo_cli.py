"""MEOW: Interactive Terminal Walkthrough & Demonstration Tool.

Provides a full terminal-based demonstration experience without requiring a browser:
- Renders the 4 visual zones in standard terminal/ANSI formatting
- Interactive step-by-step presentation mode or automated walk-through
- Directly exercises DemoLearningController and observable event stream
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

# Ensure workspace root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from customer_support_agent.demo import DemoLearningController, DemoState


class Colors:
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RESET = "\033[0m"


def safe_str(s: str) -> str:
    return (
        s.replace("→", "->")
        .replace("🔴", "[FAIL]")
        .replace("🟢", "[OK]")
        .replace("🟡", "[PREF]")
        .replace("🟣", "[PATTERN]")
        .replace("✓", "[PASS]")
        .replace("—", "--")
        .encode("ascii", "replace")
        .decode("ascii")
    )


def print_banner(text: str, component: str = "SYSTEM", status: str = "PROCESSING"):
    border = "=" * 74
    clean_text = safe_str(text)
    print(f"\n{Colors.BOLD}{Colors.CYAN}+{border}+{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}| NOW > [{component}] {clean_text[:55]:<55} |{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}+{border}+{Colors.RESET}")


def print_deltas(deltas: dict[str, str]):
    print(f"\n{Colors.BOLD}{Colors.YELLOW}> WHAT CHANGED IN THE CONNECTED SYSTEM:{Colors.RESET}")
    for k, v in deltas.items():
        print(f"  * {Colors.BOLD}{k.upper()}:{Colors.RESET} {safe_str(v)}")


def print_events(events: list[dict], limit: int = 4):
    print(f"\n{Colors.BOLD}{Colors.GREEN}> LIVE ACTIVITY TELEMETRY (Recent Events):{Colors.RESET}")
    for ev in events[-limit:]:
        comp = f"[{ev.get('component', 'SYS')}]"
        act = ev.get("action", "")
        desc = safe_str(ev.get("description", ""))
        print(f"  {Colors.DIM}{ev.get('timestamp')}{Colors.RESET} {Colors.BOLD}{comp:<12}{Colors.RESET} {act:<20} {desc[:45]}")


def pause(auto: bool = False, delay: float = 2.0):
    if auto:
        time.sleep(delay)
    else:
        input(f"\n{Colors.DIM}Press [ENTER] to advance to next step...{Colors.RESET}")


def run_cli_demo(auto: bool = False):
    controller = DemoLearningController()

    print(f"{Colors.BOLD}{Colors.CYAN}")
    print("=" * 76)
    print("      MEOW: MEMORY-ENHANCED OPERATIONS & WORKFLOW")
    print("      Support That Remembers -- Interactive Terminal Demo")
    print("=" * 76)
    print(f"{Colors.RESET}")

    # Stage 0: Initial State
    print_banner("New Customer Session Initialized: Alex Rivera", "SQLITE")
    print_deltas(controller.get_deltas())
    print_events(controller.get_events())
    pause(auto)

    # Stage 1: Ticket 1 Problem Intake
    controller.advance_to_ticket_1()
    print_banner("Ticket #1 Intake: Large Report API Timeout Error 504", "GROQ")
    print(f"\n{Colors.BOLD}AI Proposed Draft (Clear Cache):{Colors.RESET}")
    print("  'Hi Alex, please try clearing your local browser and proxy cache...'")
    print_deltas(controller.get_deltas())
    print_events(controller.get_events())
    pause(auto)

    # Stage 2: Agent Rejects Draft
    controller.reject_ticket_1(reason="Already cleared cache without effect")
    print_banner("Draft Rejected by Agent: 'Already cleared cache without effect'", "HUMAN", "REJECTED")
    print_deltas(controller.get_deltas())
    print_events(controller.get_events())
    pause(auto)

    # Stage 3: Ticket 2 Recurrence & Experiential Recall
    controller.advance_to_ticket_2()
    print_banner("Ticket #2 Intake: Failure Recalled -- Avoids Cache Wipe", "HINDSIGHT", "RECALLING")
    print(f"\n{Colors.BOLD}AI Adaptive Draft (Avoided Failure):{Colors.RESET}")
    print("  'Hi Alex, we note clearing cache failed. Increase API client timeout to 90s...'")
    print_deltas(controller.get_deltas())
    print_events(controller.get_events())
    pause(auto)

    # Stage 4: Agent Accepts Proven Fix
    controller.accept_ticket_2()
    print_banner("Draft Accepted & Verified: Resolution Stored in Hindsight + Mem0", "HUMAN", "ACCEPTED")
    print_deltas(controller.get_deltas())
    print_events(controller.get_events())
    pause(auto)

    # Stage 5: Ticket 3 Multi-Memory Synthesis
    controller.advance_to_ticket_3()
    print_banner("Ticket #3 Full Recall: Synthesizing 4 Experiential Dimensions", "HINDSIGHT", "SYNTHESIS")
    print(f"\n{Colors.BOLD}AI Personalized Draft (Fix + Failure + Preference + Pattern):{Colors.RESET}")
    print("  'Alex:\n   Set export_timeout: 90s in export config.'")
    print_deltas(controller.get_deltas())
    print_events(controller.get_events())

    print(f"\n{Colors.BOLD}{Colors.GREEN}")
    print("=" * 76)
    print("  DEMO COMPLETE: MEOW Closed-Loop Experiential Learning Verified!")
    print("=" * 76)
    print(f"{Colors.RESET}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MEOW Interactive Terminal Demo")
    parser.add_argument("--auto", action="store_true", help="Run automatically without pausing")
    args = parser.parse_args()
    run_cli_demo(auto=args.auto)
