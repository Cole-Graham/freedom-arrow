"""Tab UI state round-trip without a live catalog."""

from __future__ import annotations

import unittest

import tkinter as tk
from tkinter import ttk

from dpm_visualizer.units_tab import UnitsTab
from dpm_visualizer.weapons_tab import WeaponsTab


class _App:
    catalog = None
    custom_units: dict = {}
    custom_weapons: dict = {}

    def auto_save_state(self) -> None:
        pass

    def save_user_data(self) -> None:
        pass


class TabStateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.root = tk.Tk()
        cls.root.withdraw()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.root.destroy()

    def test_units_tab_roundtrip(self) -> None:
        tab = UnitsTab(ttk.Frame(self.root), _App())
        tab.unit_names = ["Motostrelki [398]", "T-72B [9]"]
        tab.rows[0]["unit"].set_values(tab.unit_names)
        tab.add_row()
        tab.rows[0]["unit"].set("Motostrelki [398]")
        tab.rows[0]["armor"].set("Default — Armor T72B [9]")
        tab.rows[0]["visible"].set(False)
        tab.rows[0]["cost"].set(60)
        tab.rows[1]["unit"].set("T-72B [9]")
        tab.face_var.set("Top")
        tab.damage_type.set("Stress")
        tab.ammo_pref.set("HEAT")
        tab.include_upgrade.set(True)
        tab.normalize.set(True)
        tab.assume_hits.set(True)
        tab.log_scale.set(True)
        tab.target_armor.set("Armor T72B [9]")
        tab.chart.selected_range = 400.0
        saved = tab.save_tab_state()
        other = UnitsTab(ttk.Frame(self.root), _App())
        other.unit_names = list(tab.unit_names)
        other.load_tab_state(saved)
        restored = other.save_tab_state()
        self.assertEqual(restored["rows"][0]["unit"], "Motostrelki [398]")
        self.assertEqual(restored["rows"][0]["cost"], 60)
        self.assertFalse(restored["rows"][0]["visible"])
        self.assertEqual(restored["rows"][1]["unit"], "T-72B [9]")
        self.assertEqual(restored["face"], "Top")
        self.assertEqual(restored["damage_type"], "Stress")
        self.assertEqual(restored["ammo_pref"], "HEAT")
        self.assertTrue(restored["include_upgrade"])
        self.assertTrue(restored["normalize"])
        self.assertTrue(restored["assume_hits"])
        self.assertTrue(restored["log_scale"])
        self.assertEqual(restored["target_armor"], "Armor T72B [9]")
        self.assertEqual(restored["pinned_range"], 400.0)

    def test_weapons_tab_roundtrip(self) -> None:
        tab = WeaponsTab(ttk.Frame(self.root), _App())
        tab.weapon_names = ["Javelin [44] — Javelin [99]"]
        tab.rows[0]["weapon"].set_values(tab.weapon_names)
        tab.rows[0]["weapon"].set("Javelin [44] — Javelin [99]")
        tab.rows[0]["qty"].set(3)
        tab.rows[0]["visible"].set(False)
        tab.face_var.set("Rear")
        tab.sweep_faces.set(True)
        tab.damage_type.set("Stress")
        tab.assume_hits.set(True)
        tab.log_scale.set(True)
        tab.target_armor.set("Armor T72B [9]")
        saved = tab.save_tab_state()
        other = WeaponsTab(ttk.Frame(self.root), _App())
        other.weapon_names = list(tab.weapon_names)
        other.load_tab_state(saved)
        restored = other.save_tab_state()
        self.assertEqual(restored["rows"][0]["weapon"], "Javelin [44] — Javelin [99]")
        self.assertEqual(restored["rows"][0]["qty"], 3)
        self.assertFalse(restored["rows"][0]["visible"])
        self.assertEqual(restored["face"], "Rear")
        self.assertTrue(restored["sweep_faces"])
        self.assertTrue(restored["assume_hits"])
        self.assertEqual(restored["target_armor"], "Armor T72B [9]")


if __name__ == "__main__":
    unittest.main()
