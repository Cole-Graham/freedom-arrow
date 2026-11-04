"""Ground spotting envelope, range arithmetic, and the five-second signature window."""

from __future__ import annotations

import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from pipeline.config import Config
from pipeline.formulas import validate_formula
from pipeline.package import package


CAP = 1076.923076923
EXCEPTIONAL_CAP = 1292.307692308
EXCEPTIONAL_OPTICS = 2550
SPOTTED = 1.5
WINDOW = 5


def range_raw(optics: float, stealth: float, noise: float, cover: float, penalty: float) -> float:
    """min(cap, optics * stealth * max(noise, penalty) / cover), cover before the cap."""
    spotted = SPOTTED if penalty > 0 else 0
    effective = max(noise, spotted)
    raw = optics * stealth * effective / cover
    cap = EXCEPTIONAL_CAP if abs(optics - EXCEPTIONAL_OPTICS) < 0.5 else CAP
    return min(cap, raw)


class Window:
    def __init__(self) -> None:
        self._shots: dict[int, tuple[float, float]] = {}

    def fire(self, now: float, weapon_id: int, factor: float) -> None:
        self._shots[weapon_id] = (factor, now + WINDOW)

    def noise(self, now: float, penalty: float = 0) -> float:
        best = 1.0
        for factor, expiry in self._shots.values():
            if now < expiry and factor > best:
                best = factor
        spotted = SPOTTED if penalty > 0 else 0
        return max(best, spotted)


class SpottingTests(unittest.TestCase):
    def test_committed_formula_matches_the_envelope(self):
        repo = Path(__file__).resolve().parents[2]
        directory = repo / "mod" / "testing" / "formulas"
        path = directory / "FogOfWarUnit" / "CalculateVisionRangeForTarget.json"
        loaded = validate_formula(path, directory)
        parameters = loaded["parameters"]
        self.assertEqual(loaded["change"], "after")
        self.assertEqual(parameters["spottedPenalty"], 1.5)
        self.assertEqual(parameters["bocageCover"], 3)
        ids = parameters["weaponId"]
        self.assertEqual(len(ids), len(parameters["noise"]))
        self.assertEqual(len(ids), len(parameters["vehicleNoise"]))
        self.assertEqual(len(ids), len(set(ids)))
        stable = repo / "mod" / "formulas" / "FogOfWarUnit" / "CalculateVisionRangeForTarget.json"
        self.assertFalse(stable.exists())

    def test_cover_is_applied_before_the_absolute_cap(self):
        quiet_open = range_raw(925, 0.5, 1, 1, 0)
        self.assertAlmostEqual(quiet_open, 462.5)
        spotted_open = range_raw(925, 0.5, 1, 1, 2)
        self.assertAlmostEqual(spotted_open, 693.75)
        forest = range_raw(925, 0.5, 1.5, 3, 0)
        self.assertAlmostEqual(forest, 231.25)
        building = range_raw(925, 0.5, 1, 4, 0)
        self.assertAlmostEqual(building, 115.625)
        below_cap = range_raw(1375, 1, 2.2, 3, 0)
        self.assertAlmostEqual(below_cap, 1375 * 2.2 / 3)
        self.assertLess(below_cap, CAP)
        self.assertNotAlmostEqual(below_cap, min(CAP, 1375 * 2.2) / 3)
        capped = range_raw(1950, 1, 2.2, 3, 0)
        self.assertAlmostEqual(capped, CAP)
        exceptional = range_raw(2550, 1, 1, 1, 0)
        self.assertAlmostEqual(exceptional, EXCEPTIONAL_CAP)
        strong_spotted = range_raw(1950, 0.5, 1, 1, 2)
        self.assertAlmostEqual(strong_spotted, CAP)

    def test_louder_signature_outlasts_a_later_quieter_shot(self):
        window = Window()
        window.fire(0, 1, 2.2)
        window.fire(1, 2, 1.3)
        self.assertAlmostEqual(window.noise(4), 2.2)
        self.assertAlmostEqual(window.noise(5), 1.3)
        self.assertAlmostEqual(window.noise(6), 1.0)
        self.assertAlmostEqual(window.noise(6, penalty=2), 1.5)
        window.fire(4, 1, 2.2)
        self.assertAlmostEqual(window.noise(8), 2.2)
        self.assertAlmostEqual(window.noise(4), 2.2)

    def test_testing_package_contains_the_spotting_formula_and_constants(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            testing = root / "mod" / "testing"
            (testing / "constants").mkdir(parents=True)
            (testing / "formulas" / "FogOfWarUnit").mkdir(parents=True)
            (testing / "constants" / "sensors.json").write_text(
                '{\n  "4": { "OpticsGround": 700 }\n}\n',
                encoding="utf-8",
            )
            (testing / "constants" / "units.json").write_text(
                '{\n  "59": { "Stealth": 0.5, "CurrentStealth": 0.5 }\n}\n',
                encoding="utf-8",
            )
            formula = {
                "method": "BrokenArrow.Client.Ecs.FogOfWar.FogOfWarUnit.CalculateVisionRangeForTarget",
                "change": "after",
                "parameters": {"capRaw": CAP, "log": True},
            }
            relative = Path("FogOfWarUnit") / "CalculateVisionRangeForTarget.json"
            (testing / "formulas" / relative).write_text(json.dumps(formula), encoding="utf-8")
            (root / "mod" / "modpack.json").write_text(
                json.dumps(
                    {
                        "id": "freedomarrow.gameplay",
                        "name": "Freedom Arrow",
                        "version": "0.1.0",
                        "description": "Gameplay changes for Broken Arrow.",
                        "repo": "example/freedom-arrow",
                        "testingRepo": "example/freedom-arrow-testing",
                    }
                ),
                encoding="utf-8",
            )
            plugin = root / "runtime" / "FreedomArrow" / "bin" / "Release" / "net6.0" / "FreedomArrow.dll"
            plugin.parent.mkdir(parents=True)
            plugin.write_bytes(b"MZ-freedom-arrow")
            cfg = Config(
                repo_root=root,
                game_root=root / "game",
                cache_dir=root / "cache",
                dist_dir=root / "dist",
                constants_dir=root / "mod" / "constants",
                manifest_path=root / "mod" / "manifest.json",
                write_game_bundle=False,
                backup_dir=root / "cache" / "backups",
                game_exe=None,
                launch_args=(),
            )
            produced = package(cfg, "testing")
            with zipfile.ZipFile(produced) as archive:
                info = json.loads(archive.read("mod.json"))
                self.assertEqual(info["type"], "modpack")
                names = set(archive.namelist())
                self.assertIn(
                    "UserData/FreedomArrow/formulas/FogOfWarUnit/CalculateVisionRangeForTarget.json",
                    names,
                )
                self.assertIn("UserData/FreedomArrow/constants/sensors.json", names)
                self.assertIn("UserData/FreedomArrow/constants/units.json", names)
                sensors = archive.read("UserData/FreedomArrow/constants/sensors.json")
                self.assertIn(b"700", sensors)
