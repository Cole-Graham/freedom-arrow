"""Vanilla loader and constants overlay."""

from __future__ import annotations

import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from dpm_visualizer.tables import apply_overlay, default_vanilla_dir, extract_package, load_vanilla


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


class NullRowTests(unittest.TestCase):
    def test_null_overlay_row_deletes_the_row(self) -> None:
        tables = {"SquadMembersJson": {1: {"Id": 1, "UnitId": 9}, 2: {"Id": 2, "UnitId": 9}}}
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "squad_members.json").write_text(json.dumps({"2": None}), encoding="utf-8")
            merged = apply_overlay(tables, Path(tmp))
        self.assertEqual(sorted(merged["SquadMembersJson"]), [1])
        self.assertEqual(sorted(tables["SquadMembersJson"]), [1, 2])


class PartialRowTests(unittest.TestCase):
    def test_patch_on_a_row_missing_from_vanilla_is_refused(self) -> None:
        tables = {"WeaponsJson": {1: {"Id": 1, "Type": 1, "MagazineSize": 30}}}
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "weapons.json").write_text(json.dumps({"7": {"MagazineSize": 5}}), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "pipeline decrypt"):
                apply_overlay(tables, Path(tmp))


class PackageTests(unittest.TestCase):
    def test_extract_package_reads_constants_config_and_version(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            package = Path(tmp) / "FreedomArrow-0.9.0-dev.99.bamod"
            with zipfile.ZipFile(package, "w") as bamod:
                bamod.writestr("mod.json", json.dumps({"version": "0.9.0-dev.99"}))
                bamod.writestr("UserData/FreedomArrow/constants/units.json", json.dumps({"9": {"Cost": 1}}))
                bamod.writestr("UserData/FreedomArrow/game-config.json", json.dumps({"ForestDamageTaken": 0.5}))
                bamod.writestr("UserData/FAModels/x.fam", b"model")
            constants, version = extract_package(package, Path(tmp))
            self.assertEqual(version, "0.9.0-dev.99")
            self.assertEqual(json.loads((constants / "units.json").read_text()), {"9": {"Cost": 1}})
            self.assertTrue((constants.parent / "game-config.json").is_file())
            self.assertFalse((Path(tmp) / "cache" / "fa-package" / "UserData" / "FAModels").exists())
