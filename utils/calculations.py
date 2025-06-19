import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import math

def solar_position(latitude, longitude, datetime_utc):
    """
    Calculate solar position (elevation and azimuth) for given location and time.
    
    Args:
        latitude (float): Latitude in degrees
        longitude (float): Longitude in degrees
        datetime_utc (datetime): UTC datetime
    
    Returns:
        dict: Solar elevation and azimuth in degrees
    """
    
    # Convert to Julian day
    jd = datetime_utc.toordinal() + 1721425.5 + datetime_utc.hour/24.0 + datetime_utc.minute/1440.0 + datetime_utc.second/86400.0
    
    # Solar calculations
    n = jd - 2451545.0
    L = (280.460 + 0.9856474 * n) % 360
    g = math.radians((357.528 + 0.9856003 * n) % 360)
    lambda_sun = math.radians(L + 1.915 * math.sin(g) + 0.020 * math.sin(2 * g))
    
    # Solar declination
    epsilon = math.radians(23.439 - 0.0000004 * n)
    alpha = math.atan2(math.cos(epsilon) * math.sin(lambda_sun), math.cos(lambda_sun))
    delta = math.asin(math.sin(epsilon) * math.sin(lambda_sun))
    
    # Hour angle
    gmst = (18.697374558 + 24.06570982441908 * n) % 24
    lmst = (gmst + longitude / 15.0) % 24
    hour_angle = math.radians(15.0 * (lmst - math.degrees(alpha) / 15.0))
    
    # Solar position
    lat_rad = math.radians(latitude)
    elevation = math.asin(math.sin(lat_rad) * math.sin(delta) + 
                         math.cos(lat_rad) * math.cos(delta) * math.cos(hour_angle))
    
    azimuth = math.atan2(math.sin(hour_angle),
                        math.cos(hour_angle) * math.sin(lat_rad) - 
                        math.tan(delta) * math.cos(lat_rad))
    
    return {
        'elevation': math.degrees(elevation),
        'azimuth': (math.degrees(azimuth) + 180) % 360,
        'zenith': 90 - math.degrees(elevation)
    }

def calculate_irradiance_on_tilted_surface(ghi, dni, dhi, solar_elevation, solar_azimuth, 
                                          surface_tilt, surface_azimuth):
    """
    Calculate irradiance on a tilted surface using the Perez model.
    
    Args:
        ghi (float): Global horizontal irradiance (W/m²)
        dni (float): Direct normal irradiance (W/m²)
        dhi (float): Diffuse horizontal irradiance (W/m²)
        solar_elevation (float): Solar elevation angle (degrees)
        solar_azimuth (float): Solar azimuth angle (degrees)
        surface_tilt (float): Surface tilt angle (degrees)
        surface_azimuth (float): Surface azimuth angle (degrees)
    
    Returns:
        float: Plane of array irradiance (W/m²)
    """
    
    if solar_elevation <= 0:
        return 0
    
    # Convert angles to radians
    solar_elevation_rad = math.radians(solar_elevation)
    solar_azimuth_rad = math.radians(solar_azimuth)
    surface_tilt_rad = math.radians(surface_tilt)
    surface_azimuth_rad = math.radians(surface_azimuth)
    
    # Angle of incidence
    cos_incidence = (math.sin(solar_elevation_rad) * math.cos(surface_tilt_rad) +
                    math.cos(solar_elevation_rad) * math.sin(surface_tilt_rad) *
                    math.cos(solar_azimuth_rad - surface_azimuth_rad))
    
    cos_incidence = max(0, cos_incidence)
    
    # Direct component
    direct_component = dni * cos_incidence
    
    # Diffuse component (isotropic sky model)
    diffuse_component = dhi * (1 + math.cos(surface_tilt_rad)) / 2
    
    # Ground reflected component
    albedo = 0.2  # Typical ground albedo
    ground_reflected = ghi * albedo * (1 - math.cos(surface_tilt_rad)) / 2
    
    # Total plane of array irradiance
    poa_irradiance = direct_component + diffuse_component + ground_reflected
    
    return max(0, poa_irradiance)

