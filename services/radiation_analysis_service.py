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
                cursor.execute("""
                    SELECT element_id, element_type, orientation, azimuth, 
                           glass_area, building_level, family, pv_suitable
                    FROM building_elements 
                    WHERE project_id = %s AND pv_suitable = TRUE
                    ORDER BY element_id
                """, (self.project_id,))
                
                return [dict(row) for row in cursor.fetchall()]
        
        except Exception as e:
            st.error(f"Error fetching suitable elements: {str(e)}")
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
                    
                    # Apply orientation correction
                    orientation_factor = self._get_orientation_factor(orientation)
                    corrected_irradiance = surface_irradiance * orientation_factor
                    
                    annual_radiation += corrected_irradiance
                    peak_irradiance = max(peak_irradiance, corrected_irradiance)
                    
                    # Monthly aggregation
                    month = hour_data.get('month', 1) - 1  # 0-based indexing
                    monthly_totals[month] += corrected_irradiance
                    
            except Exception as e:
                continue  # Skip problematic hours
        
        # Convert to kWh/m²/year
        annual_radiation_kwh = annual_radiation / 1000
        
        return {
            'element_id': element_id,
            'annual_radiation': annual_radiation_kwh,
            'irradiance': peak_irradiance,
            'orientation_multiplier': self._get_orientation_factor(orientation),
            'glass_area': glass_area,
            'monthly_radiation': monthly_totals
        }
    
    def save_element_radiation(self, element_id, radiation_data):
        """Save single element radiation data directly to database"""
        conn = self.db_manager.get_connection()
        if not conn:
            return False
        
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO element_radiation 
                    (project_id, element_id, annual_radiation, irradiance, orientation_multiplier)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (project_id, element_id) 
                    DO UPDATE SET
                        annual_radiation = EXCLUDED.annual_radiation,
                        irradiance = EXCLUDED.irradiance,
                        orientation_multiplier = EXCLUDED.orientation_multiplier
                """, (
                    self.project_id,
                    element_id,
                    radiation_data['annual_radiation'],
                    radiation_data['irradiance'],
                    radiation_data['orientation_multiplier']
                ))
                
                conn.commit()
                return True
                
        except Exception as e:
            conn.rollback()
            st.error(f"Error saving element radiation: {str(e)}")
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
                        SUM(annual_radiation * (SELECT glass_area FROM building_elements be 
                                               WHERE be.element_id = er.element_id AND be.project_id = er.project_id)) as total_potential
                    FROM element_radiation er
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
        # Simplified solar position calculation
        lat_rad = math.radians(latitude)
        
        # Solar declination
        declination = math.radians(23.45) * math.sin(math.radians(360 * (284 + day_of_year) / 365))
        
        # Hour angle
        hour_angle = math.radians(15 * (hour - 12))
        
        # Solar elevation
        elevation = math.asin(
            math.sin(lat_rad) * math.sin(declination) + 
            math.cos(lat_rad) * math.cos(declination) * math.cos(hour_angle)
        )
        
        # Solar azimuth
        azimuth = math.atan2(
            math.sin(hour_angle),
            math.cos(hour_angle) * math.sin(lat_rad) - math.tan(declination) * math.cos(lat_rad)
        )
        
        return {
            'elevation': math.degrees(elevation),
            'azimuth': math.degrees(azimuth) + 180  # Convert to 0-360 range
        }
    
    def _calculate_surface_irradiance(self, ghi, dni, dhi, solar_pos, surface_azimuth, surface_tilt):
        """Calculate irradiance on tilted surface"""
        sun_elevation = math.radians(solar_pos['elevation'])
        sun_azimuth = math.radians(solar_pos['azimuth'])
        surf_azimuth = math.radians(surface_azimuth)
        surf_tilt = math.radians(surface_tilt)
        
        # Angle of incidence
        cos_incidence = (
            math.sin(sun_elevation) * math.cos(surf_tilt) +
            math.cos(sun_elevation) * math.sin(surf_tilt) * math.cos(sun_azimuth - surf_azimuth)
        )
        
        # Direct component
        direct_component = dni * max(0, cos_incidence)
        
        # Diffuse component (isotropic sky model)
        diffuse_component = dhi * (1 + math.cos(surf_tilt)) / 2
        
        # Ground reflected component
        ground_reflected = ghi * 0.2 * (1 - math.cos(surf_tilt)) / 2  # Assuming 20% ground reflectance
        
        return direct_component + diffuse_component + ground_reflected
    
    def _get_orientation_factor(self, orientation):
        """Get orientation correction factor"""
        orientation_factors = {
            'South': 1.0,
            'South (135-225°)': 1.0,
            'Southwest': 0.95,
            'Southeast': 0.95,
            'West': 0.85,
            'West (225-315°)': 0.85,
            'East': 0.85,
            'East (45-135°)': 0.85,
            'Northwest': 0.70,
            'Northeast': 0.70,
            'North': 0.50,
            'North (315-45°)': 0.50
        }
        return orientation_factors.get(orientation, 0.8)
    
    def run_full_analysis(self, tmy_data, latitude, longitude):
        """Run complete radiation analysis - database-driven"""
        suitable_elements = self.get_suitable_elements()
        
        if not suitable_elements:
            st.warning("No suitable building elements found for radiation analysis")
            return False
        
        st.info(f"Running database-driven radiation analysis for {len(suitable_elements)} elements")
        
        # Process each element and save directly to database
        progress_bar = st.progress(0)
        processed_count = 0
        
        for i, element in enumerate(suitable_elements):
            # Calculate radiation for this element
            radiation_data = self.calculate_element_radiation(
                element, tmy_data, latitude, longitude
            )
            
            # Save directly to database
            if self.save_element_radiation(element['element_id'], radiation_data):
                processed_count += 1
            
            # Update progress
            progress_bar.progress((i + 1) / len(suitable_elements))
        
        # Update analysis summary
        self._update_analysis_summary(processed_count)
        
        st.success(f"✅ Database-driven analysis completed: {processed_count} elements processed")
        return True
    
    def _update_analysis_summary(self, processed_count):
        """Update radiation analysis summary in database"""
        summary_data = self.get_analysis_summary()
        if summary_data:
            summary = summary_data['summary']
            
            radiation_data = {
                'avg_irradiance': summary.get('avg_annual_radiation', 0),
                'peak_irradiance': summary.get('peak_irradiance', 0),
                'shading_factor': 0.9,  # Default shading factor
                'grid_points': processed_count,
                'analysis_complete': True
            }
            
            self.db_manager.save_radiation_analysis(self.project_id, radiation_data)