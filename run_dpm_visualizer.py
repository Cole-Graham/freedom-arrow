"""Launch the Broken Arrow DPM visualizer from the repository root."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "dev-tools"))

from dpm_visualizer.main import main

if __name__ == "__main__":
    main()