def calculate_pv_power_output(irradiance, temperature, panel_power_rating, panel_efficiency,
                             temperature_coefficient=-0.004, reference_temperature=25,
                             reference_irradiance=1000):
    """
    Calculate PV power output considering temperature effects.
    
    Args:
        irradiance (float): Plane of array irradiance (W/m²)
        temperature (float): Cell temperature (°C)
        panel_power_rating (float): Panel power rating at STC (W)
        panel_efficiency (float): Panel efficiency at STC
        temperature_coefficient (float): Temperature coefficient (%/°C)
        reference_temperature (float): Reference temperature (°C)
        reference_irradiance (float): Reference irradiance (W/m²)
    
    Returns:
        float: Power output (W)
    """
    
    # Irradiance factor
    irradiance_factor = irradiance / reference_irradiance
    
    # Temperature factor
    temperature_factor = 1 + temperature_coefficient * (temperature - reference_temperature)
    
    # Power output
    power_output = panel_power_rating * irradiance_factor * temperature_factor
    
    return max(0, power_output)

def calculate_shading_factor(tree_positions, tree_heights, tree_canopy_radii, 
                           surface_position, solar_elevation, solar_azimuth):
    """
    Calculate shading factor from trees and obstacles.
    
    Args:
        tree_positions (list): List of (x, y) tree positions
        tree_heights (list): List of tree heights
        tree_canopy_radii (list): List of tree canopy radii
        surface_position (tuple): (x, y, z) position of surface center
        solar_elevation (float): Solar elevation angle (degrees)
        solar_azimuth (float): Solar azimuth angle (degrees)
    
    Returns:
        float: Shading factor (0 = fully shaded, 1 = no shade)
    """
    
    if solar_elevation <= 0:
        return 0
    
    total_shading = 0
    surface_x, surface_y, surface_z = surface_position
    
    # Convert solar angles to direction vector
    solar_elevation_rad = math.radians(solar_elevation)
    solar_azimuth_rad = math.radians(solar_azimuth)
    
    # Solar vector (pointing towards sun)
    sun_vector = np.array([
        math.sin(solar_azimuth_rad) * math.cos(solar_elevation_rad),
        math.cos(solar_azimuth_rad) * math.cos(solar_elevation_rad),
        math.sin(solar_elevation_rad)
    ])
    
    for i, (tree_x, tree_y) in enumerate(tree_positions):
        tree_height = tree_heights[i]
        canopy_radius = tree_canopy_radii[i]
        
        # Vector from surface to tree
        tree_vector = np.array([tree_x - surface_x, tree_y - surface_y, 0])
        tree_distance = np.linalg.norm(tree_vector[:2])
        
        if tree_distance == 0:
            continue
        
        # Calculate shadow length
        if solar_elevation > 0:
            shadow_length = tree_height / math.tan(solar_elevation_rad)
            
            # Check if surface is in shadow path
            shadow_direction = -sun_vector[:2]  # Shadow direction (opposite of sun)
            shadow_end = np.array([tree_x, tree_y]) + shadow_direction * shadow_length
            
            # Distance from surface to shadow line
            surface_point = np.array([surface_x, surface_y])
            tree_point = np.array([tree_x, tree_y])
            
            # Project surface point onto shadow line
            shadow_vec = shadow_end - tree_point
            if np.linalg.norm(shadow_vec) > 0:
                t = np.dot(surface_point - tree_point, shadow_vec) / np.dot(shadow_vec, shadow_vec)
                t = np.clip(t, 0, 1)
                closest_point = tree_point + t * shadow_vec
                
                distance_to_shadow = np.linalg.norm(surface_point - closest_point)
                
                # Calculate shading effect
                if distance_to_shadow < canopy_radius:
                    shade_fraction = (canopy_radius - distance_to_shadow) / canopy_radius
                    shade_fraction = max(0, min(1, shade_fraction))
                    
                    # Consider height effect
                    height_factor = min(1, tree_height / (surface_z + 1))
                    
                    total_shading += shade_fraction * height_factor
    
    # Total shading factor (0 = fully shaded, 1 = no shading)
    shading_factor = max(0, 1 - min(1, total_shading))
    
    return shading_factor

def calculate_optimal_tilt(latitude):
    """
    Calculate optimal tilt angle for PV panels based on latitude.
    
    Args:
        latitude (float): Latitude in degrees
    
    Returns:
        float: Optimal tilt angle in degrees
    """
    
    # Rule of thumb: optimal tilt ≈ latitude for year-round optimization
    # Adjustments for seasonal optimization:
    # - Summer: latitude - 15°
    # - Winter: latitude + 15°
    # - Year-round: latitude
    
    optimal_tilt = abs(latitude)
    
    # Limit tilt angle to reasonable range
    optimal_tilt = max(0, min(90, optimal_tilt))
    
    return optimal_tilt

