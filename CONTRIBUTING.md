# Contributing to MEOW

Thank you for your interest in contributing to **MEOW: Memory-Enhanced Operations & Workflow**!

This project adheres to a four-tier memory architecture (SQLite, Mem0, ChromaDB, Hindsight) and maintains strict isolation between demo scenarios and live production customer banks.

---

## 1. Development Environment Setup

### Prerequisites
- Python 3.11
- `uv` package manager (`curl -LsSf https://astral.sh/uv/install.sh | sh` or `winget install astral-sh.uv`)
- Git

### Installation
```bash
# Clone the repository
git clone https://github.com/s4meer-dev/meow-ms-.git
cd meow-ms-

# Synchronize dependencies with uv
uv sync --dev

# Activate virtual environment
source .venv/bin/activate  # On Linux/macOS
# or: .\.venv\Scripts\Activate.ps1  # On Windows
```

---

## 2. Running Local Services

### Start Full Application
```bash
# Run both FastAPI backend and Streamlit frontend concurrently:
python scripts/run_all.py
```

### Start Services Individually
```bash
# Backend (FastAPI on http://localhost:8000)
python main.py

# Frontend (Streamlit on http://localhost:8501)
streamlit run app.py
```

---

## 3. Testing & Verification

Always run the full test suite and demo lifecycle verification before opening a pull request:

```bash
# Run pytest test suite:
pytest tests/test_demo_observability.py tests/test_phase3_shadow.py tests/test_sanitizer.py tests/test_prompt_integrity.py -v

# Run end-to-end demo lifecycle verification:
python scripts/verify_demo.py

# Run interactive terminal demo in headless auto mode:
python scripts/demo_cli.py --auto
```

---

## 4. Coding Standards & Commit Style

- We follow **Conventional Commits**:
  - `feat(...)`: New feature or capability
  - `fix(...)`: Bug fix or patch
  - `docs(...)`: Documentation additions or revisions
  - `test(...)`: Adding or modifying tests
  - `chore(...)`: Tooling, dependencies, or configuration changes
- Format code with `ruff format` and lint with `ruff check`.
- Preserve existing comments and docstrings.
