"""Legacy trend/seasonal projection, explicitly unevaluated; no fitted ML estimator."""
from datetime import datetime, timedelta

def get_forecast_start_date(date_data):
    """Determine the forecast start date based on historical data dates."""
    if not date_data:
        return datetime.now().replace(day=1) + timedelta(days=32)
    
    try:
        # Parse the last date in historical data
        last_date_str = date_data[-1]
        if '-' in last_date_str:
            # Parse YYYY-MM-DD format
            last_date = datetime.strptime(last_date_str, '%Y-%m-%d')
        else:
            # Fallback to current date
            return datetime.now().replace(day=1) + timedelta(days=32)
        
        # Start forecast from next month after last historical data
        if last_date.month == 12:
            return datetime(last_date.year + 1, 1, 1)
        else:
            return datetime(last_date.year, last_date.month + 1, 1)
    except:
        # Fallback to current date
        return datetime.now().replace(day=1) + timedelta(days=32)


def generate_demand_forecast(consumption_data, temperature_data, occupancy_data, date_data=None, occupancy_modifiers=None, building_type=None):
    """Generate 25-year demand forecast based on historical data and educational building patterns."""
    import numpy as np
    from datetime import datetime, timedelta
    
    values = np.asarray(consumption_data, dtype=float)
    if values.ndim != 1 or not len(values) or not np.isfinite(values).all() or (values < 0).any():
        raise ValueError("Consumption must contain finite, nonnegative monthly observations")
    if values.sum() <= 0:
        raise ValueError("At least one positive consumption observation is required")
    consumption_data = values.tolist()

    # Calculate base consumption - use annual total, not monthly average
    if consumption_data:
        if len(consumption_data) >= 12:
            # Use full year data
            base_consumption = sum(consumption_data[:12])  # Annual total
        else:
            # Extrapolate to annual from available months
            monthly_avg = sum(consumption_data) / len(consumption_data)
            base_consumption = monthly_avg * 12  # Estimate annual total
    else:
        base_consumption = 300000  # Default annual consumption in kWh
    
    # Calculate growth rate based on data trend
    if len(consumption_data) >= 12:
        # Linear trend analysis
        x = list(range(len(consumption_data)))
        y = consumption_data
        n = len(x)
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(x[i] * y[i] for i in range(n))
        sum_x2 = sum(x[i] ** 2 for i in range(n))
        
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2) if (n * sum_x2 - sum_x ** 2) != 0 else 0
        
        # Calculate more conservative growth rate
        if base_consumption > 0:
            monthly_growth_rate = slope / base_consumption
            annual_growth_rate = monthly_growth_rate * 12
            
            # Apply more conservative caps for educational buildings (typically 0.5-2% annual growth)
            growth_rate = max(-0.005, min(0.02, annual_growth_rate))  # Cap between -0.5% and 2%
        else:
            growth_rate = 0.01  # Default 1% if no base consumption
    else:
        growth_rate = 0.015  # Default 1.5% annual growth
    
    # Generate seasonal patterns based on historical data and educational building patterns
    seasonal_factors = []
    if len(consumption_data) >= 12:
        # Use actual monthly distribution from historical data
        total_annual = sum(consumption_data[:12])
        monthly_avg = total_annual / 12
        base_seasonal_factors = [c / monthly_avg for c in consumption_data[:12]]
        
        # For existing historical data, use actual patterns without heavy modification
        # Educational building patterns are already reflected in the historical consumption
        if occupancy_modifiers:
            # Apply gentle adjustments only, since historical data already shows building patterns
            modified_factors = []
            for month_idx, base_factor in enumerate(base_seasonal_factors):
                # Apply mild seasonal adjustments (reduced impact for historical data)
                adjustment_strength = 0.1  # Only 10% adjustment strength
                
                if month_idx in [5, 6, 7]:  # Summer months (Jun-Aug)
                    modifier = 1.0 + (occupancy_modifiers['summer_factor'] - 1.0) * adjustment_strength
                elif month_idx in [11, 0, 1]:  # Winter months (Dec-Feb) 
                    modifier = 1.0 + (occupancy_modifiers['winter_factor'] - 1.0) * adjustment_strength
                else:  # Transition months (Mar-May, Sep-Nov)
                    modifier = 1.0 + (occupancy_modifiers['transition_factor'] - 1.0) * adjustment_strength
                
                modified_factor = base_factor * modifier
                modified_factors.append(modified_factor)
            
            # For Year-Round Operation, maintain continuity with historical data
            if 'Year-Round' in occupancy_modifiers.get('description', ''):
                # Minimal adjustment for year-round operations
                seasonal_factors = modified_factors
            else:
                # Apply gentle annual operation factor for other patterns
                annual_factor = 1.0 + (occupancy_modifiers.get('annual_factor', 1.0) - 1.0) * 0.05
                seasonal_factors = [f * annual_factor for f in modified_factors]
        else:
            seasonal_factors = base_seasonal_factors
    else:
        # Use educational building pattern from occupancy modifiers or defaults
        if occupancy_modifiers:
            # Create pattern based on educational building type
            base_pattern = [1.0] * 12  # Start with uniform distribution
            
            # Apply seasonal modifiers
            for month_idx in range(12):
                if month_idx in [5, 6, 7]:  # Summer months (Jun-Aug)
                    base_pattern[month_idx] *= occupancy_modifiers['summer_factor']
                elif month_idx in [11, 0, 1]:  # Winter months (Dec-Feb)
                    base_pattern[month_idx] *= occupancy_modifiers['winter_factor']
                else:  # Transition months
                    base_pattern[month_idx] *= occupancy_modifiers['transition_factor']
            
            # Apply annual operation factor
            annual_factor = occupancy_modifiers.get('annual_factor', 1.0)
            seasonal_factors = [f * annual_factor for f in base_pattern]
        else:
            # Default seasonal pattern for educational buildings
            seasonal_factors = [1.1, 1.05, 1.0, 0.95, 0.9, 0.8, 0.75, 0.8, 0.95, 1.0, 1.05, 1.1]
    
    # Generate 25 years of monthly predictions with proper calendar alignment
    monthly_predictions = []
    annual_predictions = []
    
    # Use a fixed seed for consistent results
    rng = np.random.RandomState(42)  # Local RNG: preserve legacy scenario values without global side effects
    
    for year in range(25):
        # Fixed: Proper annual growth calculation
        annual_consumption = base_consumption * (1 + growth_rate) ** year
        
        # Ensure reasonable bounds - cap at 5x original consumption to prevent astronomical values
        if annual_consumption > base_consumption * 5:
            annual_consumption = base_consumption * 5
        
        year_monthly = []
        
        for month_index in range(12):
            # Calendar months: 0=Jan, 1=Feb, ..., 11=Dec
            seasonal_factor = seasonal_factors[month_index]
            monthly_value = (annual_consumption / 12) * seasonal_factor
            
            # Add controlled randomness for realism but keep predictable patterns
            noise_factor = 1 + (rng.random_sample() - 0.5) * 0.05  # ±2.5% variation
            monthly_value *= noise_factor
            
            final_value = max(0, monthly_value)
            monthly_predictions.append(final_value)
            year_monthly.append(final_value)
        
        annual_predictions.append(sum(year_monthly))
    
    return {
        'monthly_predictions': monthly_predictions,
        'annual_predictions': annual_predictions,
        'growth_rate': growth_rate,
        'base_consumption': base_consumption,
        'seasonal_factors': seasonal_factors,
        'forecast_start_date': get_forecast_start_date(date_data),
        'model_parameters': {
            'algorithm': 'Trend and seasonal scenario',
            'features': ['seasonality', 'historical_trend', 'educational_modifiers'],
            'accuracy': None,
            'evaluation_status': 'not_evaluated',
            'model_version': 'trend-scenario-v2',
            'excluded_features': ['temperature', 'occupancy_data'],
            'building_type': building_type if building_type else 'Educational',
            'occupancy_pattern': occupancy_modifiers.get('description', 'Standard') if occupancy_modifiers else 'Standard',
            'seasonal_adjustments': {
                'summer_factor': occupancy_modifiers.get('summer_factor', 1.0) if occupancy_modifiers else 1.0,
                'winter_factor': occupancy_modifiers.get('winter_factor', 1.0) if occupancy_modifiers else 1.0,
                'annual_factor': occupancy_modifiers.get('annual_factor', 1.0) if occupancy_modifiers else 1.0
            }
        }
    }


