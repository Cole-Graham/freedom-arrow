"""Searchable combobox used by both tabs."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable


class SearchableCombobox(ttk.Frame):
    _instances: list["SearchableCombobox"] = []

    def __init__(self, parent, values=None, width=28, on_select: Callable | None = None):
        super().__init__(parent)
        self._original_values = list(values or [])
        self.values = list(self._original_values)
        self.on_select = on_select
        self.var = tk.StringVar()
        self.entry = ttk.Entry(self, textvariable=self.var, width=width)
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.dropdown_btn = ttk.Button(self, text="▼", width=3, command=self.toggle_dropdown)
        self.dropdown_btn.pack(side=tk.RIGHT)
        self.popup = None
        self.listbox = None
        self.is_open = False
        self._just_selected = False
        SearchableCombobox._instances.append(self)
        self.entry.bind("<KeyRelease>", self.on_key_release)
        self.entry.bind("<Button-1>", lambda _e: self.show_dropdown())

    @classmethod
    def close_all_dropdowns(cls) -> None:
        for instance in cls._instances:
            if instance.is_open:
                instance.hide_dropdown()

    def destroy(self) -> None:
        if self in SearchableCombobox._instances:
            SearchableCombobox._instances.remove(self)
        if self.popup:
            self.popup.destroy()
        super().destroy()

    def set_values(self, values) -> None:
        self._original_values = list(values)
        self.values = list(values)
        if self.listbox:
            self.update_listbox()

    def get(self) -> str:
        return self.var.get()

    def set(self, value: str) -> None:
        self.var.set(value)

    def on_key_release(self, event) -> None:
        text = self.var.get().lower()
        if not text:
            self.values = list(self._original_values)
        else:
            self.values = [item for item in self._original_values if text in item.lower()]
        if self.is_open:
            self.update_listbox()
        elif event.keysym not in ("Return", "Tab", "Escape"):
            self.show_dropdown()

    def toggle_dropdown(self) -> None:
        if self.is_open:
            self.hide_dropdown()
        else:
            self.show_dropdown()

    def show_dropdown(self) -> None:
        if not self.values:
            return
        root = self.winfo_toplevel()
        if not self.popup:
            self.popup = tk.Toplevel(root)
            self.popup.overrideredirect(True)
            self.popup.attributes("-topmost", True)
            frame = ttk.Frame(self.popup)
            frame.pack(fill=tk.BOTH, expand=True)
            scrollbar = ttk.Scrollbar(frame)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            self.listbox = tk.Listbox(frame, yscrollcommand=scrollbar.set, height=min(12, len(self.values)))
            self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.config(command=self.listbox.yview)
            self.listbox.bind("<Button-1>", self.on_listbox_select)
            self.listbox.bind("<Double-Button-1>", self.on_listbox_select)
        if not hasattr(SearchableCombobox, "_root_click_bound"):
            root.bind("<ButtonRelease-1>", self._root_release, add="+")
            SearchableCombobox._root_click_bound = True
        self.update_listbox()
        self.position_popup()
        self.popup.deiconify()
        self.is_open = True

    def _root_release(self, event) -> None:
        root_x, root_y = event.x_root, event.y_root
        clicked = event.widget

        def later() -> None:
            for instance in SearchableCombobox._instances:
                if not instance.is_open or not instance.popup or instance._just_selected:
                    continue
                widget = clicked
                inside = False
                while widget:
                    if widget in (instance.popup, instance.listbox, instance.entry, instance.dropdown_btn, instance):
                        inside = True
                        break
                    widget = getattr(widget, "master", None)
                if inside:
                    continue
                try:
                    px, py = instance.popup.winfo_x(), instance.popup.winfo_y()
                    pw, ph = instance.popup.winfo_width(), instance.popup.winfo_height()
                    ex, ey = instance.winfo_rootx(), instance.winfo_rooty()
                    ew, eh = instance.winfo_width(), instance.winfo_height()
                    in_popup = px <= root_x <= px + pw and py <= root_y <= py + ph
                    in_entry = ex <= root_x <= ex + ew and ey <= root_y <= ey + eh
                    if not in_popup and not in_entry:
                        instance.hide_dropdown()
                except tk.TclError:
                    pass

        self.winfo_toplevel().after(150, later)

    def update_listbox(self) -> None:
        if not self.listbox:
            return
        self.listbox.delete(0, tk.END)
        for value in self.values:
            self.listbox.insert(tk.END, value)
        self.listbox.config(height=min(12, max(1, len(self.values))))

    def position_popup(self) -> None:
        self.update_idletasks()
        x = self.winfo_rootx()
        y = self.winfo_rooty() + self.winfo_height()
        width = max(self.winfo_width(), 240)
        height = min(240, max(40, len(self.values) * 18 + 8))
        self.popup.geometry(f"{width}x{height}+{x}+{y}")

    def hide_dropdown(self) -> None:
        if self.popup:
            self.popup.withdraw()
        self.is_open = False

    def on_listbox_select(self, _event) -> None:
        self._just_selected = True

        def apply() -> None:
            if not self.listbox:
                self._just_selected = False
                return
            selection = self.listbox.curselection()
            if selection:
                value = self.listbox.get(selection[0])
                self.var.set(value)
                self.hide_dropdown()
                if self.on_select:
                    self.on_select(value)
                self.event_generate("<<ComboboxSelected>>")
            self.after(50, lambda: setattr(self, "_just_selected", False))

        self.after(10, apply)


class CoverControls:
    """Cover picker for infantry targets: Open, Woods or Building, with the loaded data set's values."""

    def __init__(self, parent, app, on_change: Callable):
        self.app = app
        row = ttk.Frame(parent)
        row.pack(anchor=tk.W, pady=(6, 0))
        ttk.Label(row, text="Cover (infantry targets)").pack(side=tk.LEFT)
        self.kind = tk.StringVar(value="Open")
        ttk.Combobox(row, textvariable=self.kind, values=["Open", "Woods", "Building"], state="readonly", width=9).pack(side=tk.LEFT, padx=4)
        ttk.Label(row, text="Soldiers in building").pack(side=tk.LEFT)
        self.soldiers = tk.IntVar(value=6)
        ttk.Spinbox(row, from_=1, to=60, textvariable=self.soldiers, width=4).pack(side=tk.LEFT, padx=4)
        self.info = tk.StringVar()
        ttk.Label(parent, textvariable=self.info, foreground="#555", wraplength=380, justify=tk.LEFT).pack(anchor=tk.W)
        self.kind.trace_add("write", lambda *_: (self.update_info(), on_change()))
        self.soldiers.trace_add("write", lambda *_: (self.update_info(), on_change()))

    def cover(self):
        from .calculations import Cover

        rules = self.app.cover_rules
        try:
            soldiers = max(1, int(self.soldiers.get()))
        except (tk.TclError, ValueError):
            soldiers = 1
        return Cover(self.kind.get(), rules["forest_taken"], rules["building_floor"], rules["building_per_soldier"], soldiers)

    def update_info(self) -> None:
        cover = self.cover()
        if cover.kind == "Woods":
            if cover.forest_taken >= 1:
                text = "Woods: no reduction in this data set (vanilla has none)."
            else:
                text = f"Woods: infantry take {cover.forest_taken:.0%}, plus ignore cover × the rest."
        elif cover.kind == "Building":
            share = min(1.0, cover.building_floor + cover.building_per_soldier * cover.soldiers)
            text = (f"Building: take {share:.0%} (floor {cover.building_floor:g} + {cover.building_per_soldier:g} × "
                    f"{cover.soldiers} soldiers), plus ignore cover × the rest. Shells hit the building: no misses.")
        else:
            text = ""
        self.info.set(text)

    def save(self) -> dict:
        return {"cover": self.kind.get(), "cover_soldiers": self.cover().soldiers}

    def load(self, state: dict) -> None:
        if state.get("cover") in ("Open", "Woods", "Building"):
            self.kind.set(state["cover"])
        if state.get("cover_soldiers"):
            self.soldiers.set(int(state["cover_soldiers"]))


