"""Argparse helpers + standard top-level flags + capability summary."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional, Sequence

from . import out as _out
from . import prompt as _prompt


def build_parser(tool_name: str, description: str) -> argparse.ArgumentParser:
    """Returns a parser with --out / --yes / capability `?` token wired in."""
    p = argparse.ArgumentParser(prog=tool_name, description=description, add_help=True)
    p.add_argument("--out", metavar="PATH", help="redirect command output to PATH instead of stdout")
    p.add_argument("--yes", action="store_true",
                   help="skip confirmation prompts (required for non-interactive use of destructive verbs)")
    return p


def add_verb(parser: argparse.ArgumentParser, verb_name: str, help_text: str) -> argparse.ArgumentParser:
    """Return a subparser for a verb. Adds the subparsers container lazily."""
    if not getattr(parser, "_v3_subparsers", None):
        parser._v3_subparsers = parser.add_subparsers(dest="verb")
    sp = parser._v3_subparsers.add_parser(verb_name, help=help_text)
    return sp


def print_help_summary(
    parser: argparse.ArgumentParser,
    one_line_purpose: str,
    verbs: Sequence[tuple],
    examples: Sequence[str],
    extra_notes: Sequence[str] = (),
) -> None:
    """Print the capability summary triggered by `?`.

    verbs: sequence of (verb_name, one_line_help) tuples.
    examples: sequence of example command lines.
    extra_notes: free-form notes (paragraphs).
    """
    _out.emit(f"{parser.prog} — {one_line_purpose}")
    _out.emit()
    if verbs:
        _out.emit("Verbs:")
        for name, help_text in verbs:
            _out.emit(f"  {name:<14} {help_text}")
        _out.emit()
    _out.emit("Standard flags:")
    _out.emit("  --out <path>   write this command's output to <path>; prompts on overwrite unless --yes")
    _out.emit("  --yes          skip confirmation prompts (destructive ops, overwrites)")
    _out.emit("  ?              show this help (also shown when no args are passed)")
    _out.emit()
    if examples:
        _out.emit("Examples:")
        for ex in examples:
            _out.emit(f"  {ex}")
        _out.emit()
    for note in extra_notes:
        _out.emit(note)
        _out.emit()


def parse_or_help(
    parser: argparse.ArgumentParser,
    purpose: str,
    verbs: Sequence[tuple],
    examples: Sequence[str],
    extra_notes: Sequence[str] = (),
    argv: Optional[List[str]] = None,
) -> argparse.Namespace:
    """Parse argv. If empty OR first arg is `?`, print help and exit 0.

    MUST be the entry point for every v3 tool's main function.
    """
    if argv is None:
        argv = sys.argv[1:]
    if not argv or argv[0] == "?":
        print_help_summary(parser, purpose, verbs, examples, extra_notes)
        sys.exit(0)
    return parser.parse_args(argv)


def resolve_out_target(args: argparse.Namespace) -> None:
    """If --out was given, route emit() to the file. Honors --yes for overwrite.

    MUST be called by tools before any emit() output if they support --out.
    Raises prompt.Cancelled if user declines an overwrite.
    """
    out_path = getattr(args, "out", None)
    if not out_path:
        return
    p = Path(out_path)
    if p.exists():
        _prompt.confirm_destructive(
            f"--out target {p} exists. Overwrite?",
            yes_flag=getattr(args, "yes", False),
        )
    _out.use_file_sink(p)
