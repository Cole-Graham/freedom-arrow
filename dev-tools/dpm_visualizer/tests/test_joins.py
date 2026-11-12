"""Join smoke tests against the decrypted vanilla snapshot when present."""

from __future__ import annotations

import unittest
from pathlib import Path

from dpm_visualizer.joins import Catalog
from dpm_visualizer.tables import default_vanilla_dir, load_vanilla


def _vanilla() -> Path | None:
    return default_vanilla_dir(Path(__file__).resolve().parents[3])


@unittest.skipUnless(_vanilla() is not None, "cache/vanilla snapshot is missing; run python -m pipeline decrypt")
class T72BJoinTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        vanilla = _vanilla()
        assert vanilla is not None
        cls.catalog = Catalog(load_vanilla(vanilla))

    def test_unit_9_is_t72b(self) -> None:
        self.assertIn("T-72B", self.catalog.unit_label(9))

    def test_default_main_gun_and_ammo(self) -> None:
        mounted = {row.weapon_id: row for row in self.catalog.mounted_weapons(9)}
        self.assertIn(516, mounted)
        self.assertNotIn(9, mounted)
        self.assertNotIn(349, mounted)
        ammo_ids = {choice.ammunition_id for choice in mounted[516].ammos}
        self.assertTrue(ammo_ids)

    def test_default_armor(self) -> None:
        self.assertEqual(self.catalog.default_armor[9], 9)
        options = self.catalog.armor_options(9)
        self.assertTrue(options[0].is_default)
        self.assertEqual(options[0].armor_id, 9)

    def test_loadout_dropdown_follows_armor_and_weapons(self) -> None:
        default = self.catalog.default_loadout(9)
        self.assertTrue(default.is_default)
        self.assertEqual(default.armor_id, 9)
        labels = self.catalog.loadout_labels(9)
        self.assertTrue(any("T-72BA / K5 ERA" == label for label in labels))
        kit = self.catalog.loadout_by_label(9, "T-72BA / K5 ERA")
        assert kit is not None
        self.assertEqual(kit.armor_id, 204)
        weapons = {row.weapon_id for row in self.catalog.mounted_weapons(9, loadout=kit)}
        self.assertIn(349, weapons)
        self.assertNotIn(516, weapons)
        self.assertNotIn(9, weapons)

    def test_squad_loadout_changes_armor(self) -> None:
        standoff = self.catalog.loadout_by_label(150, "Standoff")
        assert standoff is not None
        self.assertEqual(standoff.replace_unit_id, 411)
        self.assertEqual(standoff.armor_id, 314)

    def test_kinetic_preference_picks_ap(self) -> None:
        gun = next(row for row in self.catalog.mounted_weapons(9) if row.weapon_id == 516)
        choice = self.catalog.pick_ammo(gun, "Kinetic")
        assert choice is not None
        ammo = self.catalog.ammos[choice.ammunition_id]
        self.assertEqual(int(ammo["ArmorTargeted"]), 1)

    def test_infantry_dpm_omits_rpg(self) -> None:
        self.assertTrue(self.catalog.is_infantry(398))
        all_ids = {row.weapon_id for row in self.catalog.mounted_weapons(398)}
        dpm_ids = {row.weapon_id for row in self.catalog.dpm_weapons(398)}
        self.assertIn(168, all_ids)
        self.assertNotIn(168, dpm_ids)
        self.assertIn(29, dpm_ids)

    def test_vehicle_dpm_keeps_atgm(self) -> None:
        self.assertFalse(self.catalog.is_infantry(9))
        self.assertEqual(
            {row.weapon_id for row in self.catalog.mounted_weapons(9)},
            {row.weapon_id for row in self.catalog.dpm_weapons(9)},
        )

    def test_t72b_silhouette_is_min_length_width(self) -> None:
        self.assertEqual(self.catalog.silhouette(9), (3.4, 2.1))
        size = self.catalog.silhouette_for_armor(self.catalog.default_armor[9])
        self.assertIsNotNone(size)
        self.assertGreater(size[0], 0)
        self.assertGreater(size[1], 0)

    def test_infantry_box_is_one_plus_half_per_soldier(self) -> None:
        unit_id = next(uid for uid in self.catalog.playable_units() if self.catalog.squad_size.get(uid) == 7)
        width, height = self.catalog.silhouette(unit_id)
        self.assertAlmostEqual(width, 4.5)
        self.assertGreater(height, 0)

    def test_vehicle_box_is_min_length_width(self) -> None:
        self.assertNotIn(9, self.catalog.squad_size)
        self.assertEqual(self.catalog.silhouette(9), (3.4, 2.1))

    def test_kit_armor_uses_wearer_silhouette(self) -> None:
        busk = self.catalog.silhouette_for_armor(47)
        self.assertIsNotNone(busk)
        self.assertGreater(busk[0], 0)
        self.assertGreater(busk[1], 0)


if __name__ == "__main__":
    unittest.main()


@unittest.skipUnless(_vanilla() is not None, "cache/vanilla snapshot is missing")
class InfantryArmorTests(unittest.TestCase):
    def test_any_men_count_for_a_class(self) -> None:
        catalog = Catalog(load_vanilla(_vanilla()))
        classes = catalog.infantry_armor_classes()
        self.assertIn("Armor Infantry Elite", classes)
        self.assertNotIn(10, classes["Armor Infantry Elite"])
        armor, box = catalog.infantry_armor("Armor Infantry Elite", 10)
        self.assertEqual(armor["ArmorValue"], 10)
        self.assertEqual(armor["MaxHealthPoints"], 50)
        self.assertEqual(box[0], 6.0)
        self.assertEqual(catalog.split_infantry_label("Armor Infantry 8Men [84]"), ("Armor Infantry", 8))
        labels = catalog.armor_menu_labels()
        self.assertIn("Armor Infantry Shock", labels)
        self.assertFalse(any(label.startswith("Armor Infantry 8Men") for label in labels))
