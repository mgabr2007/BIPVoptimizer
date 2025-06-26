"""
Core mathematical functions and solar calculations for BIPV Optimizer
"""
import math
import streamlit as st
from datetime import datetime, timedelta


class SimpleMath:
    """Pure Python implementations for mathematical operations"""
    
    @staticmethod
    def mean(values):
        return sum(values) / len(values) if values else 0
    
    @staticmethod
    def std(values):
        if len(values) < 2:
            return 0
        mean_val = SimpleMath.mean(values)
        variance = sum((x - mean_val) ** 2 for x in values) / (len(values) - 1)
        return math.sqrt(variance)
    
    @staticmethod
    def linspace(start, stop, num):
        if num == 1:
            return [start]
        step = (stop - start) / (num - 1)
        return [start + i * step for i in range(num)]
    
    @staticmethod
    def interpolate(x_vals, y_vals, x_new):
        if not x_vals or not y_vals or len(x_vals) != len(y_vals):
            return 0
        
        # Simple linear interpolation
        for i in range(len(x_vals) - 1):
            if x_vals[i] <= x_new <= x_vals[i + 1]:
                ratio = (x_new - x_vals[i]) / (x_vals[i + 1] - x_vals[i])
                return y_vals[i] + ratio * (y_vals[i + 1] - y_vals[i])
        
        # Extrapolation
        if x_new < x_vals[0]:
            return y_vals[0]
        return y_vals[-1]


def get_currency_symbol(currency):
    """Get currency symbol from currency code"""
    symbols = {
        'USD': '$', 'EUR': '€', 'GBP': '£', 'JPY': '¥',
        'CAD': 'C$', 'AUD': 'A$', 'CHF': 'CHF', 'CNY': '¥',
        'SEK': 'kr', 'NOK': 'kr', 'DKK': 'kr', 'PLN': 'zł',
        'CZK': 'Kč', 'HUF': 'Ft', 'RUB': '₽', 'BRL': 'R$',
        'INR': '₹', 'KRW': '₩', 'SGD': 'S$', 'HKD': 'HK$',
        'NZD': 'NZ$', 'MXN': '$', 'ZAR': 'R', 'TRY': '₺'
    }
    return symbols.get(currency, currency)


def get_currency_exchange_rate(from_currency, to_currency='EUR'):
    """Get simplified exchange rates for currency conversion"""
    # Simplified exchange rates (EUR base)
    rates = {
        'USD': 1.10, 'EUR': 1.00, 'GBP': 0.85, 'JPY': 130.0,
        'CAD': 1.45, 'AUD': 1.55, 'CHF': 0.95, 'CNY': 7.8,
        'SEK': 11.2, 'NOK': 11.8, 'DKK': 7.45, 'PLN': 4.35,
        'CZK': 24.5, 'HUF': 385.0, 'RUB': 85.0, 'BRL': 5.5,
        'INR': 88.0, 'KRW': 1420.0, 'SGD': 1.48, 'HKD': 8.6,
        'NZD': 1.68, 'MXN': 19.2, 'ZAR': 20.1, 'TRY': 29.5
    }
    
    from_rate = rates.get(from_currency, 1.0)
    to_rate = rates.get(to_currency, 1.0)
    
    return to_rate / from_rate


def determine_timezone_from_coordinates(lat, lon):
    """Determine timezone based on coordinates"""
    # Simplified timezone estimation based on longitude
    utc_offset = round(lon / 15)
    utc_offset = max(-12, min(12, utc_offset))
    
    if utc_offset >= 0:
        return f"UTC+{utc_offset}"
    else:
        return f"UTC{utc_offset}"


