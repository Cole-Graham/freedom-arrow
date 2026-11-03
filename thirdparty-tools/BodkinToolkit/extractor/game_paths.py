"""game_paths.py — resolve the data.unity3d bundle path.

Generic directory roots (_workdir/, json/, repo root) come from
``core.paths`` — this module owns only the *game-specific* bundle-location
logic, which has no place in core.

Bundle resolution priority:
  1. Explicit --bundle CLI argument (handled by callers, not here)
  2. BA_GAME_ROOT environment variable
  3. game_root.txt file at the repo root
  4. Well-known Steam / default install locations
"""
from __future__ import annotations

import os
from pathlib import Path

from ..core import paths as _paths


# ── Default runtime directories (delegated to core) ───────────────────────────

def default_workdir() -> Path:
    """v3/world/_workdir/ — provided by core.paths."""
    return _paths.WORK_DIR


def default_json_dir() -> Path:
    """v3/world/json/ — provided by core.paths."""
    return _paths.JSON_DIR


# ── Bundle-path candidates (game-specific; not core's concern) ─────────────────

_DATA_RELATIVE = Path("BrokenArrow_Data") / "data.unity3d"

_FALLBACK_ROOTS = [
    # Windows — common Steam library locations
    Path("C:/Program Files (x86)/Steam/steamapps/common/Broken Arrow"),
    Path("C:/Program Files/Steam/steamapps/common/Broken Arrow"),
    Path("D:/Steam/steamapps/common/broken_arrow"),
    Path("D:/SteamLibrary/steamapps/common/broken_arrow"),
    Path("E:/SteamLibrary/steamapps/common/broken_arrow"),
    # macOS
    Path.home() / "Library/Application Support/Steam/steamapps/common/Broken Arrow",
    # Linux (Steam Play / Proton)
    Path.home() / ".steam/steam/steamapps/common/Broken Arrow",
    Path.home() / ".local/share/Steam/steamapps/common/Broken Arrow",
]


def _bundle_under(root: Path) -> Path:
    """Return the expected bundle path inside a game root directory."""
    candidate = root / _DATA_RELATIVE
    if candidate.exists():
        return candidate
    # Some installs capitalise differently
    for alt in root.glob("*_Data/data.unity3d"):
        return alt
    return candidate          # return even if missing; caller checks


# ── Public API ────────────────────────────────────────────────────────────────

def resolve_bundle(explicit: str | None = None) -> Path:
    """Return the resolved bundle path.

    Existence is NOT guaranteed — callers must check and emit the
    appropriate ERR message.
    """
    # 1. Explicit arg wins unconditionally.
    if explicit:
        return Path(explicit)

    # 2. BA_GAME_ROOT environment variable.
    env_root = os.environ.get("BA_GAME_ROOT")
    if env_root:
        return _bundle_under(Path(env_root))

    # 3. game_root.txt inside the project (location owned by core.paths).
    cfg = _paths.GAME_ROOT_FILE
    if cfg.exists():
        text = cfg.read_text(encoding="utf-8").strip()
        if text:
            return _bundle_under(Path(text))

    # 4. The toolkit may sit directly inside the game folder; check the
    #    directory that contains the toolkit (its parent).
    here = _bundle_under(_paths.V3_ROOT.parent)
    if here.exists():
        return here

    # 5. A copy placed inside the project (v3/data.unity3d) is the default.
    if _paths.DEFAULT_BUNDLE.exists():
        return _paths.DEFAULT_BUNDLE

    # 6. Scan well-known game install locations (the external game itself).
    for root in _FALLBACK_ROOTS:
        candidate = root / _DATA_RELATIVE
        if candidate.exists():
            return candidate

    # Nothing found — return the first fallback so the error message is helpful.
    return _FALLBACK_ROOTS[0] / _DATA_RELATIVE
