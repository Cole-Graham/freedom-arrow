"""Startup sanity check: is the toolkit placed where it can find the game?

The toolkit is meant to live as a folder directly inside the Broken Arrow game
directory (next to `BrokenArrow_Data/`), so the bundle resolves automatically.
If it can't find the game and no bundle is otherwise configured, the menu warns.
"""
from __future__ import annotations

import os
from pathlib import Path

from ..core import paths

_DATA_RELATIVE = Path("BrokenArrow_Data") / "data.unity3d"


def _game_beside_toolkit() -> Path | None:
    """If the toolkit's parent folder is a Broken Arrow install, return the
    bundle path found there."""
    parent = paths.V3_ROOT.parent
    cand = parent / _DATA_RELATIVE
    if cand.exists():
        return cand
    for alt in parent.glob("*_Data/data.unity3d"):
        return alt
    return None


def check_placement():
    """Return (ok, bundle_or_none, reason).

    ok=True when the game bundle is locatable (either the toolkit sits inside
    the game folder, or a bundle is explicitly configured). ok=False otherwise.
    """
    here = _game_beside_toolkit()
    if here is not None:
        return True, here, "toolkit is inside the Broken Arrow game folder"

    if os.environ.get("BA_GAME_ROOT"):
        return True, None, "BA_GAME_ROOT is set"
    if paths.GAME_ROOT_FILE.exists():
        return True, None, f"{paths.GAME_ROOT_FILE.name} is set"
    if paths.DEFAULT_BUNDLE.exists():
        return True, paths.DEFAULT_BUNDLE, "a bundle copy is present in the toolkit"

    return False, None, "no Broken Arrow game folder found and no bundle configured"


def warning_lines() -> list[str]:
    """Human warning shown at menu startup when placement check fails."""
    toolkit = paths.V3_ROOT
    return [
        "!" * 70,
        "  WARNING: this toolkit can't locate your Broken Arrow game files.",
        "",
        f"  Toolkit folder : {toolkit}",
        f"  Looked next to : {toolkit.parent}  (expected a BrokenArrow_Data/ here)",
        "",
        "  The extractor (unpack / decrypt / encrypt / pack) and heavy backups",
        "  will fail until the game is reachable. Fix it one of these ways:",
        "    1. Move this toolkit folder directly INSIDE your Broken Arrow game",
        "       folder, next to BrokenArrow_Data/  (recommended).",
        f"    2. Put the game's root path in {paths.GAME_ROOT_FILE.name} (in the toolkit root).",
        "    3. Set the BA_GAME_ROOT environment variable, or pass --bundle.",
        "",
        "  Database tools (db / import / export / link / etc.) still work on any",
        "  data already under world/.",
        "!" * 70,
    ]
