"""Vanilla loader and constants overlay."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from dpm_visualizer.tables import apply_overlay, default_vanilla_dir, load_vanilla


def _vanilla() -> Path | None:
    return default_vanilla_dir(Path(__file__).resolve().parents[3])


@unittest.skipUnless(_vanilla() is not None, "cache/vanilla snapshot is missing")
class OverlayTests(unittest.TestCase):
    def test_overlay_changes_cost_without_dropping_other_fields(self) -> None:
        vanilla = _vanilla()
        assert vanilla is not None
        tables = load_vanilla(vanilla)
        original = tables["Units"][9]
        hud = original["HUDName"]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "units.json"
            path.write_text(json.dumps({"9": {"Cost": 1}}), encoding="utf-8")
            merged = apply_overlay(tables, Path(tmp))
        self.assertEqual(merged["Units"][9]["Cost"], 1)
        self.assertEqual(merged["Units"][9]["HUDName"], hud)
        self.assertEqual(tables["Units"][9]["Cost"], original["Cost"])
