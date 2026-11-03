"""Fixture tests for crypto, identity, constants, rebase, config, and hangar."""

from __future__ import annotations

import json
import re
import struct
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from pipeline.apply import apply_overrides, build_object
from pipeline.bundle import FoundObject, _select_database, read_unity_version
from pipeline.bundle_stream import extract_file, pack_files, read_index, write_bundle
from pipeline.config import load_config
from pipeline.constants import load_constants
from pipeline.crypto import MARKER, aes_decrypt, aes_encrypt
from pipeline.database import parse_database, rebuild
from pipeline.errors import PipelineError, RebaseConflictError
from pipeline.hangar import run_hangar
from pipeline.rebase import collect_conflicts, rebase
from pipeline.snapshot import write_json, write_manifest
from pipeline.il2cpp import decode_fields, extract_classes
from pipeline.survey import catalog_monobehaviour, index_tables
from pipeline.tables import FIELD_ORDER, TABLE_FILES

REPO = Path(__file__).resolve().parents[2]


def _pptr(buf: bytearray, file_id: int, path_id: int) -> None:
    buf += struct.pack("<I", file_id)
    buf += struct.pack("<q", path_id)


def _string(buf: bytearray, text: str) -> None:
    encoded = text.encode("utf-8")
    buf += struct.pack("<i", len(encoded))
    buf += encoded
    remainder = len(buf) % 4
    if remainder:
        buf += b"\x00" * (4 - remainder)


def make_blob(fields: dict[str, str], level: int = 3) -> bytes:
    buf = bytearray()
    _pptr(buf, 0, 0)
    buf += struct.pack("<i", 1)
    _pptr(buf, 1, 42)
    _string(buf, "DataBaseCompiled")
    for name in FIELD_ORDER:
        _string(buf, fields[name])
    buf += struct.pack("<i", level)
    return bytes(buf)


def sample_fields() -> dict[str, str]:
    return {name: aes_encrypt(json.dumps([{"Id": 1, "Cost": 10}]).encode("utf-8")) for name in FIELD_ORDER}


class CryptoTests(unittest.TestCase):
    def test_round_trip_and_marker(self):
        wire = aes_encrypt(b'[{"Id": 1}]')
        self.assertTrue(aes_decrypt(wire).startswith(b"[") or aes_decrypt(wire).startswith(b"["))
        self.assertEqual(aes_decrypt(wire), b'[{"Id": 1}]')
        raw = MARKER + b"\x00" * 16 + b"not-a-block"
        import base64

        with self.assertRaises(ValueError):
            aes_decrypt(base64.b64encode(b"no-mark" + b"\x00" * 24).decode("ascii"))
        self.assertTrue(raw.startswith(MARKER))

    def test_field_order_matches_bodkin(self):
        text = (REPO / "thirdparty-tools" / "BodkinToolkit" / "extractor" / "crypto.py").read_text(
            encoding="utf-8"
        )
        match = re.search(r"FIELD_ORDER: list = \[(.*?)\]", text, re.S)
        self.assertIsNotNone(match)
        names = re.findall(r'"(\w+)"', match.group(1))
        self.assertEqual(names, [field for field, _filename in TABLE_FILES])


