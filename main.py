# -*- coding: utf-8 -*-
"""Десктопная версия «Охота на лис» на Tkinter.

Запуск: python main.py.

Интерфейс SDI (одно окно, три колонки): слева — описание игры, в центре —
игровое поле, справа — панель управления, информация и протокол.
"""

import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox

from control_panel import ControlPanel
from game import SAVE_FILE, FoxGame

# --- Цвета (в духе веб-версии) ---
BG_MAIN = "#1b3a2a"       # тёмно-зелёный фон окна
BG_CARD = "#24402f"       # фон карточек
TEXT = "#f5f0e1"          # основной текст
TEXT_DIM = "#c9c2b0"      # приглушённый текст
ACCENT = "#e8a33d"        # акцентные кнопки
ACCENT_FG = "#3a2a0a"
HIDDEN = "#6b4f2a"        # закрытая клетка
HIDDEN_GREY = "#a3a3a3"   # закрытая клетка на серой линии / с пометкой
NUMBER = "#f5f0e1"        # открытая клетка с числом
NUMBER_FG = "#2b4d33"
NUMBER_GREY = "#d9d9d9"   # открытая клетка на серой линии
NUMBER_GREY_FG = "#555555"
FOX_BG = "#ffffff"
WIN_BG = "#2f9e44"
LOSE_BG = "#c92a2a"

# Курсор над клетками поля — «прицел» (перекрестие с кружком).
CURSOR_TARGET = "target"

# Отступ под подписи координат (слева — цифры, снизу — буквы)
COORD_MARGIN = 24

RULES_TEXT = (
    "Охота на лис — логическая игра-поиск.\n\n"
    "Цель: найти всех лис, спрятанных на поле.\n\n"
    "Как играть:\n"
    "• ЛКМ по клетке открывает её и показывает пеленг — сколько лис стоит "
    "на той же вертикали, горизонтали и обеих диагоналях.\n"
    "• Пеленг 0 означает, что на всех линиях клетки лис нет — такие линии "
    "закрашиваются серым.\n"
    "• ПКМ помечает клетку серым (вы считаете, что там пусто); повторный ПКМ "
    "снимает пометку. Помеченную клетку всё равно можно открыть.\n"
    "• Клетка с лисой открывается и отмечается иконкой лисы; лиса продолжает "
    "учитываться в пеленгах других клеток.\n"
    "• Победа — когда найдены все лисы. Поражение — когда закончились ходы "
    "(лимит: размер поля в квадрате минус 1).\n"
    "• Все ходы записываются в протокол игры.\n\n"
    "Выберите размер поля и количество лис на панели справа "
    "и нажмите «Начать игру»."
)


def resource_path(*parts):
    """Путь к ресурсу, работающий и внутри собранного PyInstaller .exe."""
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, *parts)


class FoxApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("🦊 Охота на лис")
        self.configure(bg=BG_MAIN)
        self.resizable(False, False)
        self.game = FoxGame()
        self.fox_photo = None   # иконка лисы в клетке (масштабированная)
        self.app_icon = None    # иконка приложения (заголовок окна)
        self.cell = 46
        self.canvas = None
        self._load_app_icon()
        self._build_layout()
        self.show_start()

    # --- Окно / иконка ----------------------------------------------------

    def _load_app_icon(self):
        """Ставит иконку лисы в заголовок окна (и всех дочерних окон)."""
        path = resource_path("assets", "fox.png")
        if not os.path.exists(path):
            return
        try:
            self.app_icon = tk.PhotoImage(file=path)
            self.iconphoto(True, self.app_icon)
        except tk.TclError:
            self.app_icon = None

    def _heading(self):
        tk.Label(self, text="🦊 Охота на лис", bg=BG_MAIN, fg=TEXT,
                 font=("Segoe UI", 20, "bold")).pack(pady=(14, 6))

    def _build_layout(self):
        """SDI: три колонки — описание, игровое поле, управление и информация."""
        self._heading()
        main = tk.Frame(self, bg=BG_MAIN)
        main.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        # Слева — описание и правила игры (видно постоянно)
        self._build_description(main)

        # Справа — панель управления, информация и протокол
        self.control = ControlPanel(self, main)
        self.control.pack(side="right", fill="y", padx=(12, 0))

        # В центре — игровое поле
        self.board_area = tk.Frame(main, bg=BG_CARD)
        self.board_area.pack(side="left", fill="both", expand=True)

    def _build_description(self, parent):
        """Левая колонка главного окна: заголовок и правила игры."""
        panel = tk.Frame(parent, bg=BG_CARD)
        panel.pack(side="left", fill="y", padx=(0, 12))
        tk.Label(panel, text="Описание", bg=BG_CARD, fg=TEXT,
                 font=("Segoe UI", 13, "bold")).pack(anchor="w", padx=16,
                                                     pady=(14, 6))
        tk.Label(panel, text=RULES_TEXT, bg=BG_CARD, fg=TEXT,
                 font=("Segoe UI", 10), justify="left", wraplength=290).pack(
                     anchor="w", padx=16, pady=(0, 16))
        self.desc_panel = panel

    def _clear_board(self):
        """Очищает область игры (поле или стартовый экран)."""
        for w in self.board_area.winfo_children():
            w.destroy()

    # --- Экраны -----------------------------------------------------------

    def show_start(self):
        """Экран до начала игры: подсказка в центре (описание — слева)."""
        self._clear_board()
        tk.Label(self.board_area,
                 text="Выберите размер поля и количество лис\n"
                      "на панели справа и нажмите «Начать игру».",
                 bg=BG_CARD, fg=TEXT, font=("Segoe UI", 13),
                 justify="center").pack(expand=True, padx=30, pady=30)
        self.control.refresh()

    def show_board(self):
        """Игровое поле с баннером результата над ним."""
        self._clear_board()

        # Баннер результата — над полем (пуст, пока игра идёт)
        self.banner_var = tk.StringVar(value="")
        self.banner = tk.Label(self.board_area, textvariable=self.banner_var,
                               font=("Segoe UI", 13, "bold"), fg="#ffffff",
                               bg=BG_CARD, padx=14, pady=8, wraplength=520)
        self.banner.pack(pady=(12, 6))

        board = tk.Frame(self.board_area, bg=BG_CARD)
        board.pack(pady=(0, 12))
        # Клетки — квадраты фиксированного размера; вокруг отступ под координаты
        self.cell = 34 if self.game.size == 15 else 46
        width = COORD_MARGIN + self.game.size * self.cell
        height = self.game.size * self.cell + COORD_MARGIN
        canvas = tk.Canvas(board, width=width, height=height,
                           bg=BG_CARD, highlightthickness=0)
        canvas.pack()
        canvas.bind("<Button-1>", self.on_canvas_click)        # ЛКМ — ход
        canvas.bind("<Button-3>", self.on_canvas_right_click)  # ПКМ — пометка
        canvas.configure(cursor=CURSOR_TARGET)
        self.canvas = canvas

        self._load_fox_icon()
        self._paint_board()
        self._update_banner()
        self.control.refresh()

    def _load_fox_icon(self):
        """Загружает иконку лисы (PNG) и масштабирует её под размер клетки."""
        self.fox_photo = None
        path = resource_path("assets", "fox.png")
        if not os.path.exists(path):
            return  # останется эмодзи-запасной вариант
        try:
            img = tk.PhotoImage(file=path)
            target = self.cell - (6 if self.game.size == 15 else 10)
            factor = max(1, round(img.width() / max(1, target)))
            self.fox_photo = img.subsample(factor, factor)
        except tk.TclError:
            self.fox_photo = None

    # --- События поля -----------------------------------------------------

    def on_canvas_click(self, event):
        """ЛКМ: ход в клетку."""
        r, col = self._cell_at(event)
        if r is not None:
            self.on_cell(r, col)

    def on_canvas_right_click(self, event):
        """ПКМ: пометить/снять пометку закрытой клетки (серая, как пеленг 0)."""
        r, col = self._cell_at(event)
        if r is not None and self.game.toggle_mark(r, col):
            self._paint_board()

    def _cell_at(self, event):
        """Переводит координаты клика в (строка, колонка) или (None, None)."""
        x = event.x - COORD_MARGIN
        y = event.y
        if x < 0 or y < 0 or y >= self.game.size * self.cell:
            return None, None
        col = x // self.cell
        r = y // self.cell
        if 0 <= r < self.game.size and 0 <= col < self.game.size:
            return int(r), int(col)
        return None, None

    def on_cell(self, r, c):
        if self.game.move(r, c):
            self._paint_board()
            self._update_banner()
            self.control.refresh()

    # --- Действия игры ----------------------------------------------------

    def start_game(self, size, foxes):
        self.game.new_game(size, foxes)
        self.show_board()

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

    def quit_app(self):
        self.destroy()

    # --- Отрисовка --------------------------------------------------------

    def _update_banner(self):
        """Показывает сообщение о победе/поражении над полем."""
        g = self.game
        if g.status == "playing":
            self.banner_var.set("")
            self.banner.config(bg=BG_CARD)
        else:
            self.banner_var.set(g.message or "")
            self.banner.config(bg=WIN_BG if g.status == "win" else LOSE_BG)

    def _paint_board(self):
        """Рисует поле, содержимое клеток и координаты (буквы/цифры)."""
        c = self.canvas
        c.delete("all")
        g = self.game
        cell = self.cell
        m = COORD_MARGIN
        tiny = g.size == 15

        for r in range(g.size):
            for col in range(g.size):
                x0 = m + col * cell
                y0 = r * cell
                x1 = x0 + cell
                y1 = y0 + cell
                grey = g.is_on_grey_line(r, col) or g.is_marked(r, col)

                if (r, col) in g.revealed:
                    if (r, col) in g.found_cells:
                        fill, fg, text = FOX_BG, "#000000", "🦊"
                    else:
                        fill = NUMBER_GREY if grey else NUMBER
                        fg = NUMBER_GREY_FG if grey else NUMBER_FG
                        text = str(g.revealed[(r, col)])
                else:
                    fill = HIDDEN_GREY if grey else HIDDEN
                    fg, text = TEXT, ""

                c.create_rectangle(x0 + 1, y0 + 1, x1 - 1, y1 - 1,
                                   fill=fill, outline="#444444")

                if (r, col) in g.found_cells and self.fox_photo is not None:
                    c.create_image(x0 + cell / 2, y0 + cell / 2, image=self.fox_photo)
                elif text:
                    c.create_text(x0 + cell / 2, y0 + cell / 2, text=text, fill=fg,
                                  font=("Segoe UI", max(9, int(cell * 0.38)), "bold"))

        # Координаты: снизу — латинские буквы (слева направо),
        # слева — цифры снизу вверх (нижняя строка — 1)
        font = ("Segoe UI", 8 if tiny else 9)
        for col in range(g.size):
            c.create_text(m + col * cell + cell / 2, g.size * cell + m / 2,
                          text=chr(ord("a") + col), fill=TEXT, font=font)
        for r in range(g.size):
            c.create_text(m / 2, r * cell + cell / 2,
                          text=str(g.size - r), fill=TEXT, font=font)


def main():
    app = FoxApp()
    app.mainloop()


if __name__ == "__main__":
    main()
