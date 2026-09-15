"""Actual fresh-schema workflow under a nonprivileged owned-project connection."""
import pandas as pd
from tests.postgres_fixture import PostgresFixture
from tests import test_research_workflow as search_tests
from core.multiobjective import compare_searches
from services.run_store import append_run,get_run,list_runs
from services.authentication import Principal
from scripts.migrate import migrate,grant_runtime
from contextlib import closing

class WorkflowDatabaseTests(PostgresFixture):
    def test_input_stages_search_and_history_under_runtime_role(self):
        p=self.project_id
        dates=pd.date_range('2020-01-01',periods=36,freq='MS').strftime('%Y-%m-%d').tolist()
        self.assertTrue(self.db.save_historical_data(p,{'consumption_data':[250]*36,'date_data':dates,'annual_consumption':3000}))
        self.assertTrue(self.db.save_ai_model_data(p,{'model_type':'scenario-unvalidated','forecast_data':{},'demand_predictions':[]}))
        self.assertEqual(len(self.db.get_historical_data(p)['consumption_data']),36)
        self.assertTrue(self.db.save_weather_data(p,{'annual_ghi':1000,'generation_method':'test-fixture','tmy_data':[]}))
        self.assertEqual(float(self.db.get_weather_data(p)['annual_ghi']),1000)
        self.assertTrue(self.db.save_building_elements(p,[{'element_id':'a','glass_area':10,'pv_suitable':True}]))
        self.assertTrue(self.db.save_radiation_analysis(p,{'element_radiation':[{'element_id':'a','annual_radiation':1000}]}))
        self.assertTrue(self.db.save_pv_specifications(p,{'panel_type':'fixture','efficiency':.15,'transparency':.2,'cost_per_m2':100,'power_density':150,'installation_factor':1.2}))
        self.assertTrue(self.db.save_yield_demand_data(p,{'total_annual_yield':1500,'annual_demand':3000,'active_area_m2':10}))
        comparison=compare_searches(*search_tests.SearchTests().inputs())
        data={'method':'nsga-ii-v1','model_version':'dual-search-v1','solutions':comparison['nsga2'].to_dict('records'),
              'optimization_config':{'input_snapshot':{'fixture':'explicit'}},'comparison':comparison}
        self.assertTrue(self.db.save_optimization_results(p,data))
        first=self.db.get_optimization_results(p)['solutions'].iloc[0]['run_id']
        self.assertTrue(self.db.save_optimization_results(p,data))
        with self.connect() as c:
            self.assertEqual(len(list_runs(c,p)),2)
            self.assertEqual(get_run(c,first)['inputs']['input_snapshot'],{'fixture':'explicit'})
            with c.cursor() as cur:
                cur.execute('SELECT project_id FROM project_report_view');self.assertTrue(cur.fetchall())
        with self.connect_as(Principal('https://test.example','b')) as c:
            with c.cursor() as cur:
                cur.execute('SELECT * FROM project_report_view');self.assertEqual(cur.fetchall(),[])

    def test_migration_repeat_preserves_owners_and_existing_evidence(self):
        with self.connect() as c:
            run=append_run(c,self.project_id,'fixture','fixture',{'x':1},{'y':2},'v1')
        with closing(self.admin()) as c:
            migrate(c);grant_runtime(c,self.role)
        with self.connect() as c:self.assertEqual(get_run(c,run)['results'],{'y':2})
