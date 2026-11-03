"""v3 menu — interactive launcher (the toolkit's top-level entrypoint).

Preserves the structure of the legacy actions/menu.py (nested menus,
arrow-key navigation on Windows, typed-key fallback elsewhere) but dispatches
ONLY to the new self-contained v3 tools, through their single fronts via
core.proc. No domain logic lives here.
"""
