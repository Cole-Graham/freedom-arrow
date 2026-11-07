"""Weapons tab: overlay individual ammo DPM vs armor faces."""

from __future__ import annotations

import csv
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Any

from .calculations import card_range_text, hit_chance, interpolate_dpm, sample_dpm, shots_per_minute, time_to_kill_s
from .chart_panel import ChartPanel
from .constants import CARD_RANGE_MULTIPLIER, FACE_LINE_STYLES, FACES
from .ui_components import SearchableCombobox


def _id_from_label(label: str) -> int | None:
    if "[" not in label or not label.endswith("]"):
        return None
    try:
        return int(label[label.rfind("[") + 1 : -1])
    except ValueError:
        return None


class WeaponsTab:
    def __init__(self, parent: ttk.Frame, app):
        self.app = app
        self.rows: list[dict[str, Any]] = []
        self.weapon_names: list[str] = []
        self.armor_names: list[str] = []
        self.unit_names: list[str] = []
        self._pair_index: dict[str, tuple[int, int]] = {}
        self._series_meta: list[dict[str, Any]] = []
        self._silhouette: tuple[float, float] | None = None
        self._apply_accuracy = False
        self._ammo_extras: dict[str, Any] = {}
        self._is_loading_state = False
        self._build(parent)

    def _build(self, parent: ttk.Frame) -> None:
        pane = ttk.Panedwindow(parent, orient=tk.HORIZONTAL)
        pane.pack(fill=tk.BOTH, expand=True)
        left = ttk.Frame(pane, padding=6)
        right = ttk.Frame(pane, padding=6)
        pane.add(left, weight=1)
        pane.add(right, weight=3)

        ttk.Label(left, text="Weapons to compare").pack(anchor=tk.W)
        btns = ttk.Frame(left)
        btns.pack(fill=tk.X, pady=4)
        ttk.Button(btns, text="Add weapon", command=self._add_row_clicked).pack(side=tk.LEFT)
        ttk.Button(btns, text="Remove last", command=self._remove_row_clicked).pack(side=tk.LEFT, padx=4)
        self.rows_frame = ttk.Frame(left)
        self.rows_frame.pack(fill=tk.BOTH, expand=True)

        cfg = ttk.LabelFrame(left, text="Target", padding=6)
        cfg.pack(fill=tk.X, pady=6)
        ttk.Label(cfg, text="Armor").pack(anchor=tk.W)
        self.target_armor = SearchableCombobox(cfg, width=32)
        self.target_armor.pack(fill=tk.X)
        ttk.Label(cfg, text="Or unit (uses its size and default armor)").pack(anchor=tk.W, pady=(6, 0))
        self.target_unit = SearchableCombobox(cfg, width=32, on_select=lambda _v: self._touch())
        self.target_unit.pack(fill=tk.X)
        ttk.Label(cfg, text="Face").pack(anchor=tk.W, pady=(6, 0))
        self.face_var = tk.StringVar(value="Front")
        ttk.Combobox(cfg, textvariable=self.face_var, values=list(FACES), state="readonly", width=12).pack(anchor=tk.W)
        self.sweep_faces = tk.BooleanVar(value=False)
        ttk.Checkbutton(cfg, text="Sweep all four faces", variable=self.sweep_faces, command=self._touch).pack(anchor=tk.W)
        self.damage_type = tk.StringVar(value="Physical")
        ttk.Radiobutton(cfg, text="Physical", variable=self.damage_type, value="Physical").pack(anchor=tk.W)
        ttk.Radiobutton(cfg, text="Stress", variable=self.damage_type, value="Stress").pack(anchor=tk.W)
        self.assume_hits = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            cfg,
            text="Assume hits (ignore spread)",
            variable=self.assume_hits,
            command=self._touch,
        ).pack(anchor=tk.W)
        self.log_scale = tk.BooleanVar(value=False)
        ttk.Checkbutton(cfg, text="Log DPM scale", variable=self.log_scale, command=self._touch).pack(anchor=tk.W)

        actions = ttk.Frame(left)
        actions.pack(fill=tk.X, pady=6)
        ttk.Button(actions, text="Generate chart", command=self._generate_clicked).pack(fill=tk.X)
        ttk.Button(actions, text="Export PNG", command=self.export_png).pack(fill=tk.X, pady=2)
        ttk.Button(actions, text="Export CSV", command=self.export_csv).pack(fill=tk.X)

        self.chart = ChartPanel(right, "Weapon DPM vs range", self._on_pin_and_save)
        self.info = tk.Text(right, height=12, wrap=tk.WORD)
        self.info.pack(fill=tk.BOTH, expand=False, pady=(6, 0))

        custom = ttk.LabelFrame(parent, text="Custom weapon", padding=6)
        custom.pack(fill=tk.X, padx=6, pady=6)
        top = ttk.Frame(custom)
        top.pack(fill=tk.X)
        ttk.Label(top, text="Load").pack(side=tk.LEFT)
        self.load_existing = SearchableCombobox(top, width=36, on_select=self._fill_from_existing)
        self.load_existing.pack(side=tk.LEFT, padx=4)
        ttk.Label(top, text="Name").pack(side=tk.LEFT)
        self.custom_name = ttk.Entry(top, width=18)
        self.custom_name.pack(side=tk.LEFT, padx=4)
        grid = ttk.Frame(custom)
        grid.pack(fill=tk.X, pady=4)
        self.fields: dict[str, ttk.Entry] = {}
        specs = [
            ("Damage", "damage"),
            ("Stress", "stress"),
            ("Pen min", "pen_min"),
            ("Pen ground", "pen_ground"),
            ("Min range", "min_range"),
            ("Ground range", "ground_range"),
            ("Mag", "mag"),
            ("Reload min", "reload_min"),
            ("Reload max", "reload_max"),
            ("Burst min", "burst_min"),
            ("Burst max", "burst_max"),
            ("Between bursts min", "burst_gap_min"),
            ("Between bursts max", "burst_gap_max"),
            ("Shot gap", "shot_gap"),
        ]
        for index, (caption, key) in enumerate(specs):
            ttk.Label(grid, text=caption).grid(row=index // 4, column=(index % 4) * 2, sticky=tk.W, padx=2)
            entry = ttk.Entry(grid, width=8)
            entry.grid(row=index // 4, column=(index % 4) * 2 + 1, padx=2, pady=1)
            self.fields[key] = entry
        self.targeted = tk.StringVar(value="1")
        ttk.Label(grid, text="ArmorTargeted").grid(row=4, column=0, sticky=tk.W)
        ttk.Combobox(grid, textvariable=self.targeted, values=["0", "1", "2"], width=6, state="readonly").grid(
            row=4, column=1, sticky=tk.W
        )
        ttk.Button(custom, text="Create / edit custom weapon", command=self.save_custom_weapon).pack(anchor=tk.W)
        self.preview = ttk.Label(custom, text="Live preview: load a weapon")
        self.preview.pack(anchor=tk.W, pady=4)
        self.add_row()
        self.face_var.trace_add("write", lambda *_: self._touch())
        self.damage_type.trace_add("write", lambda *_: self._touch())
        self.target_armor.on_select = lambda _v: self._touch()

    def _touch(self) -> None:
        if not self._is_loading_state:
            self.app.auto_save_state()

    def _add_row_clicked(self) -> None:
        self.add_row()
        self._touch()

    def _remove_row_clicked(self) -> None:
        self.remove_row()
        self._touch()

    def _generate_clicked(self) -> None:
        self.generate()
        self._touch()

    def refresh_lists(self) -> None:
        catalog = self.app.catalog
        if catalog is None:
            return
        pairs = catalog.weapon_ammo_labels()
        self._pair_index = {label: (weapon_id, ammo_id) for label, weapon_id, ammo_id in pairs}
        self.weapon_names = [label for label, _, _ in pairs]
        self.weapon_names.extend(sorted(self.app.custom_weapons))
        self.armor_names = [label for label, _ in catalog.armor_labels()]
        self.unit_names = [catalog.unit_label(uid) for uid in catalog.playable_units()]
        self.unit_names.extend(sorted(self.app.custom_units))
        for row in self.rows:
            row["weapon"].set_values(self.weapon_names)
        self.target_armor.set_values(self.armor_names)
        self.target_unit.set_values(self.unit_names)
        self.load_existing.set_values([label for label, _, _ in pairs])
        if self.weapon_names and not self.rows[0]["weapon"].get():
            self.rows[0]["weapon"].set(self.weapon_names[0])
        if self.armor_names and not self.target_armor.get():
            self.target_armor.set(self.armor_names[0])

    def add_row(self) -> None:
        frame = ttk.Frame(self.rows_frame)
        frame.pack(fill=tk.X, pady=2)
        visible = tk.BooleanVar(value=True)
        ttk.Checkbutton(frame, variable=visible, command=self._touch).pack(side=tk.LEFT)
        weapon = SearchableCombobox(frame, values=self.weapon_names, width=40, on_select=lambda _v: self._touch())
        weapon.pack(side=tk.LEFT, fill=tk.X, expand=True)
        qty = tk.IntVar(value=1)
        ttk.Spinbox(frame, from_=1, to=10, textvariable=qty, width=4).pack(side=tk.LEFT, padx=4)
        qty.trace_add("write", lambda *_: self._touch())
        self.rows.append({"frame": frame, "visible": visible, "weapon": weapon, "qty": qty})

    def remove_row(self) -> None:
        if len(self.rows) <= 1:
            return
        row = self.rows.pop()
        row["frame"].destroy()

    def _resolve_pair(self, label: str) -> tuple[dict[str, Any], dict[str, Any], str]:
        catalog = self.app.catalog
        assert catalog is not None
        if label in self.app.custom_weapons:
            custom = self.app.custom_weapons[label]
            return custom["weapon"], custom["ammo"], label
        pair = self._pair_index.get(label)
        if not pair:
            raise ValueError(f"Unknown weapon {label}")
        weapon_id, ammo_id = pair
        return catalog.weapons[weapon_id], catalog.ammos[ammo_id], label

    def _resolve_armor(self) -> dict[str, Any]:
        catalog = self.app.catalog
        assert catalog is not None
        unit_label = self.target_unit.get().strip()
        if unit_label in self.app.custom_units:
            return self.app.custom_units[unit_label]["armor"]
        unit_id = _id_from_label(unit_label)
        if unit_id and unit_id in catalog.default_armor:
            return catalog.armors[catalog.default_armor[unit_id]]
        armor_id = _id_from_label(self.target_armor.get())
        if armor_id is None or armor_id not in catalog.armors:
            raise ValueError("Pick a target armor or unit.")
        return catalog.armors[armor_id]

    def _resolve_silhouette(self) -> tuple[float, float] | None:
        catalog = self.app.catalog
        assert catalog is not None
        unit_label = self.target_unit.get().strip()
        if unit_label in self.app.custom_units:
            return catalog.silhouette(self.app.custom_units[unit_label]["source_unit_id"])
        unit_id = _id_from_label(unit_label)
        if unit_id:
            return catalog.silhouette(unit_id)
        armor_id = _id_from_label(self.target_armor.get())
        if armor_id is None:
            return None
        return catalog.silhouette_for_armor(armor_id)

    def generate(self) -> None:
        if self.app.catalog is None:
            messagebox.showinfo("DPM", "Load a vanilla snapshot first.")
            return
        try:
            armor = self._resolve_armor()
        except ValueError as exc:
            messagebox.showerror("DPM", str(exc))
            return
        faces = list(FACES) if self.sweep_faces.get() else [self.face_var.get()]
        damage_type = self.damage_type.get()
        apply_accuracy = not self.assume_hits.get()
        silhouette = self._resolve_silhouette() if apply_accuracy else None
        plotted = []
        self._series_meta = []
        self._silhouette = silhouette
        self._apply_accuracy = apply_accuracy
        for row in self.rows:
            if not row["visible"].get() or not row["weapon"].get():
                continue
            try:
                weapon, ammo, label = self._resolve_pair(row["weapon"].get())
            except ValueError:
                continue
            qty = max(1, int(row["qty"].get()))
            for face in faces:
                series = sample_dpm(
                    weapon,
                    ammo,
                    armor,
                    face,
                    qty,
                    damage_type,
                    silhouette=silhouette,
                    apply_accuracy=apply_accuracy,
                )
                name = label if len(faces) == 1 else f"{label} / {face}"
                plotted.append((name, series, FACE_LINE_STYLES.get(face, "-")))
                self._series_meta.append(
                    {
                        "label": name,
                        "series": series,
                        "weapon": weapon,
                        "ammo": ammo,
                        "qty": qty,
                        "face": face,
                        "hp": float(armor.get("MaxHealthPoints") or 0),
                    }
                )
        ylabel = "Expected DPM" if apply_accuracy else "DPM if hits"
        target_name = self.target_unit.get().strip() or self.target_armor.get()
        title = f"Weapon DPM vs {target_name}"
        self.chart.draw(plotted, self.log_scale.get(), ylabel, title)
        if self.chart.selected_range is not None:
            self._on_pin(self.chart.selected_range)
        self._update_preview()

    def _on_pin_and_save(self, card: float | None) -> None:
        self._on_pin(card)
        self._touch()

    def _on_pin(self, card: float | None) -> None:
        self.info.delete("1.0", tk.END)
        if card is None:
            self.info.insert(tk.END, "Click the chart to pin a range.")
            return
        world = card / CARD_RANGE_MULTIPLIER
        lines = [f"Pinned {card:.0f} card m ({world:.0f} world m)\n"]
        ranked = sorted(self._series_meta, key=lambda meta: interpolate_dpm(meta["series"], card), reverse=True)
        for meta in ranked:
            dpm = interpolate_dpm(meta["series"], card)
            ttk_s = time_to_kill_s(meta["hp"], dpm)
            ttk_txt = f"{ttk_s:.1f}s TTK" if ttk_s is not None else "no TTK"
            ammo = meta["ammo"]
            weapon = meta["weapon"]
            spm = shots_per_minute(weapon, meta["qty"])
            chance = hit_chance(ammo, world, self._silhouette)
            hit_txt = f"  hit {chance:.0%}" if self._apply_accuracy else ""
            range_txt = card_range_text(ammo)
            range_line = f"  {range_txt}\n" if range_txt else ""
            lines.append(
                f"\n{meta['label']}\n"
                f"  DPM {dpm:.1f}  {ttk_txt}  face {meta['face']}{hit_txt}\n"
                f"{range_line}"
                f"  dmg {ammo.get('Damage')}  stress {ammo.get('StressDamage')}  "
                f"pen {ammo.get('PenetrationAtMinRange')}→{ammo.get('PenetrationAtGroundRange')}\n"
                f"  shots/min {spm:.1f}  mag {weapon.get('MagazineSize')}  "
                f"reload {weapon.get('MagazineReloadTimeMin')}-{weapon.get('MagazineReloadTimeMax')}s"
            )
        self.info.insert(tk.END, "\n".join(lines))

    def export_png(self) -> None:
        path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG", "*.png")])
        if path:
            self.chart.fig.savefig(path, dpi=120)

    def export_csv(self) -> None:
        if not self._series_meta:
            messagebox.showinfo("DPM", "Generate a chart first.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
        if not path:
            return
        with open(path, "w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(["Range (card m)", "Weapon", "Face", "DPM"])
            for meta in self._series_meta:
                for card, dpm in meta["series"]:
                    writer.writerow([card, meta["label"], meta["face"], f"{dpm:.4f}"])

    def _fill_from_existing(self, label: str) -> None:
        catalog = self.app.catalog
        if catalog is None:
            return
        pair = self._pair_index.get(label)
        if not pair:
            return
        weapon_id, ammo_id = pair
        weapon = catalog.weapons[weapon_id]
        ammo = catalog.ammos[ammo_id]
        mapping = {
            "damage": ammo.get("Damage"),
            "stress": ammo.get("StressDamage"),
            "pen_min": ammo.get("PenetrationAtMinRange"),
            "pen_ground": ammo.get("PenetrationAtGroundRange"),
            "min_range": ammo.get("MinimalRange"),
            "ground_range": ammo.get("GroundRange"),
            "mag": weapon.get("MagazineSize"),
            "reload_min": weapon.get("MagazineReloadTimeMin"),
            "reload_max": weapon.get("MagazineReloadTimeMax"),
            "burst_min": weapon.get("ShotsPerBurstMin"),
            "burst_max": weapon.get("ShotsPerBurstMax"),
            "burst_gap_min": weapon.get("TimeBetweenBurstsMin"),
            "burst_gap_max": weapon.get("TimeBetweenBurstsMax"),
            "shot_gap": weapon.get("TimeBetweenShotsInBurst"),
        }
        self._ammo_extras = {
            "DispersionHorizontalRadius": ammo.get("DispersionHorizontalRadius") or 0,
            "DispersionVerticalRadius": ammo.get("DispersionVerticalRadius") or 0,
            "DispersionMinimal": ammo.get("DispersionMinimal") or 0,
            "Seeker": ammo.get("Seeker") or 0,
        }
        for key, value in mapping.items():
            self.fields[key].delete(0, tk.END)
            self.fields[key].insert(0, str(value))
        self.targeted.set(str(int(ammo.get("ArmorTargeted") or 1)))
        if not self.custom_name.get().strip():
            self.custom_name.insert(0, f"{ammo.get('HUDName')} custom")
        self._update_preview()

    def _float(self, key: str, default: float = 0.0) -> float:
        raw = self.fields[key].get().strip()
        if not raw:
            return default
        return float(raw)

    def _custom_dicts(self) -> tuple[dict[str, Any], dict[str, Any]]:
        weapon = {
            "HUDName": self.custom_name.get().strip() or "Custom",
            "MagazineSize": self._float("mag", 1),
            "MagazineReloadTimeMin": self._float("reload_min"),
            "MagazineReloadTimeMax": self._float("reload_max"),
            "ShotsPerBurstMin": self._float("burst_min", 1),
            "ShotsPerBurstMax": self._float("burst_max", 1),
            "TimeBetweenBurstsMin": self._float("burst_gap_min"),
            "TimeBetweenBurstsMax": self._float("burst_gap_max"),
            "TimeBetweenShotsInBurst": self._float("shot_gap"),
        }
        ammo = {
            "HUDName": weapon["HUDName"],
            "Damage": self._float("damage"),
            "StressDamage": self._float("stress"),
            "PenetrationAtMinRange": self._float("pen_min"),
            "PenetrationAtGroundRange": self._float("pen_ground"),
            "MinimalRange": self._float("min_range"),
            "GroundRange": self._float("ground_range"),
            "ArmorTargeted": int(self.targeted.get() or 1),
        }
        ammo.update(self._ammo_extras)
        return weapon, ammo

    def _update_preview(self) -> None:
        try:
            weapon, ammo = self._custom_dicts()
            armor = self._resolve_armor() if self.app.catalog else {"ArmorValue": 0, "KinArmorFront": 0, "HeatArmorFront": 0, "MaxHealthPoints": 14}
            face = self.face_var.get()
            ground = float(ammo.get("GroundRange") or 0)
            dpm = 0.0
            if ground > 0:
                from .calculations import dpm_at_world

                dpm = dpm_at_world(
                    weapon,
                    ammo,
                    armor,
                    ground,
                    face,
                    1,
                    self.damage_type.get(),
                    silhouette=self._resolve_silhouette() if self.app.catalog and not self.assume_hits.get() else None,
                    apply_accuracy=not self.assume_hits.get(),
                )
            spm = shots_per_minute(weapon, 1)
            self.preview.config(text=f"Live preview at max range: DPM {dpm:.1f}  shots/min {spm:.1f}")
        except (ValueError, KeyError):
            self.preview.config(text="Live preview: fill the fields")

    def save_custom_weapon(self) -> None:
        name = self.custom_name.get().strip()
        if not name:
            messagebox.showerror("DPM", "Name the custom weapon.")
            return
        try:
            weapon, ammo = self._custom_dicts()
        except ValueError:
            messagebox.showerror("DPM", "Numeric fields must be numbers.")
            return
        key = f"[custom] {name}"
        self.app.custom_weapons[key] = {"weapon": weapon, "ammo": ammo}
        self.app.save_user_data()
        self.refresh_lists()
        self._update_preview()
        messagebox.showinfo("DPM", f"Saved {key}")

    def save_tab_state(self) -> dict[str, Any]:
        return {
            "rows": [
                {
                    "weapon": row["weapon"].get(),
                    "qty": int(row["qty"].get()),
                    "visible": bool(row["visible"].get()),
                }
                for row in self.rows
            ],
            "target_armor": self.target_armor.get(),
            "target_unit": self.target_unit.get(),
            "face": self.face_var.get(),
            "sweep_faces": bool(self.sweep_faces.get()),
            "damage_type": self.damage_type.get(),
            "assume_hits": bool(self.assume_hits.get()),
            "log_scale": bool(self.log_scale.get()),
            "pinned_range": self.chart.selected_range,
        }

    def load_tab_state(self, state: dict[str, Any] | None) -> None:
        if not state:
            return
        self._is_loading_state = True
        try:
            if state.get("face"):
                self.face_var.set(state["face"])
            if state.get("damage_type"):
                self.damage_type.set(state["damage_type"])
            if "sweep_faces" in state:
                self.sweep_faces.set(bool(state["sweep_faces"]))
            if "assume_hits" in state:
                self.assume_hits.set(bool(state["assume_hits"]))
            if "log_scale" in state:
                self.log_scale.set(bool(state["log_scale"]))
            if state.get("target_armor"):
                self.target_armor.set(state["target_armor"])
            if "target_unit" in state:
                self.target_unit.set(state.get("target_unit") or "")
            rows = state.get("rows") or []
            while len(self.rows) < len(rows):
                self.add_row()
            while len(rows) and len(self.rows) > len(rows):
                self.remove_row()
            known = set(self.weapon_names) | set(self.app.custom_weapons)
            for row, saved in zip(self.rows, rows):
                weapon = saved.get("weapon") or ""
                if weapon and weapon in known:
                    row["weapon"].set(weapon)
                row["visible"].set(bool(saved.get("visible", True)))
                if saved.get("qty") is not None:
                    try:
                        row["qty"].set(int(saved["qty"]))
                    except (tk.TclError, ValueError):
                        pass
            self.chart.selected_range = state.get("pinned_range")
            if self.app.catalog and any(row["weapon"].get() for row in self.rows):
                self.generate()
        finally:
            self._is_loading_state = False