class IdentityTests(unittest.TestCase):
    def test_empty_rebuild_is_original_bytes(self):
        fields = sample_fields()
        raw = make_blob(fields, level=7)
        blob = parse_database(raw)
        self.assertEqual(blob.level, 7)
        self.assertEqual(blob.script, (1, 42))
        self.assertEqual(rebuild(blob, dict(blob.fields)), raw)

    def test_one_field_keeps_the_other_ciphertext(self):
        fields = sample_fields()
        raw = make_blob(fields)
        blob = parse_database(raw)
        replacement = aes_encrypt(b'[{"Id": 1, "Cost": 40}]')
        updated = dict(blob.fields)
        updated["Units"] = replacement
        rebuilt = rebuild(blob, updated)
        again = parse_database(rebuilt)
        self.assertEqual(again.fields["Units"], replacement)
        for name in FIELD_ORDER:
            if name == "Units":
                continue
            self.assertEqual(again.fields[name], fields[name])
        self.assertEqual(again.trailer, blob.trailer)
        self.assertTrue(rebuilt.startswith(blob.prefix))

    def test_leading_empty_string_stays_in_the_prefix(self):
        fields = sample_fields()
        buf = bytearray()
        _pptr(buf, 0, 0)
        buf += struct.pack("<i", 1)
        _pptr(buf, 1, 42)
        _string(buf, "DataBaseCompiled")
        _string(buf, "")
        for name in FIELD_ORDER:
            _string(buf, fields[name])
        buf += struct.pack("<i", 2)
        raw = bytes(buf)
        blob = parse_database(raw)
        self.assertEqual(blob.level, 2)
        self.assertFalse(blob.main_build_database)
        self.assertEqual(blob.fields["Units"], fields["Units"])
        self.assertEqual(rebuild(blob, dict(blob.fields)), raw)

    def test_main_flag_is_true_and_round_trips(self):
        fields = sample_fields()
        buf = bytearray()
        _pptr(buf, 0, 0)
        buf += struct.pack("<i", 1)
        _pptr(buf, 1, 42)
        _string(buf, "DataBaseCompiled")
        buf += b"\x01\x00\x00\x00"
        for name in FIELD_ORDER:
            _string(buf, fields[name])
        buf += struct.pack("<i", 2)
        raw = bytes(buf)
        blob = parse_database(raw)
        self.assertTrue(blob.main_build_database)
        self.assertEqual(blob.level, 2)
        self.assertEqual(rebuild(blob, dict(blob.fields)), raw)


class ApplyTests(unittest.TestCase):
    def test_merge_cost_and_reject_type_and_missing_id(self):
        rows = [{"Id": 3, "Cost": 55, "Name": "BMP-3"}]
        merged, dirty = apply_overrides(rows, {"3": {"Cost": 80}}, "units.json")
        self.assertTrue(dirty)
        self.assertEqual(merged[0]["Cost"], 80)
        self.assertEqual(merged[0]["Name"], "BMP-3")
        self.assertEqual(rows[0]["Cost"], 55)

        _unchanged, clean = apply_overrides(rows, {"3": {"Cost": 55}}, "units.json")
        self.assertFalse(clean)

        with self.assertRaises(PipelineError):
            apply_overrides(rows, {"3": {"Cost": "high"}}, "units.json")
        with self.assertRaises(PipelineError):
            apply_overrides(rows, {"9": {"Cost": 1}}, "units.json")

    def test_empty_constants_round_trip_on_disk(self):
        fields = sample_fields()
        raw = make_blob(fields)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            vanilla = root / "vanilla"
            vanilla.mkdir()
            (vanilla / "object.bin").write_bytes(raw)
            plaintext = [{"Id": 1, "Cost": 10}]
            for name in FIELD_ORDER:
                write_json(vanilla / f"{name}.json", plaintext)
                (vanilla / f"{name}.b64").write_text(fields[name], encoding="ascii")
            constants = root / "constants"
            constants.mkdir()
            (constants / "units.json").write_text("{}\n", encoding="utf-8")
            rebuilt, dirty = build_object(vanilla, load_constants(constants))
            self.assertEqual(dirty, [])
            self.assertEqual(rebuilt, raw)

    def test_dirty_field_changes_only_that_ciphertext(self):
        fields = sample_fields()
        raw = make_blob(fields)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            vanilla = root / "vanilla"
            vanilla.mkdir()
            (vanilla / "object.bin").write_bytes(raw)
            for name in FIELD_ORDER:
                write_json(vanilla / f"{name}.json", [{"Id": 1, "Cost": 10}])
                (vanilla / f"{name}.b64").write_text(fields[name], encoding="ascii")
            constants = root / "constants"
            constants.mkdir()
            (constants / "units.json").write_text('{"1": {"Cost": 40}}\n', encoding="utf-8")
            rebuilt, dirty = build_object(vanilla, load_constants(constants))
            self.assertEqual(dirty, ["Units"])
            parsed = parse_database(rebuilt)
            self.assertNotEqual(parsed.fields["Units"], fields["Units"])
            rows = json.loads(aes_decrypt(parsed.fields["Units"]))
            self.assertEqual(rows[0]["Cost"], 40)
            for name in FIELD_ORDER:
                if name != "Units":
                    self.assertEqual(parsed.fields[name], fields[name])

    def test_broken_link_is_rejected_before_ciphertext_changes(self):
        fields = sample_fields()
        raw = make_blob(fields)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            vanilla = root / "vanilla"
            vanilla.mkdir()
            (vanilla / "object.bin").write_bytes(raw)
            for name in FIELD_ORDER:
                row = {"Id": 1, "Cost": 10}
                if name == "WeaponAmmunitionsJson":
                    row["AmmunitionId"] = 1
                write_json(vanilla / f"{name}.json", [row])
                (vanilla / f"{name}.b64").write_text(fields[name], encoding="ascii")
            constants = root / "constants"
            constants.mkdir()
            (constants / "weapon_ammunitions.json").write_text(
                '{"1": {"AmmunitionId": 99}}\n',
                encoding="utf-8",
            )
            with self.assertRaises(PipelineError) as caught:
                build_object(vanilla, load_constants(constants))
            self.assertIn("weapon_ammunitions.json", str(caught.exception))
            self.assertIn("AmmunitionId", str(caught.exception))
            self.assertIn("ammunitions.json", str(caught.exception))
            self.assertEqual((vanilla / "object.bin").read_bytes(), raw)


