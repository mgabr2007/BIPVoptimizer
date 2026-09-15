import unittest
import numpy as np
from core.demand_scenario import generate_demand_forecast


class DemandScenarioTests(unittest.TestCase):
    def test_metadata_is_unevaluated_and_rng_is_local(self):
        values = [100 + month for month in range(12)]
        np.random.seed(123)
        before = np.random.get_state()
        first = generate_demand_forecast(values, [], [], [f'2024-{month:02d}-01' for month in range(1, 13)])
        after = np.random.get_state()
        np.testing.assert_array_equal(before[1], after[1])
        self.assertEqual(before[2:], after[2:])
        second = generate_demand_forecast(values, [], [], [f'2024-{month:02d}-01' for month in range(1, 13)])
        self.assertEqual(first['monthly_predictions'], second['monthly_predictions'])
        self.assertIsNone(first['model_parameters']['accuracy'])
        self.assertEqual(first['model_parameters']['evaluation_status'], 'not_evaluated')
        self.assertNotIn('temperature', first['model_parameters']['features'])
        self.assertEqual(len(first['monthly_predictions']), 300)
        for year, total in enumerate(first['annual_predictions']):
            self.assertAlmostEqual(total, sum(first['monthly_predictions'][year * 12:(year + 1) * 12]))

    def test_missing_and_invalid_consumption_rejected(self):
        for values in ([], [0] * 12, [-1] * 12, [float('nan')], [float('inf')]):
            with self.assertRaises(ValueError):
                generate_demand_forecast(values, [], [])
