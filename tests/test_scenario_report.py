import unittest
from core.scenario_report import render_unevaluated_demand


class ScenarioReportTests(unittest.TestCase):
    def test_missing_metrics_do_not_become_scores(self):
        html = render_unevaluated_demand({'historical_data': {'consumption_data': [123, None]},
                                        'demand_forecast': {'model_parameters': {'algorithm': '<script>'},
                                                            'annual_predictions': [1476]}})
        self.assertIn('Not evaluated', html)
        self.assertIn('123.00', html)
        self.assertIn('1,476.00', html)
        self.assertNotIn('<script>', html)
        self.assertIn('&lt;script&gt;', html)
        self.assertNotIn('0.920', html)
