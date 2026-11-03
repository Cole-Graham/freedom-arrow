"""Subprocess wrapper for invoking sibling v3 tools.

Every cross-tool call in the toolkit goes through here, and every target is a
standalone entry script (`<tool>/<tool>.py`) run by absolute path — so calls
work regardless of the caller's working directory and never reach into another
tool's internals.
"""
from __future__ import annotations

import os
import subprocess
import sys
from typing import List, NamedTuple, Optional

from . import paths as _paths


class ProcResult(NamedTuple):
    returncode: int
    stdout: Optional[str]
    stderr: Optional[str]


class ToolFailed(RuntimeError):
    pass


def tool_entry(tool_name: str):
    """Absolute path to a tool's standalone entry script (`<tool>/<tool>.py`)."""
    return _paths.tool_root(tool_name) / f"{tool_name}.py"


def run_entry(entry_path, *args: str, check: bool = True, capture: bool = False) -> ProcResult:
    """Run any v3 entry script (a tool front or a pipeline front) by path.

    capture=True captures stdout/stderr; capture=False streams them through
    (required for interactive sub-tools). check=True raises on non-zero.
    """
    cmd: List[str] = [sys.executable, str(entry_path), *args]
    # Force the child to read/write UTF-8 regardless of host console code page
    # (Windows defaults to cp1252; unit names contain non-ASCII characters).
    env = {**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"}
    if capture:
        cp = subprocess.run(cmd, capture_output=True, text=True,
                            encoding="utf-8", errors="replace", env=env)
        result = ProcResult(cp.returncode, cp.stdout, cp.stderr)
    else:
        cp = subprocess.run(cmd, env=env)
        result = ProcResult(cp.returncode, None, None)
    if check and result.returncode != 0:
        msg = f"entry '{entry_path}' failed with exit {result.returncode}"
        if result.stderr:
            msg += f"\nstderr:\n{result.stderr}"
        raise ToolFailed(msg)
    return result


def run_tool(tool_name: str, *args: str, check: bool = True, capture: bool = False) -> ProcResult:
    """Invoke a sibling tool through its single front (`<tool>/<tool>.py`)."""
    return run_entry(tool_entry(tool_name), *args, check=check, capture=capture)