class SelectTests(unittest.TestCase):
    def test_main_level_two_beats_a_larger_snapshot(self):
        small = _flagged_blob(main=True, level=2, units=1)
        large = _flagged_blob(main=False, level=2, units=4)
        chosen = _select_database([_found(large, 10), _found(small, 20)])
        self.assertEqual(chosen.path_id, 20)

    def test_without_a_flag_the_most_units_win(self):
        small = make_blob(sample_fields(), level=2)
        fields = sample_fields()
        fields["Units"] = aes_encrypt(json.dumps([{"Id": 1}, {"Id": 2}]).encode("utf-8"))
        large = make_blob(fields, level=2)
        chosen = _select_database([_found(small, 1), _found(large, 2)])
        self.assertEqual(chosen.path_id, 2)


def _found(raw: bytes, path_id: int) -> FoundObject:
    return FoundObject(
        obj=None,
        path_id=path_id,
        raw=raw,
        blob=parse_database(raw),
        typetree=False,
        inspected=[],
    )


def _flagged_blob(*, main: bool, level: int, units: int) -> bytes:
    fields = sample_fields()
    rows = [{"Id": index + 1, "Cost": 1} for index in range(units)]
    fields["Units"] = aes_encrypt(json.dumps(rows).encode("utf-8"))
    buf = bytearray()
    _pptr(buf, 0, 0)
    buf += struct.pack("<i", 1)
    _pptr(buf, 1, 42)
    _string(buf, "DataBaseCompiled")
    buf += b"\x01\x00\x00\x00" if main else b"\x00\x00\x00\x00"
    for name in FIELD_ORDER:
        _string(buf, fields[name])
    buf += struct.pack("<i", level)
    return bytes(buf)


