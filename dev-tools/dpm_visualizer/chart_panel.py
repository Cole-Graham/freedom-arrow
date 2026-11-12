"""Shared matplotlib chart with hover and click-to-pin."""

from __future__ import annotations

from typing import Callable

import matplotlib

matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import tkinter as tk

from .chart_axes import apply_dpm_y_axis_scale
from .constants import LINE_COLORS


class ChartPanel:
    def __init__(self, parent, title: str, on_pin: Callable[[float | None], None]):
        self.on_pin = on_pin
        self.line_data: dict[str, list[tuple[float, float]]] = {}
        self.selected_range: float | None = None
        self._hover = None
        self._pin = None
        self.fig = Figure(figsize=(8.5, 4.6), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_title(title)
        self.ax.set_xlabel("Range (card metres, ×2)")
        self.ax.set_ylabel("DPM if hits")
        self.canvas = FigureCanvasTkAgg(self.fig, master=parent)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.canvas.mpl_connect("motion_notify_event", self._on_hover)
        self.canvas.mpl_connect("button_press_event", self._on_click)

    def draw(
        self,
        series: list[tuple[str, list[tuple[float, float]], str | None]],
        log_scale: bool,
        ylabel: str,
        title: str,
    ) -> None:
        self.ax.clear()
        self.line_data = {}
        self._hover = None
        self._pin = None
        for index, (label, points, style) in enumerate(series):
            if not points:
                continue
            xs = [p[0] for p in points]
            ys = [p[1] for p in points]
            color = LINE_COLORS[index % len(LINE_COLORS)]
            self.ax.plot(xs, ys, label=label, color=color, linestyle=style or "-", linewidth=1.8)
            self.line_data[label] = points
        self.ax.set_title(title)
        self.ax.set_xlabel("Range (card metres, ×2)")
        self.ax.set_ylabel(ylabel)
        if self.line_data:
            self.ax.legend(loc="upper right", fontsize=8)
        apply_dpm_y_axis_scale(self.ax, log_scale)
        if self.selected_range is not None:
            self._pin = self.ax.axvline(self.selected_range, color="black", linestyle=":", linewidth=1)
        self.fig.tight_layout()
        self.canvas.draw_idle()

    def _nearest_card(self, xdata: float) -> float | None:
        cards: list[float] = []
        for points in self.line_data.values():
            cards.extend(p[0] for p in points)
        if not cards:
            return None
        return min(cards, key=lambda card: abs(card - xdata))

    def _on_hover(self, event) -> None:
        if event.inaxes != self.ax or event.xdata is None:
            return
        card = self._nearest_card(event.xdata)
        if card is None:
            return
        if self._hover:
            self._hover.remove()
        self._hover = self.ax.axvline(card, color="red", alpha=0.35, linewidth=1)
        self.canvas.draw_idle()

    def _on_click(self, event) -> None:
        if event.inaxes != self.ax or event.xdata is None:
            return
        card = self._nearest_card(event.xdata)
        if card is None:
            return
        if self.selected_range is not None and abs(self.selected_range - card) < 12.5:
            self.selected_range = None
            self.on_pin(None)
        else:
            self.selected_range = card
            self.on_pin(card)
        if self._pin:
            self._pin.remove()
            self._pin = None
        if self.selected_range is not None:
            self._pin = self.ax.axvline(self.selected_range, color="black", linestyle=":", linewidth=1)
        self.canvas.draw_idle()
