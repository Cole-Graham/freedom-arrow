"""Broken Arrow DPM visualizer."""

from __future__ import annotations

import json
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog, ttk

from .joins import Catalog
from .tables import default_vanilla_dir, load_dataset, repo_root
from .ui_components import SearchableCombobox
from .units_tab import UnitsTab
from .weapons_tab import WeaponsTab

USER_DATA = Path(__file__).resolve().parent / "user_data.json"


class DPMVisualizerApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Broken Arrow DPM Visualizer")
        self.root.geometry("1600x1200")
        self.catalog: Catalog | None = None
        self.custom_weapons: dict = {}
        self.custom_units: dict = {}
        self.current_profile = "default"
        self.profiles: dict = {}
        self._pending_ui: dict = {}
        self._loading = True
        self._build()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.load_user_data()
        self._try_autoload()
        self.load_ui_state()
        self._loading = False

    def _build(self) -> None:
        chrome = ttk.Frame(self.root, padding=8)
        chrome.pack(fill=tk.X)
        ttk.Label(chrome, text="Vanilla tables").grid(row=0, column=0, sticky=tk.W)
        self.vanilla_var = tk.StringVar()
        ttk.Entry(chrome, textvariable=self.vanilla_var, width=70).grid(row=0, column=1, sticky=tk.EW, padx=4)
        ttk.Button(chrome, text="Browse", command=self._browse_vanilla).grid(row=0, column=2)
        ttk.Label(chrome, text="Constants overlay").grid(row=1, column=0, sticky=tk.W, pady=(4, 0))
        self.overlay_var = tk.StringVar()
        ttk.Entry(chrome, textvariable=self.overlay_var, width=70).grid(row=1, column=1, sticky=tk.EW, padx=4, pady=(4, 0))
        ttk.Button(chrome, text="Browse", command=self._browse_overlay).grid(row=1, column=2, pady=(4, 0))
        ttk.Button(chrome, text="Load data", command=self.load_data).grid(row=0, column=3, rowspan=2, padx=8)

        profile = ttk.Frame(self.root, padding=(8, 0, 8, 4))
        profile.pack(fill=tk.X)
        ttk.Label(profile, text="Profile").pack(side=tk.LEFT)
        self.profile_var = tk.StringVar(value="default")
        self.profile_combo = ttk.Combobox(profile, textvariable=self.profile_var, width=20, state="readonly")
        self.profile_combo.pack(side=tk.LEFT, padx=4)
        self.profile_combo.bind("<<ComboboxSelected>>", self._on_profile)
        ttk.Button(profile, text="New", command=self._new_profile).pack(side=tk.LEFT)
        ttk.Button(profile, text="Delete", command=self._delete_profile).pack(side=tk.LEFT, padx=4)

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        units_frame = ttk.Frame(self.notebook)
        weapons_frame = ttk.Frame(self.notebook)
        self.notebook.add(units_frame, text="Units")
        self.notebook.add(weapons_frame, text="Weapons")
        self.units_tab = UnitsTab(units_frame, self)
        self.weapons_tab = WeaponsTab(weapons_frame, self)
        self.notebook.bind(
            "<<NotebookTabChanged>>",
            lambda _e: (SearchableCombobox.close_all_dropdowns(), self.auto_save_state()),
        )
        chrome.columnconfigure(1, weight=1)

    def _browse_vanilla(self) -> None:
        path = filedialog.askdirectory(title="Vanilla snapshot (cache/vanilla/<build-id>)")
        if path:
            self.vanilla_var.set(path)

    def _browse_overlay(self) -> None:
        path = filedialog.askdirectory(title="Constants overlay directory")
        if path:
            self.overlay_var.set(path)

    def _try_autoload(self) -> None:
        if self.vanilla_var.get().strip():
            try:
                self.load_data()
                return
            except Exception:
                pass
        vanilla = default_vanilla_dir(repo_root())
        if vanilla:
            self.vanilla_var.set(str(vanilla))
            try:
                self.load_data()
            except Exception as exc:
                messagebox.showwarning("DPM", f"Could not autoload {vanilla}: {exc}")

    def load_data(self) -> None:
        vanilla = Path(self.vanilla_var.get().strip())
        if not vanilla.is_dir():
            messagebox.showerror(
                "DPM",
                "Set vanilla tables to cache/vanilla/<build-id>. Run python -m pipeline decrypt first.",
            )
            return
        overlay_raw = self.overlay_var.get().strip()
        overlay = Path(overlay_raw) if overlay_raw else None
        try:
            tables = load_dataset(vanilla, overlay)
            self.catalog = Catalog(tables)
        except Exception as exc:
            messagebox.showerror("DPM", str(exc))
            return
        self.units_tab.refresh_lists()
        self.weapons_tab.refresh_lists()
        count = len(self.catalog.playable_units())
        self.root.title(f"Broken Arrow DPM Visualizer — {count} units")

    def _apply_profile(self, name: str) -> None:
        self.current_profile = name
        profile = self.profiles.get(name, {})
        self.custom_units = dict(profile.get("custom_units") or {})
        self.custom_weapons = dict(profile.get("custom_weapons") or {})
        if self.catalog:
            self.units_tab.refresh_lists()
            self.weapons_tab.refresh_lists()

    def _store_profile(self) -> None:
        self.profiles[self.current_profile] = {
            "custom_units": self.custom_units,
            "custom_weapons": self.custom_weapons,
        }

    def _on_profile(self, _event=None) -> None:
        self._store_profile()
        self._apply_profile(self.profile_var.get())
        self.save_user_data()

    def _new_profile(self) -> None:
        name = simpledialog.askstring("Profile", "Name")
        if not name:
            return
        self._store_profile()
        self.profiles[name] = {"custom_units": {}, "custom_weapons": {}}
        self.profile_combo["values"] = sorted(self.profiles)
        self.profile_var.set(name)
        self._apply_profile(name)
        self.save_user_data()

    def _delete_profile(self) -> None:
        name = self.profile_var.get()
        if name == "default" or name not in self.profiles:
            return
        if not messagebox.askyesno("Profile", f"Delete {name}?"):
            return
        del self.profiles[name]
        self.profile_combo["values"] = sorted(self.profiles) or ["default"]
        self.profile_var.set("default")
        self._apply_profile("default")
        self.save_user_data()

    def load_user_data(self) -> None:
        if not USER_DATA.is_file():
            self.profiles = {"default": {"custom_units": {}, "custom_weapons": {}}}
            self._apply_profile("default")
            self.profile_combo["values"] = ["default"]
            return
        data = json.loads(USER_DATA.read_text(encoding="utf-8"))
        self.vanilla_var.set(data.get("vanilla_dir") or "")
        self.overlay_var.set(data.get("overlay_dir") or "")
        self.profiles = data.get("profiles") or {"default": {"custom_units": {}, "custom_weapons": {}}}
        self.current_profile = data.get("current_profile") or "default"
        if self.current_profile not in self.profiles:
            self.current_profile = "default"
        self.profile_combo["values"] = sorted(self.profiles)
        self.profile_var.set(self.current_profile)
        self._apply_profile(self.current_profile)
        self._pending_ui = data.get("ui_state") or {}
        geometry = data.get("geometry")
        if geometry:
            try:
                self.root.geometry(geometry)
            except tk.TclError:
                pass

    def load_ui_state(self) -> None:
        state = self._pending_ui
        if not state:
            return
        geometry = state.get("window_geometry") or state.get("geometry")
        if geometry:
            try:
                self.root.geometry(geometry)
            except tk.TclError:
                pass
        tab = state.get("selected_tab", state.get("tab"))
        try:
            if tab == "Weapons" or tab == 1:
                self.notebook.select(1)
            elif tab == "Units" or tab == 0:
                self.notebook.select(0)
        except tk.TclError:
            pass
        try:
            self.units_tab.load_tab_state(state.get("units_tab") or state.get("infantry_tab"))
        except Exception:
            pass
        try:
            self.weapons_tab.load_tab_state(state.get("weapons_tab"))
        except Exception:
            pass

    def auto_save_state(self) -> None:
        if self._loading:
            return
        try:
            self.save_user_data()
        except OSError:
            pass

    def save_user_data(self) -> None:
        self._store_profile()
        ui_state = {
            "window_geometry": self.root.geometry(),
            "selected_tab": self.notebook.index(self.notebook.select()),
            "tab": self.notebook.tab(self.notebook.select(), "text"),
            "units_tab": self.units_tab.save_tab_state(),
            "weapons_tab": self.weapons_tab.save_tab_state(),
        }
        payload = {
            "vanilla_dir": self.vanilla_var.get(),
            "overlay_dir": self.overlay_var.get(),
            "current_profile": self.current_profile,
            "profiles": self.profiles,
            "geometry": ui_state["window_geometry"],
            "ui_state": ui_state,
        }
        USER_DATA.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def on_close(self) -> None:
        try:
            self.save_user_data()
        except OSError:
            pass
        self.root.destroy()


def main() -> None:
    root = tk.Tk()
    DPMVisualizerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
