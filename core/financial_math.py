"""Periodic cash-flow metrics. Cash flows include investment at time zero.

IRR is a fraction here; callers convert to percent only at presentation boundaries.
Non-conventional cash flows may have multiple IRRs and intentionally return None.
Reference: https://numpy.org/numpy-financial/latest/irr.html
"""

import math

MODEL_VERSION = "financial-v2"


def _cash_flows(values):
    flows = [float(value) for value in values]
    if not all(math.isfinite(value) for value in flows):
        raise ValueError("Cash flows must be finite numbers")
    return flows


def calculate_npv(cash_flows, discount_rate):
    flows = _cash_flows(cash_flows)
    rate = float(discount_rate)
    if not math.isfinite(rate) or rate <= -1:
        raise ValueError("Discount rate must be finite and greater than -1")
    return math.fsum(cf / (1 + rate) ** i for i, cf in enumerate(flows))


def calculate_irr(cash_flows, max_iterations=1000, tolerance=1e-6):
    """Return the unique conventional investment IRR, or None if unavailable.

Supports an initial negative investment followed by nonnegative periodic flows.
Use discount factor x=1/(1+r) and bisection of the cash-flow polynomial.
This also handles negative and zero IRRs without an arbitrary rate ceiling.
"""
    flows = _cash_flows(cash_flows)
    if len(flows) < 2 or flows[0] >= 0 or any(cf < 0 for cf in flows[1:]):
        return None
    if not any(cf > 0 for cf in flows[1:]):
        return None
    if tolerance <= 0 or max_iterations < 1:
        raise ValueError("IRR tolerance and iteration count must be positive")
    scale = max(abs(cf) for cf in flows)
    normalized = [cf / scale for cf in flows]

    def residual(x):
        value = normalized[-1]
        for cf in reversed(normalized[:-1]):
            value = value * x + cf
        return value

    if abs(residual(1.0)) <= 1e-14:
        return 0.0
    low, high = 0.0, 1.0
    for _ in range(max_iterations):
        if residual(high) >= 0:
            break
        high *= 2
        if not math.isfinite(high):
            return None
    else:
        return None
    for _ in range(max_iterations):
        x = (low + high) / 2
        value = residual(x)
        if abs(value) <= min(tolerance, 1e-12):
            rate = 1 / x - 1
            return rate if math.isfinite(rate) else None
        if value > 0:
            high = x
        else:
            low = x
    return None


def calculate_payback_period(cash_flows):
    """Simple payback with linear recovery within the crossing period.

Return None when cumulative cash flow never recovers the investment.
"""
    flows = _cash_flows(cash_flows)
    if not flows:
        return None
    cumulative = flows[0]
    if cumulative >= 0:
        return 0.0
    for year, flow in enumerate(flows[1:], start=1):
        previous = cumulative
        cumulative += flow
        if cumulative >= 0:
            return year - 1 + (-previous / flow)
    return None
