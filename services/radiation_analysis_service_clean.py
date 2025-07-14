"""
Database-driven radiation analysis service
Replaces pandas-based processing with direct database operations
"""

import streamlit as st
from database_manager import db_manager
from psycopg2.extras import RealDictCursor
import math
import numpy as np
from datetime import datetime

class DatabaseRadiationAnalyzer:
    """Database-driven radiation analysis - no pandas DataFrames"""
    
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
                # First check if any building elements exist for this project
                cursor.execute("""
                    SELECT COUNT(*) as total_elements,
                           COUNT(CASE WHEN pv_suitable = TRUE THEN 1 END) as suitable_elements
                    FROM building_elements 
                    WHERE project_id = %s
                """, (self.project_id,))
                
                counts = cursor.fetchone()
                st.write(f"**Debug Info**: Project {self.project_id} has {counts['total_elements']} total elements, {counts['suitable_elements']} suitable")
                
                if counts['total_elements'] == 0:
                    st.warning(f"⚠️ No building elements found for project {self.project_id}. Please complete Step 4 (BIM Upload) first.")
                    return []
                
                if counts['suitable_elements'] == 0:
                    st.warning(f"⚠️ No suitable elements found for project {self.project_id}. All elements may be North-facing or unsuitable for PV.")
                    return []
                
                # Get suitable elements
                cursor.execute("""
                    SELECT element_id, orientation, azimuth, glass_area, building_level, family
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
    
    def calculate_element_radiation(self, element_data, tmy_data, latitude, longitude):
        """Calculate radiation for a single element - database-driven"""
        element_id = element_data['element_id']
        orientation = element_data['orientation']
        azimuth = float(element_data['azimuth'])
        glass_area = float(element_data['glass_area'])
        
        # Solar calculations using TMY data
        annual_radiation = 0
        peak_irradiance = 0
        monthly_totals = [0] * 12
        
        # Process TMY data for this element
        for hour_data in tmy_data:
            try:
                # Get solar position for this hour
                solar_pos = self._calculate_solar_position(
                    latitude, longitude, 
                    hour_data.get('day_of_year', 180),
                    hour_data.get('hour', 12)
                )
                
                # Calculate irradiance on tilted surface
                ghi = hour_data.get('ghi', 0)
                dni = hour_data.get('dni', 0)
                dhi = hour_data.get('dhi', 0)
                
                if ghi > 0:  # Only process daylight hours
                    surface_irradiance = self._calculate_surface_irradiance(
                        ghi, dni, dhi, solar_pos, azimuth, 90  # 90° tilt for vertical windows
                    )
                    
                    # Accumulate radiation
                    annual_radiation += surface_irradiance / 1000  # Convert W/m² to kWh/m²
                    peak_irradiance = max(peak_irradiance, surface_irradiance)
                    
                    # Monthly totals
                    month = hour_data.get('month', 1) - 1  # 0-based indexing
                    if 0 <= month < 12:
                        monthly_totals[month] += surface_irradiance / 1000
                
            except Exception as e:
                continue  # Skip problematic hours
        
        # Orientation-based multiplier
        orientation_multiplier = self._get_orientation_multiplier(orientation)
        annual_radiation *= orientation_multiplier
        
        return {
            'element_id': element_id,
            'annual_radiation': annual_radiation,
            'peak_irradiance': peak_irradiance,
            'monthly_totals': monthly_totals,
            'orientation_multiplier': orientation_multiplier
        }
    
    def save_radiation_results(self, radiation_results):
        """Save radiation results to database"""
        conn = self.db_manager.get_connection()
        if not conn:
            return False
        
        try:
            with conn.cursor() as cursor:
                # Clear existing radiation data for this project
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
                        result['orientation_multiplier']
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
                    1.0,  # Default shading factor
                    len(radiation_results),
                    True
                ))
                
                conn.commit()
                return True
                
        except Exception as e:
            conn.rollback()
            st.error(f"Error saving radiation results: {str(e)}")
            return False
        finally:
            conn.close()
    
    def get_analysis_summary(self):
        """Get radiation analysis summary from database"""
        conn = self.db_manager.get_connection()
        if not conn:
            return None
        
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Get summary statistics
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_elements,
                        AVG(annual_radiation) as avg_annual_radiation,
                        MAX(irradiance) as peak_irradiance,
                        SUM(annual_radiation) as total_potential
                    FROM element_radiation 
                    WHERE project_id = %s
                """, (self.project_id,))
                
                summary = cursor.fetchone()
                
                # Get orientation distribution
                cursor.execute("""
                    SELECT be.orientation, COUNT(*) as count, AVG(er.annual_radiation) as avg_radiation
                    FROM element_radiation er
                    JOIN building_elements be ON er.element_id = be.element_id AND er.project_id = be.project_id
                    WHERE er.project_id = %s
                    GROUP BY be.orientation
                    ORDER BY avg_radiation DESC
                """, (self.project_id,))
                
                orientation_dist = cursor.fetchall()
                
                return {
                    'summary': dict(summary) if summary else {},
                    'orientation_distribution': [dict(row) for row in orientation_dist]
                }
                
        except Exception as e:
            st.error(f"Error getting analysis summary: {str(e)}")
            return None
        finally:
            conn.close()
    
    def _calculate_solar_position(self, latitude, longitude, day_of_year, hour):
        """Calculate solar position using astronomical algorithms"""
        # Convert to radians
        lat_rad = math.radians(latitude)
        
        # Solar declination
        declination = 23.45 * math.sin(math.radians(360 * (284 + day_of_year) / 365))
        decl_rad = math.radians(declination)
        
        # Hour angle
        hour_angle = 15 * (hour - 12)  # degrees
        hour_angle_rad = math.radians(hour_angle)
        
        # Solar elevation angle
        sin_elevation = (math.sin(lat_rad) * math.sin(decl_rad) + 
                        math.cos(lat_rad) * math.cos(decl_rad) * math.cos(hour_angle_rad))
        elevation = math.degrees(math.asin(max(-1, min(1, sin_elevation))))
        
        # Solar azimuth angle
        cos_azimuth = ((math.sin(decl_rad) * math.cos(lat_rad) - 
                       math.cos(decl_rad) * math.sin(lat_rad) * math.cos(hour_angle_rad)) /
                      math.cos(math.radians(elevation)))
        
        azimuth = math.degrees(math.acos(max(-1, min(1, cos_azimuth))))
        
        # Adjust azimuth for afternoon hours
        if hour > 12:
            azimuth = 360 - azimuth
        
        return {
            'elevation': max(0, elevation),
            'azimuth': azimuth
        }
    
    def _calculate_surface_irradiance(self, ghi, dni, dhi, solar_pos, surface_azimuth, surface_tilt):
        """Calculate irradiance on tilted surface"""
        solar_elevation = solar_pos['elevation']
        solar_azimuth = solar_pos['azimuth']
        
        if solar_elevation <= 0:
            return 0
        
        # Convert angles to radians
        surf_tilt_rad = math.radians(surface_tilt)
        surf_azimuth_rad = math.radians(surface_azimuth)
        sol_elevation_rad = math.radians(solar_elevation)
        sol_azimuth_rad = math.radians(solar_azimuth)
        
        # Calculate angle of incidence
        cos_incidence = (math.sin(sol_elevation_rad) * math.cos(surf_tilt_rad) +
                        math.cos(sol_elevation_rad) * math.sin(surf_tilt_rad) *
                        math.cos(sol_azimuth_rad - surf_azimuth_rad))
        
        # Direct normal irradiance on surface
        direct_surface = dni * max(0, cos_incidence)
        
        # Diffuse irradiance (simplified model)
        diffuse_surface = dhi * (1 + math.cos(surf_tilt_rad)) / 2
        
        # Ground reflected irradiance
        ground_reflected = ghi * 0.2 * (1 - math.cos(surf_tilt_rad)) / 2
        
        return direct_surface + diffuse_surface + ground_reflected
    
    def _get_orientation_multiplier(self, orientation):
        """Get orientation correction multiplier"""
        orientation_factors = {
            'South': 1.0,
            'Southeast': 0.9,
            'Southwest': 0.9,
            'East': 0.85,
            'West': 0.85,
            'Northeast': 0.7,
            'Northwest': 0.7,
            'North': 0.3
        }
        return orientation_factors.get(orientation, 0.8)