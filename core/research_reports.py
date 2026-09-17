"""Conservative report boundaries: no inferred evaluation or financial units."""
from html import escape
import math
from core.scenario_report import render_unevaluated_demand


def demand_section(data):
    # This application currently has no evaluated forecasting pipeline. Legacy
    # scores alone cannot establish validation provenance or a model identity.
    return render_unevaluated_demand(data)


def financial_section(data):
    financial = data.get('financial_analysis', data) or {}
    if not isinstance(financial, dict):
        financial = {}
    metadata = financial.get('analysis_metadata') or financial
    metrics = financial.get('financial_metrics', financial)
    if not isinstance(metrics, dict):
        metrics = {}
    verified_units = metadata.get('irr_unit') == 'percent'

    def display(value, suffix=''):
        try:
            value = float(value)
            return f'{value:,.2f}{suffix}' if math.isfinite(value) else 'Unavailable'
        except (TypeError, ValueError):
            return 'Unavailable'

    rows = [('NPV', metrics.get('npv'), ' €'),
            ('IRR', metrics.get('irr') if verified_units else None, '%'),
            ('Simple payback', metrics.get('payback_period'), ' years'),
            ('First-year net benefit', metrics.get('annual_savings'), ' €'),
            ('Lifetime net cash flows', metrics.get('lifetime_savings'), ' €')]
    html = '<section class="step-section"><h2>Step 9: Financial scenario</h2>'
    html += '<p>Experimental annual-netting scenario, not a validated time-matched energy balance.</p>'
    if not verified_units:
        html += '<p>Legacy IRR units are unverified; IRR is withheld.</p>'
    html += '<p>Unavailable payback means recovery is not established; it does not mean immediate recovery.</p>'
    html += '<table><tr><th>Metric</th><th>Value</th></tr>'
    html += ''.join(f'<tr><td>{label}</td><td>{display(value, unit)}</td></tr>' for label, value, unit in rows)
    html += '</table><h3>Cash flows</h3><table><tr><th>Year</th><th>Net cash flow (€)</th></tr>'
    for row in financial.get('cash_flow_analysis') or []:
        html += f"<tr><td>{escape(str(row.get('year', '')))}</td><td>{display(row.get('cash_flow'))}</td></tr>"
    return html + '</table></section>'
