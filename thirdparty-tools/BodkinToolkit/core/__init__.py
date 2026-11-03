"""core — generic infrastructure library.

See the per-module docstrings for the API. Importing `core` (or any of its
submodules) first forces the process's stdout/stderr to UTF-8, so every tool
emits UTF-8 regardless of the host console code page (critical on Windows,
where the default is cp1252 and unit names contain Cyrillic).
"""
import sys as _sys

for _stream in (_sys.stdout, _sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")   # py3.7+
    except (AttributeError, ValueError):
        pass

from . import args, prompt, paths, io, proc, out, ui

__all__ = ["args", "prompt", "paths", "io", "proc", "out", "ui"]