def calculate_system_losses(inverter_efficiency=0.96, dc_losses=0.02, ac_losses=0.01,
                          soiling_losses=0.02, shading_losses=0.0, mismatch_losses=0.02):
    """
    Calculate total system losses for PV system.
    
    Args:
        inverter_efficiency (float): Inverter efficiency
        dc_losses (float): DC side losses (cables, connections)
        ac_losses (float): AC side losses
        soiling_losses (float): Soiling losses
        shading_losses (float): Shading losses
        mismatch_losses (float): Module mismatch losses
    
    Returns:
        float: Total system efficiency factor
    """
    
    # Calculate combined efficiency
    efficiency_factor = (inverter_efficiency * 
                        (1 - dc_losses) * 
                        (1 - ac_losses) * 
                        (1 - soiling_losses) * 
                        (1 - shading_losses) * 
                        (1 - mismatch_losses))
    
    return efficiency_factor

def calculate_annual_degradation(annual_energy, degradation_rate=0.005, years=25):
    """
    Calculate energy production with annual degradation.
    
    Args:
        annual_energy (float): First year energy production
        degradation_rate (float): Annual degradation rate (0.005 = 0.5%)
        years (int): Number of years
    
    Returns:
        list: Annual energy production for each year
    """
    
    annual_production = []
    
    for year in range(years):
        degraded_energy = annual_energy * ((1 - degradation_rate) ** year)
        annual_production.append(degraded_energy)
    
    return annual_production

def calculate_financial_metrics(initial_investment, annual_cash_flows, discount_rate):
    """
    Calculate financial metrics: NPV, IRR, payback period.
    
    Args:
        initial_investment (float): Initial investment cost
        annual_cash_flows (list): Annual cash flows
        discount_rate (float): Discount rate
    
    Returns:
        dict: Financial metrics
    """
    
    # Net Present Value
    npv = -initial_investment
    for i, cash_flow in enumerate(annual_cash_flows):
        npv += cash_flow / ((1 + discount_rate) ** (i + 1))
    
    # Simple Payback Period
    cumulative_cash_flow = 0
    payback_period = None
    
    for i, cash_flow in enumerate(annual_cash_flows):
        cumulative_cash_flow += cash_flow
        if cumulative_cash_flow >= initial_investment and payback_period is None:
            if i == 0:
                payback_period = initial_investment / cash_flow
            else:
                # Interpolate
                prev_cumulative = cumulative_cash_flow - cash_flow
                payback_period = i + (initial_investment - prev_cumulative) / cash_flow
            break
    
    # Internal Rate of Return (simplified approximation)
    irr = None
    if len(annual_cash_flows) > 0:
        avg_annual_return = sum(annual_cash_flows) / len(annual_cash_flows)
        if avg_annual_return > 0:
            irr = (avg_annual_return / initial_investment) * 100
    
    return {
        'npv': npv,
        'irr': irr,
        'payback_period': payback_period
    }

def calculate_co2_emissions_avoided(annual_energy_kwh, grid_emission_factor, years=25):
    """
    Calculate CO2 emissions avoided by PV system.
    
    Args:
        annual_energy_kwh (float): Annual energy production in kWh
        grid_emission_factor (float): Grid CO2 emission factor (kg CO2/kWh)
        years (int): System lifetime
    
    Returns:
        dict: CO2 emissions avoided
    """
    
    # Annual CO2 avoided
    annual_co2_avoided = annual_energy_kwh * grid_emission_factor
    
    # Lifetime CO2 avoided (considering degradation)
    annual_production = calculate_annual_degradation(annual_energy_kwh, years=years)
    lifetime_co2_avoided = sum(production * grid_emission_factor for production in annual_production)
    
    return {
        'annual_co2_kg': annual_co2_avoided,
        'lifetime_co2_kg': lifetime_co2_avoided,
        'lifetime_co2_tons': lifetime_co2_avoided / 1000
    }

