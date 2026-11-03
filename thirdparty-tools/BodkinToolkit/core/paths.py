"""Path resolution.

Everything the toolkit reads or writes lives INSIDE the project (``/v3/``),
under ``world/``. The toolkit has no dependency on any folder outside ``/v3/``.
The only legitimately external artifact is the game's own ``data.unity3d``
install, which the user points at explicitly (``--bundle`` / ``BA_GAME_ROOT`` /
``game_root.txt``); a copy placed at ``v3/data.unity3d`` is the default.
"""
from __future__ import annotations
from pathlib import Path

_HERE = Path(__file__).resolve()
V3_ROOT = _HERE.parent.parent          # the /v3/ project root
PROJECT_ROOT = V3_ROOT                  # alias: the project IS the root

# All world / data folders live under v3/world/ (never outside /v3/).
WORLD_DIR = V3_ROOT / "world"
JSON_DIR = WORLD_DIR / "json"
YAML_DIR = WORLD_DIR / "yaml"
BACKUPS_DIR = WORLD_DIR / "backups"
RESEARCH_DIR = WORLD_DIR / "research"
WORK_DIR = WORLD_DIR / "_workdir"

# Config + default bundle copy live inside the project too.
GAME_ROOT_FILE = V3_ROOT / "game_root.txt"
DEFAULT_BUNDLE = V3_ROOT / "data.unity3d"


def tool_root(tool_name: str) -> Path:
    return V3_ROOT / tool_name
