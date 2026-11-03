"""Resolve the game bundle path for heavy backups, without importing
extractor (tool boundary). Same precedence as extractor.game_paths:
explicit --bundle, BA_GAME_ROOT, game_root.txt, then default locations.
"""
from __future__ import annotations

import os
from pathlib import Path

from ..core import paths as _paths

_DATA_RELATIVE = Path("BrokenArrow_Data") / "data.unity3d"


def resolve_bundle(explicit=None) -> Path:
    if explicit:
        return Path(explicit)
    env = os.environ.get("BA_GAME_ROOT")
    if env:
        return Path(env) / _DATA_RELATIVE
    cfg = _paths.GAME_ROOT_FILE
    if cfg.exists():
        t = cfg.read_text(encoding="utf-8").strip()
        if t:
            return Path(t) / _DATA_RELATIVE
    here = Path(_paths.V3_ROOT.parent) / _DATA_RELATIVE
    if here.exists():
        return here
    if _paths.DEFAULT_BUNDLE.exists():
        return _paths.DEFAULT_BUNDLE
    return _paths.DEFAULT_BUNDLE
