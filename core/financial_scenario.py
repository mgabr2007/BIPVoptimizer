"""Cash flows for an explicitly annual-netted, unevaluated energy scenario."""
import hashlib
import json
from core.energy_contracts import annual_netting, nonnegative, BALANCE_METHOD

MODEL_VERSION = 'financial-scenario-v3'


def input_fingerprint(project_id, solution, parameters, lifetime, upstream):
    def normalize(value):
        if hasattr(value, 'to_dict') and hasattr(value, 'columns'):
            return normalize(value.to_dict('records'))
        if isinstance(value, dict):
            return {str(k): normalize(v) for k, v in value.items()}
        if isinstance(value, (list, tuple)):
            return [normalize(v) for v in value]
        if hasattr(value, 'tolist'):
            return normalize(value.tolist())
        return value
    payload = normalize([MODEL_VERSION, project_id, solution, parameters, lifetime, upstream])
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str, allow_nan=False).encode()).hexdigest()


def create_cash_flow_analysis(solution_data, financial_params, system_lifetime, interval_profile=None):
    cost = nonnegative(solution_data['total_cost'], 'Initial cost')
    energy = nonnegative(solution_data['annual_energy_kwh'], 'Annual energy')
    demand = nonnegative(solution_data['annual_demand_kwh'], 'Annual demand')
    profile=None
    if interval_profile is not None:
        import numpy as np
        from core.time_series_research import matched_balance, BALANCE_VERSION
        profile,summary=matched_balance(interval_profile,0,0,require_year=True)
        if solution_data.get('balance_method')!=BALANCE_VERSION:
            raise ValueError('Time-matched inputs require matching method metadata')
        if not np.isclose(summary['generation_kwh'],energy) or not np.isclose(summary['demand_kwh'],demand):
            raise ValueError('Annual totals must equal the supplied interval profile')
    elif solution_data.get('balance_method') != BALANCE_METHOD:
        raise ValueError('Regenerate optimization with explicit annual-netting scenario metadata')
    if isinstance(system_lifetime, bool) or int(system_lifetime) != system_lifetime or system_lifetime < 1:
        raise ValueError('Lifetime must be a positive integer')
    lifetime = int(system_lifetime)
    degradation = nonnegative(financial_params['system_degradation'], 'Degradation')
    tax = nonnegative(financial_params['tax_credit'], 'Tax credit')
    if degradation >= 1 or tax > 1:
        raise ValueError('Degradation must be below one and tax credit at most one')
    maintenance = cost * nonnegative(financial_params['maintenance_cost_rate'], 'Maintenance rate')
    replacement_cost = cost * nonnegative(financial_params['inverter_replacement_cost_ratio'], 'Replacement ratio')
    replacement_year = financial_params['inverter_replacement_year']
    if int(replacement_year) != replacement_year or replacement_year < 1:
        raise ValueError('Replacement year must be a positive integer')
    net_investment = cost * (1 - tax) - nonnegative(financial_params['rebate_amount'], 'Rebate')
    if net_investment < 0:
        raise ValueError('Incentives must not exceed initial investment')
    escalation = nonnegative(financial_params['price_escalation'], 'Price escalation')
    import_rate = nonnegative(financial_params['electricity_price'], 'Import tariff')
    export_rate = nonnegative(financial_params['export_rate'], 'Export tariff')
    flows = [-net_investment]
    details = [{'year': 0, 'cash_flow': -net_investment, 'cumulative_cash_flow': -net_investment,
                'annual_savings': 0.0, 'maintenance_cost': 0.0, 'inverter_cost': 0.0,
                'annual_generation': 0.0, 'export_revenue': 0.0}]
    for year in range(1, lifetime + 1):
        generation = energy * (1 - degradation) ** (year - 1)
        # Import and export prices share the explicitly selected escalation scenario.
        price_factor = (1 + escalation) ** (year - 1)
        if profile is None:
            balance = annual_netting(generation, demand, import_rate * price_factor, export_rate * price_factor)
        else:
            supply=profile.generation_kwh.to_numpy()*(1-degradation)**(year-1)
            load=profile.demand_kwh.to_numpy()
            offset=float(np.minimum(supply,load).sum())
            surplus=float(supply.sum()-offset)
            balance={'offset_kwh':offset,'surplus_kwh':surplus,'net_import_kwh':float(load.sum()-offset),
                     'avoided_import_cost':offset*import_rate*price_factor,
                     'export_revenue':surplus*export_rate*price_factor,'balance_method':BALANCE_VERSION}
            balance['gross_benefit']=balance['avoided_import_cost']+balance['export_revenue']
        inverter = replacement_cost if year == replacement_year else 0.0
        flow = balance['gross_benefit'] - maintenance - inverter
        flows.append(flow)
        details.append({'year': year, 'cash_flow': flow, 'cumulative_cash_flow': sum(flows),
                        'annual_savings': balance['gross_benefit'], 'maintenance_cost': maintenance,
                        'inverter_cost': inverter, 'annual_generation': generation,
                        'export_revenue': balance['export_revenue'], **balance})
    return flows, details