class RebaseTests(unittest.TestCase):
    def _write_snapshot(self, directory: Path, cost: int) -> None:
        directory.mkdir(parents=True)
        for name in FIELD_ORDER:
            write_json(directory / f"{name}.json", [{"Id": 3, "Cost": cost, "Name": "BMP-3"}])

    def test_keeps_constant_when_vanilla_is_unchanged(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            old = root / "old"
            new = root / "new"
            self._write_snapshot(old, 55)
            self._write_snapshot(new, 55)
            constants = root / "constants"
            constants.mkdir()
            (constants / "units.json").write_text('{"3": {"Cost": 40}}\n', encoding="utf-8")
            self.assertEqual(collect_conflicts(old, new, load_constants(constants)), [])

    def test_conflict_when_both_sides_change_and_accept_moves_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            old = root / "build-old"
            new = root / "build-new"
            self._write_snapshot(old, 55)
            self._write_snapshot(new, 60)
            constants = root / "constants"
            constants.mkdir()
            (constants / "units.json").write_text('{"3": {"Cost": 40}}\n', encoding="utf-8")
            conflicts = collect_conflicts(old, new, load_constants(constants))
            self.assertEqual(len(conflicts), 1)
            self.assertEqual(conflicts[0].reason, "both_changed")
            self.assertEqual(conflicts[0].old_vanilla, 55)
            self.assertEqual(conflicts[0].new_vanilla, 60)

            manifest = root / "manifest.json"
            report = root / "rebase-conflicts.json"
            with self.assertRaises(RebaseConflictError):
                rebase(old, new, constants, manifest, "build-new", report, accept=False)
            self.assertFalse(manifest.exists())
            self.assertTrue(report.is_file())

            rebase(old, new, constants, manifest, "build-new", report, accept=True)
            self.assertEqual(json.loads(manifest.read_text(encoding="utf-8"))["build_id"], "build-new")
            self.assertIn('"Cost": 40', (constants / "units.json").read_text(encoding="utf-8"))

    def test_row_deleted_and_type_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            old = root / "old"
            new = root / "new"
            self._write_snapshot(old, 55)
            new.mkdir()
            for name in FIELD_ORDER:
                rows = [{"Id": 3, "Cost": "sixty", "Name": "BMP-3"}] if name == "Units" else [{"Id": 3, "Cost": 55, "Name": "BMP-3"}]
                if name == "Units":
                    rows = [{"Id": 9, "Cost": 60, "Name": "other"}]
                write_json(new / f"{name}.json", rows)
            constants = root / "constants"
            constants.mkdir()
            (constants / "units.json").write_text('{"3": {"Cost": 40}}\n', encoding="utf-8")
            conflicts = collect_conflicts(old, new, load_constants(constants))
            self.assertEqual(conflicts[0].reason, "row_deleted")

            for name in FIELD_ORDER:
                write_json(
                    new / f"{name}.json",
                    [{"Id": 3, "Cost": "sixty", "Name": "BMP-3"}],
                )
            conflicts = collect_conflicts(old, new, load_constants(constants))
            self.assertEqual(conflicts[0].reason, "type_changed")


class ConfigTests(unittest.TestCase):
    def test_missing_config_tells_you_to_copy_the_template(self):
        with self.assertRaises(PipelineError) as raised:
            load_config(Path(tempfile.gettempdir()) / "does-not-exist-config.YAML")
        self.assertIn("config.template.YAML", str(raised.exception))
        self.assertIn("config.YAML", str(raised.exception))

    def test_paths_and_empty_game_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.YAML"
            path.write_text(
                'game_root: ""\ncache_dir: cache\n',
                encoding="utf-8",
            )
            with self.assertRaises(PipelineError) as raised:
                load_config(path)
            self.assertIn("game_root", str(raised.exception))

            path.write_text(
                "\n".join(
                    [
                        'game_root: "D:/Games/Broken Arrow"',
                        "cache_dir: cache",
                        "dist_dir: out",
                        "constants_dir: mod/constants",
                        "manifest_path: mod/manifest.json",
                        "write_game_bundle: false",
                        "backup_dir: cache/backups",
                        'game_exe: ""',
                        "launch_args: []",
                        "",
                    ]
                ),
                encoding="utf-8",
            )
            cfg = load_config(path)
            self.assertEqual(cfg.game_root, Path("D:/Games/Broken Arrow"))
            self.assertEqual(cfg.bundle_path, Path("D:/Games/Broken Arrow/BrokenArrow_Data/data.unity3d"))
            self.assertEqual(cfg.cache_dir, REPO / "cache")
            self.assertFalse(cfg.write_game_bundle)
            self.assertEqual(cfg.launch_args, ())


class BundleStreamTests(unittest.TestCase):
    def test_pack_extract_and_replace(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "data.unity3d"
            pack_files(source, {"a.txt": b"alpha", "b.txt": b"bravo"})
            index = read_index(source)
            self.assertEqual(extract_file(index, "a.txt"), b"alpha")
            self.assertEqual(extract_file(index, "b.txt"), b"bravo")

            patched = root / "patched.unity3d"
            write_bundle(index, patched, {"a.txt": b"ALPHA-LONGER"})
            again = read_index(patched)
            self.assertEqual(extract_file(again, "a.txt"), b"ALPHA-LONGER")
            self.assertEqual(extract_file(again, "b.txt"), b"bravo")

    def test_real_bundle_index(self):
        bundle = REPO / "BrokenArrow_Data" / "data.unity3d"
        if not bundle.is_file():
            self.skipTest("local bundle is not present")
        index = read_index(bundle)
        self.assertEqual(index.version_engine, "6000.3.24f1")
        self.assertTrue(any(entry.name == "globalgamemanagers.assets" for entry in index.files))


class HeaderTests(unittest.TestCase):
    def test_unityfs_version(self):
        with tempfile.TemporaryDirectory() as tmp:
            bundle = Path(tmp) / "data.unity3d"
            bundle.write_bytes(b"UnityFS\x00\x00\x00\x00\x085.x.x\x006000.3.24f1\x00")
            self.assertEqual(read_unity_version(bundle), "6000.3.24f1")


class HangarTests(unittest.TestCase):
    def test_refuses_without_write_flag_then_swaps_and_restores(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            game = root / "Broken Arrow"
            data = game / "BrokenArrow_Data"
            data.mkdir(parents=True)
            bundle = data / "data.unity3d"
            bundle.write_bytes(b"vanilla")
            dist = root / "dist" / "stable"
            dist.mkdir(parents=True)
            (dist / "data.unity3d").write_bytes(b"patched")
            marker = root / "launched.txt"
            script = root / "launch.py"
            script.write_text(
                f"from pathlib import Path\nPath({str(marker)!r}).write_text(Path({str(bundle)!r}).read_text())\n",
                encoding="utf-8",
            )

            from pipeline.config import Config

            cfg = Config(
                repo_root=root,
                game_root=game,
                cache_dir=root / "cache",
                dist_dir=root / "dist",
                constants_dir=root / "constants",
                manifest_path=root / "manifest.json",
                write_game_bundle=False,
                backup_dir=root / "backups",
                game_exe=Path(sys.executable),
                launch_args=(str(script),),
            )
            with self.assertRaises(PipelineError):
                run_hangar(cfg)

            cfg = Config(
                repo_root=cfg.repo_root,
                game_root=cfg.game_root,
                cache_dir=cfg.cache_dir,
                dist_dir=cfg.dist_dir,
                constants_dir=cfg.constants_dir,
                manifest_path=cfg.manifest_path,
                write_game_bundle=True,
                backup_dir=cfg.backup_dir,
                game_exe=cfg.game_exe,
                launch_args=cfg.launch_args,
            )
            code = run_hangar(cfg)
            self.assertEqual(code, 0)
            self.assertEqual(bundle.read_bytes(), b"vanilla")
            self.assertEqual(marker.read_text(encoding="utf-8"), "patched")
            self.assertTrue(any(cfg.backup_dir.glob("data.unity3d.*")))


class ManifestTests(unittest.TestCase):
    def test_write_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "mod" / "manifest.json"
            write_manifest(path, "6000.3.24f1-abc")
            self.assertEqual(json.loads(path.read_text(encoding="utf-8"))["build_id"], "6000.3.24f1-abc")


def _serialization_types() -> dict:
    field = {"access": "public", "static": False, "const": False, "serialized": True}
    return {
        "SerializationData": {
            "name": "SerializationData",
            "base": "ValueType",
            "own_generic": [],
            "base_args": [],
            "fields": [
                {**field, "type": "DataFormat", "name": "SerializedFormat"},
                {**field, "type": "byte[]", "name": "SerializedBytes"},
                {**field, "type": "List<Object>", "name": "ReferencedUnityObjects"},
                {**field, "type": "string", "name": "SerializedBytesString"},
                {**field, "type": "Object", "name": "Prefab"},
                {**field, "type": "List<Object>", "name": "PrefabModificationsReferencedUnityObjects"},
                {**field, "type": "List<string>", "name": "PrefabModifications"},
                {**field, "type": "List<SerializationNode>", "name": "SerializationNodes"},
            ],
        },
        "SerializationNode": {
            "name": "SerializationNode",
            "base": "ValueType",
            "own_generic": [],
            "base_args": [],
            "fields": [
                {**field, "type": "string", "name": "Name"},
                {**field, "type": "EntryType", "name": "Entry"},
                {**field, "type": "string", "name": "Data"},
            ],
        },
    }


def _serialization_data(fmt: int, payload: bytes = b"", nodes: list[tuple[str, int, str]] | None = None) -> bytes:
    buf = bytearray()
    buf += struct.pack("<i", fmt)
    buf += struct.pack("<i", len(payload))
    buf += payload
    while len(buf) % 4:
        buf += b"\x00"
    buf += struct.pack("<i", 0)
    buf += struct.pack("<i", 0)
    _pptr(buf, 0, 0)
    buf += struct.pack("<i", 0)
    buf += struct.pack("<i", 0)
    nodes = nodes or []
    buf += struct.pack("<i", len(nodes))
    for name, entry, data in nodes:
        _string(buf, name)
        buf += struct.pack("<i", entry)
        _string(buf, data)
    return bytes(buf)


def _mono(name: str, strings: list[str]) -> bytes:
    buf = bytearray()
    _pptr(buf, 0, 0)
    buf += struct.pack("<i", 1)
    _pptr(buf, 1, 42)
    _string(buf, name)
    for text in strings:
        _string(buf, text)
    return bytes(buf)


class SurveyTests(unittest.TestCase):
    def test_catalog_lists_encrypted_config_and_ignores_plain(self):
        payload = {"DamageModifier": 0.5, "PerSoldierPenalty": 0.02}
        wire = aes_encrypt(json.dumps(payload).encode("utf-8"))
        buildings = _mono("BuildingsConfig", [wire])
        plain = _mono("AudioSource", ["hello"])

        listed = catalog_monobehaviour(buildings)
        self.assertIsNotNone(listed)
        self.assertEqual(listed["m_name"], "BuildingsConfig")
        self.assertEqual(listed["script_file_id"], 1)
        self.assertEqual(listed["script_path_id"], 42)
        self.assertFalse(listed["typetree"])
        self.assertEqual(listed["byte_size"], len(buildings))
        self.assertEqual(listed["aes"][0]["keys"], ["DamageModifier", "PerSoldierPenalty"])
        self.assertEqual(listed["aes"][0]["json"], payload)
        self.assertNotIn("numeric_fields", listed)
        json.dumps(listed)

        self.assertIsNone(catalog_monobehaviour(plain))
        self.assertIsNone(catalog_monobehaviour(make_blob(sample_fields())))

    def test_name_without_numbers_records_the_script(self):
        listed = catalog_monobehaviour(_mono("ForestConcealment", []))
        self.assertEqual(listed["m_name"], "ForestConcealment")
        self.assertEqual(listed["numeric_fields"], "not in the blob")
        self.assertNotIn("aes", listed)
        self.assertEqual(listed["script_path_id"], 42)

    def test_typetree_values_are_kept_for_a_small_object(self):
        listed = catalog_monobehaviour(
            _mono("AudioSource", []),
            typetree={"forestViewDistance": 40, "volume": 1},
            typetree_present=True,
        )
        self.assertEqual(listed["field_matches"], [{"path": "forestViewDistance", "value": 40}])
        self.assertEqual(listed["fields"]["forestViewDistance"], 40)
        self.assertTrue(listed["typetree"])
        self.assertNotIn("numeric_fields", listed)

    def test_table_index_reports_stealth_and_skips_buffer(self):
        indexed = index_tables(
            {
                "Units": [
                    {"Id": 1, "Cost": 10, "Stealth": 1.0, "Buffer": 4},
                    {"Id": 2, "Cost": 20, "Stealth": 0.5, "Buffer": 4},
                    {"Id": 3, "Cost": 30, "Stealth": 1.0, "Buffer": 8},
                ]
            }
        )
        units = indexed[0]
        self.assertEqual(units["field"], "Units")
        self.assertEqual(units["file"], "units.json")
        self.assertEqual(units["rows"], 3)
        self.assertIn("Cost", units["keys"])
        keys = [item["key"] for item in units["matches"]]
        self.assertEqual(keys, ["Stealth"])
        stealth = units["matches"][0]
        self.assertEqual(stealth["distinct"], [1.0, 0.5])
        self.assertEqual(stealth["min"], 0.5)
        self.assertEqual(stealth["max"], 1.0)
        self.assertEqual(stealth["examples"][0], {"id": 1, "value": 1.0})


class Il2CppTests(unittest.TestCase):
    def test_cutter_keeps_cover_fields_and_matching_methods(self):
        extracted = extract_classes(
            "\n".join(
                [
                    "public class AudioSource // TypeDefIndex: 1",
                    "{",
                    "\t// Fields",
                    "\tpublic float volume; // 0x10",
                    "",
                    "\t// Methods",
                    "\t// RVA: 0x1",
                    "\tpublic void Play() { }",
                    "}",
                    "public class BuildingsConfig // TypeDefIndex: 2",
                    "{",
                    "\t// Fields",
                    "\tpublic float DamageModifier; // 0x18",
                    "\tpublic bool Enabled; // 0x1C",
                    "\tpublic static int Count; // 0x0",
                    "",
                    "\t// Methods",
                    "\tpublic void ApplyCover() { }",
                    "\tpublic void Update() { }",
                    "}",
                    "public class Combat // TypeDefIndex: 3",
                    "{",
                    "\tpublic void ForestStealth() { }",
                    "}",
                    "",
                ]
            )
        )
        buildings = extracted["classes"][0]
        self.assertEqual(buildings["name"], "BuildingsConfig")
        self.assertEqual(
            [(field["name"], field["type"], field["static"]) for field in buildings["fields"]],
            [("DamageModifier", "float", False), ("Enabled", "bool", False), ("Count", "int", True)],
        )
        self.assertEqual(buildings["methods"], ["public void ApplyCover()"])
        self.assertEqual(extracted["related_methods"], [{"class": "Combat", "signature": "public void ForestStealth()"}])

    def test_walker_round_trips_float_and_bool_and_rejects_a_short_read(self):
        fields = [
            {"access": "public", "static": False, "const": False, "type": "float", "name": "DamageModifier", "offset": "0x18"},
            {"access": "public", "static": False, "const": False, "type": "bool", "name": "Enabled", "offset": "0x1C"},
            {"access": "public", "static": True, "const": False, "type": "int", "name": "Count", "offset": "0x0"},
        ]
        raw = bytearray(_mono("BuildingsConfig", []))
        raw += struct.pack("<f", 0.5)
        raw += b"\x01\x00\x00\x00"
        values = decode_fields(bytes(raw), fields)
        self.assertEqual(values, {"DamageModifier": 0.5, "Enabled": True})
        self.assertIsNone(decode_fields(bytes(raw) + b"\x00\x00\x00\x00", fields))
        self.assertEqual(
            decode_fields(bytes(raw), fields, base="ScriptableObject"),
            {"DamageModifier": 0.5, "Enabled": True},
        )

    def test_serialized_object_reads_odin_block_before_its_own_float(self):
        fields = [
            {"access": "public", "static": False, "const": False, "type": "float", "name": "FontSize", "offset": "0x18"},
        ]
        raw = bytearray(_mono("FOWToolConfig", []))
        raw += _serialization_data(0)
        raw += struct.pack("<f", 1.5)
        values = decode_fields(bytes(raw), fields, types=_serialization_types(), base="SerializedScriptableObject")
        self.assertEqual(values["FontSize"], 1.5)
        self.assertEqual(values["serializationData"]["SerializedFormat"], 0)
        self.assertEqual(values["serializationData"]["SerializedBytes"], [])

    def test_hashset_between_floats_is_not_read_from_the_unity_cursor(self):
        fields = [
            {"access": "public", "static": False, "const": False, "type": "float", "name": "Before", "offset": "0x18"},
            {"access": "public", "static": False, "const": False, "type": "HashSet<int>", "name": "ShowWeaponRangesByRelation", "offset": "0x20"},
            {"access": "public", "static": False, "const": False, "type": "float", "name": "After", "offset": "0x28"},
        ]
        payload = b"ShowWeaponRangesByRelation"
        raw = bytearray(_mono("FOWToolConfig", []))
        raw += _serialization_data(0, payload)
        raw += struct.pack("<f", 1.0)
        raw += struct.pack("<f", 2.0)
        values = decode_fields(bytes(raw), fields, types=_serialization_types(), base="SerializedScriptableObject")
        self.assertEqual(values["Before"], 1.0)
        self.assertEqual(values["After"], 2.0)
        self.assertEqual(values["ShowWeaponRangesByRelation"], {"undecoded": True, "in_payload": True})

    def test_nodes_format_attaches_named_collection_entries(self):
        fields = [
            {"access": "public", "static": False, "const": False, "type": "HashSet<int>", "name": "LowHighAltRangeWeapons", "offset": "0x18"},
            {"access": "public", "static": False, "const": False, "type": "float", "name": "FontSize", "offset": "0x20"},
        ]
        raw = bytearray(_mono("FOWToolConfig", []))
        raw += _serialization_data(2, nodes=[("LowHighAltRangeWeapons", 3, "kept"), ("Other", 1, "no")])
        raw += struct.pack("<f", 14.0)
        values = decode_fields(
            bytes(raw),
            fields,
            enums={"EntryType": "int"},
            types=_serialization_types(),
            base="SerializedScriptableObject",
        )
        self.assertEqual(values["FontSize"], 14.0)
        self.assertEqual(
            values["LowHighAltRangeWeapons"],
            {"undecoded": True, "nodes": [{"Name": "LowHighAltRangeWeapons", "Entry": 3, "Data": "kept"}]},
        )

    def test_odin_binary_names_may_be_utf16(self):
        from pipeline.il2cpp import _note_odin_collections

        names = ("ShowWeaponRangesByRelation", "LowHighAltRangeWeapons")
        for encoding in ("utf-8", "utf-16-le"):
            with self.subTest(encoding=encoding):
                payload = b"\x01" + b"\x00".join(name.encode(encoding) for name in names)
                values = {"serializationData": {"SerializedFormat": 0, "SerializedBytes": list(payload)}}
                values.update({name: {"undecoded": True} for name in names})
                noted = _note_odin_collections(values)
                for name in names:
                    self.assertEqual(noted[name], {"undecoded": True, "in_payload": True})
        values["serializationData"]["SerializedBytes"] = []
        self.assertFalse(_note_odin_collections(values)[names[0]]["in_payload"])


class CliTests(unittest.TestCase):
    def test_help(self):
        completed = subprocess.run(
            [sys.executable, "-m", "pipeline", "--help"],
            cwd=REPO,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0)
        self.assertIn("discover", completed.stdout)
        self.assertIn("survey", completed.stdout)
        self.assertIn("il2cpp", completed.stdout)
        self.assertIn("hangar", completed.stdout)


if __name__ == "__main__":
    unittest.main()
