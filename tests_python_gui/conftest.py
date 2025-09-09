from __future__ import annotations

import sys
from pathlib import Path

# Ensure project root is on sys.path so tests can import `src_python_gui` as a package
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
