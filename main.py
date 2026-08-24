# -*- coding: utf-8 -*-
"""Десктопная версия «Охота на лис» на Tkinter.

Запуск: python main.py
"""

import tkinter as tk
from tkinter import filedialog, messagebox

from game import DEFAULT_FOXES, FIELD_SIZES, SAVE_FILE, FoxGame

# --- Цвета (в духе веб-версии) ---
BG_MAIN = "#1b3a2a"       # тёмно-зелёный фон окна
BG_CARD = "#24402f"       # фон карточек
TEXT = "#f5f0e1"          # основной текст
TEXT_DIM = "#c9c2b0"      # приглушённый текст
ACCENT = "#e8a33d"        # акцентные кнопки
ACCENT_FG = "#3a2a0a"
HIDDEN = "#6b4f2a"        # закрытая клетка
HIDDEN_GREY = "#a3a3a3"   # закрытая клетка на серой линии
NUMBER = "#f5f0e1"        # открытая клетка с числом
NUMBER_FG = "#2b4d33"
NUMBER_GREY = "#d9d9d9"   # открытая клетка на серой линии
NUMBER_GREY_FG = "#555555"
FOX_BG = "#ffffff"
WIN_BG = "#2f9e44"
LOSE_BG = "#c92a2a"

# Курсор над клетками поля — «прицел» (перекрестие с кружком).
# Tk 9 на Windows не поддерживает кастомные XBM/PhotoImage-курсоры,
# поэтому используем встроенный именованный курсор "target".
CURSOR_TARGET = "target"


class FoxApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("🦊 Охота на лис")
        self.configure(bg=BG_MAIN)
        self.resizable(False, False)
        self.game = FoxGame()
        self._updating_foxes = False
        self.buttons = {}
        self.show_menu()

    # --- Вспомогательные ---

    def _clear(self):
        for w in self.winfo_children():
            w.destroy()

    def _heading(self):
        tk.Label(self, text="🦊 Охота на лис", bg=BG_MAIN, fg=TEXT,
                 font=("Segoe UI", 20, "bold")).pack(pady=(16, 4))

    def _card(self):
        card = tk.Frame(self, bg=BG_CARD)
        card.pack(pady=10, padx=12, fill="both", expand=True)
        return card

    def _accent_button(self, parent, text, command):
        return tk.Button(parent, text=text, bg=ACCENT, fg=ACCENT_FG,
                         font=("Segoe UI", 11, "bold"), command=command)

    # --- Экраны ---

    def show_menu(self):
        """Стартовое меню: выбор размера и количества лис."""
        self._clear()
        self._heading()
        card = self._card()

        tk.Label(card, text="Новая игра", bg=BG_CARD, fg=TEXT,
                 font=("Segoe UI", 14, "bold")).pack(pady=(8, 4))

        row = tk.Frame(card, bg=BG_CARD)
        row.pack(pady=6)
        tk.Label(row, text="Размер поля:", bg=BG_CARD, fg=TEXT).pack(side="left", padx=4)
        self.size_var = tk.IntVar(value=9)
        size_box = tk.OptionMenu(row, self.size_var, *FIELD_SIZES)
        size_box.config(bg=BG_CARD, fg=TEXT, highlightthickness=0)
        size_box.pack(side="left", padx=4)

        row2 = tk.Frame(card, bg=BG_CARD)
        row2.pack(pady=6)
        tk.Label(row2, text="Количество лис:", bg=BG_CARD, fg=TEXT).pack(side="left", padx=4)
        self.foxes_var = tk.IntVar(value=DEFAULT_FOXES[9])
        self.foxes_box = tk.OptionMenu(row2, self.foxes_var, 5)
        self.foxes_box.config(bg=BG_CARD, fg=TEXT, highlightthickness=0)
        self.foxes_box.pack(side="left", padx=4)
        self.size_var.trace_add("write", self._update_foxes_options)
        self._update_foxes_options()

        tk.Label(card, text=(
            "Лимит ходов: размер поля в квадрате минус 1 (9×9 — 80, 15×15 — 224).\n"
            "Чем больше лис — тем сложнее игра."
        ), bg=BG_CARD, fg=TEXT_DIM, font=("Segoe UI", 10), justify="center").pack(pady=6)

        self._accent_button(card, "Начать игру", self.start_game).pack(pady=8)

        tk.Label(card, text=(
            "Правила:\n"
            "• Лисы спрятаны на поле — кликайте по клеткам, чтобы найти их.\n"
            "• В открытой клетке показывается пеленг — сколько лис стоит на той же\n"
            "  вертикали, горизонтали и обеих диагоналях.\n"
            "• Пеленг 0 закрашивает серым все линии клетки — там гарантированно нет лис.\n"
            "• Игру можно сохранить в любой момент и продолжить позже."
        ), bg=BG_CARD, fg=TEXT_DIM, font=("Segoe UI", 10), justify="left").pack(
            pady=8, padx=16, anchor="w")

    def show_board(self):
        """Игровое поле."""
        self._clear()
        self._heading()
        card = self._card()

        self.stats_var = tk.StringVar()
        tk.Label(card, textvariable=self.stats_var, bg=BG_CARD, fg=TEXT,
                 font=("Segoe UI", 12, "bold")).pack(pady=6)
        self._update_stats()

        board = tk.Frame(card, bg=BG_CARD)
        board.pack(pady=6)
        # Клетки рисуются на Canvas прямоугольниками фиксированного размера
        # в пикселях — гарантированно квадратные при любом размере поля.
        self.cell = 34 if self.game.size == 15 else 46
        canvas = tk.Canvas(board,
                           width=self.game.size * self.cell,
                           height=self.game.size * self.cell,
                           bg=BG_CARD, highlightthickness=0)
        canvas.pack()
        canvas.bind("<Button-1>", self.on_canvas_click)
        canvas.configure(cursor=CURSOR_TARGET)
        self.canvas = canvas
        self._paint_board()

        row = tk.Frame(card, bg=BG_CARD)
        row.pack(pady=8)
        self._accent_button(row, "Сохранить", self.save_game).pack(side="left", padx=4)
        self._accent_button(row, "Загрузить", self.load_game).pack(side="left", padx=4)
        self._accent_button(row, "В начало", self.show_menu).pack(side="left", padx=4)

    def show_end(self):
        """Финальный экран: победа или поражение."""
        self._clear()
        self._heading()
        card = self._card()
        bg = WIN_BG if self.game.status == "win" else LOSE_BG
        tk.Label(card, text=self.game.message, bg=bg, fg="#ffffff",
                 font=("Segoe UI", 14, "bold"), wraplength=500,
                 padx=18, pady=14).pack(pady=10)
        tk.Label(card, text="Можно начать новую игру или загрузить сохранение.",
                 bg=BG_CARD, fg=TEXT_DIM).pack(pady=4)
        row = tk.Frame(card, bg=BG_CARD)
        row.pack(pady=10)
        self._accent_button(row, "В начало", self.show_menu).pack(side="left", padx=4)
        self._accent_button(row, "Загрузить", self.load_game).pack(side="left", padx=4)

    # --- Действия ---

    def start_game(self):
        self.game.new_game(self.size_var.get(), self.foxes_var.get())
        self.show_board()

    def on_cell(self, r, c):
        if self.game.move(r, c):
            self._update_stats()
            self._paint_board()
            if self.game.status != "playing":
                self.after(300, self.show_end)

    def save_game(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            initialfile=SAVE_FILE,
            filetypes=[("JSON-файл", "*.json")],
            title="Сохранить игру",
        )
        if not path:
            return
        try:
            self.game.save(path)
        except OSError as e:
            messagebox.showerror("Ошибка сохранения", str(e))
            return
        messagebox.showinfo("Сохранено", f"Игра сохранена:\n{path}")

    def load_game(self):
        path = filedialog.askopenfilename(
            filetypes=[("JSON-файл", "*.json")],
            title="Загрузить игру",
        )
        if not path:
            return
        try:
            self.game.load(path)
        except (OSError, ValueError, KeyError) as e:
            messagebox.showerror("Ошибка загрузки", f"Не удалось загрузить игру:\n{e}")
            return
        self.show_board()

    # --- Отрисовка состояния ---

    def _update_stats(self):
        self.stats_var.set(
            f"Ходы: {self.game.moves} / {self.game.max_moves}    •    "
            f"Лисы найдены: {self.game.found} / {len(self.game.foxes)}"
        )

    def on_canvas_click(self, event):
        """Клик по Canvas: определяем клетку по координатам и ходим."""
        r = event.y // self.cell
        c = event.x // self.cell
        if 0 <= r < self.game.size and 0 <= c < self.game.size:
            self.on_cell(r, c)

    def _paint_board(self):
        """Рисует всё поле заново: клетки, числа, серые линии, лис."""
        c = self.canvas
        c.delete("all")
        g = self.game
        cell = self.cell
        for r in range(g.size):
            for col in range(g.size):
                x0, y0 = col * cell, r * cell
                x1, y1 = x0 + cell, y0 + cell
                grey = g.is_on_grey_line(r, col)
                if (r, col) in g.revealed:
                    if (r, col) in g.found_cells:
                        fill, fg, text = FOX_BG, "#000000", "🦊"
                    else:
                        fill = NUMBER_GREY if grey else NUMBER
                        fg = NUMBER_GREY_FG if grey else NUMBER_FG
                        text = str(g.revealed[(r, col)])
                else:
                    fill = HIDDEN_GREY if grey else HIDDEN
                    fg = TEXT
                    text = ""
                c.create_rectangle(x0 + 1, y0 + 1, x1 - 1, y1 - 1,
                                   fill=fill, outline="#444444")
                if text:
                    c.create_text(x0 + cell / 2, y0 + cell / 2, text=text,
                                  fill=fg,
                                  font=("Segoe UI", max(9, int(cell * 0.38)), "bold"))

    def _update_foxes_options(self, *args):
        """Пересобирает список количества лис при смене размера поля."""
        if self._updating_foxes:
            return
        # Виджет существует только на экране меню — защита от trace вне меню
        if not hasattr(self, "foxes_box") or not self.foxes_box.winfo_exists():
            return
        self._updating_foxes = True
        try:
            size = self.size_var.get()
            menu = self.foxes_box["menu"]
            menu.delete(0, "end")
            chosen = min(DEFAULT_FOXES.get(size, 5), size)
            self.foxes_var.set(chosen)
            for n in range(5, size + 1):
                menu.add_command(label=str(n), command=tk._setit(self.foxes_var, n))
        finally:
            self._updating_foxes = False


def main():
    app = FoxApp()
    app.mainloop()


if __name__ == "__main__":
    main()
