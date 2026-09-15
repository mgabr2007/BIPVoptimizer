import itertools
import random
import unittest
import numpy as np
import pandas as pd
from core.time_series_research import matched_balance,pv_profile,interval_frame
from core.evaluated_forecast import evaluate_forecast
from core.multiobjective import nsga2,compare_searches,objective_values

class IntervalTests(unittest.TestCase):
    def test_mismatch_is_not_annual_netting_and_conserves_every_interval(self):
        f=pd.DataFrame({'timestamp':pd.date_range('2024-01-01',periods=4,freq='30min',tz='UTC'),
                        'generation_kwh':[2,0,3,0],'demand_kwh':[0,2,1,2]})
        rows,s=matched_balance(f,.3,.1)
        self.assertEqual(s['gross_benefit'],.7)
        np.testing.assert_allclose(rows.generation_kwh,rows.offset_kwh+rows.surplus_kwh)
        np.testing.assert_allclose(rows.demand_kwh,rows.offset_kwh+rows.net_import_kwh)
        self.assertEqual(s['net_import_kwh'],4)

    def test_invalid_time_and_missing_intervals_rejected(self):
        f=pd.DataFrame({'timestamp':['2024-01-01T00:00Z','2024-01-01T01:00Z','2024-01-01T03:00Z'],
                        'generation_kwh':[1,2,3],'demand_kwh':[1,2,3]})
        with self.assertRaises(ValueError):matched_balance(f,.3,.1)
        f.timestamp=['2024-01-01T00:00','2024-01-01T01:00','2024-01-01T02:00']
        with self.assertRaises(ValueError):matched_balance(f,.3,.1)
        f.timestamp=pd.date_range('2024-01-01',periods=3,freq='h',tz='UTC')
        with self.assertRaises(ValueError):matched_balance(f,.3,.1,require_year=True)

    def test_horizontal_diffuse_benchmark_and_half_hour_energy(self):
        f=pd.DataFrame({'timestamp':pd.date_range('2024-03-20T11:00Z',periods=2,freq='30min'),
                        'ghi':100.,'dni':0.,'dhi':100.,'temp_air':25.,'wind_speed':1.})
        p=pv_profile(f,latitude=0,longitude=0,tilt=0,azimuth=180,active_area_m2=10,
                     efficiency=.2,gamma_pdc=0,inverter_efficiency=1)
        np.testing.assert_allclose(p.poa_w_m2,100)
        np.testing.assert_allclose(p.dc_kw,.2)
        np.testing.assert_allclose(p.generation_kwh,.1)
        p=pv_profile(f,latitude=0,longitude=0,tilt=0,azimuth=180,active_area_m2=10,
                     efficiency=.2,gamma_pdc=0,inverter_efficiency=1,ac_limit_kw=.1)
        np.testing.assert_allclose(p.generation_kwh,.05)
        f.timestamp=pd.date_range('2024-03-20T00:00Z',periods=2,freq='30min')
        p=pv_profile(f,latitude=0,longitude=0,tilt=0,azimuth=180,active_area_m2=10,efficiency=.2)
        np.testing.assert_allclose(p.generation_kwh,0)

class ForecastTests(unittest.TestCase):
    def test_holdout_is_never_used_as_features_or_training(self):
        f=pd.DataFrame({'date':pd.date_range('2020-01-01',periods=48,freq='MS'),
                        'consumption_kwh':np.tile(np.arange(1,13)*100.,4)})
        a=evaluate_forecast(f)
        f.loc[36:,'consumption_kwh']*=3
        b=evaluate_forecast(f)
        np.testing.assert_allclose(a['evaluation'].random_forest_kwh,b['evaluation'].random_forest_kwh)
        self.assertEqual(a['metrics'].iloc[1].mae_kwh,0)
        self.assertGreater(b['metrics'].iloc[1].mae_kwh,0)
        self.assertEqual(len(a['forecast']),12)
        self.assertEqual(a['forecast'].date.iloc[0],pd.Timestamp('2024-01-01'))

class SearchTests(unittest.TestCase):
    def inputs(self):
        specs=pd.DataFrame({'element_id':['a','b','c'],'glass_area_m2':[10,10,10],
                            'bipv_area_m2':[10,10,10],'efficiency':[.1,.2,.15],
                            'total_cost_eur':[100,200,500],'capacity_kw':[1,2,1.5]})
        demand=pd.DataFrame({'predicted_demand':[3000.]})
        params={'electricity_price':.3,'export_rate':.1,'min_coverage':.1}
        settings={'population_size':40,'generations':5,'mutation_rate':.3,'seed':42}
        return specs,demand,params,settings,{'a':1000,'b':1000,'c':1000}

    def test_front_matches_exhaustive_three_element_oracle_and_rng_is_local(self):
        args=self.inputs();before=random.getstate()
        front,meta=nsga2(*args)
        self.assertEqual(before,random.getstate())
        evaluated={m:objective_values(m,args[0],args[1],args[2],args[4]) for m in itertools.product([0,1],repeat=3)}
        feasible={k:v for k,v in evaluated.items() if v is not None}
        def dominates(a,b):return a[0]<=b[0] and a[1]>=b[1] and a[2]>=b[2] and a!=b
        expected={k for k,v in feasible.items() if not any(dominates(o,v) for o in feasible.values())}
        self.assertEqual({tuple(m) for m in front.selection_mask},expected)
        repeated,_=nsga2(*args)
        self.assertEqual(front.to_dict('records'),repeated.to_dict('records'))
        comparison=compare_searches(*args)
        self.assertEqual(len(comparison['comparison']),2)
        self.assertFalse(comparison['metadata']['global_optimality_certified'])
