import unittest

from core.financial_math import calculate_irr, calculate_npv, calculate_payback_period
from utils.calculations import calculate_financial_metrics


class FinancialMathTests(unittest.TestCase):
    def test_payback_uses_cumulative_deficit(self):
        self.assertAlmostEqual(calculate_payback_period([-1000, 600, 600]), 1 + 400 / 600)
        self.assertAlmostEqual(calculate_payback_period([-100, 40, -20, 100]), 2.8)

    def test_payback_boundaries(self):
        self.assertIsNone(calculate_payback_period([-100, 0, 30]))
        self.assertEqual(calculate_payback_period([-100, 0, 100]), 2)
        self.assertEqual(calculate_payback_period([0, 100]), 0)
        self.assertIsNone(calculate_payback_period([]))

    def test_independent_cash_flow_cases(self):
        self.assertAlmostEqual(calculate_irr([-100, 110]), 0.10)
        self.assertAlmostEqual(calculate_irr([-100, 0, 121]), 0.10)
        self.assertAlmostEqual(calculate_irr([-100, 90]), -0.10)
        self.assertAlmostEqual(calculate_irr([-1, 100]), 99.0, places=6)
        self.assertEqual(calculate_irr([-100, 100]), 0)
        self.assertAlmostEqual(calculate_npv([-100, 110], 0.10), 0)

    def test_undefined_or_ambiguous_irr(self):
        for flows in ([], [-100, 0], [0, 100], [100, 110], [-100, 230, -132]):
            self.assertIsNone(calculate_irr(flows))

    def test_legacy_utility_retains_percent_contract(self):
        result = calculate_financial_metrics(100, [110], 0.10)
        self.assertAlmostEqual(result['irr'], 10)
        self.assertAlmostEqual(result['npv'], 0)
        self.assertAlmostEqual(result['payback_period'], 100 / 110)

    def test_invalid_values(self):
        for value in (float('nan'), float('inf')):
            with self.assertRaises(ValueError):
                calculate_payback_period([-100, value])
        with self.assertRaises(ValueError):
            calculate_npv([-100, 110], -1)


if __name__ == '__main__':
    unittest.main()
