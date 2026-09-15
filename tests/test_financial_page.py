"""Streamlit rerun/save boundary tests; external services and DB are stubbed."""
import unittest
from unittest.mock import patch, MagicMock
import pandas as pd
from streamlit.testing.v1 import AppTest
from core.energy_contracts import BALANCE_METHOD


class FinancialPageTests(unittest.TestCase):
    def run_page(self, save_success=True):
        from pages_modules import financial_analysis as page
        db=MagicMock()
        db.get_project_by_id.return_value={'id':1,'location':'Berlin','electricity_rates':{'import_rate':.3,'export_rate':.1}}
        db.get_optimization_results.return_value={'solutions':pd.DataFrame([dict(solution_id='weighted-best',total_cost=1000,capacity=1,
            annual_energy_kwh=1000,annual_demand_kwh=1000,balance_method=BALANCE_METHOD,maintenance_rate=.015,export_rate=.1,roi=20)])}
        db.get_pv_specifications.return_value={'fixture':'pv'}
        db.get_historical_data.return_value={'fixture':'demand'}
        db.get_radiation_analysis_data.return_value={'fixture':'radiation'}
        from services.analysis_inputs import upstream_snapshot
        from core.financial_scenario import input_fingerprint
        db.get_optimization_results.return_value['solutions']['upstream_fingerprint'] = input_fingerprint(1, {}, {}, 0, upstream_snapshot(db, 1))
        db.get_financial_analysis.return_value=None
        db.save_financial_analysis.return_value=save_success
        patches=[patch.object(page,'db_manager',db),patch('services.io.ensure_project_data_loaded',return_value=True),
                 patch('services.io.get_current_project_id',return_value=1),
                 patch.object(page,'get_grid_carbon_factor',return_value={'factor':.4}),
                 patch.object(page,'display_carbon_factor_info'),patch.object(page,'render_navigation_buttons')]
        for p in patches:p.start();self.addCleanup(p.stop)
        app=AppTest.from_string('from pages_modules.financial_analysis import render_financial_analysis\nrender_financial_analysis()')
        app.run(timeout=20)
        self.assertFalse(app.exception, str(app.exception))
        app.button(key='run_financial_analysis').click().run(timeout=20)
        self.assertFalse(app.exception,str(app.exception))
        self.assertEqual(db.save_financial_analysis.call_count,1)
        return app,db

    def test_single_save_and_input_change_hides_cached_results(self):
        app,db=self.run_page()
        self.assertIn('Net Present Value',[m.label for m in app.metric])
        app.slider(key='degradation_fin').set_value(.6).run()
        self.assertFalse(app.exception,str(app.exception))
        self.assertNotIn('Net Present Value',[m.label for m in app.metric])
        self.assertEqual(db.save_financial_analysis.call_count,1)

    def test_failed_save_does_not_report_completion(self):
        app,db=self.run_page(False)
        self.assertTrue(any('not saved' in e.value for e in app.error))
        self.assertFalse(any('completed successfully' in e.value for e in app.success))
