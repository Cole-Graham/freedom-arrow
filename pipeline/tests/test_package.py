"""The .bamod package is a zip BAModManager can install."""

from __future__ import annotations

import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from pipeline.config import Config
from pipeline.errors import PipelineError
from pipeline.package import package


def _cfg(root: Path) -> Config:
    return Config(
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


class PackageTests(unittest.TestCase):
    def test_bamod_keeps_changed_constants_and_skips_empty_ones(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            stable = root / "mod" / "constants"
            testing = root / "mod" / "testing" / "constants"
            stable.mkdir(parents=True)
            testing.mkdir(parents=True)
            (stable / "units.json").write_text('{\n  "1": { "Cost": 40 }\n}\n', encoding="utf-8")
            (stable / "weapons.json").write_text("{}\n", encoding="utf-8")
            (testing / "units.json").write_text('{\n  "2": { "Cost": 10 }\n}\n', encoding="utf-8")
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
            (root / "dist" / "stable").mkdir(parents=True)
            (root / "dist" / "stable" / "channel.json").write_text(
                json.dumps({"channel": "stable", "build_id": "6000.3.24f1-abc", "sha256": "ff"}),
                encoding="utf-8",
            )

            cfg = _cfg(root)
            produced = package(cfg, "stable")
            self.assertEqual(produced.name, "FreedomArrow-0.1.0.bamod")
            with zipfile.ZipFile(produced) as archive:
                names = set(archive.namelist())
                self.assertIn("mod.json", names)
                self.assertIn("README.md", names)
                self.assertIn("UserData/FreedomArrow/constants/units.json", names)
                self.assertNotIn("UserData/FreedomArrow/constants/weapons.json", names)
                info = json.loads(archive.read("mod.json"))
                self.assertEqual(info["type"], "modpack")
                self.assertEqual(info["id"], "freedomarrow.gameplay")
                self.assertEqual(info["repo"], "example/freedom-arrow")
                marker = json.loads(archive.read("UserData/FreedomArrow/channel.json"))
                self.assertEqual(marker["build_id"], "6000.3.24f1-abc")

            testing_pkg = package(cfg, "testing")
            with zipfile.ZipFile(testing_pkg) as archive:
                info = json.loads(archive.read("mod.json"))
                self.assertEqual(info["repo"], "example/freedom-arrow-testing")
                body = archive.read("UserData/FreedomArrow/constants/units.json")
                self.assertIn(b'"2"', body)

            launcher = json.loads((root / "dist" / "launcher.json").read_text(encoding="utf-8"))
            self.assertEqual(launcher["modpack"], "example/freedom-arrow")
            self.assertEqual(launcher["testing"], "example/freedom-arrow-testing")

    def test_modpack_requires_id_name_and_version(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "mod").mkdir()
            (root / "mod" / "modpack.json").write_text("{}\n", encoding="utf-8")
            with self.assertRaises(PipelineError):
                package(_cfg(root), "stable")