def calculate_panel_layout_optimization(available_width, available_height, panel_width, 
                                      panel_height, spacing_factor=0.05, orientation='portrait'):
    """
    Optimize panel layout for given area.
    
    Args:
        available_width (float): Available width (m)
        available_height (float): Available height (m)
        panel_width (float): Panel width (m)
        panel_height (float): Panel height (m)
        spacing_factor (float): Spacing as fraction of panel size
        orientation (str): 'portrait' or 'landscape'
    
    Returns:
        dict: Optimal layout configuration
    """
    
    layouts = []
    
    # Try both orientations
    orientations = ['portrait', 'landscape'] if orientation == 'auto' else [orientation]
    
    for orient in orientations:
        if orient == 'landscape':
            # Rotate panel dimensions
            p_width, p_height = panel_height, panel_width
        else:
            p_width, p_height = panel_width, panel_height
        
        # Account for spacing
        effective_width = p_width * (1 + spacing_factor)
        effective_height = p_height * (1 + spacing_factor)
        
        # Calculate number of panels
        panels_horizontal = int(available_width // effective_width)
        panels_vertical = int(available_height // effective_height)
        
        total_panels = panels_horizontal * panels_vertical
        
        if total_panels > 0:
            # Calculate actual area used
            actual_width = panels_horizontal * effective_width - p_width * spacing_factor
            actual_height = panels_vertical * effective_height - p_height * spacing_factor
            area_used = actual_width * actual_height
            coverage_ratio = area_used / (available_width * available_height)
            
            layouts.append({
                'orientation': orient,
                'panels_horizontal': panels_horizontal,
                'panels_vertical': panels_vertical,
                'total_panels': total_panels,
                'coverage_ratio': coverage_ratio,
                'area_used': area_used,
                'unused_width': available_width - actual_width,
                'unused_height': available_height - actual_height
            })
    
    # Return layout with maximum panel count
    if layouts:
        optimal_layout = max(layouts, key=lambda x: x['total_panels'])
        return optimal_layout
    else:
        return {
            'orientation': orientation,
            'panels_horizontal': 0,
            'panels_vertical': 0,
            'total_panels': 0,
            'coverage_ratio': 0,
            'area_used': 0,
            'unused_width': available_width,
            'unused_height': available_height
        }

def interpolate_solar_data(data_points, target_timestamps):
    """
    Interpolate solar irradiance data for missing timestamps.
    
    Args:
        data_points (list): List of (timestamp, irradiance) tuples
        target_timestamps (list): Target timestamps for interpolation
    
    Returns:
        list: Interpolated irradiance values
    """
    
    if len(data_points) < 2:
        return [0] * len(target_timestamps)
    
    # Convert to arrays for interpolation
    timestamps = np.array([dp[0].timestamp() for dp in data_points])
    irradiance_values = np.array([dp[1] for dp in data_points])
    target_ts = np.array([ts.timestamp() for ts in target_timestamps])
    
    # Interpolate
    interpolated = np.interp(target_ts, timestamps, irradiance_values)
    
    # Ensure non-negative values
    interpolated = np.maximum(0, interpolated)
    
    return interpolated.tolist()

def calculate_energy_yield_profile(hourly_irradiance, panel_power, panel_efficiency, 
                                 system_losses=0.15, temperature_data=None):
    """
    Calculate hourly energy yield profile for a PV system.
    
    Args:
        hourly_irradiance (list): Hourly irradiance data (W/m²)
        panel_power (float): Total panel power (W)
        panel_efficiency (float): Panel efficiency
        system_losses (float): Total system losses
        temperature_data (list): Hourly temperature data (°C)
    
    Returns:
        dict: Energy yield profile
    """
    
    hourly_energy = []
    daily_energy = []
    monthly_energy = [0] * 12
    
    current_day = 0
    daily_sum = 0
    
    for hour, irradiance in enumerate(hourly_irradiance):
        # Calculate temperature effect if data available
        if temperature_data and len(temperature_data) > hour:
            temperature = temperature_data[hour]
            temp_factor = 1 + (-0.004) * (temperature - 25)  # Standard temperature coefficient
        else:
            temp_factor = 1.0
        
        # Calculate hourly energy (kWh)
        if irradiance > 0:
            power_output = (panel_power * irradiance / 1000 * 
                          panel_efficiency * temp_factor * (1 - system_losses))
            energy_output = power_output / 1000  # Convert W to kWh
        else:
            energy_output = 0
        
        hourly_energy.append(energy_output)
        daily_sum += energy_output
        
        # Check if day is complete (every 24 hours)
        if (hour + 1) % 24 == 0:
            daily_energy.append(daily_sum)
            
            # Add to monthly total (simplified - assume 30 days per month)
            month_index = min(11, hour // (24 * 30))
            monthly_energy[month_index] += daily_sum
            
            daily_sum = 0
    
    # Add remaining partial day
    if daily_sum > 0:
        daily_energy.append(daily_sum)
    
    return {
        'hourly_energy': hourly_energy,
        'daily_energy': daily_energy,
        'monthly_energy': monthly_energy,
        'annual_energy': sum(monthly_energy),
        'peak_hourly': max(hourly_energy) if hourly_energy else 0,
        'peak_daily': max(daily_energy) if daily_energy else 0
    }
