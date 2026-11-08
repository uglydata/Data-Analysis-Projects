"""
Tests for the real-wage calculation.

    python test_real_wages.py          # offline (also run in CI)
    python test_real_wages.py --live   # + live check against CSP's own real-wage series
"""

import sys
import unittest

from csp_client import to_number
from real_wages import compute, industries, real_index, yoy_real
from svg_chart import line_chart


class Offline(unittest.TestCase):
    def test_real_index_hand_computed(self):
        # wage +50%, prices +20% -> real wage +25%
        idx = real_index({"2015": 1000, "2020": 1500}, {"2015": 100.0, "2020": 120.0})
        self.assertEqual(idx["2015"], (1000.0, 100.0))
        self.assertEqual(idx["2020"], (1250.0, 125.0))

    def test_real_index_skips_missing(self):
        self.assertEqual(real_index({"2015": None, "2020": 1500}, {"2015": 100.0, "2020": 120.0}), {})
        idx = real_index({"2015": 1000, "2016": None, "2017": 1100}, {"2015": 100.0, "2016": 101.0, "2017": 110.0})
        self.assertNotIn("2016", idx)
        self.assertEqual(idx["2017"][1], 100.0)

    def test_yoy_real(self):
        # net +10%, CPI +5% -> 104.8% of previous year
        self.assertEqual(yoy_real({"2015": 1000, "2016": 1100}, {"2015": 100.0, "2016": 105.0}), {"2016": 104.8})

    def test_industries_from_metadata(self):
        meta = {"variables": [{"code": "NACE", "values": ["TOTAL", "A", "A01", "J", "J62", "J63"],
                               "valueTexts": ["TOTAL", "Agri", "Crop", "ICT", "Programming", "Info"]}]}
        self.assertEqual(list(industries(meta)), ["TOTAL", "A", "J", "J62"])

    def test_compute_end_to_end(self):
        labels = {"TOTAL": "Total", "X": "Confidential sector"}
        wages = [
            {"GRS_NET": "GRS", "NACE": "TOTAL", "TIME": "2015", "value": 1000},
            {"GRS_NET": "GRS", "NACE": "TOTAL", "TIME": "2025", "value": 2000},
            {"GRS_NET": "GRS", "NACE": "X", "TIME": "2015", "value": to_number(".")},
            {"GRS_NET": "GRS", "NACE": "X", "TIME": "2025", "value": 3000},
            {"GRS_NET": "NET", "NACE": "TOTAL", "TIME": "2015", "value": 800},
            {"GRS_NET": "NET", "NACE": "TOTAL", "TIME": "2025", "value": 1600},
        ]
        cpi = [{"TIME": "2015", "value": 100.0}, {"TIME": "2025", "value": 160.0}]
        official = [{"TIME": "2025", "Real wages and salaries of the employees": 125.0}]
        long_rows, summary, check = compute(labels, wages, cpi, official)
        self.assertEqual([r["nace"] for r in summary], ["TOTAL"])          # confidential base year dropped
        self.assertEqual(summary[0]["nominal_change_pct"], 100.0)
        self.assertEqual(summary[0]["real_change_pct"], 25.0)
        self.assertEqual(check, [{"year": "2025", "computed_real_net_pct_prev": 125.0,
                                  "csp_real_net_pct_prev": 125.0, "diff_pp": 0.0}])
        self.assertEqual(len(long_rows), 2)

    def test_svg_is_well_formed(self):
        import xml.etree.ElementTree as ET
        svg = line_chart([{"name": "A & B", "points": [(2015, 100), (2016, 110)], "highlight": True},
                          {"name": "C", "points": [(2015, 100), (2016, 95)], "highlight": False}], title="t <x>")
        ET.fromstring(svg)


class Live(unittest.TestCase):
    def test_matches_csp_real_wage_series(self):
        from csp_client import CspClient
        from real_wages import pull
        _, _, check = compute(*pull(CspClient()))
        self.assertGreaterEqual(len(check), 10)
        # CSP publishes rounded averages and indices, so allow a few tenths of a point
        self.assertLessEqual(max(abs(c["diff_pp"]) for c in check), 0.3)


if __name__ == "__main__":
    live = "--live" in sys.argv
    sys.argv = [a for a in sys.argv if a != "--live"]
    loader, suite = unittest.TestLoader(), unittest.TestSuite()
    suite.addTests(loader.loadTestsFromTestCase(Offline))
    if live:
        suite.addTests(loader.loadTestsFromTestCase(Live))
    sys.exit(not unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful())
