"""Combat math tests. HEAT 6.95 is the 0.3 Javelin check."""

from __future__ import annotations

import unittest

from dpm_visualizer.calculations import (
    card_range_text,
    damage_formula_heat,
    damage_formula_kinetic,
    dispersion_reference_range,
    dpm_at_world,
    face_armor,
    hit_chance,
    hit_damage,
    penetration_at_range,
    rate_of_fire_second,
    sample_dpm,
    shots_per_minute,
    time_to_kill_s,
    uses_value_armor,
)
from dpm_visualizer.constants import CARD_RANGE_MULTIPLIER


class HeatFormulaTests(unittest.TestCase):
    def test_javelin_top_100(self) -> None:
        hit = damage_formula_heat(10.5, 140, 100)
        self.assertAlmostEqual(hit, 6.95, places=2)

    def test_javelin_top_80(self) -> None:
        hit = damage_formula_heat(10.5, 140, 80)
        self.assertAlmostEqual(hit, 7.92, places=2)

    def test_equal_pen_is_half(self) -> None:
        self.assertAlmostEqual(damage_formula_heat(10, 100, 100), 5.0)

    def test_double_pen_is_80_percent(self) -> None:
        self.assertAlmostEqual(damage_formula_heat(10, 200, 100), 8.0)

    def test_zero_armor_full_damage(self) -> None:
        self.assertEqual(damage_formula_heat(10, 50, 0), 10)


class KineticFormulaTests(unittest.TestCase):
    def test_overmatch_full(self) -> None:
        self.assertEqual(damage_formula_kinetic(10, 500, 400), 10)

    def test_equal_full(self) -> None:
        self.assertEqual(damage_formula_kinetic(10, 400, 400), 10)

    def test_half_or_below_zero(self) -> None:
        self.assertEqual(damage_formula_kinetic(10, 200, 400), 0)
        self.assertEqual(damage_formula_kinetic(10, 100, 400), 0)

    def test_three_quarters_is_two_thirds(self) -> None:
        self.assertAlmostEqual(damage_formula_kinetic(10, 300, 400), 10 * (2 - 1 / 0.75))

    def test_just_above_half_floors_at_10_percent(self) -> None:
        self.assertAlmostEqual(damage_formula_kinetic(10, 201, 400), 1.0)


class PenetrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.ammo = {
            "PenetrationAtMinRange": 840.0,
            "PenetrationAtGroundRange": 525.0,
            "GroundRange": 700.0,
            "MinimalRange": 0.0,
            "Damage": 10.0,
            "ArmorTargeted": 1,
        }

    def test_point_blank(self) -> None:
        self.assertAlmostEqual(penetration_at_range(self.ammo, 0), 840)

    def test_max_range(self) -> None:
        self.assertAlmostEqual(penetration_at_range(self.ammo, 700), 525)

    def test_midpoint(self) -> None:
        self.assertAlmostEqual(penetration_at_range(self.ammo, 350), (840 + 525) / 2)


class RateOfFireTests(unittest.TestCase):
    def test_t72_autoloader(self) -> None:
        weapon = {
            "MagazineSize": 1,
            "MagazineReloadTimeMin": 7.0,
            "MagazineReloadTimeMax": 8.0,
            "ShotsPerBurstMin": 1,
            "ShotsPerBurstMax": 1,
            "TimeBetweenBurstsMin": 0.0,
            "TimeBetweenBurstsMax": 0.0,
            "TimeBetweenShotsInBurst": 0.0,
        }
        self.assertAlmostEqual(rate_of_fire_second(weapon), 1 / 7.5)
        self.assertAlmostEqual(shots_per_minute(weapon), 8.0)

    def test_two_guns_double_rof(self) -> None:
        weapon = {
            "MagazineSize": 1,
            "MagazineReloadTimeMin": 6.0,
            "MagazineReloadTimeMax": 6.0,
            "ShotsPerBurstMin": 1,
            "ShotsPerBurstMax": 1,
            "TimeBetweenBurstsMin": 0.0,
            "TimeBetweenBurstsMax": 0.0,
            "TimeBetweenShotsInBurst": 0.0,
        }
        self.assertAlmostEqual(rate_of_fire_second(weapon, gun_count=2), 2 / 6)


class HitAndDpmTests(unittest.TestCase):
    def test_value_armor_uses_heat_curve(self) -> None:
        armor = {"ArmorValue": 10, "KinArmorFront": 0, "HeatArmorFront": 0}
        self.assertTrue(uses_value_armor(armor))
        self.assertEqual(face_armor(armor, "Front", 1), 10)
        ammo = {
            "Damage": 10,
            "ArmorTargeted": 1,
            "PenetrationAtMinRange": 20,
            "PenetrationAtGroundRange": 20,
            "GroundRange": 300,
            "MinimalRange": 0,
        }
        self.assertAlmostEqual(hit_damage(ammo, armor, 100, "Front"), 8.0)

    def test_out_of_range_is_zero(self) -> None:
        weapon = {
            "MagazineSize": 1,
            "MagazineReloadTimeMin": 7,
            "MagazineReloadTimeMax": 8,
            "ShotsPerBurstMin": 1,
            "ShotsPerBurstMax": 1,
            "TimeBetweenBurstsMin": 0,
            "TimeBetweenBurstsMax": 0,
            "TimeBetweenShotsInBurst": 0,
        }
        ammo = {
            "Damage": 10,
            "ArmorTargeted": 1,
            "PenetrationAtMinRange": 500,
            "PenetrationAtGroundRange": 300,
            "GroundRange": 600,
            "MinimalRange": 50,
        }
        armor = {"ArmorValue": 0, "KinArmorFront": 100, "HeatArmorFront": 100}
        self.assertEqual(dpm_at_world(weapon, ammo, armor, 40, "Front"), 0.0)
        self.assertGreater(dpm_at_world(weapon, ammo, armor, 100, "Front"), 0.0)

    def test_sample_uses_card_metres(self) -> None:
        weapon = {
            "MagazineSize": 1,
            "MagazineReloadTimeMin": 6,
            "MagazineReloadTimeMax": 6,
            "ShotsPerBurstMin": 1,
            "ShotsPerBurstMax": 1,
            "TimeBetweenBurstsMin": 0,
            "TimeBetweenBurstsMax": 0,
            "TimeBetweenShotsInBurst": 0,
        }
        ammo = {
            "Damage": 10,
            "ArmorTargeted": 1,
            "PenetrationAtMinRange": 800,
            "PenetrationAtGroundRange": 800,
            "GroundRange": 700,
            "MinimalRange": 0,
        }
        armor = {"ArmorValue": 0, "KinArmorFront": 100, "HeatArmorFront": 100}
        series = sample_dpm(weapon, ammo, armor, "Front")
        self.assertEqual(series[0][0], 0.0)
        self.assertAlmostEqual(series[-1][0], 700 * CARD_RANGE_MULTIPLIER)

    def test_time_to_kill(self) -> None:
        self.assertAlmostEqual(time_to_kill_s(14, 84), 10.0)
        self.assertIsNone(time_to_kill_s(14, 0))


