"""
Database-driven radiation analysis service
Replaces pandas-based processing with direct database operations
DEPRECATED: Use radiation_analysis_service_clean.py instead
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
                    st.warning(f"⚠️ No PV-suitable elements found for project {self.project_id}. All elements may be north-facing or filtered out.")
                    return []
                
                # Get the suitable elements
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
    
    def run_full_analysis(self, tmy_data, latitude, longitude, progress_callback=None):
        """Run complete radiation analysis - database-driven with live progress"""
        suitable_elements = self.get_suitable_elements()
        
        if not suitable_elements:
            if progress_callback:
                progress_callback("❌ No suitable building elements found", 0)
            st.warning("No suitable building elements found for radiation analysis")
            return False
        
        total_elements = len(suitable_elements)
        if progress_callback:
            progress_callback(f"Found {total_elements} suitable elements for analysis", 5)
        
        # Process each element and save directly to database
        processed_count = 0
        
        for i, element in enumerate(suitable_elements):
            element_id = element['element_id']
            orientation = element.get('orientation', 'Unknown')
            glass_area = element.get('glass_area', 0)
            
            if progress_callback:
                progress_callback(
                    f"Processing element {i+1}/{total_elements}: {element_id} ({orientation})",
                    int(10 + (i / total_elements) * 80),  # Progress from 10% to 90%
                    f"Element {element_id} - {orientation} - {glass_area:.1f}m²"
                )
            
            # Calculate radiation for this element
            radiation_data = self.calculate_element_radiation(
                element, tmy_data, latitude, longitude
            )
            
            # Save directly to database
            if self.save_element_radiation(element['element_id'], radiation_data):
                processed_count += 1
                if progress_callback:
                    annual_rad = radiation_data.get('annual_radiation', 0)
                    progress_callback(
                        f"✅ Completed element {element_id}: {annual_rad:.0f} kWh/m²/year",
                        int(10 + ((i+1) / total_elements) * 80),
                        f"Saved: {element_id} - {annual_rad:.0f} kWh/m²/year"
                    )
            else:
                if progress_callback:
                    progress_callback(f"❌ Failed to save element {element_id}", None, None)
        
        # Update analysis summary
        if progress_callback:
            progress_callback("Updating analysis summary...", 95)
        
        self._update_analysis_summary(processed_count)
        
        if progress_callback:
            progress_callback(f"✅ Analysis completed: {processed_count} elements processed", 100)
        
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