@st.cache_data(ttl=3600)
def get_location_solar_parameters(location):
    """Get location-specific solar parameters based on location string"""
    # Enhanced global location database with comprehensive coverage
    location_params = {
        # Europe
        'berlin': {'ghi': 1000, 'dni': 1200, 'dhi': 600, 'clearness': 0.45, 'latitude': 52.5, 'temp_coeff': -0.004},
        'london': {'ghi': 950, 'dni': 1100, 'dhi': 580, 'clearness': 0.42, 'latitude': 51.5, 'temp_coeff': -0.004},
        'madrid': {'ghi': 1650, 'dni': 2100, 'dhi': 800, 'clearness': 0.62, 'latitude': 40.4, 'temp_coeff': -0.0045},
        'paris': {'ghi': 1050, 'dni': 1300, 'dhi': 620, 'clearness': 0.48, 'latitude': 48.9, 'temp_coeff': -0.004},
        'rome': {'ghi': 1550, 'dni': 2000, 'dhi': 750, 'clearness': 0.58, 'latitude': 41.9, 'temp_coeff': -0.0045},
        'amsterdam': {'ghi': 980, 'dni': 1150, 'dhi': 590, 'clearness': 0.43, 'latitude': 52.4, 'temp_coeff': -0.004},
        'vienna': {'ghi': 1200, 'dni': 1450, 'dhi': 680, 'clearness': 0.52, 'latitude': 48.2, 'temp_coeff': -0.004},
        'stockholm': {'ghi': 950, 'dni': 1100, 'dhi': 580, 'clearness': 0.42, 'latitude': 59.3, 'temp_coeff': -0.0035},
        
        # North America
        'phoenix': {'ghi': 2200, 'dni': 2800, 'dhi': 900, 'clearness': 0.72, 'latitude': 33.4, 'temp_coeff': -0.005},
        'denver': {'ghi': 1800, 'dni': 2300, 'dhi': 850, 'clearness': 0.65, 'latitude': 39.7, 'temp_coeff': -0.0045},
        'miami': {'ghi': 1950, 'dni': 2200, 'dhi': 950, 'clearness': 0.62, 'latitude': 25.8, 'temp_coeff': -0.005},
        'seattle': {'ghi': 1200, 'dni': 1350, 'dhi': 700, 'clearness': 0.48, 'latitude': 47.6, 'temp_coeff': -0.0035},
        'toronto': {'ghi': 1350, 'dni': 1600, 'dhi': 720, 'clearness': 0.52, 'latitude': 43.7, 'temp_coeff': -0.004},
        'mexico_city': {'ghi': 1900, 'dni': 2400, 'dhi': 850, 'clearness': 0.68, 'latitude': 19.4, 'temp_coeff': -0.0045},
        
        # Middle East & Africa
        'dubai': {'ghi': 2100, 'dni': 2600, 'dhi': 900, 'clearness': 0.75, 'latitude': 25.3, 'temp_coeff': -0.005},
        'riyadh': {'ghi': 2300, 'dni': 2900, 'dhi': 950, 'clearness': 0.78, 'latitude': 24.7, 'temp_coeff': -0.005},
        'cairo': {'ghi': 2200, 'dni': 2800, 'dhi': 900, 'clearness': 0.75, 'latitude': 30.0, 'temp_coeff': -0.0048},
        'cape_town': {'ghi': 2000, 'dni': 2500, 'dhi': 850, 'clearness': 0.68, 'latitude': -33.9, 'temp_coeff': -0.0045},
        'nairobi': {'ghi': 2100, 'dni': 2400, 'dhi': 950, 'clearness': 0.65, 'latitude': -1.3, 'temp_coeff': -0.004},
        'tel_aviv': {'ghi': 2000, 'dni': 2500, 'dhi': 850, 'clearness': 0.70, 'latitude': 32.1, 'temp_coeff': -0.0048},
        
        # Asia
        'tokyo': {'ghi': 1350, 'dni': 1650, 'dhi': 720, 'clearness': 0.52, 'latitude': 35.7, 'temp_coeff': -0.0045},
        'singapore': {'ghi': 1650, 'dni': 1800, 'dhi': 900, 'clearness': 0.55, 'latitude': 1.4, 'temp_coeff': -0.004},
        'hong_kong': {'ghi': 1400, 'dni': 1600, 'dhi': 750, 'clearness': 0.50, 'latitude': 22.3, 'temp_coeff': -0.0045},
        'mumbai': {'ghi': 1900, 'dni': 2200, 'dhi': 950, 'clearness': 0.60, 'latitude': 19.1, 'temp_coeff': -0.0045},
        'beijing': {'ghi': 1550, 'dni': 1900, 'dhi': 800, 'clearness': 0.55, 'latitude': 39.9, 'temp_coeff': -0.004},
        'seoul': {'ghi': 1400, 'dni': 1700, 'dhi': 750, 'clearness': 0.52, 'latitude': 37.6, 'temp_coeff': -0.004},
        'sydney': {'ghi': 1800, 'dni': 2200, 'dhi': 850, 'clearness': 0.65, 'latitude': -33.9, 'temp_coeff': -0.0045},
        
        # South America
        'sao_paulo': {'ghi': 1650, 'dni': 1900, 'dhi': 850, 'clearness': 0.58, 'latitude': -23.5, 'temp_coeff': -0.0045},
        'buenos_aires': {'ghi': 1700, 'dni': 2000, 'dhi': 850, 'clearness': 0.60, 'latitude': -34.6, 'temp_coeff': -0.0045},
        'lima': {'ghi': 1800, 'dni': 2100, 'dhi': 900, 'clearness': 0.62, 'latitude': -12.0, 'temp_coeff': -0.004}
    }
    
    # Normalize location string for lookup
    location_key = location.lower().replace(' ', '_').replace(',', '').replace('.', '')
    
    if location_key in location_params:
        return location_params[location_key]
    
    # Default parameters based on latitude estimation if location not found
    # This provides reasonable estimates for unknown locations
    return {
        'ghi': 1400,  # Global average
        'dni': 1700,  # Global average
        'dhi': 750,   # Global average
        'clearness': 0.55,  # Global average
        'latitude': 50.0,   # Temperate default
        'temp_coeff': -0.004  # Standard silicon coefficient
    }