class HitChanceTests(unittest.TestCase):
    def test_reference_range_prefers_ground(self) -> None:
        ammo = {"GroundRange": 250, "LowAltRange": 400, "HighAltRange": 800}
        self.assertEqual(dispersion_reference_range(ammo), 250)

    def test_seeker_uses_horizontal_radius(self) -> None:
        ammo = {
            "Seeker": 10,
            "DispersionHorizontalRadius": 1.0,
            "DispersionVerticalRadius": 0.0,
            "GroundRange": 2000,
        }
        self.assertEqual(hit_chance(ammo, 500, (3.0, 2.0)), 1.0)

    def test_zero_spread_is_always_a_hit(self) -> None:
        ammo = {
            "Seeker": 0,
            "DispersionHorizontalRadius": 0.0,
            "DispersionVerticalRadius": 0.0,
            "DispersionMinimal": 0.0,
            "GroundRange": 250,
        }
        self.assertEqual(hit_chance(ammo, 75, (3.0, 2.0)), 1.0)

    def test_rifle_vs_infantry_at_75_world_m(self) -> None:
        ammo = {
            "Seeker": 0,
            "DispersionHorizontalRadius": 4.5,
            "DispersionVerticalRadius": 1.0,
            "DispersionMinimal": 0.0,
            "GroundRange": 250,
        }
        self.assertAlmostEqual(hit_chance(ammo, 75, (3.0, 2.0)), 1.0)

    def test_grenade_vs_infantry_at_75_world_m(self) -> None:
        ammo = {
            "Seeker": 0,
            "DispersionHorizontalRadius": 10.0,
            "DispersionVerticalRadius": 2.0,
            "DispersionMinimal": 0.0,
            "GroundRange": 200,
        }
        self.assertAlmostEqual(hit_chance(ammo, 75, (3.0, 2.0)), 0.8)

    def test_rifle_at_max_range_vs_infantry(self) -> None:
        ammo = {
            "Seeker": 0,
            "DispersionHorizontalRadius": 4.5,
            "DispersionVerticalRadius": 1.0,
            "DispersionMinimal": 0.0,
            "GroundRange": 250,
        }
        self.assertAlmostEqual(hit_chance(ammo, 250, (3.0, 2.0)), 3.0 / 4.5)

    def test_dpm_scales_by_hit_chance(self) -> None:
        weapon = {
            "MagazineSize": 1,
            "MagazineReloadTimeMin": 6,
            "MagazineReloadTimeMax": 6,
            "ShotsPerBurstMin": 1,
            "ShotsPerBurstMax": 1,
            "TimeBetweenBurstsMin": 0,
            "TimeBetweenBurstsMax": 0,
            "TimeBetweenShotsInBurst": 0,
        }
        ammo = {
            "Damage": 2.0,
            "ArmorTargeted": 2,
            "PenetrationAtMinRange": 20,
            "PenetrationAtGroundRange": 20,
            "GroundRange": 200,
            "MinimalRange": 0,
            "Seeker": 0,
            "DispersionHorizontalRadius": 10.0,
            "DispersionVerticalRadius": 2.0,
            "DispersionMinimal": 0.0,
        }
        armor = {"ArmorValue": 6, "KinArmorFront": 0, "HeatArmorFront": 0}
        full = dpm_at_world(weapon, ammo, armor, 75, "Front")
        expected = dpm_at_world(
            weapon,
            ammo,
            armor,
            75,
            "Front",
            silhouette=(3.0, 2.0),
            apply_accuracy=True,
        )
        self.assertAlmostEqual(expected, full * 0.8)


class CardRangeTextTests(unittest.TestCase):
    def test_ground_only(self) -> None:
        self.assertEqual(
            card_range_text({"MinimalRange": 0, "GroundRange": 250}),
            "range 0–500 card m",
        )

    def test_min_and_ground(self) -> None:
        self.assertEqual(
            card_range_text({"MinimalRange": 6, "GroundRange": 200}),
            "range 12–400 card m",
        )

    def test_includes_air_bands(self) -> None:
        self.assertEqual(
            card_range_text(
                {
                    "MinimalRange": 0,
                    "GroundRange": 600,
                    "LowAltRange": 3500,
                    "HighAltRange": 4000,
                },
            ),
            "range 0–1200  low 7000  high 8000 card m",
        )


if __name__ == "__main__":
    unittest.main()
