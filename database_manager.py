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
                # Check if project exists - prioritize project_id if available, then fall back to project_name
                existing = None
                project_id_to_update = None
                
                if 'project_id' in project_data and project_data['project_id']:
                    # If we have a project_id, check by ID first (for updates/renames)
                    cursor.execute(
                        "SELECT id FROM projects WHERE id = %s",
                        (project_data['project_id'],)
                    )
                    existing = cursor.fetchone()
                    if existing:
                        project_id_to_update = existing[0]
                else:
                    # For new projects without ID, check by name to avoid duplicates
                    cursor.execute(
                        "SELECT id FROM projects WHERE project_name = %s",
                        (project_data.get('project_name'),)
                    )
                    existing = cursor.fetchone()
                    if existing:
                        project_id_to_update = existing[0]
                
                if existing:
                    # Update existing project
                    # Prepare electricity rates JSON
                    import json
                    electricity_rates_json = None
                    if 'electricity_rates' in project_data:
                        electricity_rates_json = json.dumps(project_data['electricity_rates'])
                    
                    # Extract weather station data
                    weather_station = project_data.get('selected_weather_station', {})
                    
                    cursor.execute("""
                        UPDATE projects SET 
                            project_name = %s, location = %s, latitude = %s, longitude = %s, 
                            timezone = %s, currency = %s, weather_api_choice = %s, 
                            location_method = %s, search_radius = %s, electricity_rates = %s,
                            weather_station_name = %s, weather_station_id = %s, weather_station_distance = %s,
                            weather_station_latitude = %s, weather_station_longitude = %s, weather_station_elevation = %s,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = %s
                        RETURNING id
                    """, (
                        project_data.get('project_name'),
                        project_data.get('location'),
                        project_data.get('coordinates', {}).get('lat'),
                        project_data.get('coordinates', {}).get('lon'),
                        project_data.get('timezone'),
                        project_data.get('currency', 'EUR'),
                        project_data.get('weather_api_choice', 'auto'),
                        project_data.get('location_method', 'map'),
                        project_data.get('search_radius', 500),
                        electricity_rates_json,
                        weather_station.get('name'),
                        weather_station.get('wmo_id'),
                        weather_station.get('distance_km'),
                        weather_station.get('latitude'),
                        weather_station.get('longitude'),
                        weather_station.get('height'),
                        project_id_to_update
                    ))
                else:
                    # Insert new project
                    # Prepare electricity rates JSON
                    import json
                    electricity_rates_json = None
                    if 'electricity_rates' in project_data:
                        electricity_rates_json = json.dumps(project_data['electricity_rates'])
                    
                    # Extract weather station data
                    weather_station = project_data.get('selected_weather_station', {})
                    
                    cursor.execute("""
                        INSERT INTO projects (project_name, location, latitude, longitude, timezone, currency, weather_api_choice, location_method, search_radius, electricity_rates,
                                            weather_station_name, weather_station_id, weather_station_distance, weather_station_latitude, weather_station_longitude, weather_station_elevation)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """, (
                        project_data.get('project_name'),
                        project_data.get('location'),
                        project_data.get('coordinates', {}).get('lat'),
                        project_data.get('coordinates', {}).get('lon'),
                        project_data.get('timezone'),
                        project_data.get('currency', 'EUR'),
                        project_data.get('weather_api_choice', 'auto'),
                        project_data.get('location_method', 'map'),
                        project_data.get('search_radius', 500),
                        electricity_rates_json,
                        weather_station.get('name'),
                        weather_station.get('wmo_id'),
                        weather_station.get('distance_km'),
                        weather_station.get('latitude'),
                        weather_station.get('longitude'),
                        weather_station.get('height')
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
    
    def get_project_by_id(self, project_id):
        """Get project data by ID"""
        conn = self.get_connection()
        if not conn:
            return None
        
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    "SELECT * FROM projects WHERE id = %s",
                    (project_id,)
                )
                result = cursor.fetchone()
                if result:
                    project_data = dict(result)
                    # Deserialize JSON fields
                    if 'electricity_rates' in project_data and project_data['electricity_rates']:
                        try:
                            import json
                            project_data['electricity_rates'] = json.loads(project_data['electricity_rates'])
                        except (json.JSONDecodeError, TypeError):
                            project_data['electricity_rates'] = {'import_rate': 0.25, 'source': 'fallback'}
                    return project_data
                return None
                
        except Exception as e:
            st.error(f"Error getting project: {str(e)}")
            return None
        finally:
            conn.close()
    
    def get_project_info(self, project_id):
        """Get project information including weather station data for Step 3"""
        return self.get_project_by_id(project_id)
    
    def get_project_data(self, project_identifier):
        """Get project data by ID or name - compatible method for AI consultation"""
        # If it's a string, treat as project name and get ID first
        if isinstance(project_identifier, str):
            conn = self.get_connection()
            if not conn:
                return None
            
            try:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT id FROM projects WHERE project_name = %s", (project_identifier,))
                    result = cursor.fetchone()
                    if result:
                        project_id = result[0]
                        conn.close()
                        return self.get_project_by_id(project_id)
                    return None
            except Exception as e:
                st.error(f"Error getting project by name: {str(e)}")
                return None
            finally:
                conn.close()
        else:
            # Treat as project ID
            return self.get_project_by_id(project_identifier)
    
    def save_weather_data(self, project_identifier, weather_data):
        """Save weather and TMY data"""
        conn = self.get_connection()
        if not conn:
            return False
        
        try:
            with conn.cursor() as cursor:
                # Get project_id if identifier is a string (project name)
                if isinstance(project_identifier, str):
                    cursor.execute("SELECT id FROM projects WHERE project_name = %s", (project_identifier,))
                    result = cursor.fetchone()
                    if not result:
                        st.error(f"Project '{project_identifier}' not found in database")
                        return False
                    project_id = result[0]
                else:
                    project_id = int(project_identifier)
                
                # Delete existing weather data for this project
                cursor.execute("DELETE FROM weather_data WHERE project_id = %s", (project_id,))
                
                # Prepare data with proper type conversion
                temperature = weather_data.get('temperature')
                humidity = weather_data.get('humidity') 
                description = weather_data.get('description', '')
                annual_ghi = weather_data.get('annual_ghi', 0)
                annual_dni = weather_data.get('annual_dni', 0)
                annual_dhi = weather_data.get('annual_dhi', 0)
                
                # Convert to proper types
                temperature = float(temperature) if temperature is not None else None
                humidity = float(humidity) if humidity is not None else None
                annual_ghi = float(annual_ghi) if annual_ghi is not None else 0.0
                annual_dni = float(annual_dni) if annual_dni is not None else 0.0
                annual_dhi = float(annual_dhi) if annual_dhi is not None else 0.0
                
                # Insert new weather data
                cursor.execute("""
                    INSERT INTO weather_data 
                    (project_id, temperature, humidity, description, annual_ghi, annual_dni, annual_dhi)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    project_id,
                    float(temperature) if temperature is not None else 15.0,
                    float(humidity) if humidity is not None else 65.0,
                    description,
                    float(annual_ghi) if annual_ghi is not None else 0.0,
                    float(annual_dni) if annual_dni is not None else 0.0,
                    float(annual_dhi) if annual_dhi is not None else 0.0
                ))
                
                conn.commit()
                return True
                
        except Exception as e:
            conn.rollback()
            st.error(f"Error saving weather data: {str(e)}")
            return False
        finally:
            conn.close()
    
    def save_historical_data(self, project_id, historical_data):
        """Save historical energy consumption and AI model data"""
        conn = self.get_connection()
        if not conn:
            return False
        
        try:
            with conn.cursor() as cursor:
                # Store historical data analysis results in energy_analysis table
                cursor.execute("DELETE FROM energy_analysis WHERE project_id = %s", (project_id,))
                
                annual_consumption = historical_data.get('annual_consumption', 0)
                model_accuracy = historical_data.get('model_accuracy', 0)
                
                cursor.execute("""
                    INSERT INTO energy_analysis 
                    (project_id, annual_demand, self_consumption_rate, energy_yield_per_m2)
                    VALUES (%s, %s, %s, %s)
                """, (
                    project_id,
                    annual_consumption,
                    model_accuracy,
                    0  # energy_yield_per_m2 will be calculated later
                ))
                
                conn.commit()
                return True
                
        except Exception as e:
            conn.rollback()
            st.error(f"Error saving historical data: {str(e)}")
            return False
        finally:
            conn.close()
    
    def get_historical_data_basic(self, project_id):
        """Get basic historical data analysis results from energy_analysis table"""
        conn = self.get_connection()
        if not conn:
            return None
        
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT annual_demand, self_consumption_rate 
                    FROM energy_analysis 
                    WHERE project_id = %s
                """, (project_id,))
                
                result = cursor.fetchone()
                if result:
                    annual_demand, model_accuracy = result
                    return {
                        'annual_consumption': float(annual_demand) if annual_demand is not None else 0.0,
                        'model_accuracy': float(model_accuracy) if model_accuracy is not None else 0.0,
                        'data_analysis_complete': True
                    }
                return None
                
        except Exception as e:
            st.error(f"Error retrieving historical data: {str(e)}")
            return None
        finally:
            conn.close()
    
    def save_yield_demand_data(self, project_id, yield_demand_data):
        """Save yield vs demand analysis results"""
        conn = self.get_connection()
        if not conn:
            return False
        
        try:
            with conn.cursor() as cursor:
                # Extract actual field names from Step 7 data structure
                total_annual_yield = yield_demand_data.get('total_annual_yield', 0)
                annual_demand = yield_demand_data.get('annual_demand', 0)
                net_energy_balance = total_annual_yield - annual_demand
                
                # Calculate self-consumption rate
                self_consumption_rate = 0
                if annual_demand > 0:
                    consumed_energy = min(total_annual_yield, annual_demand)
                    self_consumption_rate = (consumed_energy / annual_demand) * 100
                
                # Calculate energy yield per m2 if building area available
                energy_yield_per_m2 = 0
                if 'analysis_config' in yield_demand_data:
                    building_area = yield_demand_data['analysis_config'].get('building_area', 0)
                    if building_area > 0:
                        energy_yield_per_m2 = total_annual_yield / building_area
                
                # Check if record exists for this project
                cursor.execute("SELECT id FROM energy_analysis WHERE project_id = %s", (project_id,))
                existing = cursor.fetchone()
                
                if existing:
                    # Update existing record
                    cursor.execute("""
                        UPDATE energy_analysis SET 
                            annual_generation = %s,
                            annual_demand = %s,
                            net_energy_balance = %s,
                            self_consumption_rate = %s,
                            energy_yield_per_m2 = %s,
                            created_at = CURRENT_TIMESTAMP
                        WHERE project_id = %s
                    """, (
                        total_annual_yield,
                        annual_demand,
                        net_energy_balance,
                        self_consumption_rate,
                        energy_yield_per_m2,
                        project_id
                    ))
                else:
                    # Insert new record
                    cursor.execute("""
                        INSERT INTO energy_analysis (
                            project_id, annual_generation, annual_demand, 
                            net_energy_balance, self_consumption_rate, energy_yield_per_m2
                        ) VALUES (%s, %s, %s, %s, %s, %s)
                    """, (
                        project_id,
                        total_annual_yield,
                        annual_demand,
                        net_energy_balance,
                        self_consumption_rate,
                        energy_yield_per_m2
                    ))
                
                conn.commit()
                return True
                
        except Exception as e:
            conn.rollback()
            st.error(f"Error saving yield demand data: {str(e)}")
            return False
        finally:
            conn.close()
    
    def save_optimization_results(self, project_id, optimization_data):
        """Save optimization results"""
        import json
        conn = self.get_connection()
        if not conn:
            return False
        
        try:
            with conn.cursor() as cursor:
                # Delete existing optimization results
                cursor.execute("DELETE FROM optimization_results WHERE project_id = %s", (project_id,))
                
                # Save optimization solutions with proper field mapping
                solutions = optimization_data.get('solutions', [])
                for i, solution in enumerate(solutions):
                    # Map field names correctly from analyze_optimization_results output
                    capacity = solution.get('total_power_kw', solution.get('capacity', 0))  # Map total_power_kw to capacity
                    net_import = solution.get('net_import_kwh', solution.get('net_import', 0))  # Map net_import_kwh to net_import
                    total_cost = solution.get('total_investment', solution.get('total_cost', 0))  # Map total_investment to total_cost
                    
                    # Include annual energy in optimization results
                    annual_energy = solution.get('annual_energy_kwh', solution.get('annual_energy', capacity * 1200 if capacity else 0))
                    
                    # Prepare selection details JSON
                    selection_details = {
                        'selection_mask': solution.get('selection_mask', []),
                        'selected_element_ids': solution.get('selected_elements', []),
                        'optimization_parameters': solution.get('optimization_params', {})
                    }
                    
                    cursor.execute("""
                        INSERT INTO optimization_results 
                        (project_id, solution_id, capacity, roi, net_import, total_cost, annual_energy_kwh, rank_position, pareto_optimal, selection_details)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        project_id,
                        solution.get('solution_id', f'solution_{i}'),
                        float(capacity) if capacity is not None else 0,  # Ensure float conversion
                        float(solution.get('roi', 0)) if solution.get('roi') is not None else 0,
                        float(net_import) if net_import is not None else 0,
                        float(total_cost) if total_cost is not None else 0,
                        float(annual_energy) if annual_energy is not None else 0,
                        i + 1,
                        solution.get('pareto_optimal', False),
                        json.dumps(selection_details)
                    ))
                
                conn.commit()
                return True
                
        except Exception as e:
            conn.rollback()
            st.error(f"Error saving optimization results: {str(e)}")
            return False
        finally:
            conn.close()
    
    def get_optimization_results(self, project_id):
        """Get optimization results for a project"""
        conn = self.get_connection()
        if not conn:
            return None
        
        try:
            import pandas as pd
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT solution_id, capacity, roi, net_import, total_cost, rank_position, pareto_optimal
                    FROM optimization_results 
                    WHERE project_id = %s 
                    ORDER BY rank_position
                """, (project_id,))
                
                results = cursor.fetchall()
                if results:
                    # Convert to DataFrame and ensure float conversion for decimal.Decimal values
                    solutions_data = []
                    for row in results:
                        solution = dict(row)
                        # Convert decimal.Decimal to float to prevent arithmetic errors
                        for key in ['capacity', 'roi', 'net_import', 'total_cost']:
                            if solution[key] is not None:
                                solution[key] = float(solution[key])
                        solutions_data.append(solution)
                    
                    solutions_df = pd.DataFrame(solutions_data)
                    return {'solutions': solutions_df}
                
                return None
                
        except Exception as e:
            st.error(f"Error getting optimization results: {str(e)}")
            return None
        finally:
            conn.close()
    
    def save_building_elements(self, project_id, building_elements):
        """Save BIM building elements data with enhanced field name handling"""
        conn = self.get_connection()
        if not conn:
            return False
        
        try:
            with conn.cursor() as cursor:
                # Delete existing building elements for this project
                cursor.execute("DELETE FROM building_elements WHERE project_id = %s", (project_id,))
                
                # Handle multiple data formats - DataFrame, list, dict
                if hasattr(building_elements, 'iterrows'):
                    # DataFrame format
                    for _, element in building_elements.iterrows():
                        # Enhanced glass area extraction with debug logging
                        glass_area_value = None
                        for glass_col in ['Glass Area (m²)', 'glass_area', 'Glass_Area', 'window_area', 'Glass Area', 'area']:
                            if glass_col in element and element[glass_col] not in [None, '', 0, '0']:
                                try:
                                    glass_area_value = float(element[glass_col])
                                    if glass_area_value > 0:
                                        break
                                except (ValueError, TypeError):
                                    continue
                        
                        # Fallback to 0 if no valid glass area found (will be calculated later)
                        if glass_area_value is None:
                            glass_area_value = 0
                        
                        # Extract azimuth with proper handling
                        azimuth_value = 0
                        for azimuth_col in ['Azimuth (°)', 'azimuth', 'Azimuth']:
                            if azimuth_col in element and element[azimuth_col] not in [None, '']:
                                try:
                                    azimuth_value = float(element[azimuth_col])
                                    break
                                except (ValueError, TypeError):
                                    continue
                        
                        cursor.execute("""
                            INSERT INTO building_elements 
                            (project_id, element_id, wall_element_id, element_type, orientation, 
                             azimuth, glass_area, window_width, window_height, building_level, 
                             family, pv_suitable)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """, (
                            project_id,
                            element.get('ElementId', element.get('Element_ID', element.get('element_id', ''))),
                            element.get('HostWallId', element.get('Wall_Element_ID', element.get('wall_element_id', ''))),
                            element.get('element_type', 'Window'),
                            element.get('orientation', ''),
                            azimuth_value,
                            glass_area_value,
                            element.get('window_width', 0),
                            element.get('window_height', 0),
                            element.get('Level', element.get('level', '')),
                            element.get('Family', element.get('family', '')),
                            element.get('pv_suitable', element.get('PV_Suitable', element.get('suitable', False)))
                        ))
                else:
                    # List or dict format
                    for element in building_elements:
                        # Enhanced glass area extraction with debug logging
                        glass_area_value = None
                        for glass_col in ['Glass Area (m²)', 'glass_area', 'Glass_Area', 'window_area', 'Glass Area', 'area']:
                            if glass_col in element and element[glass_col] not in [None, '', 0, '0']:
                                try:
                                    glass_area_value = float(element[glass_col])
                                    if glass_area_value > 0:
                                        break
                                except (ValueError, TypeError):
                                    continue
                        
                        # Fallback to 0 if no valid glass area found (will be calculated later)
                        if glass_area_value is None:
                            glass_area_value = 0
                        
                        # Extract azimuth with proper handling
                        azimuth_value = 0
                        for azimuth_col in ['Azimuth (°)', 'azimuth', 'Azimuth']:
                            if azimuth_col in element and element[azimuth_col] not in [None, '']:
                                try:
                                    azimuth_value = float(element[azimuth_col])
                                    break
                                except (ValueError, TypeError):
                                    continue
                        
                        cursor.execute("""
                            INSERT INTO building_elements 
                            (project_id, element_id, wall_element_id, element_type, orientation, 
                             azimuth, glass_area, window_width, window_height, building_level, 
                             family, pv_suitable)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """, (
                            project_id,
                            element.get('ElementId', element.get('Element_ID', element.get('element_id', ''))),
                            element.get('HostWallId', element.get('Wall_Element_ID', element.get('wall_element_id', ''))),
                            element.get('element_type', 'Window'),
                            element.get('orientation', ''),
                            azimuth_value,
                            glass_area_value,
                            element.get('window_width', 0),
                            element.get('window_height', 0),
                            element.get('Level', element.get('level', '')),
                            element.get('Family', element.get('family', '')),
                            element.get('pv_suitable', element.get('PV_Suitable', element.get('suitable', False)))
                        ))
                
                conn.commit()
                return True
                
        except Exception as e:
            conn.rollback()
            st.error(f"Error saving building elements: {str(e)}")
            return False
        finally:
            conn.close()
    
    def save_building_elements_with_progress(self, project_id, building_elements, progress_callback=None):
        """Save BIM building elements data with enhanced field name handling and progress tracking"""
        conn = self.get_connection()
        if not conn:
            return False
        
        try:
            with conn.cursor() as cursor:
                # Delete existing building elements for this project
                cursor.execute("DELETE FROM building_elements WHERE project_id = %s", (project_id,))
                
                total_elements = len(building_elements)
                
                # Handle multiple data formats - DataFrame, list, dict
                if hasattr(building_elements, 'iterrows'):
                    # DataFrame format with progress tracking
                    for idx, (_, element) in enumerate(building_elements.iterrows()):
                        # Enhanced glass area extraction with debug logging
                        glass_area_value = None
                        for glass_col in ['Glass Area (m²)', 'glass_area', 'Glass_Area', 'window_area', 'Glass Area', 'area']:
                            if glass_col in element and element[glass_col] not in [None, '', 0, '0']:
                                try:
                                    glass_area_value = float(element[glass_col])
                                    if glass_area_value > 0:
                                        break
                                except (ValueError, TypeError):
                                    continue
                        
                        # Fallback to 0 if no valid glass area found (will be calculated later)
                        if glass_area_value is None:
                            glass_area_value = 0
                        
                        # Extract azimuth with proper handling
                        azimuth_value = 0
                        for azimuth_col in ['Azimuth (°)', 'azimuth', 'Azimuth']:
                            if azimuth_col in element and element[azimuth_col] not in [None, '']:
                                try:
                                    azimuth_value = float(element[azimuth_col])
                                    break
                                except (ValueError, TypeError):
                                    continue
                        
                        cursor.execute("""
                            INSERT INTO building_elements 
                            (project_id, element_id, wall_element_id, element_type, orientation, 
                             azimuth, glass_area, window_width, window_height, building_level, 
                             family, pv_suitable)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """, (
                            project_id,
                            element.get('ElementId', element.get('Element_ID', element.get('element_id', ''))),
                            element.get('HostWallId', element.get('Wall_Element_ID', element.get('wall_element_id', ''))),
                            element.get('element_type', 'Window'),
                            element.get('orientation', ''),
                            azimuth_value,
                            glass_area_value,
                            element.get('window_width', 0),
                            element.get('window_height', 0),
                            element.get('Level', element.get('level', '')),
                            element.get('Family', element.get('family', '')),
                            element.get('pv_suitable', element.get('PV_Suitable', element.get('suitable', False)))
                        ))
                        
                        # Update progress every 10 elements or at the end
                        if progress_callback and (idx % 10 == 0 or idx == total_elements - 1):
                            progress = 20 + int((idx + 1) / total_elements * 40)  # 20-60% range
                            progress_callback(progress, "Saving window elements to database...")
                
                conn.commit()
                return True
                
        except Exception as e:
            conn.rollback()
            st.error(f"Error saving building elements: {str(e)}")
            return False
        finally:
            conn.close()
    
    def save_radiation_analysis(self, project_id, radiation_data):
        """Save radiation analysis results - fully database-driven"""
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
                        # Simple INSERT since we already deleted existing records
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
    
    def get_radiation_analysis_data(self, project_id):
        """Get radiation analysis data from database - fully database-driven"""
        conn = self.get_connection()
        if not conn:
            return None
        
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Get radiation analysis summary
                cursor.execute("""
                    SELECT * FROM radiation_analysis 
                    WHERE project_id = %s AND analysis_complete = TRUE
                    ORDER BY created_at DESC LIMIT 1
                """, (project_id,))
                
                radiation_summary = cursor.fetchone()
                
                # Get detailed element radiation data - avoid JOIN duplication by using subquery
                cursor.execute("""
                    SELECT er.id, er.project_id, er.element_id, er.annual_radiation, 
                           er.irradiance, er.orientation_multiplier, er.created_at, 
                           er.calculation_method, er.calculated_at,
                           be.element_type, be.orientation, be.azimuth, 
                           be.glass_area, be.building_level, be.family
                    FROM element_radiation er
                    JOIN (
                        SELECT DISTINCT element_id, element_type, orientation, azimuth, 
                               glass_area, building_level, family
                        FROM building_elements 
                        WHERE project_id = %s
                    ) be ON er.element_id = be.element_id 
                    WHERE er.project_id = %s
                    ORDER BY er.annual_radiation DESC
                """, (project_id, project_id))
                
                element_radiation = cursor.fetchall()
                
                return {
                    'radiation_summary': dict(radiation_summary) if radiation_summary else None,
                    'element_radiation': [dict(row) for row in element_radiation],
                    'total_elements': len(element_radiation)
                }
                
        except Exception as e:
            st.error(f"Error retrieving radiation analysis: {str(e)}")
            return None
        finally:
            conn.close()
    
    def save_element_radiation_batch(self, project_id, element_radiation_list):
        """Save radiation data for multiple elements - optimized for large datasets"""
        conn = self.get_connection()
        if not conn:
            return False
        
        try:
            with conn.cursor() as cursor:
                # Prepare batch insert
                insert_data = []
                for element in element_radiation_list:
                    insert_data.append((
                        project_id,
                        element.get('element_id'),
                        element.get('annual_radiation'),
                        element.get('irradiance'),
                        element.get('orientation_multiplier', 1.0)
                    ))
                
                # Clear existing records first
                cursor.execute("DELETE FROM element_radiation WHERE project_id = %s", (project_id,))
                
                # Use execute_batch for efficient bulk insert
                from psycopg2.extras import execute_batch
                execute_batch(cursor, """
                    INSERT INTO element_radiation 
                    (project_id, element_id, annual_radiation, irradiance, orientation_multiplier)
                    VALUES (%s, %s, %s, %s, %s)
                """, insert_data)
                
                conn.commit()
                return True
                
        except Exception as e:
            conn.rollback()
            st.error(f"Error saving element radiation batch: {str(e)}")
            return False
        finally:
            conn.close()
    
    def save_pv_specifications(self, project_id, pv_specs):
        """Save PV specifications"""
        conn = self.get_connection()
        if not conn:
            return False
        
        try:
            import json
            with conn.cursor() as cursor:
                # Delete existing PV specs for this project
                cursor.execute("DELETE FROM pv_specifications WHERE project_id = %s", (project_id,))
                
                # Extract panel specs if nested
                panel_specs = pv_specs.get('panel_specs', pv_specs)
                
                # Validate required fields to prevent NULL constraint errors
                required_fields = ['efficiency', 'transparency', 'cost_per_m2', 'power_density']
                for field in required_fields:
                    if panel_specs.get(field) is None:
                        raise ValueError(f"Required field '{field}' is missing from PV specifications")
                
                panel_type = panel_specs.get('panel_type') or panel_specs.get('name')
                if not panel_type:
                    raise ValueError("Panel type or name is required for PV specifications")
                
                installation_factor = panel_specs.get('installation_factor')
                if installation_factor is None:
                    # Provide default installation factor if missing (1.2 = 20% markup)
                    installation_factor = 1.2
                    st.warning("⚠️ Installation factor not provided, using default value of 1.2 (20% markup)")
                
                # Insert PV specifications - only authentic data, validated
                cursor.execute("""
                    INSERT INTO pv_specifications 
                    (project_id, panel_type, efficiency, transparency, cost_per_m2, power_density, installation_factor, specification_data)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    project_id,
                    panel_type,
                    panel_specs.get('efficiency'),
                    panel_specs.get('transparency'),
                    panel_specs.get('cost_per_m2'),
                    panel_specs.get('power_density'),
                    installation_factor,
                    json.dumps(pv_specs)  # Store complete specifications as JSON
                ))
                
                conn.commit()
                return True
                
        except Exception as e:
            conn.rollback()
            st.error(f"Error saving PV specifications: {str(e)}")
            return False
        finally:
            conn.close()
    
    def get_building_elements(self, project_id):
        """Get building elements for a project"""
        conn = self.get_connection()
        if not conn:
            return []
        
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT DISTINCT element_id, element_type, orientation, azimuth, 
                           glass_area, building_level, family, pv_suitable,
                           wall_element_id
                    FROM building_elements 
                    WHERE project_id = %s AND element_type IN ('Window', 'Windows')
                    ORDER BY element_id
                """, (project_id,))
                
                results = cursor.fetchall()
                return [dict(row) for row in results]
                
        except Exception as e:
            st.error(f"Error getting building elements: {str(e)}")
            return []
        finally:
            conn.close()

    def get_project_name_by_id(self, project_id):
        """Get project name by project ID"""
        conn = self.get_connection()
        if not conn:
            return None
        
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT project_name FROM projects WHERE id = %s", (project_id,))
                result = cursor.fetchone()
                return result[0] if result else None
        except Exception as e:
            st.error(f"Error getting project name: {str(e)}")
            return None
        finally:
            conn.close()

    def save_ai_model_data(self, project_id, model_data):
        """Save AI model data including forecast predictions for Step 7"""
        conn = self.get_connection()
        if not conn:
            return False
        
        try:
            import json
            with conn.cursor() as cursor:
                # Delete existing AI model data for this project
                cursor.execute("DELETE FROM ai_models WHERE project_id = %s", (project_id,))
                
                # Prepare forecast data and demand predictions as JSON
                forecast_data = json.dumps(model_data.get('forecast_data', {}))
                demand_predictions = json.dumps(model_data.get('demand_predictions', []))
                
                cursor.execute("""
                    INSERT INTO ai_models 
                    (project_id, model_type, r_squared_score, training_data_size, forecast_years,
                     forecast_data, demand_predictions, growth_rate, base_consumption, 
                     peak_demand, building_area, occupancy_pattern, building_type)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    project_id,
                    model_data.get('model_type', 'RandomForestRegressor'),
                    model_data.get('r_squared_score', 0.92),
                    model_data.get('training_data_size', 12),
                    model_data.get('forecast_years', 25),
                    forecast_data,
                    demand_predictions,
                    model_data.get('growth_rate', 0.01),
                    model_data.get('base_consumption', 0),
                    model_data.get('peak_demand', 0),
                    model_data.get('building_area', 5000),
                    model_data.get('occupancy_pattern', 'academic_year'),
                    model_data.get('building_type', 'university')
                ))
                
                conn.commit()
                return True
                
        except Exception as e:
            conn.rollback()
            st.error(f"Error saving AI model data: {str(e)}")
            return False
        finally:
            conn.close()

    def get_historical_data(self, project_id):
        """Get historical data for a project including AI model predictions"""
        conn = self.get_connection()
        if not conn:
            return None
        
        try:
            import json
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Get historical data from both tables
                cursor.execute("""
                    SELECT hd.*, am.forecast_data, am.demand_predictions, am.growth_rate,
                           am.base_consumption, am.peak_demand, am.building_area,
                           am.occupancy_pattern, am.building_type, am.r_squared_score
                    FROM historical_data hd
                    LEFT JOIN ai_models am ON hd.project_id = am.project_id
                    WHERE hd.project_id = %s
                    ORDER BY hd.created_at DESC
                    LIMIT 1
                """, (project_id,))
                
                result = cursor.fetchone()
                
                if result:
                    historical_data = dict(result)
                    
                    # Parse JSON fields
                    try:
                        if historical_data.get('consumption_data'):
                            historical_data['consumption_data'] = json.loads(historical_data['consumption_data'])
                        if historical_data.get('temperature_data'):
                            historical_data['temperature_data'] = json.loads(historical_data['temperature_data'])
                        if historical_data.get('occupancy_data'):
                            historical_data['occupancy_data'] = json.loads(historical_data['occupancy_data'])
                        if historical_data.get('date_data'):
                            historical_data['date_data'] = json.loads(historical_data['date_data'])
                        if historical_data.get('forecast_data'):
                            historical_data['forecast_data'] = json.loads(historical_data['forecast_data'])
                        if historical_data.get('demand_predictions'):
                            historical_data['demand_predictions'] = json.loads(historical_data['demand_predictions'])
                    except json.JSONDecodeError as e:
                        st.warning(f"Error parsing JSON data: {str(e)}")
                    
                    return historical_data
                
                return None
                
        except Exception as e:
            st.error(f"Error getting historical data: {str(e)}")
            return None
        finally:
            conn.close()

    def save_historical_data(self, project_id, historical_data):
        """Save historical data including consumption patterns for Step 7"""
        conn = self.get_connection()
        if not conn:
            return False
        
        try:
            import json
            with conn.cursor() as cursor:
                # Delete existing historical data for this project
                cursor.execute("DELETE FROM historical_data WHERE project_id = %s", (project_id,))
                
                # Convert arrays to JSON strings
                consumption_data = json.dumps(historical_data.get('consumption_data', []))
                temperature_data = json.dumps(historical_data.get('temperature_data', []))
                occupancy_data = json.dumps(historical_data.get('occupancy_data', []))
                date_data = json.dumps(historical_data.get('date_data', []))
                
                cursor.execute("""
                    INSERT INTO historical_data 
                    (project_id, annual_consumption, consumption_data, temperature_data,
                     occupancy_data, date_data, model_accuracy, energy_intensity,
                     peak_load_factor, seasonal_variation)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    project_id,
                    historical_data.get('annual_consumption', 0),
                    consumption_data,
                    temperature_data,
                    occupancy_data,
                    date_data,
                    historical_data.get('model_accuracy', 0.92),
                    historical_data.get('energy_intensity', 0),
                    historical_data.get('peak_load_factor', 0),
                    historical_data.get('seasonal_variation', 0)
                ))
                
                conn.commit()
                return True
                
        except Exception as e:
            conn.rollback()
            st.error(f"Error saving historical data: {str(e)}")
            return False
        finally:
            conn.close()

    def save_weather_data(self, project_id, weather_analysis):
        """Save comprehensive weather data including TMY for Steps 5-7"""
        conn = self.get_connection()
        if not conn:
            return False
        
        try:
            import json
            with conn.cursor() as cursor:
                # Delete existing weather data for this project
                cursor.execute("DELETE FROM weather_data WHERE project_id = %s", (project_id,))
                
                # Convert complex data structures to JSON
                tmy_data = json.dumps(weather_analysis.get('tmy_data', []))
                monthly_profiles = json.dumps(weather_analysis.get('monthly_profiles', {}))
                solar_position_data = json.dumps(weather_analysis.get('solar_position_data', {}))
                environmental_factors = json.dumps(weather_analysis.get('environmental_factors', {}))
                station_metadata = json.dumps(weather_analysis.get('station_metadata', {}))
                
                cursor.execute("""
                    INSERT INTO weather_data 
                    (project_id, temperature, humidity, description, annual_ghi, annual_dni, annual_dhi,
                     tmy_data, monthly_profiles, solar_position_data, environmental_factors,
                     clearness_index, station_metadata, generation_method)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    project_id,
                    float(weather_analysis.get('temperature', 15.0) or 15.0),
                    float(weather_analysis.get('humidity', 65.0) or 65.0),
                    weather_analysis.get('description', 'TMY Generated'),
                    float(weather_analysis.get('annual_ghi', 0) or 0),
                    float(weather_analysis.get('annual_dni', 0) or 0),
                    float(weather_analysis.get('annual_dhi', 0) or 0),
                    tmy_data,
                    monthly_profiles,
                    solar_position_data,
                    environmental_factors,
                    float(weather_analysis.get('clearness_index', 0.5) or 0.5),
                    station_metadata,
                    weather_analysis.get('generation_method', 'ISO_15927-4')
                ))
                
                conn.commit()
                return True
                
        except Exception as e:
            conn.rollback()
            st.error(f"Error saving weather data: {str(e)}")
            return False
        finally:
            conn.close()

    def get_weather_data(self, project_id):
        """Get complete weather data including TMY for radiation analysis"""
        conn = self.get_connection()
        if not conn:
            return None
        
        try:
            import json
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT * FROM weather_data 
                    WHERE project_id = %s
                    ORDER BY created_at DESC
                    LIMIT 1
                """, (project_id,))
                
                result = cursor.fetchone()
                
                if result:
                    weather_data = dict(result)
                    
                    # Convert decimal.Decimal values to float immediately to prevent arithmetic errors
                    numeric_fields = ['annual_ghi', 'annual_dni', 'annual_dhi', 'temperature', 'humidity', 'clearness_index']
                    for field in numeric_fields:
                        if field in weather_data and weather_data[field] is not None:
                            weather_data[field] = float(weather_data[field])
                    
                    # Parse JSON fields safely
                    try:
                        if weather_data.get('tmy_data'):
                            weather_data['tmy_data'] = json.loads(weather_data['tmy_data'])
                        if weather_data.get('monthly_profiles'):
                            weather_data['monthly_profiles'] = json.loads(weather_data['monthly_profiles'])
                        if weather_data.get('solar_position_data'):
                            weather_data['solar_position_data'] = json.loads(weather_data['solar_position_data'])
                        if weather_data.get('environmental_factors'):
                            weather_data['environmental_factors'] = json.loads(weather_data['environmental_factors'])
                        if weather_data.get('station_metadata'):
                            weather_data['station_metadata'] = json.loads(weather_data['station_metadata'])
                    except json.JSONDecodeError as e:
                        st.warning(f"Error parsing weather JSON data: {str(e)}")
                    
                    return weather_data
                
                return None
                
        except Exception as e:
            st.error(f"Error getting weather data: {str(e)}")
            return None
        finally:
            conn.close()

    def save_environmental_factors(self, project_id, environmental_factors):
        """Save environmental factors (trees, buildings) affecting TMY data"""
        conn = self.get_connection()
        if not conn:
            return False
        
        try:
            import json
            with conn.cursor() as cursor:
                # Update weather_data with environmental factors
                environmental_json = json.dumps(environmental_factors)
                
                cursor.execute("""
                    UPDATE weather_data 
                    SET environmental_factors = %s
                    WHERE project_id = %s
                """, (environmental_json, project_id))
                
                conn.commit()
                return True
                
        except Exception as e:
            conn.rollback()
            st.error(f"Error saving environmental factors: {str(e)}")
            return False
        finally:
            conn.close()

    def get_pv_specifications(self, project_id):
        """Get PV specifications for a project"""
        conn = self.get_connection()
        if not conn:
            return None
        
        try:
            import json
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT * FROM pv_specifications 
                    WHERE project_id = %s
                    ORDER BY created_at DESC
                    LIMIT 1
                """, (project_id,))
                
                result = cursor.fetchone()
                
                if result and result['specification_data']:
                    # Parse the JSON specification data
                    pv_data = json.loads(result['specification_data'])
                    return pv_data
                
                return None
                
        except Exception as e:
            st.error(f"Error getting PV specifications: {str(e)}")
            return None
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
                
                # Store detailed analysis data as JSON
                import json
                cash_flow_json = json.dumps(financial_data.get('cash_flow_analysis', []))
                sensitivity_json = json.dumps(financial_data.get('sensitivity_analysis', {}))
                
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
                
                # Save detailed analysis data in a separate table or update existing if supported
                cursor.execute("DELETE FROM detailed_financial_analysis WHERE project_id = %s", (project_id,))
                cursor.execute("""
                    INSERT INTO detailed_financial_analysis 
                    (project_id, cash_flow_data, sensitivity_data, created_at)
                    VALUES (%s, %s, %s, NOW())
                """, (project_id, cash_flow_json, sensitivity_json))
                
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
    
    def get_financial_analysis(self, project_id):
        """Get financial analysis results from database"""
        conn = self.get_connection()
        if not conn:
            return None
        
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Get financial analysis data
                cursor.execute("""
                    SELECT * FROM financial_analysis 
                    WHERE project_id = %s AND analysis_complete = TRUE
                    ORDER BY created_at DESC LIMIT 1
                """, (project_id,))
                
                financial_result = cursor.fetchone()
                
                if not financial_result:
                    return None
                
                # Get environmental impact data
                cursor.execute("""
                    SELECT * FROM environmental_impact 
                    WHERE project_id = %s
                    ORDER BY created_at DESC LIMIT 1
                """, (project_id,))
                
                environmental_result = cursor.fetchone()
                
                # Get detailed analysis data (cash flow, sensitivity)
                cursor.execute("""
                    SELECT cash_flow_data, sensitivity_data FROM detailed_financial_analysis 
                    WHERE project_id = %s
                    ORDER BY created_at DESC LIMIT 1
                """, (project_id,))
                
                detailed_result = cursor.fetchone()
                
                # Parse detailed analysis JSON data
                cash_flow_analysis = []
                sensitivity_analysis = {}
                
                if detailed_result:
                    try:
                        import json
                        if detailed_result['cash_flow_data']:
                            cash_flow_analysis = json.loads(detailed_result['cash_flow_data'])
                        if detailed_result['sensitivity_data']:
                            sensitivity_analysis = json.loads(detailed_result['sensitivity_data'])
                    except json.JSONDecodeError:
                        pass  # Use empty defaults
                
                # Format data structure similar to what the UI expects
                financial_data = {
                    'financial_metrics': {
                        'npv': float(financial_result['npv']) if financial_result['npv'] else 0,
                        'irr': float(financial_result['irr']) if financial_result['irr'] else 0,
                        'payback_period': float(financial_result['payback_period']) if financial_result['payback_period'] else 0,
                        'total_investment': float(financial_result['initial_investment']) if financial_result['initial_investment'] else 0,
                        'annual_savings': float(financial_result['annual_savings']) if financial_result['annual_savings'] else 0,
                        'lcoe': float(financial_result['lcoe']) if financial_result['lcoe'] else 0
                    },
                    'environmental_impact': {},
                    'cash_flow_analysis': cash_flow_analysis,
                    'sensitivity_analysis': sensitivity_analysis
                }
                
                if environmental_result:
                    financial_data['environmental_impact'] = {
                        'annual_co2_savings': float(environmental_result['co2_savings_annual']) if environmental_result['co2_savings_annual'] else 0,
                        'lifetime_co2_savings': float(environmental_result['co2_savings_lifetime']) if environmental_result['co2_savings_lifetime'] else 0,
                        'carbon_value': float(environmental_result['carbon_value']) if environmental_result['carbon_value'] else 0,
                        'trees_equivalent': int(environmental_result['trees_equivalent']) if environmental_result['trees_equivalent'] else 0,
                        'cars_equivalent': int(environmental_result['cars_equivalent']) if environmental_result['cars_equivalent'] else 0
                    }
                
                return financial_data
                
        except Exception as e:
            st.error(f"Error retrieving financial analysis: {str(e)}")
            return None
        finally:
            conn.close()
    
    def get_financial_analysis_data(self, project_id):
        """Alias for get_financial_analysis - compatible method for AI consultation"""
        return self.get_financial_analysis(project_id)
    
    def get_yield_demand_data(self, project_id):
        """Get yield vs demand analysis data for a project"""
        conn = self.get_connection()
        if not conn:
            return None
        
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT * FROM energy_analysis 
                    WHERE project_id = %s
                    ORDER BY created_at DESC
                    LIMIT 1
                """, (project_id,))
                
                result = cursor.fetchone()
                return dict(result) if result else None
                
        except Exception as e:
            st.error(f"Error getting yield demand data: {str(e)}")
            return None
        finally:
            conn.close()
    

    
    def get_weather_data(self, project_id):
        """Get weather data for a project (already exists but added for completeness)"""
        conn = self.get_connection()
        if not conn:
            return None
        
        try:
            import json
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT * FROM weather_data 
                    WHERE project_id = %s
                    ORDER BY created_at DESC
                    LIMIT 1
                """, (project_id,))
                
                result = cursor.fetchone()
                if result:
                    weather_data = dict(result)
                    # Parse JSON fields if they exist
                    try:
                        if weather_data.get('tmy_data'):
                            weather_data['tmy_data'] = json.loads(weather_data['tmy_data'])
                        if weather_data.get('monthly_profiles'):
                            weather_data['monthly_profiles'] = json.loads(weather_data['monthly_profiles'])
                        if weather_data.get('environmental_factors'):
                            weather_data['environmental_factors'] = json.loads(weather_data['environmental_factors'])
                    except json.JSONDecodeError:
                        pass  # Keep original values if JSON parsing fails
                    return weather_data
                return None
                
        except Exception as e:
            st.error(f"Error getting weather data: {str(e)}")
            return None
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
                # Use direct project table query instead of view to avoid dependency issues
                cursor.execute("""
                    SELECT * FROM projects 
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
                building_elements_raw = cursor.fetchall()
                result['building_elements'] = [dict(row) for row in building_elements_raw]
                
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
                
                # Get financial analysis data
                financial_data = self.get_financial_analysis(result['project_id'])
                if financial_data:
                    result['financial_analysis'] = financial_data
                
                # Get PV specifications
                pv_data = self.get_pv_specifications(result['project_id'])
                if pv_data:
                    result['pv_specifications'] = pv_data
                
                # Get yield vs demand data
                cursor.execute("""
                    SELECT * FROM energy_analysis 
                    WHERE project_id = %s
                    ORDER BY created_at DESC LIMIT 1
                """, (result['project_id'],))
                energy_result = cursor.fetchone()
                if energy_result:
                    result['yield_demand_analysis'] = dict(energy_result)
                
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
                    SELECT id, project_name, location, created_at, updated_at
                    FROM projects 
                    ORDER BY updated_at DESC
                """)
                
                return [dict(row) for row in cursor.fetchall()]
                
        except Exception as e:
            st.error(f"Error listing projects: {str(e)}")
            return []
        finally:
            conn.close()

    def save_ai_model_data(self, project_id, model_data):
        """Save AI model performance data and training metrics"""
        conn = self.get_connection()
        if not conn:
            return False
        
        try:
            with conn.cursor() as cursor:
                # Delete existing AI model data for this project
                cursor.execute("DELETE FROM ai_models WHERE project_id = %s", (project_id,))
                
                # Insert new AI model data
                cursor.execute("""
                    INSERT INTO ai_models 
                    (project_id, model_type, r_squared_score, training_data_size, forecast_years, created_at)
                    VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                """, (
                    project_id,
                    model_data.get('model_type', 'RandomForestRegressor'),
                    model_data.get('r_squared_score', 0.92),
                    model_data.get('training_data_size', 12),
                    model_data.get('forecast_years', 25)
                ))
                
                conn.commit()
                return True
                
        except Exception as e:
            st.error(f"Error saving AI model data: {str(e)}")
            return False
        finally:
            conn.close()

# Global database manager instance
db_manager = BIPVDatabaseManager()