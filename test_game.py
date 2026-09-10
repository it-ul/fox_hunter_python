# -*- coding: utf-8 -*-
"""Тесты логики игры (game.py). Запуск: python test_game.py"""

import json
import os
import sys
import tempfile
import unittest

import game as gm


class FoxGameTest(unittest.TestCase):
    def test_new_game_places_unique_foxes(self):
        g = gm.FoxGame()
        g.new_game(9, 5)
        self.assertEqual(g.size, 9)
        self.assertEqual(len(g.foxes), 5)
        self.assertEqual(len(set(g.foxes)), 5)  # лисы не повторяются
        for r, c in g.foxes:
            self.assertTrue(0 <= r < 9 and 0 <= c < 9)

    def test_foxes_count_clamped(self):
        g = gm.FoxGame()
        g.new_game(8, 99)   # больше размера поля
        self.assertEqual(len(g.foxes), 8)
        g.new_game(8, 1)    # меньше минимума
        self.assertEqual(len(g.foxes), 5)
        g.new_game(999)     # неизвестный размер -> 9x9
        self.assertEqual(g.size, 9)

    def test_bearing_logic(self):
        g = gm.FoxGame()
        g.new_game(8, 5)
        g.foxes = [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4)]  # детерминированно
        # (0,0) — лиса: все 5 на строке 0
        self.assertEqual(g.bearing(0, 0), 5)
        # (1,1): вертикаль (0,1) + диагонали (0,0),(0,2) -> 3
        self.assertEqual(g.bearing(1, 1), 3)
        # (7,6): ни одной линии -> 0
        self.assertEqual(g.bearing(7, 6), 0)

    def test_move_reveals_and_counts(self):
        g = gm.FoxGame()
        g.new_game(8, 5)
        g.foxes = [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4)]
        self.assertTrue(g.move(0, 0))       # попадание в лису
        self.assertEqual(g.found, 1)
        self.assertIn((0, 0), g.found_cells)
        self.assertEqual(g.revealed[(0, 0)], 5)
        self.assertEqual(g.moves, 1)
        self.assertFalse(g.move(0, 0))      # повторный ход не засчитан
        self.assertEqual(g.moves, 1)

    def test_invalid_moves_ignored(self):
        g = gm.FoxGame()
        g.new_game(8, 5)
        self.assertFalse(g.move(-1, 0))
        self.assertFalse(g.move(8, 0))
        self.assertFalse(g.move(3, 99))
        self.assertEqual(g.moves, 0)

    def test_grey_lines(self):
        g = gm.FoxGame()
        g.new_game(8, 5)
        g.foxes = [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4)]
        g.move(7, 6)  # пеленг 0
        self.assertTrue(g.is_on_grey_line(7, 0))   # та же строка
        self.assertTrue(g.is_on_grey_line(0, 6))   # та же колонка
        self.assertTrue(g.is_on_grey_line(6, 7))   # диагональ "/" (6+7=13)
        self.assertTrue(g.is_on_grey_line(6, 5))   # диагональ "\" (6-5=1)
        self.assertFalse(g.is_on_grey_line(1, 1))  # вне линий

    def test_win(self):
        g = gm.FoxGame()
        g.new_game(8, 2)
        g.foxes = [(0, 0), (0, 1)]
        g.move(0, 0)
        g.move(0, 1)
        self.assertEqual(g.status, "win")
        self.assertIn("Поздравляем", g.message)
        self.assertFalse(g.move(0, 2))  # игра окончена

    def test_max_moves_depends_on_size(self):
        g = gm.FoxGame()
        g.new_game(8)
        self.assertEqual(g.max_moves, 63)
        g.new_game(9)
        self.assertEqual(g.max_moves, 80)
        g.new_game(10)
        self.assertEqual(g.max_moves, 99)
        g.new_game(15)
        self.assertEqual(g.max_moves, 224)

    def test_lose(self):
        g = gm.FoxGame()
        g.new_game(8, 5)
        g.foxes = [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4)]
        # Лимит ходов на 8x8: 64 - 1 = 63. Обходим все клетки кроме последней
        # лисы: 63 хода, найдено 4 из 5 -> поражение.
        for r in range(8):
            for c in range(8):
                if (r, c) != (0, 4):
                    g.move(r, c)
        self.assertEqual(g.moves, 63)
        self.assertEqual(g.status, "lose")
        self.assertIn("Лимит ходов (63)", g.message)
        self.assertFalse(g.move(0, 4))  # игра окончена

    def test_save_load_roundtrip(self):
        g = gm.FoxGame()
        g.new_game(8, 5)
        g.foxes = [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4)]
        g.move(0, 0)   # лиса
        g.move(1, 1)   # пеленг 3
        g.move(7, 6)   # пеленг 0
        with tempfile.TemporaryDirectory() as td:
            path = os.path.join(td, "save.json")
            g.save(path)

            # файл существует и содержит валидный JSON с версией
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            self.assertEqual(data["version"], gm.SAVE_VERSION)

            # загрузка в новый объект восстанавливает всё состояние
            g2 = gm.FoxGame()
            g2.load(path)
            self.assertEqual(g2.size, g.size)
            self.assertEqual(g2.foxes, g.foxes)
            self.assertEqual(g2.moves, g.moves)
            self.assertEqual(g2.found, g.found)
            self.assertEqual(g2.revealed, g.revealed)
            self.assertEqual(g2.found_cells, g.found_cells)
            self.assertEqual(g2.status, g.status)
            self.assertEqual(g2.message, g.message)

            # из сохранённого состояния можно продолжать игру
            g2.move(7, 5)
            self.assertEqual(g2.moves, g.moves + 1)
            self.assertIn((7, 5), g2.revealed)

    def test_load_rejects_wrong_version(self):
        with tempfile.TemporaryDirectory() as td:
            path = os.path.join(td, "bad.json")
            with open(path, "w", encoding="utf-8") as f:
                json.dump({"version": 999, "size": 9}, f)
            g = gm.FoxGame()
            with self.assertRaises(ValueError):
                g.load(path)


    def test_coord_label(self):
        """Координаты клеток в шахматной нотации: буквы + цифры снизу вверх."""
        self.assertEqual(gm.coord_label(8, 0, 0), "a8")   # левый верх
        self.assertEqual(gm.coord_label(8, 7, 7), "h1")   # правый низ
        self.assertEqual(gm.coord_label(8, 4, 4), "e4")
        self.assertEqual(gm.coord_label(15, 14, 0), "a1")
        self.assertEqual(gm.coord_label(15, 14, 14), "o1")
        self.assertEqual(gm.coord_label(9, 0, 8), "i9")

    def test_toggle_mark(self):
        """ПКМ-пометка: переключается, только для закрытых клеток идущей игры."""
        g = gm.FoxGame()
        g.new_game(8, 5)
        self.assertTrue(g.toggle_mark(0, 0))     # поставить
        self.assertTrue(g.is_marked(0, 0))
        self.assertTrue(g.toggle_mark(0, 0))     # снять
        self.assertFalse(g.is_marked(0, 0))
        self.assertFalse(g.toggle_mark(99, 99))  # вне поля
        g.move(3, 3)                             # открытая клетка
        self.assertFalse(g.toggle_mark(3, 3))
        g.status = "win"                         # игра окончена
        self.assertFalse(g.toggle_mark(1, 1))

    def test_log_records_moves(self):
        """Протокол ходов: координата, пеленг, лиса есть/нет."""
        g = gm.FoxGame()
        g.new_game(8, 2)
        g.foxes = [(0, 0), (0, 1)]
        g.move(0, 0)
        g.move(1, 1)
        self.assertEqual(len(g.log), 2)
        self.assertEqual(g.log[0], (0, 0, 2, True))    # в (0,0) лиса, пеленг 2
        self.assertEqual(g.log[1], (1, 1, 2, False))   # (1,1) не лиса, пеленг 2

    def test_save_load_marks_and_log(self):
        """Пометки и протокол сохраняются и восстанавливаются."""
        g = gm.FoxGame()
        g.new_game(8, 5)
        g.foxes = [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4)]
        g.toggle_mark(7, 7)
        g.move(0, 0)
        with tempfile.TemporaryDirectory() as td:
            path = os.path.join(td, "s.json")
            g.save(path)
            g2 = gm.FoxGame()
            g2.load(path)
            self.assertEqual(g2.marks, g.marks)
            self.assertEqual(g2.log, g.log)
            self.assertTrue(g2.is_marked(7, 7))


if __name__ == "__main__":
    unittest.main()
