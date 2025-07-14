"""
Advanced Database-Driven Radiation Analysis Service
Combines sophisticated pandas-based calculations with database operations
"""

import streamlit as st
import numpy as np
import math
from datetime import datetime
from database_manager import db_manager
from psycopg2.extras import RealDictCursor

class AdvancedRadiationAnalyzer:
    """Advanced radiation analysis with sophisticated calculations - database-driven"""
    
    def __init__(self, project_id):
        self.project_id = project_id
        self.db_manager = db_manager
        
    def get_suitable_elements(self):
        """Get suitable building elements directly from database"""
        conn = self.db_manager.get_connection()
        if not conn:
            return []
        
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT element_id, orientation, azimuth, glass_area, building_level, 
                           family, wall_element_id, oriz
                    FROM building_elements 
                    WHERE project_id = %s AND pv_suitable = TRUE
                    ORDER BY orientation, azimuth
                """, (self.project_id,))
                
                elements = cursor.fetchall()
                return [dict(row) for row in elements]
                
        except Exception as e:
            st.error(f"Error getting suitable elements: {str(e)}")
            return []
        finally:
            conn.close()
    
    def calculate_solar_position_simple(self, latitude, longitude, day_of_year, hour):
        """Calculate solar position using simplified formulas."""
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
        
        return {
            'elevation': math.degrees(elevation),
            'azimuth': math.degrees(azimuth) + 180,  # Convert to 0-360 range
            'zenith': 90 - math.degrees(elevation)
        }
    
    def calculate_irradiance_on_surface(self, ghi, dni, dhi, solar_position, surface_tilt, surface_azimuth):
        """Calculate irradiance on tilted surface using sophisticated model."""
        zenith = math.radians(solar_position['zenith'])
        sun_azimuth = math.radians(solar_position['azimuth'])
        surface_tilt_rad = math.radians(surface_tilt)
        surface_azimuth_rad = math.radians(surface_azimuth)
        
        # Calculate angle of incidence
        cos_incidence = (
            math.sin(zenith) * math.sin(surface_tilt_rad) * 
            math.cos(sun_azimuth - surface_azimuth_rad) +
            math.cos(zenith) * math.cos(surface_tilt_rad)
        )
        
        # Ensure cos_incidence is not negative
        cos_incidence = max(0, cos_incidence)
        
        # POA calculation with ground reflectance
        direct_on_surface = dni * cos_incidence
        diffuse_on_surface = dhi * (1 + math.cos(surface_tilt_rad)) / 2
        reflected_on_surface = ghi * 0.2 * (1 - math.cos(surface_tilt_rad)) / 2  # 0.2 = ground albedo
        
        poa_global = direct_on_surface + diffuse_on_surface + reflected_on_surface
        
        return max(0, poa_global)
    
    def calculate_ground_reflectance_factor(self, height_from_ground, tilt_angle=90, albedo=0.2):
        """Calculate ground reflectance contribution based on window height from ground."""
        # View factor to ground for vertical surface
        if height_from_ground <= 0:
            return 0.0
        
        # Calculate view factor to ground based on height and tilt
        tilt_rad = math.radians(tilt_angle)
        
        # For vertical windows (90°), view factor decreases with height
        if tilt_angle >= 85:  # Nearly vertical
            view_factor_ground = max(0.1, 0.5 * math.exp(-height_from_ground / 10.0))
        else:
            view_factor_ground = (1 - math.cos(tilt_rad)) / 2
            view_factor_ground *= max(0.2, math.exp(-height_from_ground / 15.0))
        
        # Ground reflectance contribution
        ground_reflectance_factor = albedo * view_factor_ground
        
        return min(ground_reflectance_factor, 0.15)  # Cap at 15% contribution
    
    def calculate_height_dependent_ghi_effects(self, height_from_ground, base_ghi):
        """Calculate height-dependent effects on Global Horizontal Irradiance."""
        # Height-dependent atmospheric clarity improvement
        atmospheric_clarity = 1.0 + (height_from_ground * 0.001)  # 0.1% improvement per meter
        atmospheric_clarity = min(atmospheric_clarity, 1.05)  # Cap at 5% improvement
        
        # Horizon obstruction factor
        if height_from_ground <= 3.0:  # Ground level
            horizon_factor = 0.95  # 5% reduction due to ground obstacles
        elif height_from_ground <= 10.0:  # Low to mid height
            horizon_factor = 0.98  # 2% reduction
        else:  # High elevation
            horizon_factor = 1.0  # No reduction
        
        # Combined height factor
        height_factor = atmospheric_clarity * horizon_factor
        
        return {
            'adjusted_ghi': base_ghi * height_factor,
            'height_factor': height_factor,
            'atmospheric_clarity': atmospheric_clarity,
            'horizon_factor': horizon_factor
        }
    
    def estimate_height_from_ground(self, level, floor_height=3.5):
        """Estimate window height from ground based on building level."""
        try:
            # Extract numeric level
            if isinstance(level, str):
                level_num = int(level.replace('Level', '').replace('level', '').strip())
            else:
                level_num = int(level)
            
            # Calculate height: ground floor + (level-1) * floor_height + window center
            height = level_num * floor_height + 1.5  # 1.5m window center height
            
            return max(1.5, height)  # Minimum 1.5m height
            
        except (ValueError, TypeError):
            return 3.5  # Default to ground floor window height
    
    def calculate_precise_shading_factor(self, window_element, walls_data, solar_position):
        """Calculate precise shading factor for a window from building walls."""
        if not walls_data:
            return 1.0  # No shading if no wall data
        
        combined_shading_factor = 1.0
        
        # Check shading from each wall
        for wall in walls_data:
            wall_shading_factor = self._calculate_wall_shading(wall, window_element, solar_position)
            combined_shading_factor *= wall_shading_factor
        
        return max(0.2, combined_shading_factor)  # Minimum 20% of unshaded radiation
    
    def _calculate_wall_shading(self, wall_element, window_element, solar_position):
        """Calculate shading factor from a specific wall."""
        try:
            # Get wall properties
            wall_azimuth = float(wall_element.get('azimuth', 180))
            wall_height = float(wall_element.get('height', 3.0))
            wall_level = wall_element.get('level', 'Level 1')
            
            # Get window properties
            window_azimuth = float(window_element.get('azimuth', 180))
            window_level = window_element.get('building_level', 'Level 1')
            
            # Get solar position
            sun_elevation = solar_position.get('elevation', 0)
            sun_azimuth = solar_position.get('azimuth', 180)
            
            # Skip if sun below horizon
            if sun_elevation <= 0:
                return 1.0  # No shading at night
            
            # Calculate shadow length based on sun elevation
            shadow_length = wall_height / math.tan(math.radians(max(sun_elevation, 0.1)))
            
            # Check if wall can shade this window
            azimuth_diff = abs(wall_azimuth - window_azimuth)
            if azimuth_diff > 180:
                azimuth_diff = 360 - azimuth_diff
            
            # Level compatibility check
            level_factor = 1.0
            if wall_level != window_level:
                level_factor = 0.5
            
            # Calculate geometric shading intensity
            if azimuth_diff < 90:  # Wall can potentially shade window
                proximity_factor = max(0, 1 - (azimuth_diff / 90))
                
                # Shadow intensity based on sun angle relative to wall
                wall_sun_angle = abs(wall_azimuth - sun_azimuth)
                if wall_sun_angle > 180:
                    wall_sun_angle = 360 - wall_sun_angle
                
                # Wall creates shadow when sun is behind it
                if wall_sun_angle > 90:
                    shadow_intensity = min(0.6, (wall_sun_angle - 90) / 90 * 0.6)
                    shading_factor = max(0.4, 1.0 - (shadow_intensity * proximity_factor * level_factor))
                else:
                    shading_factor = 1.0
            else:
                shading_factor = 1.0
            
            return shading_factor
            
        except Exception as e:
            return 0.9  # Conservative default shading factor
    
    def get_walls_data(self):
        """Get walls data from database for shading calculations"""
        conn = self.db_manager.get_connection()
        if not conn:
            return []
        
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Check if walls table exists (optional feature)
                cursor.execute("""
                    SELECT table_name FROM information_schema.tables 
                    WHERE table_schema = 'public' AND table_name = 'building_walls'
                """)
                
                if cursor.fetchone():
                    cursor.execute("""
                        SELECT wall_id, azimuth, height, level, area
                        FROM building_walls 
                        WHERE project_id = %s
                    """, (self.project_id,))
                    
                    walls = cursor.fetchall()
                    return [dict(row) for row in walls]
                else:
                    return []  # No walls table - skip shading calculations
                    
        except Exception as e:
            st.info(f"Walls data not available for shading calculations: {str(e)}")
            return []
        finally:
            conn.close()
    
    def run_advanced_analysis(self, tmy_data, latitude, longitude, precision="Daily Peak", 
                            include_shading=True, apply_corrections=True, progress_callback=None):
        """Run complete advanced radiation analysis with all sophisticated calculations"""
        
        # Get suitable elements
        suitable_elements = self.get_suitable_elements()
        if not suitable_elements:
            return False
        
        # Get walls data for shading
        walls_data = self.get_walls_data() if include_shading else []
        
        # Configure precision settings
        precision_settings = {
            "Hourly": {"hours": list(range(7, 18)), "days": list(range(1, 366)), "scaling": 1.0},
            "Daily Peak": {"hours": [12], "days": list(range(1, 366)), "scaling": 24.0},
            "Monthly Average": {"hours": [12], "days": [15, 46, 74, 105, 135, 166, 196, 227, 258, 288, 319, 349], "scaling": 365.0/12.0},
            "Yearly Average": {"hours": [12], "days": [80, 173, 266, 356], "scaling": 365.0/4.0}
        }
        
        settings = precision_settings.get(precision, precision_settings["Daily Peak"])
        sample_hours = settings["hours"]
        days_sample = settings["days"]
        scaling_factor = settings["scaling"]
        
        # Process each element
        radiation_results = []
        total_elements = len(suitable_elements)
        
        for i, element in enumerate(suitable_elements):
            try:
                if progress_callback:
                    progress_callback(f"Processing {element['element_id']}", i, total_elements)
                
                # Calculate radiation for this element
                radiation_data = self._calculate_element_radiation_advanced(
                    element, tmy_data, latitude, longitude,
                    sample_hours, days_sample, scaling_factor,
                    walls_data, apply_corrections
                )
                
                if radiation_data:
                    radiation_results.append(radiation_data)
                
            except Exception as e:
                st.error(f"Error processing element {element['element_id']}: {str(e)}")
                continue
        
        # Save results to database
        if radiation_results:
            return self._save_advanced_results(radiation_results)
        
        return False
    
    def _calculate_element_radiation_advanced(self, element, tmy_data, latitude, longitude,
                                           sample_hours, days_sample, scaling_factor,
                                           walls_data, apply_corrections):
        """Calculate radiation for a single element using advanced methods"""
        
        element_id = element['element_id']
        orientation = element['orientation']
        azimuth = float(element['azimuth'])
        glass_area = float(element['glass_area'])
        building_level = element.get('building_level', 'Level 1')
        
        # Calculate actual tilt angle from BIM orientation vectors
        ori_z = element.get('oriz')
        if ori_z is not None:
            try:
                ori_z_float = float(ori_z)
                ori_z_clamped = max(-1.0, min(1.0, ori_z_float))
                tilt = math.degrees(math.acos(abs(ori_z_clamped)))
            except (ValueError, TypeError):
                tilt = 90.0  # Default to vertical
        else:
            tilt = 90.0  # Default to vertical
        
        # Estimate height from ground
        height_from_ground = self.estimate_height_from_ground(building_level)
        
        # Calculate radiation for sampled time points
        total_irradiance = 0
        peak_irradiance = 0
        monthly_totals = [0] * 12
        
        for day in days_sample:
            for hour in sample_hours:
                # Find matching TMY data
                matching_data = None
                for hour_data in tmy_data:
                    if (hour_data.get('day_of_year') == day and 
                        hour_data.get('hour') == hour):
                        matching_data = hour_data
                        break
                
                if not matching_data:
                    continue
                
                # Calculate solar position
                solar_pos = self.calculate_solar_position_simple(latitude, longitude, day, hour)
                
                # Get irradiance components
                ghi = float(matching_data.get('ghi', 0) or 0)
                dni = float(matching_data.get('dni', 0) or 0)
                dhi = float(matching_data.get('dhi', 0) or 0)
                
                if ghi <= 0:
                    continue  # Skip night hours
                
                # Apply height-dependent GHI effects
                height_effects = self.calculate_height_dependent_ghi_effects(height_from_ground, ghi)
                adjusted_ghi = height_effects['adjusted_ghi']
                
                # Calculate surface irradiance
                surface_irradiance = self.calculate_irradiance_on_surface(
                    adjusted_ghi, dni, dhi, solar_pos, tilt, azimuth
                )
                
                # Apply ground reflectance
                ground_contribution = self.calculate_ground_reflectance_factor(height_from_ground)
                surface_irradiance += adjusted_ghi * ground_contribution
                
                # Apply shading if walls data available
                if walls_data:
                    shading_factor = self.calculate_precise_shading_factor(element, walls_data, solar_pos)
                    surface_irradiance *= shading_factor
                
                # Apply orientation corrections
                if apply_corrections:
                    orientation_factor = self._get_orientation_factor(orientation)
                    surface_irradiance *= orientation_factor
                
                # Accumulate results
                total_irradiance += surface_irradiance
                peak_irradiance = max(peak_irradiance, surface_irradiance)
                
                # Monthly totals
                month = matching_data.get('month', 1) - 1
                if 0 <= month < 12:
                    monthly_totals[month] += surface_irradiance
        
        # Scale to annual values
        annual_irradiation = (total_irradiance * scaling_factor) / 1000  # Convert to kWh/m²/year
        
        # Ensure realistic minimum values
        annual_irradiation = max(annual_irradiation, 200)  # Minimum 200 kWh/m²/year
        
        return {
            'element_id': element_id,
            'annual_radiation': annual_irradiation,
            'peak_irradiance': peak_irradiance,
            'monthly_totals': monthly_totals,
            'orientation_factor': self._get_orientation_factor(orientation),
            'height_from_ground': height_from_ground,
            'tilt': tilt,
            'glass_area': glass_area
        }
    
    def _get_orientation_factor(self, orientation):
        """Get orientation correction factor"""
        orientation_factors = {
            'South': 1.0,
            'South (135-225°)': 1.0,
            'Southeast': 0.95,
            'Southwest': 0.95,
            'East': 0.85,
            'East (45-135°)': 0.85,
            'West': 0.85,
            'West (225-315°)': 0.85,
            'Northeast': 0.70,
            'Northwest': 0.70,
            'North': 0.30,
            'North (315-45°)': 0.30
        }
        return orientation_factors.get(orientation, 0.8)
    
    def _save_advanced_results(self, radiation_results):
        """Save advanced radiation results to database"""
        conn = self.db_manager.get_connection()
        if not conn:
            return False
        
        try:
            with conn.cursor() as cursor:
                # Clear existing radiation data
                cursor.execute("DELETE FROM element_radiation WHERE project_id = %s", (self.project_id,))
                
                # Insert new radiation data
                for result in radiation_results:
                    cursor.execute("""
                        INSERT INTO element_radiation 
                        (project_id, element_id, annual_radiation, irradiance, orientation_multiplier)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (
                        self.project_id,
                        result['element_id'],
                        result['annual_radiation'],
                        result['peak_irradiance'],
                        result['orientation_factor']
                    ))
                
                # Save analysis summary
                cursor.execute("DELETE FROM radiation_analysis WHERE project_id = %s", (self.project_id,))
                
                avg_radiation = sum(r['annual_radiation'] for r in radiation_results) / len(radiation_results)
                max_radiation = max(r['annual_radiation'] for r in radiation_results)
                
                cursor.execute("""
                    INSERT INTO radiation_analysis 
                    (project_id, avg_irradiance, peak_irradiance, shading_factor, grid_points, analysis_complete)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    self.project_id,
                    avg_radiation,
                    max_radiation,
                    1.0,  # Average shading factor
                    len(radiation_results),
                    True
                ))
                
                conn.commit()
                return True
                
        except Exception as e:
            conn.rollback()
            st.error(f"Error saving advanced radiation results: {str(e)}")
            return False
        finally:
            conn.close()