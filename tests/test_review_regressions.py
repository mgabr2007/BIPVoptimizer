import unittest
import numpy as np
import pandas as pd
from core.energy_contracts import annual_element_yield, annual_netting, reference_year, BALANCE_METHOD
from core.financial_scenario import create_cash_flow_analysis, input_fingerprint
from core.optimization_engine import simple_genetic_algorithm, analyze_optimization_results
from core.demand_scenario import generate_demand_forecast
from core.research_reports import financial_section


def months(start=2024, count=12, first=1):
    return [f'{start + (first-1+i)//12}-{(first-1+i)%12+1:02d}-01' for i in range(count)]


def finance_params():
    return dict(discount_rate=.05, electricity_price=.30, export_rate=.10,
                price_escalation=0, maintenance_cost_rate=.015, system_degradation=.10,
                inverter_replacement_year=2, inverter_replacement_cost_ratio=.20,
                tax_credit=.10, rebate_amount=50)


class CrossStepTests(unittest.TestCase):
    def test_active_area_and_fraction_contract(self):
        row = dict(glass_area_m2=10, bipv_area_m2=8.5, efficiency=.20)
        self.assertEqual(annual_element_yield(row, 1000), 1700)
        with self.assertRaises(ValueError):
            annual_element_yield(dict(row, efficiency=20), 1000)
        with self.assertRaises(KeyError):
            annual_element_yield(dict(glass_area_m2=10, efficiency_percent=20), 1000)

    def test_actual_step6_output_is_accepted_by_optimizer(self):
        from pages_modules.pv_specification_unified import calculate_unified_bipv_specifications
        elements = [dict(element_id='A',glass_area=10,orientation='South',azimuth=180)]
        panel = dict(efficiency=.2,power_density=200,cost_per_m2=100,transparency=.3)
        specs = calculate_unified_bipv_specifications(elements,{'A':1000},panel,.85)
        self.assertEqual(specs.iloc[0]['annual_energy_kwh'],1700)
        params = dict(electricity_price=.3,export_rate=.1,min_coverage=.1,maintenance_rate=.015)
        demand = pd.DataFrame({'predicted_demand':[1000]})
        result,_ = simple_genetic_algorithm(specs,demand,params,
            dict(population_size=20,generations=2,mutation_rate=.1),{'A':1000})
        report = analyze_optimization_results(result,specs,demand,params,{'A':1000})
        self.assertEqual(report.iloc[0]['annual_energy_kwh'],1700)
        self.assertAlmostEqual(report.iloc[0]['annual_savings'],370-850*.015)
        with self.assertRaises(KeyError):
            calculate_unified_bipv_specifications(elements,{},panel,.85)

    def test_stale_stored_yields_cannot_change_winner_or_weight(self):
        specs = pd.DataFrame([
            dict(element_id='A', glass_area_m2=2, bipv_area_m2=2, efficiency=.1, total_cost_eur=100, capacity_kw=.2),
            dict(element_id='B', glass_area_m2=3, bipv_area_m2=3, efficiency=.1, total_cost_eur=200, capacity_kw=.3)])
        params = dict(electricity_price=.2, export_rate=0, min_coverage=.3, maintenance_rate=.015, prioritize_roi=False)
        ga = dict(population_size=30, generations=3, mutation_rate=.1, seed=42)
        demand = pd.DataFrame({'predicted_demand': [500]})
        result, _ = simple_genetic_algorithm(specs, demand, params, ga, {'A':1000, 'B':1000})
        specs['annual_energy_kwh'] = 9999
        repeated, _ = simple_genetic_algorithm(specs, demand, params, ga, {'A':1000, 'B':1000})
        self.assertEqual(result, repeated)
        report = analyze_optimization_results(result, specs, demand, params, {'A':1000, 'B':1000})
        self.assertEqual(report.iloc[0]['selection_mask'], [1, 1])
        self.assertNotEqual(report.iloc[0]['solution_id'], report.sort_values('roi', ascending=False).iloc[0]['solution_id'])

    def test_reference_year_not_five_year_sum(self):
        result = reference_year([100]*48 + [200]*12, months(count=60))
        self.assertEqual(result['annual_demand_kwh'], 2400)
        self.assertEqual(result['start'], '2028-01-01')
        for dates in ([], months(count=11), months()[:-1]+['2024-11-01'], list(reversed(months()))):
            with self.assertRaises(ValueError):
                reference_year([100]*12, dates)

    def test_scenario_calendar_and_zero_old_year(self):
        result = generate_demand_forecast([0]*12+list(range(100,112)), [], [], months(count=24,first=7))
        self.assertEqual(str(result['forecast_start_date'].date()), '2026-07-01')
        self.assertEqual(result['base_consumption'], sum(range(100,112)))
        # July seasonality is taken from the July observation, not an assumed January.
        self.assertAlmostEqual(result['seasonal_factors'][0],100/(sum(range(100,112))/12))

    def test_annual_netting_conserves_totals_and_separates_tariffs(self):
        b = annual_netting(2000, 1000, .3, .1)
        self.assertEqual(b['offset_kwh']+b['surplus_kwh'],2000)
        self.assertEqual(b['offset_kwh']+b['net_import_kwh'],1000)
        self.assertEqual(b['gross_benefit'],400)

    def test_cash_flows_degrade_and_include_all_costs(self):
        solution = dict(total_cost=1000,annual_energy_kwh=2000,annual_demand_kwh=1000,balance_method=BALANCE_METHOD)
        flows, details = create_cash_flow_analysis(solution, finance_params(), 3)
        np.testing.assert_allclose(flows,[-850,385,165,347])
        self.assertEqual(details[1]['export_revenue'],100)
        self.assertEqual(details[2]['annual_generation'],1800)
        no_degradation = finance_params();no_degradation['system_degradation']=0
        self.assertNotEqual(flows,create_cash_flow_analysis(solution,no_degradation,3)[0])
        self.assertEqual(details[1]['cash_flow'],details[1]['gross_benefit']-details[1]['maintenance_cost'])

    def test_cache_fingerprint_changes_with_inputs(self):
        base = input_fingerprint(1, {'solution_id':'A'}, {'tariff':.3},25, {'demand':100})
        for args in ((1,{'solution_id':'B'},{'tariff':.3},25,{'demand':100}),
                     (1,{'solution_id':'A'},{'tariff':.4},25,{'demand':100}),
                     (1,{'solution_id':'A'},{'tariff':.3},25,{'demand':101})):
            self.assertNotEqual(base,input_fingerprint(*args))

    def test_report_preserves_zero_missing_and_units(self):
        html=financial_section({'irr_unit':'percent','financial_metrics':{'irr':0,'payback_period':None}})
        self.assertIn('0.00%',html)
        self.assertIn('Unavailable',html)
        self.assertNotIn('0.00 years',html)
        self.assertNotIn('10.00%',financial_section({'irr':10}))
        self.assertIn('10.00%',financial_section({'irr_unit':'percent','irr':10}))

    def test_all_updated_report_paths_with_absent_and_legacy_scores(self):
        from utils.comprehensive_report_generator import generate_step2_section
        from utils.comprehensive_report_fixed import generate_step2_section_fixed
        from utils.report_step_generators import generate_step2_section as step_section
        for fn in (generate_step2_section,generate_step2_section_fixed,step_section):
            for data in ({},{'r2_score':None},{'model_r2_score':.92}):
                html=fn(data)
                self.assertIn('Not evaluated',html)
                self.assertNotIn('Random Forest Regressor',html)
                self.assertNotIn('ASHRAE 90.1 compliance integrated',html)