class ArmorPicker:
    """Armor menu with a separate Men box for infantry classes, so any squad size can be picked."""

    def __init__(self, parent, app, width: int = 32, on_select: Callable | None = None, side: str | None = None):
        self.app = app
        self.on_select = on_select
        self.frame = ttk.Frame(parent)
        self.combo = SearchableCombobox(self.frame, width=width, on_select=lambda _v: self._picked())
        self.combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Label(self.frame, text="Men").pack(side=tk.LEFT, padx=(4, 0))
        self.men = tk.IntVar(value=8)
        self.men_box = ttk.Spinbox(self.frame, from_=1, to=30, textvariable=self.men, width=4, command=self._changed)
        self.men_box.pack(side=tk.LEFT, padx=2)
        self.men_box.bind("<FocusOut>", lambda _e: self._changed())
        if side:
            self.frame.pack(side=side, padx=4)
        else:
            self.frame.pack(fill=tk.X)
        self._update_state()

    def _classes(self) -> dict:
        return self.app.catalog.infantry_armor_classes() if self.app.catalog else {}

    def is_infantry(self) -> bool:
        return self.combo.get().strip() in self._classes()

    def _update_state(self) -> None:
        self.men_box.configure(state=tk.NORMAL if self.is_infantry() else tk.DISABLED)

    def _picked(self) -> None:
        self._update_state()
        self._changed()

    def _changed(self) -> None:
        if self.on_select:
            self.on_select(self.combo.get())

    def set_values(self, values) -> None:
        self.combo.set_values(values)
        self._update_state()

    def get(self) -> str:
        return self.combo.get()

    def men_count(self) -> int:
        try:
            return max(1, int(self.men.get()))
        except (tk.TclError, ValueError):
            return 1

    def set(self, label: str, men: int | None = None) -> None:
        """Accepts a menu label, or an old infantry row label ("Armor Infantry 8Men [84]")."""
        split = self.app.catalog.split_infantry_label(label) if self.app.catalog and label else None
        if split:
            label, men = split
        self.combo.set(label)
        if men:
            self.men.set(int(men))
        self._update_state()

    def armor(self):
        """(armor row, hit box) for the choice, or (None, None) when nothing valid is picked."""
        catalog = self.app.catalog
        label = self.combo.get().strip()
        if catalog is None or not label:
            return None, None
        if label in self._classes():
            return catalog.infantry_armor(label, self.men_count())
        armor_id = None
        if "[" in label and label.endswith("]"):
            try:
                armor_id = int(label[label.rfind("[") + 1 : -1])
            except ValueError:
                armor_id = None
        if armor_id not in catalog.armors:
            return None, None
        return catalog.armors[armor_id], catalog.silhouette_for_armor(armor_id)

    def label_text(self) -> str:
        return f"{self.combo.get()} {self.men_count()} men" if self.is_infantry() else self.combo.get()
