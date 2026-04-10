import unittest

from src.portfolio import build_long_only_weights


class TestPortfolio(unittest.TestCase):
    def test_stock_caps_small_universe(self):
        w = build_long_only_weights(
            {"A": 80, "B": 70, "C": 60, "D": 40},
            top_n=3,
            max_position=0.12,
            max_sector=0.5,
            score_floor=45,
        )
        self.assertTrue(w)
        self.assertLessEqual(sum(w.values()), 1.0 + 1e-9)
        for v in w.values():
            self.assertLessEqual(v, 0.12 + 1e-9)

    def test_sector_cap(self):
        sectors = {"A": "Tech", "B": "Tech", "C": "Fin", "D": "Fin"}
        w = build_long_only_weights(
            {"A": 75, "B": 74, "C": 73, "D": 72},
            sectors=sectors,
            top_n=4,
            max_position=0.5,
            max_sector=0.35,
            score_floor=45,
        )
        self.assertTrue(w)
        for sec in ("Tech", "Fin"):
            sw = sum(wt for s, wt in w.items() if sectors[s] == sec)
            self.assertLessEqual(sw, 0.35 + 1e-6)


if __name__ == "__main__":
    unittest.main()
