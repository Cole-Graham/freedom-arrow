"""Units tab: overlay squad/vehicle DPM vs a chosen armor face."""

from __future__ import annotations

import csv
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Any

from .calculations import card_range_text, hit_chance, interpolate_dpm, sample_dpm, sum_series, time_to_kill_s
from .chart_panel import ChartPanel
from .constants import CARD_RANGE_MULTIPLIER, FACES
from .ui_components import SearchableCombobox


def _id_from_label(label: str) -> int | None:
    if "[" not in label or not label.endswith("]"):
        return None
    try:
        return int(label[label.rfind("[") + 1 : -1])
    except ValueError:
        return None


class UnitsTab:
    def __init__(self, parent: ttk.Frame, app):
        self.app = app
        self.rows: list[dict[str, Any]] = []
        self.unit_names: list[str] = []
        self.armor_names: list[str] = []
        self._series_meta: list[dict[str, Any]] = []
        self._silhouette: tuple[float, float] | None = None
        self._apply_accuracy = False
        self._is_loading_state = False
        self._build(parent)

    def _build(self, parent: ttk.Frame) -> None:
        pane = ttk.Panedwindow(parent, orient=tk.HORIZONTAL)
        pane.pack(fill=tk.BOTH, expand=True)
        left = ttk.Frame(pane, padding=6)
        right = ttk.Frame(pane, padding=6)
        pane.add(left, weight=1)
        pane.add(right, weight=3)

        ttk.Label(left, text="Units to compare").pack(anchor=tk.W)
        btns = ttk.Frame(left)
        btns.pack(fill=tk.X, pady=4)
        ttk.Button(btns, text="Add unit", command=self._add_row_clicked).pack(side=tk.LEFT)
        ttk.Button(btns, text="Remove last", command=self._remove_row_clicked).pack(side=tk.LEFT, padx=4)
        self.duel_var = tk.BooleanVar(value=False)
        self.duel_check = ttk.Checkbutton(
            left,
            text="Each vs the other's armor",
            variable=self.duel_var,
            command=self._touch,
        )
        self.duel_check.pack(anchor=tk.W, pady=(0, 2))
        self.rows_frame = ttk.Frame(left)
        self.rows_frame.pack(fill=tk.BOTH, expand=True)

        target = ttk.LabelFrame(left, text="Target", padding=6)
        target.pack(fill=tk.X, pady=6)
        ttk.Label(target, text="Armor").pack(anchor=tk.W)
        self.target_armor = SearchableCombobox(target, width=32, on_select=lambda _v: self._touch())
        self.target_armor.pack(fill=tk.X)
        ttk.Label(target, text="Or unit (uses its default armor)").pack(anchor=tk.W, pady=(6, 0))
        self.target_unit = SearchableCombobox(target, width=32, on_select=lambda _v: self._touch())
        self.target_unit.pack(fill=tk.X)
        ttk.Label(target, text="Face").pack(anchor=tk.W, pady=(6, 0))
        self.face_var = tk.StringVar(value="Front")
        ttk.Combobox(target, textvariable=self.face_var, values=list(FACES), state="readonly", width=12).pack(anchor=tk.W)
        self.damage_type = tk.StringVar(value="Physical")
        ttk.Radiobutton(target, text="Physical", variable=self.damage_type, value="Physical").pack(anchor=tk.W)
        ttk.Radiobutton(target, text="Stress", variable=self.damage_type, value="Stress").pack(anchor=tk.W)
        self.ammo_pref = tk.StringVar(value="Default")
        ttk.Label(target, text="Ammo").pack(anchor=tk.W, pady=(6, 0))
        ttk.Combobox(
            target,
            textvariable=self.ammo_pref,
            values=["Default", "Kinetic", "HEAT"],
            state="readonly",
            width=12,
        ).pack(anchor=tk.W)
        self.include_upgrade = tk.BooleanVar(value=False)
        ttk.Checkbutton(target, text="Include non-default weapons", variable=self.include_upgrade, command=self._touch).pack(anchor=tk.W)
        self.normalize = tk.BooleanVar(value=False)
        ttk.Checkbutton(target, text="Normalize by cost", variable=self.normalize, command=self._touch).pack(anchor=tk.W)
        self.assume_hits = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            target,
            text="Assume hits (ignore spread)",
            variable=self.assume_hits,
            command=self._touch,
        ).pack(anchor=tk.W)
        self.log_scale = tk.BooleanVar(value=False)
        ttk.Checkbutton(target, text="Log DPM scale", variable=self.log_scale, command=self._touch).pack(anchor=tk.W)

        actions = ttk.Frame(left)
        actions.pack(fill=tk.X, pady=6)
        ttk.Button(actions, text="Generate chart", command=self._generate_clicked).pack(fill=tk.X)
        ttk.Button(actions, text="Export PNG", command=self.export_png).pack(fill=tk.X, pady=2)
        ttk.Button(actions, text="Export CSV", command=self.export_csv).pack(fill=tk.X)

        self.chart = ChartPanel(right, "Unit DPM vs range", self._on_pin_and_save)
        self.info = tk.Text(right, height=12, wrap=tk.WORD)
        self.info.pack(fill=tk.BOTH, expand=False, pady=(6, 0))

        custom = ttk.LabelFrame(parent, text="Custom unit (clone armor / cost)", padding=6)
        custom.pack(fill=tk.X, padx=6, pady=6)
        row = ttk.Frame(custom)
        row.pack(fill=tk.X)
        ttk.Label(row, text="From").pack(side=tk.LEFT)
        self.clone_from = SearchableCombobox(row, width=28)
        self.clone_from.pack(side=tk.LEFT, padx=4)
        ttk.Label(row, text="Name").pack(side=tk.LEFT)
        self.clone_name = ttk.Entry(row, width=18)
        self.clone_name.pack(side=tk.LEFT, padx=4)
        ttk.Label(row, text="Cost").pack(side=tk.LEFT)
        self.clone_cost = ttk.Spinbox(row, from_=1, to=2000, increment=5, width=6)
        self.clone_cost.pack(side=tk.LEFT, padx=4)
        ttk.Label(row, text="HP").pack(side=tk.LEFT)
        self.clone_hp = ttk.Spinbox(row, from_=1, to=200, increment=1, width=5)
        self.clone_hp.pack(side=tk.LEFT, padx=4)
        ttk.Button(row, text="Create", command=self.create_custom_unit).pack(side=tk.LEFT, padx=6)

        self.add_row()
        self._update_duel_enabled()
        self.face_var.trace_add("write", lambda *_: self._touch())
        self.damage_type.trace_add("write", lambda *_: self._touch())
        self.ammo_pref.trace_add("write", lambda *_: self._touch())

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
        self.unit_names = [catalog.unit_label(uid) for uid in catalog.playable_units()]
        self.unit_names.extend(sorted(self.app.custom_units))
        self.armor_names = [label for label, _ in catalog.armor_labels()]
        for row in self.rows:
            row["unit"].set_values(self.unit_names)
        self.target_unit.set_values(self.unit_names)
        self.target_armor.set_values(self.armor_names)
        self.clone_from.set_values(self.unit_names)
        if self.unit_names and not self.rows[0]["unit"].get():
            self.rows[0]["unit"].set(self.unit_names[0])
            self._on_unit_changed(self.rows[0])
        if self.armor_names and not self.target_armor.get():
            self.target_armor.set(self.armor_names[0])

    def add_row(self) -> None:
        frame = ttk.Frame(self.rows_frame)
        frame.pack(fill=tk.X, pady=2)
        visible = tk.BooleanVar(value=True)
        ttk.Checkbutton(frame, variable=visible, command=self._on_row_changed).pack(side=tk.LEFT)
        unit = SearchableCombobox(frame, values=self.unit_names, width=26, on_select=lambda _v: self._sync_row(frame))
        unit.pack(side=tk.LEFT, fill=tk.X, expand=True)
        armor = SearchableCombobox(frame, width=22, on_select=lambda _v: self._touch())
        armor.pack(side=tk.LEFT, padx=4)
        cost = tk.IntVar(value=100)
        ttk.Spinbox(frame, from_=1, to=2000, increment=5, textvariable=cost, width=6).pack(side=tk.LEFT)
        row = {"frame": frame, "visible": visible, "unit": unit, "armor": armor, "cost": cost}
        unit.entry.bind("<FocusOut>", lambda _e, r=row: self._on_unit_changed(r))
        cost.trace_add("write", lambda *_: self._touch())
        self.rows.append(row)
        if not self._is_loading_state:
            self._update_duel_enabled()

    def _on_row_changed(self) -> None:
        self._update_duel_enabled()
        self._touch()

    def _visible_compare_rows(self) -> list[dict[str, Any]]:
        return [row for row in self.rows if row["visible"].get() and row["unit"].get().strip()]

    def _update_duel_enabled(self) -> None:
        can_duel = len(self._visible_compare_rows()) == 2
        self.duel_check.configure(state=tk.NORMAL if can_duel else tk.DISABLED)
        if not can_duel and self.duel_var.get():
            self.duel_var.set(False)

    def _sync_row(self, frame: ttk.Frame) -> None:
        for row in self.rows:
            if row["frame"] is frame:
                self._on_unit_changed(row)

    def remove_row(self) -> None:
        if len(self.rows) <= 1:
            return
        row = self.rows.pop()
        row["frame"].destroy()
        if not self._is_loading_state:
            self._update_duel_enabled()

    def _on_unit_changed(self, row: dict[str, Any], restore: bool = False) -> None:
        catalog = self.app.catalog
        label = row["unit"].get()
        if catalog is None:
            return
        if label in self.app.custom_units:
            custom = self.app.custom_units[label]
            armor_label = custom.get("armor_label") or "Custom armor"
            row["armor"].set_values([armor_label])
            if not restore:
                row["cost"].set(int(custom.get("cost") or 1))
                row["armor"].set(armor_label)
            self._update_duel_enabled()
            self._touch()
            return
        unit_id = _id_from_label(label)
        if unit_id is None or unit_id not in catalog.units:
            self._update_duel_enabled()
            return
        options = catalog.armor_options(unit_id)
        labels = [opt.label for opt in options] or ["Default"]
        row["armor"].set_values(labels)
        if not restore:
            row["cost"].set(int(catalog.units[unit_id].get("Cost") or 0))
            if labels:
                row["armor"].set(labels[0])
        self._update_duel_enabled()
        self._touch()

    def _resolve_armor(self):
        catalog = self.app.catalog
        assert catalog is not None
        unit_label = self.target_unit.get().strip()
        if unit_label in self.app.custom_units:
            return self.app.custom_units[unit_label]["armor"]
        unit_id = _id_from_label(unit_label)
        if unit_id and unit_id in catalog.default_armor:
            return catalog.armors[catalog.default_armor[unit_id]]
        armor_id = _id_from_label(self.target_armor.get())
        if armor_id and armor_id in catalog.armors:
            return catalog.armors[armor_id]
        raise ValueError("Pick a target armor or unit.")

    def _row_armor(self, row: dict[str, Any]) -> dict[str, Any]:
        catalog = self.app.catalog
        assert catalog is not None
        label = row["unit"].get().strip()
        if label in self.app.custom_units:
            return self.app.custom_units[label]["armor"]
        armor_id = _id_from_label(row["armor"].get())
        if armor_id and armor_id in catalog.armors:
            return catalog.armors[armor_id]
        unit_id = _id_from_label(label)
        if unit_id and unit_id in catalog.default_armor:
            return catalog.armors[catalog.default_armor[unit_id]]
        raise ValueError(f"Pick armor for {label or 'this unit'}.")

    def _row_silhouette(self, row: dict[str, Any]) -> tuple[float, float] | None:
        catalog = self.app.catalog
        assert catalog is not None
        label = row["unit"].get().strip()
        if label in self.app.custom_units:
            return catalog.silhouette(self.app.custom_units[label]["source_unit_id"])
        unit_id = _id_from_label(label)
        if unit_id:
            return catalog.silhouette(unit_id)
        return None

    def _row_display_name(self, row: dict[str, Any]) -> str:
        catalog = self.app.catalog
        assert catalog is not None
        label = row["unit"].get().strip()
        if label in self.app.custom_units:
            return label
        unit_id = _id_from_label(label)
        if unit_id:
            return catalog.unit_label(unit_id)
        return label

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
        if armor_id:
            return catalog.silhouette_for_armor(armor_id)
        return None

    def _row_series(
        self,
        row: dict[str, Any],
        armor: dict[str, Any],
        face: str,
        damage_type: str,
        silhouette: tuple[float, float] | None,
        apply_accuracy: bool,
    ):
        catalog = self.app.catalog
        assert catalog is not None
        label = row["unit"].get()
        preference = self.ammo_pref.get()
        parts = []
        weapons_meta = []
        if label in self.app.custom_units:
            custom = self.app.custom_units[label]
            source_id = custom["source_unit_id"]
            mounted = catalog.dpm_weapons(source_id, include_upgrade=self.include_upgrade.get())
            display = label
        else:
            unit_id = _id_from_label(label)
            if unit_id is None:
                return None
            mounted = catalog.dpm_weapons(unit_id, include_upgrade=self.include_upgrade.get())
            display = catalog.unit_label(unit_id)
            source_id = unit_id
        for item in mounted:
            if not item.default and not self.include_upgrade.get():
                continue
            choice = catalog.pick_ammo(item, preference)
            if choice is None:
                continue
            weapon = catalog.weapons[item.weapon_id]
            ammo = catalog.ammos[choice.ammunition_id]
            series = sample_dpm(
                weapon,
                ammo,
                armor,
                face,
                item.gun_count,
                damage_type,
                silhouette=silhouette,
                apply_accuracy=apply_accuracy,
            )
            parts.append(series)
            weapons_meta.append(
                {
                    "weapon": weapon,
                    "ammo": ammo,
                    "gun_count": item.gun_count,
                    "carried": choice.quantity,
                    "series": series,
                }
            )
        if not parts:
            return None
        total = sum_series(parts)
        cost = max(1, int(row["cost"].get()))
        if self.normalize.get():
            total = [(card, dpm / cost) for card, dpm in total]
        return {
            "label": display,
            "series": total,
            "cost": cost,
            "hp": float(armor.get("MaxHealthPoints") or 0),
            "weapons": weapons_meta,
            "source_id": source_id,
            "silhouette": silhouette,
            "versus": None,
        }

    def generate(self) -> None:
        if self.app.catalog is None:
            messagebox.showinfo("DPM", "Load a vanilla snapshot first.")
            return
        self._update_duel_enabled()
        face = self.face_var.get()
        damage_type = self.damage_type.get()
        apply_accuracy = not self.assume_hits.get()
        active = self._visible_compare_rows()
        duel = bool(self.duel_var.get()) and len(active) == 2
        plotted = []
        self._series_meta = []
        self._apply_accuracy = apply_accuracy
        try:
            if duel:
                left, right = active
                pairs = (
                    (left, right),
                    (right, left),
                )
                for shooter, target in pairs:
                    armor = self._row_armor(target)
                    silhouette = self._row_silhouette(target) if apply_accuracy else None
                    meta = self._row_series(
                        shooter,
                        armor,
                        face,
                        damage_type,
                        silhouette,
                        apply_accuracy,
                    )
                    if not meta:
                        continue
                    meta["versus"] = self._row_display_name(target)
                    plotted.append((meta["label"], meta["series"], "-"))
                    self._series_meta.append(meta)
                self._silhouette = None
            else:
                armor = self._resolve_armor()
                silhouette = self._resolve_silhouette() if apply_accuracy else None
                self._silhouette = silhouette
                for row in active:
                    meta = self._row_series(
                        row,
                        armor,
                        face,
                        damage_type,
                        silhouette,
                        apply_accuracy,
                    )
                    if not meta:
                        continue
                    plotted.append((meta["label"], meta["series"], "-"))
                    self._series_meta.append(meta)
        except ValueError as exc:
            messagebox.showerror("DPM", str(exc))
            return
        if self.normalize.get():
            ylabel = "DPM / cost"
        elif apply_accuracy:
            ylabel = "Expected DPM"
        else:
            ylabel = "DPM if hits"
        title = f"Unit DPM duel vs {face} ({damage_type})" if duel else f"Unit DPM vs {face} ({damage_type})"
        self.chart.draw(plotted, self.log_scale.get(), ylabel, title)
        if self.chart.selected_range is not None:
            self._on_pin(self.chart.selected_range)

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
        ranked = []
        for meta in self._series_meta:
            dpm = interpolate_dpm(meta["series"], card)
            ranked.append((dpm, meta))
        ranked.sort(key=lambda item: item[0], reverse=True)
        for dpm, meta in ranked:
            ttk_s = time_to_kill_s(meta["hp"], dpm if not self.normalize.get() else dpm * meta["cost"])
            ttk_txt = f"{ttk_s:.1f}s TTK" if ttk_s is not None else "no TTK"
            versus = f"  vs {meta['versus']}" if meta.get("versus") else ""
            lines.append(f"\n{meta['label']}{versus}  cost {meta['cost']}  DPM {dpm:.1f}  {ttk_txt}")
            for weapon_meta in meta["weapons"]:
                wdpm = interpolate_dpm(weapon_meta["series"], card)
                ammo = weapon_meta["ammo"]
                weapon = weapon_meta["weapon"]
                chance = hit_chance(ammo, world, meta.get("silhouette") or self._silhouette)
                hit_txt = f"  hit {chance:.0%}" if self._apply_accuracy else ""
                range_txt = card_range_text(ammo)
                range_part = f"  {range_txt}" if range_txt else ""
                lines.append(
                    f"  {weapon.get('HUDName')}: {ammo.get('HUDName')}{range_part}  "
                    f"DPM {wdpm:.1f}  dmg {ammo.get('Damage')}  "
                    f"pen {ammo.get('PenetrationAtMinRange')}→{ammo.get('PenetrationAtGroundRange')}  "
                    f"guns {weapon_meta['gun_count']}  carried {weapon_meta['carried']}"
                    f"{hit_txt}"
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
            writer.writerow(["Range (card m)", "Unit", "DPM"])
            for meta in self._series_meta:
                for card, dpm in meta["series"]:
                    writer.writerow([card, meta["label"], f"{dpm:.4f}"])

    def create_custom_unit(self) -> None:
        catalog = self.app.catalog
        if catalog is None:
            return
        source = self.clone_from.get()
        unit_id = _id_from_label(source)
        if unit_id is None or unit_id not in catalog.units:
            messagebox.showerror("DPM", "Pick an existing unit to clone.")
            return
        name = self.clone_name.get().strip()
        if not name:
            messagebox.showerror("DPM", "Name the custom unit.")
            return
        armor_id = catalog.default_armor.get(unit_id)
        armor = dict(catalog.armors.get(armor_id, {})) if armor_id else catalog.dummy_armor()
        try:
            armor["MaxHealthPoints"] = float(self.clone_hp.get() or armor.get("MaxHealthPoints") or 14)
            cost = int(float(self.clone_cost.get() or catalog.units[unit_id].get("Cost") or 1))
        except ValueError:
            messagebox.showerror("DPM", "Cost and HP must be numbers.")
            return
        key = f"[custom] {name}"
        self.app.custom_units[key] = {
            "source_unit_id": unit_id,
            "cost": cost,
            "armor": armor,
            "armor_label": f"{name} armor",
        }
        self.app.save_user_data()
        self.refresh_lists()
        messagebox.showinfo("DPM", f"Created {key}")

    def save_tab_state(self) -> dict[str, Any]:
        return {
            "rows": [
                {
                    "unit": row["unit"].get(),
                    "armor": row["armor"].get(),
                    "visible": bool(row["visible"].get()),
                    "cost": int(row["cost"].get()),
                }
                for row in self.rows
            ],
            "target_armor": self.target_armor.get(),
            "target_unit": self.target_unit.get(),
            "face": self.face_var.get(),
            "damage_type": self.damage_type.get(),
            "ammo_pref": self.ammo_pref.get(),
            "include_upgrade": bool(self.include_upgrade.get()),
            "normalize": bool(self.normalize.get()),
            "assume_hits": bool(self.assume_hits.get()),
            "duel": bool(self.duel_var.get()),
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
            if state.get("ammo_pref"):
                self.ammo_pref.set(state["ammo_pref"])
            if "include_upgrade" in state:
                self.include_upgrade.set(bool(state["include_upgrade"]))
            if "normalize" in state:
                self.normalize.set(bool(state["normalize"]))
            if "assume_hits" in state:
                self.assume_hits.set(bool(state["assume_hits"]))
            if "duel" in state:
                self.duel_var.set(bool(state["duel"]))
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
            known_units = set(self.unit_names) | set(self.app.custom_units)
            for row, saved in zip(self.rows, rows):
                unit = saved.get("unit") or ""
                if unit and unit in known_units:
                    row["unit"].set(unit)
                    self._on_unit_changed(row, restore=True)
                if saved.get("armor"):
                    row["armor"].set(saved["armor"])
                row["visible"].set(bool(saved.get("visible", True)))
                if saved.get("cost") is not None:
                    try:
                        row["cost"].set(int(saved["cost"]))
                    except (tk.TclError, ValueError):
                        pass
            self.chart.selected_range = state.get("pinned_range")
            self._update_duel_enabled()
            if self.app.catalog and any(row["unit"].get() for row in self.rows):
                self.generate()
        finally:
            self._is_loading_state = False
