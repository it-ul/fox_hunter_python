# -*- coding: utf-8 -*-
"""Панель управления игрой «Охота на лис»: кнопки, информация, протокол ходов.

Панель встраивается прямо в главное окно (SDI-интерфейс) — отдельных окон нет.
"""

import tkinter as tk

from game import DEFAULT_FOXES, FIELD_SIZES, coord_label

BG = "#24402f"
TEXT = "#f5f0e1"
DIM = "#c9c2b0"
ACCENT = "#e8a33d"
ACCENT_FG = "#3a2a0a"
PANEL_BG = "#1f3527"

STATUS_LABEL = {
    "playing": "Идёт",
    "win": "Победа",
    "lose": "Поражение",
}


class ControlPanel(tk.Frame):
    """Правая панель главного окна: новая игра, действия, информация, протокол."""

    def __init__(self, app, parent=None):
        super().__init__(parent or app, bg=BG)
        self.app = app
        self._updating = False
        self._build()

    # --- Построение интерфейса -------------------------------------------

    def _build(self):
        pad = {"padx": 10}

        # 1. Новая игра
        box = tk.LabelFrame(self, text=" Новая игра ", bg=BG, fg=TEXT,
                            font=("Segoe UI", 10, "bold"), labelanchor="nw")
        box.pack(fill="x", pady=(0, 4))

        row = tk.Frame(box, bg=BG)
        row.pack(anchor="w", **pad, pady=3)
        tk.Label(row, text="Размер поля:", bg=BG, fg=TEXT).pack(side="left")
        self.size_var = tk.IntVar(value=9)
        size_box = tk.OptionMenu(row, self.size_var, *FIELD_SIZES)
        size_box.config(bg=BG, fg=TEXT, highlightthickness=0, width=4)
        size_box.pack(side="left", padx=6)

        row2 = tk.Frame(box, bg=BG)
        row2.pack(anchor="w", **pad, pady=3)
        tk.Label(row2, text="Количество лис:", bg=BG, fg=TEXT).pack(side="left")
        self.foxes_var = tk.IntVar(value=DEFAULT_FOXES[9])
        self.foxes_box = tk.OptionMenu(row2, self.foxes_var, 5)
        self.foxes_box.config(bg=BG, fg=TEXT, highlightthickness=0, width=4)
        self.foxes_box.pack(side="left", padx=6)
        self.size_var.trace_add("write", self._update_foxes_options)
        self._update_foxes_options()

        self._button(box, "Начать игру", self._start).pack(anchor="w", **pad, pady=(4, 10))

        # 2. Действия
        box2 = tk.LabelFrame(self, text=" Действия ", bg=BG, fg=TEXT,
                             font=("Segoe UI", 10, "bold"), labelanchor="nw")
        box2.pack(fill="x", pady=4)
        acts = tk.Frame(box2, bg=BG)
        acts.pack(**pad, pady=6, anchor="w")
        self._button(acts, "Сохранить", self.app.save_game).pack(side="left", padx=(0, 4))
        self._button(acts, "Загрузить", self.app.load_game).pack(side="left", padx=4)
        self._button(acts, "Выход", self.app.quit_app).pack(side="left", padx=4)

        # 3. Информация
        box3 = tk.LabelFrame(self, text=" Информация ", bg=BG, fg=TEXT,
                             font=("Segoe UI", 10, "bold"), labelanchor="nw")
        box3.pack(fill="x", pady=4)
        self.info_var = tk.StringVar()
        tk.Label(box3, textvariable=self.info_var, bg=BG, fg=TEXT,
                 justify="left", font=("Consolas", 9)).pack(
                     anchor="w", **pad, pady=6)

        # 4. Протокол игры
        box4 = tk.LabelFrame(self, text=" Протокол игры ", bg=BG, fg=TEXT,
                             font=("Segoe UI", 10, "bold"), labelanchor="nw")
        box4.pack(fill="both", expand=True, pady=(4, 0))

        frame = tk.Frame(box4, bg=BG)
        frame.pack(fill="both", expand=True, **pad, pady=6)
        scroll = tk.Scrollbar(frame, orient="vertical")
        self.log_list = tk.Listbox(frame, height=16, width=30, yscrollcommand=scroll.set,
                                   bg=PANEL_BG, fg=TEXT, font=("Consolas", 9),
                                   selectbackground="#3a5c47", highlightthickness=0,
                                   borderwidth=0, activestyle="none")
        scroll.config(command=self.log_list.yview)
        scroll.pack(side="right", fill="y")
        self.log_list.pack(side="left", fill="both", expand=True)

    def _button(self, parent, text, command):
        return tk.Button(parent, text=text, bg=ACCENT, fg=ACCENT_FG,
                         font=("Segoe UI", 10, "bold"), command=command)

    # --- Действия панели --------------------------------------------------

    def _start(self):
        self.app.start_game(self.size_var.get(), self.foxes_var.get())

    # --- Обновление -------------------------------------------------------

    def refresh(self):
        """Обновляет информацию и протокол по текущему состоянию игры."""
        g = self.app.game
        if not g.foxes:
            self.info_var.set("Игра не начата.")
            self.log_list.delete(0, "end")
            return
        self.info_var.set(
            f"Размер поля: {g.size}×{g.size}\n"
            f"Лис на поле:   {len(g.foxes)}\n"
            f"Ходы:          {g.moves} / {g.max_moves}\n"
            f"Найдено лис:   {g.found} / {len(g.foxes)}\n"
            f"Статус:        {STATUS_LABEL.get(g.status, g.status)}"
        )
        self.log_list.delete(0, "end")
        for i, (r, c, bearing, is_fox) in enumerate(g.log, start=1):
            self.log_list.insert(
                "end",
                f"{i:>3}. {coord_label(g.size, r, c)} — пеленг {bearing}, "
                f"лиса: {'да' if is_fox else 'нет'}",
            )
        self.log_list.yview_moveto(1.0)  # прокрутить к последнему ходу

    def _update_foxes_options(self, *args):
        """Пересобирает список количества лис при смене размера поля."""
        if self._updating:
            return
        self._updating = True
        try:
            size = self.size_var.get()
            menu = self.foxes_box["menu"]
            menu.delete(0, "end")
            chosen = min(DEFAULT_FOXES.get(size, 5), size)
            self.foxes_var.set(chosen)
            for n in range(5, size + 1):
                menu.add_command(label=str(n), command=tk._setit(self.foxes_var, n))
        finally:
            self._updating = False