@st.cache_data(ttl=3600)
def get_location_electricity_rates(location, currency='EUR'):
    """Get location-specific electricity rates in EUR (standardized currency)"""
    # All electricity rates in EUR/kWh (standardized base currency)
    rates_eur = {
        # Europe (EUR/kWh)
        'berlin': {'import': 0.32, 'export': 0.08, 'demand_charge': 0.05},
        'london': {'import': 0.28, 'export': 0.06, 'demand_charge': 0.04},
        'madrid': {'import': 0.25, 'export': 0.07, 'demand_charge': 0.03},
        'paris': {'import': 0.30, 'export': 0.09, 'demand_charge': 0.04},
        'rome': {'import': 0.27, 'export': 0.08, 'demand_charge': 0.04},
        'amsterdam': {'import': 0.29, 'export': 0.07, 'demand_charge': 0.04},
        'vienna': {'import': 0.26, 'export': 0.08, 'demand_charge': 0.03},
        'stockholm': {'import': 0.31, 'export': 0.09, 'demand_charge': 0.05},
        
        # Convert from local currencies to EUR
        'phoenix': {'import': 0.11, 'export': 0.03, 'demand_charge': 0.02},      # ~$0.12/kWh
        'denver': {'import': 0.10, 'export': 0.03, 'demand_charge': 0.02},       # ~$0.11/kWh
        'miami': {'import': 0.09, 'export': 0.02, 'demand_charge': 0.02},        # ~$0.10/kWh
        'seattle': {'import': 0.08, 'export': 0.03, 'demand_charge': 0.01},      # ~$0.09/kWh
        'toronto': {'import': 0.11, 'export': 0.04, 'demand_charge': 0.02},      # ~C$0.15/kWh
        'mexico_city': {'import': 0.08, 'export': 0.02, 'demand_charge': 0.01}, # ~$0.09/kWh
        
        # Middle East & Africa
        'dubai': {'import': 0.07, 'export': 0.02, 'demand_charge': 0.01},        # ~$0.08/kWh
        'riyadh': {'import': 0.06, 'export': 0.01, 'demand_charge': 0.01},       # ~$0.07/kWh
        'cairo': {'import': 0.04, 'export': 0.01, 'demand_charge': 0.005},       # ~$0.05/kWh
        'cape_town': {'import': 0.12, 'export': 0.03, 'demand_charge': 0.02},    # ~R2.2/kWh
        'nairobi': {'import': 0.15, 'export': 0.02, 'demand_charge': 0.02},      # Variable rates
        'tel_aviv': {'import': 0.14, 'export': 0.04, 'demand_charge': 0.02},     # Variable rates
        
        # Asia  
        'tokyo': {'import': 0.18, 'export': 0.06, 'demand_charge': 0.03},        # ~¥25/kWh
        'singapore': {'import': 0.16, 'export': 0.04, 'demand_charge': 0.02},    # ~S$0.24/kWh
        'hong_kong': {'import': 0.13, 'export': 0.03, 'demand_charge': 0.02},    # ~HK$1.2/kWh
        'mumbai': {'import': 0.08, 'export': 0.02, 'demand_charge': 0.01},       # ~₹7/kWh
        'beijing': {'import': 0.07, 'export': 0.02, 'demand_charge': 0.01},      # ~¥0.6/kWh
        'seoul': {'import': 0.08, 'export': 0.03, 'demand_charge': 0.02},        # ~₩125/kWh
        'sydney': {'import': 0.18, 'export': 0.05, 'demand_charge': 0.03},       # ~A$0.28/kWh
        
        # South America
        'sao_paulo': {'import': 0.15, 'export': 0.03, 'demand_charge': 0.02},    # ~R$0.8/kWh
        'buenos_aires': {'import': 0.12, 'export': 0.02, 'demand_charge': 0.02}, # Variable rates
        'lima': {'import': 0.10, 'export': 0.02, 'demand_charge': 0.01}          # Variable rates
    }
    
    # Normalize location string
    location_key = location.lower().replace(' ', '_').replace(',', '').replace('.', '')
    
    if location_key in rates_eur:
        rates = rates_eur[location_key]
    else:
        # Default rates (European average)
        rates = {'import': 0.28, 'export': 0.07, 'demand_charge': 0.04}
    
    # Return rates in EUR (standardized currency)
    return {
        'import_rate': rates['import'],
        'export_rate': rates['export'],
        'demand_charge': rates['demand_charge'],
        'currency': 'EUR'
    }


