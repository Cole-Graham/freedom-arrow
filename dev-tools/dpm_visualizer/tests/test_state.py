"""Tab UI state round-trip without a live catalog."""

from __future__ import annotations

import unittest

import tkinter as tk
from tkinter import ttk

from pathlib import Path

from dpm_visualizer.joins import Catalog
from dpm_visualizer.tables import default_vanilla_dir, load_vanilla
from dpm_visualizer.units_tab import UnitsTab
from dpm_visualizer.weapons_tab import WeaponsTab


class _App:
    catalog = None
    custom_units: dict = {}
    custom_weapons: dict = {}
    cover_rules = {"forest_taken": 1.0, "building_floor": 0.18, "building_per_soldier": 0.02}

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
        tab.rows[0]["loadout"].set("Default")
        tab.rows[0]["visible"].set(False)
        tab.rows[0]["cost"].set(60)
        tab.rows[1]["unit"].set("T-72B [9]")
        tab.rows[1]["loadout"].set("T-72BA / K5 ERA")
        tab.face_var.set("Top")
        tab.damage_type.set("Stress")
        tab.ammo_pref.set("HEAT")
        tab.launcher_mode.set("Show both")
        tab.include_upgrade.set(True)
        tab.normalize.set(True)
        tab.assume_hits.set(True)
        tab.duel_var.set(True)
        tab.log_scale.set(True)
        tab.target_armor.set("Armor T72B [9]")
        tab.chart.selected_range = 400.0
        saved = tab.save_tab_state()
        other = UnitsTab(ttk.Frame(self.root), _App())
        other.unit_names = list(tab.unit_names)
        other.load_tab_state(saved)
        restored = other.save_tab_state()
        self.assertEqual(restored["rows"][0]["unit"], "Motostrelki [398]")
        self.assertEqual(restored["rows"][0]["loadout"], "Default")
        self.assertEqual(restored["rows"][0]["cost"], 60)
        self.assertFalse(restored["rows"][0]["visible"])
        self.assertEqual(restored["rows"][1]["unit"], "T-72B [9]")
        self.assertEqual(restored["rows"][1]["loadout"], "T-72BA / K5 ERA")
        self.assertEqual(restored["face"], "Top")
        self.assertEqual(restored["damage_type"], "Stress")
        self.assertEqual(restored["ammo_pref"], "HEAT")
        self.assertEqual(restored["launcher_mode"], "Show both")
        self.assertTrue(restored["include_upgrade"])
        self.assertTrue(restored["normalize"])
        self.assertTrue(restored["assume_hits"])
        self.assertFalse(restored["duel"])
        self.assertTrue(restored["log_scale"])
        self.assertEqual(restored["target_armor"], "Armor T72B [9]")
        self.assertEqual(restored["pinned_range"], 400.0)

    def test_duel_checkbox_requires_two_visible_units(self) -> None:
        tab = UnitsTab(ttk.Frame(self.root), _App())
        tab.add_row()
        tab.rows[0]["unit"].set("Motostrelki [398]")
        tab.rows[1]["unit"].set("T-72B [9]")
        tab._update_duel_enabled()
        self.assertTrue(tab.duel_check.instate(["!disabled"]))
        tab.duel_var.set(True)
        tab.add_row()
        tab.rows[2]["unit"].set("M2A3 Bradley [16]")
        tab._update_duel_enabled()
        self.assertTrue(tab.duel_check.instate(["disabled"]))
        self.assertFalse(tab.duel_var.get())
        tab.rows[2]["visible"].set(False)
        tab._update_duel_enabled()
        self.assertTrue(tab.duel_check.instate(["!disabled"]))

    def test_duel_roundtrip_with_two_visible_units(self) -> None:
        names = ["Motostrelki [398]", "T-72B [9]"]
        tab = UnitsTab(ttk.Frame(self.root), _App())
        tab.unit_names = list(names)
        tab.add_row()
        tab.rows[0]["unit"].set(names[0])
        tab.rows[1]["unit"].set(names[1])
        tab._update_duel_enabled()
        tab.duel_var.set(True)
        saved = tab.save_tab_state()
        other = UnitsTab(ttk.Frame(self.root), _App())
        other.unit_names = list(names)
        other.load_tab_state(saved)
        restored = other.save_tab_state()
        self.assertTrue(restored["duel"])
        self.assertTrue(other.duel_check.instate(["!disabled"]))

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
        tab.target_unit.set("T-72B [9]")
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
        self.assertEqual(restored["target_unit"], "T-72B [9]")


if __name__ == "__main__":
    unittest.main()


def _vanilla() -> Path | None:
    return default_vanilla_dir(Path(__file__).resolve().parents[3])


@unittest.skipUnless(_vanilla() is not None, "cache/vanilla snapshot is missing")
class LauncherModeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.root = tk.Tk()
        cls.root.withdraw()
        cls.app = _App()
        cls.app.catalog = Catalog(load_vanilla(_vanilla()))

    @classmethod
    def tearDownClass(cls) -> None:
        cls.root.destroy()

    def _lines(self, mode: str, unit: str):
        tab = UnitsTab(ttk.Frame(self.root), self.app)
        tab.rows[0]["unit"].set(unit)
        tab.launcher_mode.set(mode)
        armor = self.app.catalog.infantry_armor("Armor Infantry", 8)[0]
        return tab._row_lines(tab.rows[0], armor, "Front", "Physical", None, False)

    def test_show_both_adds_a_dashed_line_with_the_launcher(self) -> None:
        # Marine Raiders [70] carry the M72A10 LAW [212].
        lines = self._lines("Show both", "Marine Raiders [70]")
        self.assertEqual([style for _meta, style in lines], ["-", "--"])
        without, full = (meta for meta, _style in lines)
        self.assertNotIn(212, [int(w["weapon"]["Id"]) for w in without["weapons"]])
        self.assertIn(212, [int(w["weapon"]["Id"]) for w in full["weapons"]])
        self.assertTrue(full["label"].endswith(" + launchers"))
        self.assertGreater(max(d for _c, d in full["series"]), max(d for _c, d in without["series"]))

    def test_without_launchers_drops_the_launcher(self) -> None:
        (meta, style), = self._lines("Show without launcher damage", "Marine Raiders [70]")
        self.assertNotIn(212, [int(w["weapon"]["Id"]) for w in meta["weapons"]])
        self.assertTrue(meta["label"].endswith(" (no launchers)"))

    def test_show_both_is_one_line_for_a_unit_without_launchers(self) -> None:
        lines = self._lines("Show both", "T-72B [9]")
        self.assertEqual([style for _meta, style in lines], ["-"])
