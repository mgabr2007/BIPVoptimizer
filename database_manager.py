"""
Database Manager for BIPV Optimizer
Handles data persistence and retrieval for all workflow analysis steps
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
import streamlit as st
from datetime import datetime
import json

class BIPVDatabaseManager:
    def __init__(self):
        self.connection_params = {
            'host': os.getenv('PGHOST'),
            'port': os.getenv('PGPORT'),
            'database': os.getenv('PGDATABASE'),
            'user': os.getenv('PGUSER'),
            'password': os.getenv('PGPASSWORD')
        }
    
    def get_connection(self):
        """Get database connection"""
        try:
            conn = psycopg2.connect(**self.connection_params)
            return conn
        except Exception as e:
            st.error(f"Database connection failed: {str(e)}")
            return None
    
    def save_project(self, project_data):
        """Save or update project data"""
        conn = self.get_connection()
        if not conn:
            return None
        
        try:
            with conn.cursor() as cursor:
                # Check if project exists
                cursor.execute(
                    "SELECT id FROM projects WHERE project_name = %s",
                    (project_data.get('project_name'),)
                )
                existing = cursor.fetchone()
                
                if existing:
                    # Update existing project
                    cursor.execute("""
                        UPDATE projects SET 
                            location = %s, latitude = %s, longitude = %s, 
                            timezone = %s, currency = %s, updated_at = CURRENT_TIMESTAMP
                        WHERE project_name = %s
                        RETURNING id
                    """, (
                        project_data.get('location'),
                        project_data.get('coordinates', {}).get('lat'),
                        project_data.get('coordinates', {}).get('lon'),
                        project_data.get('timezone'),
                        project_data.get('currency', 'EUR'),
                        project_data.get('project_name')
                    ))
                else:
                    # Insert new project
                    cursor.execute("""
                        INSERT INTO projects (project_name, location, latitude, longitude, timezone, currency)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """, (
                        project_data.get('project_name'),
                        project_data.get('location'),
                        project_data.get('coordinates', {}).get('lat'),
                        project_data.get('coordinates', {}).get('lon'),
                        project_data.get('timezone'),
                        project_data.get('currency', 'EUR')
                    ))
                
                project_id = cursor.fetchone()[0]
                conn.commit()
                return project_id
                
        except Exception as e:
            conn.rollback()
            st.error(f"Error saving project: {str(e)}")
            return None
        finally:
            conn.close()
    
    def save_weather_data(self, project_id, weather_data):
        """Save weather and TMY data"""
        conn = self.get_connection()
        if not conn:
            return False
        
        try:
            with conn.cursor() as cursor:
                # Delete existing weather data for this project
                cursor.execute("DELETE FROM weather_data WHERE project_id = %s", (project_id,))
                
                # Insert new weather data
                cursor.execute("""
                    INSERT INTO weather_data 
                    (project_id, temperature, humidity, description, annual_ghi, annual_dni, annual_dhi)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    project_id,
                    weather_data.get('temperature'),
                    weather_data.get('humidity'),
                    weather_data.get('description'),
                    weather_data.get('annual_ghi'),
                    weather_data.get('annual_dni'),
                    weather_data.get('annual_dhi')
                ))
                
                conn.commit()
                return True
                
        except Exception as e:
            conn.rollback()
            st.error(f"Error saving weather data: {str(e)}")
            return False
        finally:
            conn.close()
    
    def save_building_elements(self, project_id, building_elements):
        """Save BIM building elements data"""
        conn = self.get_connection()
        if not conn:
            return False
        
        try:
            with conn.cursor() as cursor:
                # Delete existing building elements for this project
                cursor.execute("DELETE FROM building_elements WHERE project_id = %s", (project_id,))
                
                # Handle both DataFrame and list formats
                if hasattr(building_elements, 'iterrows'):
                    # DataFrame format
                    for _, element in building_elements.iterrows():
                        cursor.execute("""
                            INSERT INTO building_elements 
                            (project_id, element_id, wall_element_id, element_type, orientation, 
                             azimuth, glass_area, window_width, window_height, building_level, 
                             family, pv_suitable)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """, (
                            project_id,
                            element.get('Element_ID'),
                            element.get('Wall_Element_ID'),
                            element.get('element_type', 'Window'),
                            element.get('orientation'),
                            element.get('azimuth'),
                            element.get('Glass_Area', 0),
                            element.get('window_width'),
                            element.get('window_height'),
                            element.get('Level'),
                            element.get('Family'),
                            element.get('PV_Suitable', False)
                        ))
                else:
                    # List format
                    for element in building_elements:
                        cursor.execute("""
                            INSERT INTO building_elements 
                            (project_id, element_id, wall_element_id, element_type, orientation, 
                             azimuth, glass_area, window_width, window_height, building_level, 
                             family, pv_suitable)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """, (
                            project_id,
                            element.get('element_id'),
                            element.get('wall_element_id'),
                            element.get('element_type', 'Window'),
                            element.get('orientation'),
                            element.get('azimuth'),
                            element.get('glass_area', 0),
                            element.get('window_width'),
                            element.get('window_height'),
                            element.get('level'),
                            element.get('family'),
                            element.get('pv_suitable', False)
                        ))
                
                conn.commit()
                return True
                
        except Exception as e:
            conn.rollback()
            st.error(f"Error saving building elements: {str(e)}")
            return False
        finally:
            conn.close()
    
    def save_radiation_analysis(self, project_id, radiation_data):
        """Save radiation analysis results"""
        conn = self.get_connection()
        if not conn:
            return False
        
        try:
            with conn.cursor() as cursor:
                # Delete existing radiation analysis for this project
                cursor.execute("DELETE FROM radiation_analysis WHERE project_id = %s", (project_id,))
                
                # Insert radiation analysis data
                cursor.execute("""
                    INSERT INTO radiation_analysis 
                    (project_id, avg_irradiance, peak_irradiance, shading_factor, grid_points, analysis_complete)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    project_id,
                    radiation_data.get('avg_irradiance'),
                    radiation_data.get('peak_irradiance'),
                    radiation_data.get('shading_factor'),
                    radiation_data.get('grid_points'),
                    radiation_data.get('analysis_complete', True)
                ))
                
                # Save element radiation data if available
                element_radiation = radiation_data.get('element_radiation', [])
                if element_radiation:
                    cursor.execute("DELETE FROM element_radiation WHERE project_id = %s", (project_id,))
                    
                    for element in element_radiation:
                        cursor.execute("""
                            INSERT INTO element_radiation 
                            (project_id, element_id, annual_radiation, irradiance, orientation_multiplier)
                            VALUES (%s, %s, %s, %s, %s)
                        """, (
                            project_id,
                            element.get('element_id'),
                            element.get('annual_radiation'),
                            element.get('irradiance'),
                            element.get('orientation_multiplier', 1.0)
                        ))
                
                conn.commit()
                return True
                
        except Exception as e:
            conn.rollback()
            st.error(f"Error saving radiation analysis: {str(e)}")
            return False
        finally:
            conn.close()
    
    def save_pv_specifications(self, project_id, pv_specs):
        """Save PV specifications"""
        conn = self.get_connection()
        if not conn:
            return False
        
        try:
            with conn.cursor() as cursor:
                # Delete existing PV specs for this project
                cursor.execute("DELETE FROM pv_specifications WHERE project_id = %s", (project_id,))
                
                # Insert PV specifications
                cursor.execute("""
                    INSERT INTO pv_specifications 
                    (project_id, panel_type, efficiency, transparency, cost_per_m2, power_density, installation_factor)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    project_id,
                    pv_specs.get('panel_type'),
                    pv_specs.get('efficiency'),
                    pv_specs.get('transparency'),
                    pv_specs.get('cost_per_m2'),
                    pv_specs.get('power_density'),
                    pv_specs.get('installation_factor')
                ))
                
                conn.commit()
                return True
                
        except Exception as e:
            conn.rollback()
            st.error(f"Error saving PV specifications: {str(e)}")
            return False
        finally:
            conn.close()
    
    def save_financial_analysis(self, project_id, financial_data):
        """Save financial analysis results"""
        conn = self.get_connection()
        if not conn:
            return False
        
        try:
            with conn.cursor() as cursor:
                # Delete existing financial analysis for this project
                cursor.execute("DELETE FROM financial_analysis WHERE project_id = %s", (project_id,))
                
                # Insert financial analysis
                cursor.execute("""
                    INSERT INTO financial_analysis 
                    (project_id, initial_investment, annual_savings, annual_generation, 
                     annual_export_revenue, annual_om_cost, net_annual_benefit, 
                     npv, irr, payback_period, lcoe, analysis_complete)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    project_id,
                    financial_data.get('initial_investment'),
                    financial_data.get('annual_savings'),
                    financial_data.get('annual_generation'),
                    financial_data.get('annual_export_revenue'),
                    financial_data.get('annual_om_cost'),
                    financial_data.get('net_annual_benefit'),
                    financial_data.get('npv'),
                    financial_data.get('irr'),
                    financial_data.get('payback_period'),
                    financial_data.get('lcoe'),
                    financial_data.get('analysis_complete', True)
                ))
                
                # Save environmental impact data
                cursor.execute("DELETE FROM environmental_impact WHERE project_id = %s", (project_id,))
                cursor.execute("""
                    INSERT INTO environmental_impact 
                    (project_id, co2_savings_annual, co2_savings_lifetime, carbon_value, trees_equivalent, cars_equivalent)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    project_id,
                    financial_data.get('co2_savings_annual'),
                    financial_data.get('co2_savings_lifetime'),
                    financial_data.get('carbon_value'),
                    financial_data.get('trees_equivalent'),
                    financial_data.get('cars_equivalent')
                ))
                
                conn.commit()
                return True
                
        except Exception as e:
            conn.rollback()
            st.error(f"Error saving financial analysis: {str(e)}")
            return False
        finally:
            conn.close()
    
    def get_project_report_data(self, project_name):
        """Get comprehensive project data for reports"""
        conn = self.get_connection()
        if not conn:
            return None
        
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Get comprehensive project data using the view
                cursor.execute("""
                    SELECT * FROM project_report_view 
                    WHERE project_name = %s
                """, (project_name,))
                
                project_data = cursor.fetchone()
                
                if not project_data:
                    return None
                
                # Convert to dict and get additional data
                result = dict(project_data)
                
                # Get building elements
                cursor.execute("""
                    SELECT * FROM building_elements 
                    WHERE project_id = %s
                    ORDER BY element_id
                """, (result['project_id'],))
                result['building_elements'] = [dict(row) for row in cursor.fetchall()]
                
                # Get element radiation data
                cursor.execute("""
                    SELECT * FROM element_radiation 
                    WHERE project_id = %s
                    ORDER BY element_id
                """, (result['project_id'],))
                result['element_radiation'] = [dict(row) for row in cursor.fetchall()]
                
                # Get optimization results
                cursor.execute("""
                    SELECT * FROM optimization_results 
                    WHERE project_id = %s
                    ORDER BY rank_position
                """, (result['project_id'],))
                result['optimization_results'] = [dict(row) for row in cursor.fetchall()]
                
                return result
                
        except Exception as e:
            st.error(f"Error retrieving project data: {str(e)}")
            return None
        finally:
            conn.close()
    
    def list_projects(self):
        """List all projects in the database"""
        conn = self.get_connection()
        if not conn:
            return []
        
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT project_name, location, created_at, updated_at
                    FROM projects 
                    ORDER BY updated_at DESC
                """)
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            st.error(f"Error listing projects: {str(e)}")
            return []
        finally:
            conn.close()

# Global database manager instance
db_manager = BIPVDatabaseManager()