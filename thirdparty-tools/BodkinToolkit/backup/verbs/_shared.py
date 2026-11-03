"""Shared backup helpers: discovery + sizing."""
from __future__ import annotations

import time
from pathlib import Path
from typing import List, NamedTuple

from ...core import paths


class Snap(NamedTuple):
    kind: str
    name: str
    path: Path
    mtime: float
    size: int


def _dir_size(p: Path) -> int:
    return sum(f.stat().st_size for f in p.rglob("*") if f.is_file())


def list_snaps(kind=None) -> List[Snap]:
    snaps = []
    kinds = [kind] if kind else ["light", "heavy"]
    for k in kinds:
        base = paths.BACKUPS_DIR / k
        if not base.is_dir():
            continue
        for d in base.iterdir():
            if d.is_dir():
                st = d.stat()
                snaps.append(Snap(k, d.name, d, st.st_mtime, _dir_size(d)))
    snaps.sort(key=lambda s: s.mtime, reverse=True)
    return snaps


def human_size(n: int) -> str:
    size = float(n)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            return f"{size:.0f}{unit}" if unit == "B" else f"{size:.1f}{unit}"
        size /= 1024
    return f"{size:.1f}GB"


def iso(mtime: float) -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(mtime))


def timestamp() -> str:
    return time.strftime("%Y%m%d_%H%M%S")
