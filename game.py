# -*- coding: utf-8 -*-
"""Логика игры «Охота на лис» — без GUI, пригодна для тестов и повторного
использования.

Правила:
- Поле size x size, лисы расставляются случайно (без повторов в клетке).
- Клик по клетке показывает «пеленг» — число лис на той же вертикали,
  горизонтали и обеих диагоналях.
- Клетка с пеленгом 0 закрашивает серым всю свою вертикаль, горизонталь
  и обе диагонали (там гарантированно нет лис).
- Конец игры: найдены все лисы (победа) или исчерпан лимит ходов (поражение).
"""

import json
import random

FIELD_SIZES = [8, 9, 10, 15]
DEFAULT_FOXES = {8: 5, 9: 5, 10: 5, 15: 10}
SAVE_FILE = "savegame.json"
SAVE_VERSION = 1


class FoxGame:
    """Состояние и правила игры «Охота на лис»."""

    def __init__(self):
        self.reset()

    def reset(self):
        """Пустая игра без поля (нужно вызвать new_game)."""
        self.size = 9
        self.foxes = []          # [(r, c), ...] — позиции лис
        self.moves = 0           # сделано ходов
        self.found = 0           # найдено лис
        self.revealed = {}       # {(r, c): пеленг} — открытые клетки
        self.found_cells = set() # {(r, c)} — клетки с найденными лисами
        self.status = "playing"  # playing | win | lose
        self.message = None

    @property
    def max_moves(self):
        """Лимит ходов: размер поля в квадрате минус 1."""
        return self.size * self.size - 1

    # --- Создание игры ---------------------------------------------------

    def new_game(self, size=9, foxes_count=None):
        """Начинает новую игру на поле size с foxes_count лисами."""
        if size not in FIELD_SIZES:
            size = 9
        if foxes_count is None:
            foxes_count = DEFAULT_FOXES.get(size, 5)
        foxes_count = max(5, min(foxes_count, size))

        self.reset()
        self.size = size
        all_cells = [(r, c) for r in range(size) for c in range(size)]
        # random.sample выбирает уникальные клетки — две лисы не совпадут
        self.foxes = random.sample(all_cells, foxes_count)

    # --- Ход -------------------------------------------------------------

    def bearing(self, r, c):
        """Пеленг клетки: лисы на той же вертикали, горизонтали и диагоналях."""
        b = 0
        for fr, fc in self.foxes:
            if fr == r or fc == c or fr - fc == r - c or fr + fc == r + c:
                b += 1
        return b

    def move(self, r, c):
        """Открывает клетку (r, c). Возвращает True, если ход засчитан."""
        if self.status != "playing":
            return False
        if not (0 <= r < self.size and 0 <= c < self.size):
            return False
        if (r, c) in self.revealed:
            return False

        self.revealed[(r, c)] = self.bearing(r, c)
        self.moves += 1

        if (r, c) in self.foxes:
            self.found_cells.add((r, c))
            self.found += 1

        if self.found == len(self.foxes):
            self.status = "win"
            self.message = (
                f"Поздравляем! Все {self.found} лис найдены за {self.moves} ходов."
            )
        elif self.moves >= self.max_moves:
            self.status = "lose"
            self.message = (
                f"Лимит ходов ({self.max_moves}) исчерпан. "
                f"Найдено {self.found} из {len(self.foxes)} лис."
            )
        return True

    # --- Серые линии -----------------------------------------------------

    def grey_lines(self):
        """Строки/колонки/диагонали открытых нулевых клеток (там нет лис)."""
        rows, cols, d1, d2 = set(), set(), set(), set()
        for (r, c), b in self.revealed.items():
            if b == 0:
                rows.add(r)
                cols.add(c)
                d1.add(r - c)  # диагональ "\"
                d2.add(r + c)  # диагональ "/"
        return rows, cols, d1, d2

    def is_on_grey_line(self, r, c):
        """Клетка лежит на линии открытой нулевой клетки?"""
        rows, cols, d1, d2 = self.grey_lines()
        return r in rows or c in cols or (r - c) in d1 or (r + c) in d2

    # --- Сохранение / загрузка -------------------------------------------

    def to_dict(self):
        """Состояние игры в JSON-совместимом виде."""
        return {
            "version": SAVE_VERSION,
            "size": self.size,
            "foxes": [list(f) for f in self.foxes],
            "moves": self.moves,
            "found": self.found,
            "revealed": {f"{r},{c}": b for (r, c), b in self.revealed.items()},
            "found_cells": [f"{r},{c}" for r, c in self.found_cells],
            "status": self.status,
            "message": self.message,
        }

    def from_dict(self, data):
        """Восстанавливает состояние из словаря (см. to_dict)."""
        if data.get("version") != SAVE_VERSION:
            raise ValueError(f"Неизвестная версия сохранения: {data.get('version')}")
        game = FoxGame()
        game.size = data["size"]
        game.foxes = [tuple(f) for f in data["foxes"]]
        game.moves = data["moves"]
        game.found = data["found"]
        game.revealed = {
            tuple(map(int, key.split(","))): b
            for key, b in data["revealed"].items()
        }
        game.found_cells = {
            tuple(map(int, key.split(","))) for key in data["found_cells"]
        }
        game.status = data["status"]
        game.message = data["message"]
        return game

    def save(self, path=SAVE_FILE):
        """Сохраняет игру в JSON-файл."""
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)

    def load(self, path=SAVE_FILE):
        """Загружает игру из JSON-файла (заменяет текущее состояние)."""
        with open(path, "r", encoding="utf-8") as f:
            loaded = self.from_dict(json.load(f))
        self.__dict__.update(loaded.__dict__)
        return self
