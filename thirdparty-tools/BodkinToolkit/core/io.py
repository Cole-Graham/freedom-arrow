"""Atomic file IO with optional validator pass."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Callable, Optional


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def read_text_safe(path: Path) -> Optional[str]:
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8")


def atomic_write_text(
    path: Path,
    text: str,
    validator: Optional[Callable[[Path], None]] = None,
) -> Path:
    """Atomic write: tmp -> validate -> replace.

    On validator failure: tmp is renamed to <path>.partial for inspection,
    live file is left untouched, validator's exception re-raised.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    if validator is not None:
        try:
            validator(tmp)
        except Exception:
            partial = path.with_suffix(path.suffix + ".partial")
            tmp.replace(partial)
            raise
    os.replace(tmp, path)
    return path
