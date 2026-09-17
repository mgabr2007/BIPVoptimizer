"""Actual PostgreSQL roundtrip/rollback tests, only on an explicit local test DB."""
import json
import os
import unittest
import uuid
from urllib.parse import urlparse
from unittest.mock import patch
import psycopg2
from psycopg2 import sql
from database_manager import BIPVDatabaseManager

from tests.postgres_fixture import PostgresFixture

class PostgresFinancialTests(PostgresFixture):
    def setUp(self):
        super().setUp()
        self.payload=dict(initial_investment=100,annual_savings=10,annual_generation=100,
                          annual_export_revenue=0,annual_om_cost=1,net_annual_benefit=9,npv=-20,
                          irr=None,payback_period=None,lcoe=None,analysis_complete=True,
                          cash_flow_analysis=[{'year':0,'cash_flow':-100}],sensitivity_analysis={},
                          analysis_metadata={'irr_unit':'percent','input_fingerprint':'fixture','model_version':'financial-scenario-v3'},
                          co2_savings_annual=1,co2_savings_lifetime=2,carbon_value=3)

    def test_missing_zero_and_percent_roundtrip(self):
        for irr in (None,0,10):
            with self.subTest(irr=irr):
                self.assertTrue(self.db.save_financial_analysis(1,dict(self.payload,irr=irr)))
                loaded=self.db.get_financial_analysis(1)
                self.assertEqual(loaded['financial_metrics']['irr'],irr)
                self.assertIsNone(loaded['financial_metrics']['payback_period'])
                self.assertEqual(loaded['input_fingerprint'],'fixture')
                self.assertEqual(loaded['financial_metrics']['annual_savings'],9)
                self.assertEqual(loaded['cash_flow_analysis'],self.payload['cash_flow_analysis'])
        self.assertIsNone(self.db.get_financial_analysis(2))

    def test_error_after_delete_rolls_back_all_tables(self):
        self.assertTrue(self.db.save_financial_analysis(1,self.payload))
        broken=dict(self.payload,npv=999,co2_savings_annual='not numeric')
        with patch('database_manager.st.error'):
            self.assertFalse(self.db.save_financial_analysis(1,broken))
        self.assertEqual(self.db.get_financial_analysis(1)['financial_metrics']['npv'],-20)

    def test_legacy_units_remain_unknown(self):
        self.assertTrue(self.db.save_financial_analysis(1,dict(self.payload,irr=10)))
        with self.connect() as c:
            with c.cursor() as cur:
                cur.execute('UPDATE detailed_financial_analysis SET cash_flow_data=%s',
                            (json.dumps([{'year':0,'cash_flow':-100}]),))
        loaded=self.db.get_financial_analysis(1)
        self.assertIsNone(loaded['financial_metrics']['irr'])
        self.assertEqual(loaded['cash_flow_analysis'][0]['year'],0)

    def test_weighted_order_and_energy_metadata_roundtrip(self):
        rows=[dict(solution_id='weighted-best',total_power_kw=1,total_investment=100,
                   annual_energy_kwh=200,roi=10,net_import_kwh=800,selection_mask=[1,0],
                   selected_elements=['A'],fitness_score=.8,optimization_method='weighted-genetic-v3',
                   energy_model_version='active-area-annual-v3',annual_demand_kwh=1000,
                   balance_method='annual-netting-scenario-v1'),
              dict(solution_id='roi-best',total_power_kw=2,total_investment=200,
                   annual_energy_kwh=400,roi=20,net_import_kwh=600,selection_mask=[0,1],
                   selected_elements=['B'],fitness_score=.7,optimization_method='weighted-genetic-v3',
                   energy_model_version='active-area-annual-v3',annual_demand_kwh=1000,
                   balance_method='annual-netting-scenario-v1')]
        data=dict(solutions=rows,model_version='weighted-genetic-v3',optimization_config={
            'financial_params':{'export_rate':.1,'electricity_price':.3,'include_maintenance':False}})
        self.assertTrue(self.db.save_optimization_results(1,data))
        loaded=self.db.get_optimization_results(1)['solutions']
        self.assertEqual(loaded.iloc[0]['solution_id'],'weighted-best')
        self.assertEqual(loaded.iloc[0]['annual_demand_kwh'],1000)
        self.assertEqual(loaded.iloc[0]['maintenance_rate'],0)
        self.assertEqual(loaded.iloc[0]['export_rate'],.1)
