"""Interactive prompts with non-TTY fallback."""
from __future__ import annotations

import sys
from typing import Any, Callable, List, Optional, Sequence


class Cancelled(Exception):
    """Raised when the user cancels a prompt, or when a prompt is needed
    but input is non-interactive and --yes was not provided."""


def _have_questionary() -> bool:
    try:
        import questionary  # noqa: F401
        return sys.stdin.isatty() and sys.stdout.isatty()
    except ImportError:
        return False


def _interactive_stdin() -> bool:
    try:
        return sys.stdin.isatty()
    except Exception:
        return False


def select_one(message: str, options: Sequence[Any], label_fn: Callable[[Any], str] = str) -> Any:
    if not options:
        raise Cancelled("no options to choose from")
    labels = [label_fn(o) for o in options]
    if _have_questionary():
        import questionary
        choice = questionary.select(message, choices=labels).ask()
        if choice is None:
            raise Cancelled("user cancelled")
        return options[labels.index(choice)]
    if not _interactive_stdin():
        raise Cancelled("interactive selection required but stdin is not a terminal; "
                        "automation should pass explicit ids")
    print(message)
    for i, lbl in enumerate(labels, 1):
        print(f"  [{i}] {lbl}")
    while True:
        raw = input("pick #: ").strip()
        if not raw:
            raise Cancelled("empty selection")
        if raw.isdigit() and 1 <= int(raw) <= len(options):
            return options[int(raw) - 1]
        print("invalid; try again")


def select_many(message: str, options: Sequence[Any], label_fn: Callable[[Any], str] = str,
                preselected: Sequence[int] = ()) -> List[Any]:
    """Multi-select. ``preselected`` is a list of indices already checked.

    Each choice carries a unique value (its index) so duplicate labels never
    toggle together, and the current selection is shown pre-checked.
    """
    options = list(options)
    if not options:
        return []
    labels = [label_fn(o) for o in options]
    pre = set(preselected)
    if _have_questionary():
        import questionary
        choices = [questionary.Choice(title=labels[i], value=i, checked=(i in pre))
                   for i in range(len(options))]
        picks = questionary.checkbox(message, choices=choices).ask()
        if picks is None:
            raise Cancelled("user cancelled")
        return [options[i] for i in picks]
    if not _interactive_stdin():
        raise Cancelled("interactive multi-select required but stdin is not a terminal")
    selected = set(pre)
    while True:
        print(message)
        for i, lbl in enumerate(labels, 1):
            mark = "x" if (i - 1) in selected else " "
            print(f"  [{mark}] {i}) {lbl}")
        raw = input("numbers to TOGGLE (comma sep), 'a'=all, 'n'=none, blank=accept: ").strip().lower()
        if raw == "":
            break
        if raw == "a":
            selected = set(range(len(options))); continue
        if raw == "n":
            selected = set(); continue
        for tok in raw.split(","):
            tok = tok.strip()
            if tok.isdigit() and 1 <= int(tok) <= len(options):
                idx = int(tok) - 1
                selected.discard(idx) if idx in selected else selected.add(idx)
    return [options[i] for i in sorted(selected)]


def text(message: str, default: Optional[str] = None) -> str:
    if _have_questionary():
        import questionary
        val = questionary.text(message, default=default or "").ask()
        if val is None:
            raise Cancelled("user cancelled")
        return val
    if not _interactive_stdin():
        if default is not None:
            return default
        raise Cancelled("text input required but stdin is not a terminal")
    suffix = f" [{default}]" if default else ""
    raw = input(f"{message}{suffix}: ").strip()
    if not raw and default is not None:
        return default
    if not raw:
        raise Cancelled("empty input")
    return raw


def confirm(message: str, default: bool = False) -> bool:
    if _have_questionary():
        import questionary
        ans = questionary.confirm(message, default=default).ask()
        if ans is None:
            raise Cancelled("user cancelled")
        return ans
    if not _interactive_stdin():
        return default
    suffix = " [Y/n]" if default else " [y/N]"
    raw = input(f"{message}{suffix}: ").strip().lower()
    if not raw:
        return default
    return raw in ("y", "yes")


def confirm_destructive(message: str, yes_flag: bool) -> None:
    """Standard gate for destructive ops. Honors --yes; otherwise prompts.
    Raises Cancelled if the user declines."""
    if yes_flag:
        return
    if not _interactive_stdin():
        raise Cancelled("destructive operation requires confirmation; "
                        "pass --yes to proceed in non-interactive mode")
    if not confirm(message, default=False):
        raise Cancelled("user declined destructive operation")
