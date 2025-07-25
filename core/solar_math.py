"""
Core mathematical functions and solar calculations for BIPV Optimizer
"""
import math
import streamlit as st
from datetime import datetime, timedelta
from typing import Tuple, List, Optional


def calculate_solar_position(latitude: float, longitude: float, timestamp: datetime) -> Tuple[float, float]:
    """
    Calculate solar position (elevation and azimuth) for given location and time.
    
    Args:
        latitude: Latitude in degrees
        longitude: Longitude in degrees  
        timestamp: UTC datetime
        
    Returns:
        Tuple of (solar_elevation, solar_azimuth) in degrees
    """
    
    # Convert to radians
    lat_rad = math.radians(latitude)
    
    # Day of year
    day_of_year = timestamp.timetuple().tm_yday
    
    # Solar declination angle
    declination = math.radians(23.45 * math.sin(math.radians(360 * (284 + day_of_year) / 365)))
    
    # Hour angle
    time_correction = 4 * (longitude - 15 * timestamp.hour)  # Simplified
    solar_time = timestamp.hour + timestamp.minute/60.0 + time_correction/60.0
    hour_angle = math.radians(15 * (solar_time - 12))
    
    # Solar elevation
    elevation_rad = math.asin(
        math.sin(declination) * math.sin(lat_rad) + 
        math.cos(declination) * math.cos(lat_rad) * math.cos(hour_angle)
    )
    elevation = math.degrees(elevation_rad)
    
    # Solar azimuth
    azimuth_rad = math.atan2(
        math.sin(hour_angle),
        math.cos(hour_angle) * math.sin(lat_rad) - math.tan(declination) * math.cos(lat_rad)
    )
    azimuth = math.degrees(azimuth_rad) + 180  # Convert from south = 0 to north = 0
    
    return max(0, elevation), azimuth % 360


def calculate_solar_position_simple(latitude: float, longitude: float, day_of_year: int, hour: float) -> dict:
    """
    Calculate solar position using simplified inputs (day/hour instead of datetime).
    
    Args:
        latitude: Latitude in degrees
        longitude: Longitude in degrees
        day_of_year: Day of year (1-365)
        hour: Hour of day (0-24)
        
    Returns:
        Dictionary with elevation, azimuth, and zenith angles
    """
    # Solar declination angle (degrees)
    declination = 23.45 * math.sin(math.radians(360 * (284 + day_of_year) / 365))
    
    # Hour angle (degrees from solar noon)
    hour_angle = 15 * (hour - 12)
    
    # Solar elevation angle
    elevation = math.asin(
        math.sin(math.radians(declination)) * math.sin(math.radians(latitude)) +
        math.cos(math.radians(declination)) * math.cos(math.radians(latitude)) * 
        math.cos(math.radians(hour_angle))
    )
    
    # Solar azimuth angle
    azimuth = math.atan2(
        math.sin(math.radians(hour_angle)),
        math.cos(math.radians(hour_angle)) * math.sin(math.radians(latitude)) -
        math.tan(math.radians(declination)) * math.cos(math.radians(latitude))
    )
    
    elevation_deg = math.degrees(elevation)
    azimuth_deg = math.degrees(azimuth) + 180  # Convert to 0-360 range
    
    return {
        'elevation': elevation_deg,
        'azimuth': azimuth_deg,
        'zenith': 90 - elevation_deg
    }


