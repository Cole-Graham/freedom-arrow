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
