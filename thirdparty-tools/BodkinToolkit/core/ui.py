"""Interactive form/menu primitives built on top of `prompt`.

Generic, game-agnostic UI helpers used by interactive tools (the editor):

- choose_one / choose_many      : single / multi-select over arbitrary items.
- value_node / submenu_node / action_node : nodes for an editable form.
- run_form                      : a multi-level menu where value nodes show
                                  their current value (and default), are edited
                                  in place, and submenu nodes recurse.

All selection/text goes through `core.prompt`, so it uses an arrow-key menu
when questionary + a TTY are present and falls back to numbered input
otherwise. Non-interactive callers get `prompt.Cancelled`.
"""
from __future__ import annotations

from typing import Any, Callable, List, Optional, Sequence

from . import out, prompt


# ── selection ────────────────────────────────────────────────────────────────

def choose_one(message: str, items: Sequence[Any], label_fn: Callable[[Any], str] = str,
               allow_back: bool = True) -> Optional[Any]:
    """Single choice. Returns the chosen item, or None if the user backs out."""
    items = list(items)
    opts = list(items) + (["< back"] if allow_back else [])
    chosen = prompt.select_one(message, opts,
                               label_fn=lambda x: x if isinstance(x, str) and x == "< back"
                               else label_fn(x))
    if allow_back and chosen == "< back":
        return None
    return chosen


def choose_many(message: str, items: Sequence[Any], label_fn: Callable[[Any], str] = str,
                preselected: Sequence[int] = ()) -> List[Any]:
    """Multi choice. ``preselected`` = indices already checked. Returns chosen items."""
    return prompt.select_many(message, list(items), label_fn=label_fn,
                              preselected=preselected)


# ── form nodes ───────────────────────────────────────────────────────────────

class Node:
    label: str

    def render(self) -> str:  # pragma: no cover - interface
        return self.label

    def activate(self) -> None:  # pragma: no cover - interface
        ...


class ValueNode(Node):
    """An editable scalar. `get` reads the current value, `set` writes the new
    (already parsed) value. `default` is shown for reference."""

    def __init__(self, label: str, get: Callable[[], Any], set: Callable[[Any], None],
                 default: Any = None, parse: Callable[[str], Any] = str,
                 show: Optional[Callable[[Any], str]] = None):
        self.label = label
        self._get = get
        self._set = set
        self.default = default
        self._parse = parse
        self._show = show or (lambda v: "(none)" if v is None else str(v))

    def render(self) -> str:
        cur = self._show(self._get())
        if self.default is not None:
            return f"{self.label}: {cur}   (default: {self._show(self.default)})"
        return f"{self.label}: {cur}"

    def activate(self) -> None:
        cur = self._get()
        raw = prompt.text(f"{self.label}", default="" if cur is None else str(cur))
        raw = raw.strip()
        if raw == "":
            return
        try:
            self._set(self._parse(raw))
        except (ValueError, TypeError) as e:
            out.emit(f"  invalid value: {e}")


class SubmenuNode(Node):
    """Enters a child form. `build` returns the child nodes (rebuilt each entry
    so live values refresh)."""

    def __init__(self, label: str, build: Callable[[], List["Node"]],
                 summary: Optional[Callable[[], str]] = None):
        self.label = label
        self._build = build
        self._summary = summary

    def render(self) -> str:
        if self._summary:
            return f"{self.label}: {self._summary()} ..."
        return f"{self.label} ..."

    def activate(self) -> None:
        run_form(self.label, self._build)


class ActionNode(Node):
    """Runs an arbitrary callback."""

    def __init__(self, label: str, fn: Callable[[], None]):
        self.label = label
        self._fn = fn

    def activate(self) -> None:
        self._fn()


def value_node(label, get, set, default=None, parse=str, show=None) -> ValueNode:
    return ValueNode(label, get, set, default=default, parse=parse, show=show)


def submenu_node(label, build, summary=None) -> SubmenuNode:
    return SubmenuNode(label, build, summary=summary)


def action_node(label, fn) -> ActionNode:
    return ActionNode(label, fn)


# ── form loop ────────────────────────────────────────────────────────────────

def run_form(title: str, nodes, done_label: str = "< done") -> None:
    """Render an editable menu until the user chooses done/back.

    `nodes` is a list of Node, or a zero-arg callable returning one (rebuilt
    each iteration so edited values and submenu summaries refresh).
    """
    while True:
        current = nodes() if callable(nodes) else nodes
        opts = list(current) + [done_label]
        try:
            chosen = prompt.select_one(
                title, opts,
                label_fn=lambda n: n if isinstance(n, str) else n.render())
        except prompt.Cancelled:
            return
        if chosen is done_label or (isinstance(chosen, str) and chosen == done_label):
            return
        chosen.activate()


# ── parse helpers ────────────────────────────────────────────────────────────

def parse_int(s: str) -> int:
    return int(s)


def parse_float(s: str) -> float:
    return float(s)


def parse_bool(s: str) -> bool:
    return s.strip().lower() in ("1", "true", "yes", "y", "on")
