import sys
from pathlib import Path

# Ensure project root is on sys.path for test discovery and execution
project_root = Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
