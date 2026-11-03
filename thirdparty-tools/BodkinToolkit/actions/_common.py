"""Shared helpers for actions pipelines: step banners and tool invocation.

Pipelines contain NO domain logic — they only sequence tool calls and stop on
the first failure (propagating that tool's exit code).
"""
from __future__ import annotations

import sys

from ..core import out, proc


def banner(title: str) -> None:
    out.emit("=" * 70)
    out.emit(f" {title}")
    out.emit("=" * 70)


def step(title: str) -> None:
    out.emit("")
    out.emit(f"--- {title} ---")


def run_step(tool: str, *tool_args: str) -> None:
    """Invoke a tool, streaming its output. On failure, halt the pipeline with
    that tool's exit code (no rollback, no retry)."""
    r = proc.run_tool(tool, *tool_args, check=False)
    if r.returncode != 0:
        out.error(f"ERR pipeline halted: '{tool} {' '.join(tool_args)}' "
                  f"exited {r.returncode}", exit_code=r.returncode)