def calculate_solar_position_iso(lat, lon, day_of_year, hour):
    """Calculate solar position using ISO 15927-4 methodology"""
    # Solar declination angle (degrees)
    declination = 23.45 * math.sin(math.radians(360 * (284 + day_of_year) / 365))
    
    # Hour angle (degrees)
    hour_angle = 15 * (hour - 12)
    
    # Solar elevation angle (degrees)
    lat_rad = math.radians(lat)
    decl_rad = math.radians(declination)
    hour_rad = math.radians(hour_angle)
    
    elevation = math.degrees(math.asin(
        math.sin(lat_rad) * math.sin(decl_rad) + 
        math.cos(lat_rad) * math.cos(decl_rad) * math.cos(hour_rad)
    ))
    
    # Solar azimuth angle (degrees from south)
    if elevation > 0:
        azimuth = math.degrees(math.atan2(
            math.sin(hour_rad),
            math.cos(hour_rad) * math.sin(lat_rad) - math.tan(decl_rad) * math.cos(lat_rad)
        ))
    else:
        azimuth = 0
    
    return {
        'elevation': max(0, elevation),
        'azimuth': azimuth,
        'declination': declination
    }


def classify_solar_resource_iso(annual_ghi):
    """Classify solar resource according to ISO 9060 standards"""
    if annual_ghi >= 2000:
        return "Excellent (>2000 kWh/m²/year)"
    elif annual_ghi >= 1600:
        return "Very Good (1600-2000 kWh/m²/year)"
    elif annual_ghi >= 1200:
        return "Good (1200-1600 kWh/m²/year)"
    elif annual_ghi >= 800:
        return "Moderate (800-1200 kWh/m²/year)"
    else:
        return "Low (<800 kWh/m²/year)"


def safe_divide(numerator, denominator, default=0.0):
    """Safe division to avoid division by zero errors"""
    try:
        return float(numerator) / float(denominator) if denominator != 0 else default
    except (TypeError, ValueError):
        return default