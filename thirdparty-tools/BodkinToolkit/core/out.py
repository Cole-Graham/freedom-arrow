"""Output routing. All human output goes through here so --out works."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional, TextIO

# Force standard streams to use UTF-8 (Crucial for Windows consoles)
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

_sink: Optional[TextIO] = None
_sink_path: Optional[Path] = None


def use_file_sink(path: Path) -> None:
    """Redirect emit() to a file. Caller MUST have already resolved any
    overwrite confirmation."""
    global _sink, _sink_path
    _sink = open(path, "w", encoding="utf-8")
    _sink_path = path


def close_sink() -> None:
    global _sink
    if _sink is not None:
        _sink.flush()
        _sink.close()
        _sink = None


def emit(text: str = "", end: str = "\n") -> None:
    target = _sink if _sink is not None else sys.stdout
    target.write(text + end)


def error(message: str, exit_code: int = 1) -> None:
    sys.stderr.write(message.rstrip() + "\n")
    close_sink()
    sys.exit(exit_code)
