"""Small, honest report section for demand data without evaluated ML metrics."""
from html import escape
import math


def render_unevaluated_demand(project_data):
    historical = project_data.get('historical_data') or {}
    if not isinstance(historical, dict):
        historical = {}
    forecast = project_data.get('demand_forecast') or historical.get('demand_forecast') or {}
    if not isinstance(forecast, dict):
        forecast = {}
    values = historical.get('consumption_data') or historical.get('consumption') or []
    if not isinstance(values, list):
        values = []
    rows = []
    for index, value in enumerate(values, 1):
        try:
            number = float(value)
            display = f'{number:,.2f}' if math.isfinite(number) else 'Unavailable'
        except (TypeError, ValueError):
            display = 'Unavailable'
        rows.append(f'<tr><td>{index}</td><td>{display}</td></tr>')
    parameters = forecast.get('model_parameters') or {}
    method = escape(str(parameters.get('algorithm', 'Trend and seasonal scenario')))
    annual = forecast.get('annual_predictions') or []
    projected = []
    for year, value in enumerate(annual, 1):
        try:
            number = float(value)
            display = f'{number:,.2f}' if math.isfinite(number) else 'Unavailable'
        except (TypeError, ValueError):
            display = 'Unavailable'
        projected.append(f'<tr><td>{year}</td><td>{display}</td></tr>')
    return f'''<section class="step-section">
    <h2>Step 2: Historical demand and scenarios</h2>
    <p>Method: {method}. Validation: <strong>Not evaluated</strong>.</p>
    <p>No measured R², cross-validation score, prediction accuracy percentage or
    feature importance is available. Long-term values are scenario projections.
    Legacy seeded variation is not a statistical uncertainty interval.</p>
    <h3>Uploaded monthly observations</h3>
    <table><tr><th>Record</th><th>Consumption (kWh)</th></tr>{''.join(rows)}</table>
    <h3>Projected 12-month periods</h3>
    <table><tr><th>Period</th><th>Scenario demand (kWh)</th></tr>{''.join(projected)}</table>
    </section>'''
