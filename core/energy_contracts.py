"""Shared experimental annual energy accounting; not a validated AC yield model."""
import math
from datetime import datetime

ENERGY_MODEL_VERSION = "active-area-annual-v3"
BALANCE_METHOD = "annual-netting-scenario-v1"


def nonnegative(value, name):
    number = float(value)
    if not math.isfinite(number) or number < 0:
        raise ValueError(f"{name} must be finite and nonnegative")
    return number


def annual_element_yield(spec, radiation):
    """Active area × annual irradiation × fractional efficiency, before losses.

    Unversioned, ambiguous legacy percent/fraction records must be regenerated.
    """
    area = nonnegative(spec['bipv_area_m2'], 'Active BIPV area')
    glass = nonnegative(spec['glass_area_m2'], 'Glass area')
    efficiency = nonnegative(spec['efficiency'], 'Fractional efficiency')
    if area > glass or efficiency > 1:
        raise ValueError("Active area must not exceed glass area; efficiency must be a fraction")
    return area * nonnegative(radiation, 'Annual irradiation') * efficiency


def annual_netting(generation, demand, import_rate, export_rate):
    """Annual netting scenario, not measured/time-matched self-consumption.

    For export_rate <= import_rate this revenue is an upper bound on time-matched
    revenue with the same annual totals, no storage and no curtailment.
    """
    generation = nonnegative(generation, 'Generation')
    demand = nonnegative(demand, 'Demand')
    import_rate = nonnegative(import_rate, 'Import tariff')
    export_rate = nonnegative(export_rate, 'Export tariff')
    offset = min(generation, demand)
    surplus = max(0.0, generation - demand)
    return {'offset_kwh': offset, 'surplus_kwh': surplus,
            'net_import_kwh': max(0.0, demand - generation),
            'avoided_import_cost': offset * import_rate,
            'export_revenue': surplus * export_rate,
            'gross_benefit': offset * import_rate + surplus * export_rate,
            'balance_method': BALANCE_METHOD}


def reference_year(consumption, dates):
    """Most recent 12 consecutive monthly observations, requiring explicit dates.

    No partial-year extrapolation or multi-year sum is silently called annual.
    Reject missing, duplicate, unordered or gapped months.
    """
    values = [nonnegative(v, 'Monthly consumption') for v in consumption]
    if len(values) < 12 or not dates or len(dates) != len(values):
        raise ValueError("Provide at least 12 monthly observations with one ISO date per observation")
    parsed = [datetime.strptime(str(d), '%Y-%m-%d').replace(day=1) for d in dates]
    months = [d.year * 12 + d.month for d in parsed]
    if any(b - a != 1 for a, b in zip(months, months[1:])):
        raise ValueError("Historical months must be ordered, unique and consecutive")
    total = math.fsum(values[-12:])
    if total <= 0:
        raise ValueError("The most recent 12 months must have positive total consumption")
    return {'annual_demand_kwh': total, 'values': values[-12:],
            'dates': parsed[-12:], 'start': parsed[-12].strftime('%Y-%m-%d'),
            'end': parsed[-1].strftime('%Y-%m-%d'),
            'method': 'latest-12-consecutive-months-v1'}