def calculate_irradiance_on_surface(dni: float, solar_elevation: float, solar_azimuth: float, 
                                  surface_azimuth: float, surface_tilt: float = 90,
                                  ghi: Optional[float] = None, dhi: Optional[float] = None) -> float:
    """
    Calculate irradiance on a tilted surface with comprehensive model.
    Supports both simple DNI-only and full GHI+DNI+DHI calculations.
    
    Args:
        dni: Direct Normal Irradiance in W/m²
        solar_elevation: Solar elevation angle in degrees
        solar_azimuth: Solar azimuth angle in degrees
        surface_azimuth: Surface azimuth angle in degrees
        surface_tilt: Surface tilt angle in degrees (90 = vertical)
        ghi: Global Horizontal Irradiance in W/m² (optional for advanced calculation)
        dhi: Diffuse Horizontal Irradiance in W/m² (optional for advanced calculation)
        
    Returns:
        Irradiance on surface in W/m²
    """
    
    if solar_elevation <= 0:
        return 0
    
    # Convert to radians
    sun_elev_rad = math.radians(solar_elevation)
    sun_azim_rad = math.radians(solar_azimuth)
    surf_azim_rad = math.radians(surface_azimuth)
    surf_tilt_rad = math.radians(surface_tilt)
    
    # Calculate zenith angle for advanced calculations
    zenith_rad = math.radians(90 - solar_elevation)
    
    # Calculate angle of incidence - corrected for vertical surfaces
    cos_incidence = (
        math.sin(zenith_rad) * math.sin(surf_tilt_rad) * 
        math.cos(sun_azim_rad - surf_azim_rad) +
        math.cos(zenith_rad) * math.cos(surf_tilt_rad)
    )
    
    # Ensure positive incidence
    cos_incidence = max(0, cos_incidence)
    
    # Simple calculation if only DNI is provided
    if ghi is None or dhi is None:
        if dni <= 0:
            return 0
        return dni * cos_incidence
    
    # Advanced calculation with GHI, DNI, DHI (POA - Plane of Array)
    if dni <= 0:
        dni = max(0, ghi - dhi) if dhi > 0 else ghi * 0.8
    
    # Direct component on surface
    direct_on_surface = dni * cos_incidence
    
    # Diffuse component (isotropic sky model)
    diffuse_on_surface = dhi * (1 + math.cos(surf_tilt_rad)) / 2
    
    # Ground reflected component (albedo = 0.2 for typical ground)
    ground_albedo = 0.2
    reflected_on_surface = ghi * ground_albedo * (1 - math.cos(surf_tilt_rad)) / 2
    
    # Total POA irradiance
    poa_global = direct_on_surface + diffuse_on_surface + reflected_on_surface
    
    return max(0, poa_global)


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
    """
    Calculate solar position using ISO 15927-4 methodology with improved accuracy
    
    Returns:
        dict: {
            'elevation': Solar elevation angle in degrees (0-90°)
            'azimuth': Solar azimuth angle in degrees from north clockwise (0-360°)
            'declination': Solar declination angle in degrees
        }
    """
    # More accurate solar declination (Cooper's equation)
    # ISO 15927-4 recommends this for higher accuracy
    B = math.radians(360 * (day_of_year - 81) / 365)
    declination = 23.45 * math.sin(B)
    
    # Convert hour to decimal (handle fractional hours)
    decimal_hour = hour + 0.5  # Center of hour
    
    # Equation of time correction (minutes)
    B_eq = math.radians(360 * (day_of_year - 81) / 364)
    equation_of_time = 9.87 * math.sin(2 * B_eq) - 7.53 * math.cos(B_eq) - 1.5 * math.sin(B_eq)
    
    # Solar time correction (longitude correction for local solar time)
    time_correction = equation_of_time + 4 * lon  # 4 minutes per degree longitude
    solar_time = decimal_hour + time_correction / 60
    
    # Hour angle (degrees from solar noon)
    hour_angle = 15 * (solar_time - 12)
    
    # Convert to radians for calculations
    lat_rad = math.radians(lat)
    decl_rad = math.radians(declination)
    hour_rad = math.radians(hour_angle)
    
    # Solar elevation angle (altitude)
    sin_elevation = (math.sin(lat_rad) * math.sin(decl_rad) + 
                    math.cos(lat_rad) * math.cos(decl_rad) * math.cos(hour_rad))
    
    # Clamp to valid range to avoid numerical errors
    sin_elevation = max(-1, min(1, sin_elevation))
    elevation = math.degrees(math.asin(sin_elevation))
    
    # Solar azimuth angle (from north, clockwise)
    if elevation > 0:
        # Calculate azimuth using proper spherical trigonometry
        # This formula gives azimuth from north, clockwise (0-360°)
        sin_azimuth = math.cos(decl_rad) * math.sin(hour_rad) / math.cos(math.radians(elevation))
        cos_azimuth = (math.sin(decl_rad) * math.cos(lat_rad) - 
                      math.cos(decl_rad) * math.sin(lat_rad) * math.cos(hour_rad)) / math.cos(math.radians(elevation))
        
        # Clamp to valid range to avoid numerical errors
        sin_azimuth = max(-1, min(1, sin_azimuth))
        cos_azimuth = max(-1, min(1, cos_azimuth))
        
        # Calculate azimuth using atan2 for proper quadrant determination
        azimuth_rad = math.atan2(sin_azimuth, cos_azimuth)
        azimuth = math.degrees(azimuth_rad)
        
        # Convert to 0-360° range from north clockwise
        if azimuth < 0:
            azimuth += 360
    else:
        # Sun below horizon
        azimuth = 0
    
    return {
        'elevation': max(0, elevation),
        'azimuth': azimuth % 360,  # Ensure 0-360° range
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