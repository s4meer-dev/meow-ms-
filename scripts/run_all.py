"""MEOW: Unified Development & Demonstration Startup Runner.

Launches both the FastAPI backend and Streamlit dashboard concurrently,
verifies API health, and manages graceful termination.
"""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent


def is_port_in_use(port: int) -> bool:
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) == 0


def main():
    print("=" * 65)
    print("MEOW: Memory-Enhanced Operations & Workflow - System Startup")
    print("=" * 65)

    python_exe = sys.executable

    # 1. Start FastAPI backend
    fastapi_cmd = [python_exe, "main.py"]
    print(f"\n[1/3] Launching FastAPI backend on http://127.0.0.1:8000 ...")
    backend_proc = subprocess.Popen(
        fastapi_cmd,
        cwd=str(ROOT_DIR),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )

    # 2. Poll for backend health
    print("[2/3] Waiting for backend to become ready ...")
    max_wait = 15
    start_time = time.time()
    backend_ready = False

    while time.time() - start_time < max_wait:
        if backend_proc.poll() is not None:
            _, err = backend_proc.communicate()
            print(f"[ERROR] FastAPI failed to start: {err.decode(errors='replace')}")
            sys.exit(1)
        if is_port_in_use(8000):
            backend_ready = True
            break
        time.sleep(0.5)

    if backend_ready:
        print("      ✓ Backend is ONLINE at http://127.0.0.1:8000")
    else:
        print("      ! Backend port check timed out (proceeding anyway)")

    # 3. Start Streamlit dashboard
    streamlit_cmd = [
        python_exe,
        "-m",
        "streamlit",
        "run",
        "app.py",
        "--server.port=8501",
        "--server.headless=true",
    ]
    print(f"\n[3/3] Launching Streamlit dashboard on http://127.0.0.1:8501 ...")
    frontend_proc = subprocess.Popen(
        streamlit_cmd,
        cwd=str(ROOT_DIR),
    )

    print("\n" + "=" * 65)
    print("MEOW IS RUNNING:")
    print("  • Frontend Dashboard: http://localhost:8501")
    print("  • Backend API Docs:   http://localhost:8000/docs")
    print("  • Health Diagnostic:  http://localhost:8000/api/health")
    print("Press Ctrl+C to stop all services.")
    print("=" * 65 + "\n")

    def shutdown(signum=None, frame=None):
        print("\nStopping MEOW services ...")
        for proc, name in [(frontend_proc, "Streamlit"), (backend_proc, "FastAPI")]:
            try:
                proc.terminate()
                proc.wait(timeout=3)
            except Exception:
                proc.kill()
            print(f"  ✓ {name} stopped")
        print("All MEOW services shut down cleanly.")
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, shutdown)

    try:
        frontend_proc.wait()
    except KeyboardInterrupt:
        shutdown()


if __name__ == "__main__":
    main()
