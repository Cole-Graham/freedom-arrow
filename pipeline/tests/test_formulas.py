"""Formula files share one envelope. The validator does not know individual hooks."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from pipeline.errors import PipelineError
from pipeline.formulas import validate_formula


def _write(directory: Path, relative: str, payload: dict) -> Path:
    path = directory / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


class FormulaTests(unittest.TestCase):
    def test_accepts_a_method_other_than_forest_cover(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = _write(
                root,
                "OtherClass/OtherMethod.json",
                {
                    "method": "Game.OtherClass.OtherMethod",
                    "change": "after",
                    "parameters": {"scale": 2, "label": "x", "enabled": True, "ids": [1, "a"]},
                },
            )
            loaded = validate_formula(path, root)
            self.assertEqual(loaded["parameters"]["scale"], 2)
            self.assertEqual(loaded["parameters"]["ids"], [1, "a"])

            empty = _write(
                root,
                "OtherClass/Bare.json",
                {"method": "Game.OtherClass.Bare", "change": "after", "parameters": {}},
            )
            self.assertEqual(validate_formula(empty, root)["parameters"], {})

    def test_committed_formula_directories_exist(self):
        repo = Path(__file__).resolve().parents[2]
        for relative in (
            Path("mod") / "formulas",
            Path("mod") / "testing" / "formulas",
        ):
            self.assertTrue((repo / relative).is_dir())

    def test_rejects_unimplemented_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = _write(
                root,
                "OtherClass/OtherMethod.json",
                {"method": "Game.OtherClass.OtherMethod", "change": "before", "parameters": {}},
            )
            with self.assertRaises(PipelineError) as caught:
                validate_formula(path, root)
            self.assertIn("not implemented", str(caught.exception))

    def test_rejects_path_that_does_not_match_method(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = _write(
                root,
                "OtherClass/OtherMethod.json",
                {"method": "Game.Other.Method", "change": "after", "parameters": {"scale": 1}},
            )
            with self.assertRaises(PipelineError) as caught:
                validate_formula(path, root)
            self.assertIn("does not match method", str(caught.exception))

    def test_rejects_a_top_level_key_other_than_the_envelope(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = _write(
                root,
                "OtherClass/OtherMethod.json",
                {
                    "method": "Game.OtherClass.OtherMethod",
                    "change": "after",
                    "parameters": {},
                    "extra": 1,
                },
            )
            with self.assertRaises(PipelineError) as caught:
                validate_formula(path, root)
            self.assertIn("keys must be", str(caught.exception))
