import itertools
import unittest
import random
import pandas as pd
from core.optimization_engine import (
    simple_genetic_algorithm, evaluate_individual, analyze_optimization_results,
)


class OptimizationTests(unittest.TestCase):
    def setUp(self):
        self.specs = pd.DataFrame([
            {'element_id': 'A', 'glass_area_m2': 2, 'efficiency_percent': 10,
             'total_cost_eur': 100, 'annual_energy_kwh': 200, 'capacity_kw': 0.2},
            {'element_id': 'B', 'glass_area_m2': 3, 'efficiency_percent': 10,
             'total_cost_eur': 200, 'annual_energy_kwh': 300, 'capacity_kw': 0.3},
        ])
        self.radiation = {'A': 1000, 'B': 1000}
        self.demand = pd.DataFrame({'predicted_demand': [250, 250]})
        self.finance = {'electricity_price': 0.2, 'min_coverage': 0.3,
                        'maintenance_rate': 0.015, 'prioritize_roi': False}
        self.ga = {'population_size': 30, 'generations': 3, 'mutation_rate': 0.1, 'seed': 42}

    def run_search(self, specs=None, **overrides):
        return simple_genetic_algorithm(self.specs if specs is None else specs, self.demand,
                                        self.finance, self.ga, overrides.get('radiation', self.radiation))

    def test_single_element_and_deduplication(self):
        result, history = self.run_search(self.specs.iloc[:1])
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][3], [1])
        self.assertEqual(len(history), 3)

    def test_small_search_matches_exhaustive_weighted_best(self):
        results, _ = self.run_search()
        exhaustive = [evaluate_individual(mask, self.specs, self.demand, self.finance, self.radiation)[0]
                      for mask in itertools.product((0, 1), repeat=2)]
        self.assertAlmostEqual(results[0][1], max(exhaustive))
        self.assertEqual(len(results), len({tuple(r[3]) for r in results}))

    def test_missing_input_not_silently_zero_fitness(self):
        with self.assertRaises(ValueError):
            self.run_search(self.specs.iloc[:0])
        with self.assertRaises(ValueError):
            self.run_search(radiation={'A': 1000})
        with self.assertRaises(ValueError):
            self.run_search(self.specs.drop(columns=['total_cost_eur']))

    def test_impossible_coverage_returns_no_solution(self):
        self.finance['min_coverage'] = 1
        self.assertEqual(self.run_search(self.specs.iloc[:1])[0], [])

    def test_seed_does_not_mutate_global_rng(self):
        random.seed(17)
        state = random.getstate()
        first = self.run_search()
        self.assertEqual(random.getstate(), state)
        self.assertEqual(first, self.run_search())

    def test_report_uses_scored_radiation_and_same_maintenance(self):
        self.specs['annual_energy_kwh'] = 9999  # Must not replace scored yield in reports.
        result, _ = self.run_search()
        report = analyze_optimization_results(result, self.specs, self.demand, self.finance, self.radiation)
        row = report[report['n_selected_elements'] == 2].iloc[0]
        self.assertEqual(row['annual_energy_kwh'], 500)
        self.assertEqual(row['annual_savings'], 100 - 300 * 0.015)
        self.assertAlmostEqual(row['roi'], row['annual_savings'] / 300 * 100)
