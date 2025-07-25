"""
Database Helper for BIPV Optimizer
Provides consistent database operations across all workflow steps
"""

import streamlit as st
from database_manager import BIPVDatabaseManager
import json

class DatabaseHelper:
    """Centralized database operations for BIPV workflow steps"""
    
    def __init__(self):
        self.db_manager = BIPVDatabaseManager()
    
    def get_project_id(self, project_name=None):
        """Get project ID directly from database - use centralized function"""
        from services.io import get_current_project_id
        return get_current_project_id()
    
    def get_project_name_by_id(self, project_id):
        """Get project name by project ID"""
        return self.db_manager.get_project_name_by_id(project_id)
    
    def save_project_data(self, project_data):
        """Save project configuration data to database"""
        try:
            return self.db_manager.save_project(project_data)
        except Exception as e:
            st.error(f"Error saving project data: {str(e)}")
            return None
    
    def save_step_data(self, step_name, data, project_name=None):
        """Save data for a specific workflow step"""
        project_id = self.get_project_id(project_name)
        if not project_id:
            st.warning(f"Cannot save {step_name} data - no project ID available")
            return False
        
        try:
            # Convert numeric step names to proper step names
            step_mapping = {
                "1": "project_setup",
                "2": "historical_data", 
                "3": "weather_analysis",
                "4": "building_elements",
                "5": "radiation_analysis",
                "6": "pv_specifications",
                "7": "yield_demand",
                "8": "optimization",
                "9": "financial_analysis"
            }
            
            # Map numeric step names to proper names
            if str(step_name) in step_mapping:
                step_name = step_mapping[str(step_name)]
            
            # Choose appropriate save method based on step
            if step_name == "weather_analysis":
                return self.db_manager.save_weather_data(project_id, data)
            elif step_name == "historical_data":
                return self.db_manager.save_historical_data(project_id, data)
            elif step_name == "building_elements":
                return self.db_manager.save_building_elements(project_id, data)
            elif step_name == "radiation_analysis":
                return self.db_manager.save_radiation_analysis(project_id, data)
            elif step_name == "pv_specifications":
                return self.db_manager.save_pv_specifications(project_id, data)
            elif step_name == "yield_demand":
                # Only save authentic yield demand data to database
                if 'energy_balance' in data and data['energy_balance']:
                    yield_demand_analysis = {
                        'total_annual_yield': sum([row.get('total_yield_kwh', 0) for row in data['energy_balance']]),
                        'annual_demand': sum([row.get('predicted_demand', 0) for row in data['energy_balance']]),
                        'analysis_config': data.get('analysis_config', {}),
                        'energy_balance': data['energy_balance']
                    }
                    return self.db_manager.save_yield_demand_data(project_id, yield_demand_analysis)
                else:
                    st.warning("No authentic energy balance data to save")
                    return False
            elif step_name == "optimization":
                return self.db_manager.save_optimization_results(project_id, data)
            elif step_name == "financial_analysis":
                return self.db_manager.save_financial_analysis(project_id, data)
            else:
                st.warning(f"Unknown step name: {step_name}")
                return False
                
        except Exception as e:
            st.error(f"Error saving {step_name} data: {str(e)}")
            return False
    
    def get_step_data(self, step_name, project_name=None):
        """Get authentic data for a specific workflow step from database only"""
        project_id = self.get_project_id(project_name)
        if not project_id:
            return None
        
        try:
            # Convert numeric step names to proper step names
            step_mapping = {
                "1": "project_setup",
                "2": "historical_data", 
                "3": "weather_analysis",
                "4": "building_elements",
                "5": "radiation_analysis",
                "6": "pv_specifications",
                "7": "yield_demand",
                "8": "optimization",
                "9": "financial_analysis"
            }
            
            # Map numeric step names to proper names
            if str(step_name) in step_mapping:
                step_name = step_mapping[str(step_name)]
            
            # Only retrieve authentic database data - no fallbacks
            if step_name == "weather_analysis":
                # Get weather data from database
                conn = self.db_manager.get_connection()
                if conn:
                    with conn.cursor() as cursor:
                        cursor.execute("""
                            SELECT temperature, annual_ghi, tmy_data, monthly_profiles, environmental_factors
                            FROM weather_data 
                            WHERE project_id = %s
                            ORDER BY created_at DESC LIMIT 1
                        """, (project_id,))
                        
                        result = cursor.fetchone()
                        if result:
                            weather_data = {
                                'temperature': result[0],
                                'annual_ghi': result[1]
                            }
                            # Parse JSON fields if they exist
                            if result[2]:  # tmy_data
                                try:
                                    weather_data['tmy_data'] = json.loads(result[2])
                                except:
                                    pass
                            if result[3]:  # monthly_profiles
                                try:
                                    weather_data['monthly_profiles'] = json.loads(result[3])
                                except:
                                    pass
                            if result[4]:  # environmental_factors
                                try:
                                    weather_data['environmental_factors'] = json.loads(result[4])
                                except:
                                    pass
                            return weather_data
                    conn.close()
                return None
            elif step_name == "yield_demand":
                # Get from energy_analysis table
                conn = self.db_manager.get_connection()
                if conn:
                    with conn.cursor() as cursor:
                        cursor.execute("""
                            SELECT annual_generation, annual_demand, net_energy_balance 
                            FROM energy_analysis 
                            WHERE project_id = %s AND annual_generation IS NOT NULL
                            ORDER BY created_at DESC LIMIT 1
                        """, (project_id,))
                        
                        result = cursor.fetchone()
                        if result:
                            return {
                                'energy_balance': [{'predicted_demand': result[1], 'total_yield_kwh': result[0]}],
                                'annual_generation': result[0],
                                'annual_demand': result[1]
                            }
                    conn.close()
            
            # For other steps, use project report data
            project_data = self.db_manager.get_project_report_data(project_name or st.session_state.get('project_name'))
            if project_data:
                return project_data.get(step_name, {})
            return None
            
        except Exception as e:
            # Silent error handling for optional data retrieval
            return None
    
    def update_session_from_database(self, project_name=None):
        """Update session state with latest database data"""
        if project_name is None:
            project_name = st.session_state.get('project_name', 'Default Project')
        
        try:
            project_data = self.db_manager.get_project_report_data(project_name)
            if project_data:
                # Update session state with database data
                st.session_state.project_data = project_data
                st.session_state.project_name = project_data.get('project_name', project_name)
                return True
            return False
            
        except Exception as e:
            st.warning(f"Could not update session from database: {str(e)}")
            return False
    
    def check_step_completion(self, step_name, project_name=None):
        """Check if a workflow step has been completed"""
        project_id = self.get_project_id(project_name)
        if not project_id:
            return False
        
        try:
            conn = self.db_manager.get_connection()
            if conn:
                with conn.cursor() as cursor:
                    # Check different tables based on step
                    if step_name == "project_setup":
                        cursor.execute("SELECT COUNT(*) FROM projects WHERE project_id = %s", (project_id,))
                    elif step_name == "historical_data":
                        cursor.execute("SELECT COUNT(*) FROM historical_data WHERE project_id = %s", (project_id,))
                    elif step_name == "weather_analysis":
                        cursor.execute("SELECT COUNT(*) FROM weather_data WHERE project_id = %s", (project_id,))
                    elif step_name == "building_elements":
                        cursor.execute("SELECT COUNT(*) FROM building_elements WHERE project_id = %s", (project_id,))
                    elif step_name == "radiation_analysis":
                        cursor.execute("SELECT COUNT(*) FROM element_radiation WHERE project_id = %s", (project_id,))
                    elif step_name == "pv_specifications":
                        cursor.execute("SELECT COUNT(*) FROM pv_specifications WHERE project_id = %s", (project_id,))
                    elif step_name == "yield_demand":
                        cursor.execute("SELECT COUNT(*) FROM yield_demand WHERE project_id = %s", (project_id,))
                    elif step_name == "optimization":
                        cursor.execute("SELECT COUNT(*) FROM optimization_results WHERE project_id = %s", (project_id,))
                    elif step_name == "financial_analysis":
                        cursor.execute("SELECT COUNT(*) FROM financial_analysis WHERE project_id = %s", (project_id,))
                    else:
                        return False
                    
                    result = cursor.fetchone()
                    conn.close()
                    return result[0] > 0 if result else False
                conn.close()
        except Exception as e:
            st.warning(f"Could not check {step_name} completion: {str(e)}")
            return False
        
        return False
    
    def count_step_records(self, step_name, project_name=None):
        """Count records for a specific step"""
        project_id = self.get_project_id(project_name)
        if not project_id:
            return 0
        
        try:
            conn = self.db_manager.get_connection()
            if conn:
                with conn.cursor() as cursor:
                    if step_name == "building_elements":
                        cursor.execute("SELECT COUNT(*) FROM building_elements WHERE project_id = %s", (project_id,))
                    elif step_name == "radiation_analysis":
                        cursor.execute("SELECT COUNT(*) FROM element_radiation WHERE project_id = %s", (project_id,))
                    elif step_name == "optimization":
                        cursor.execute("SELECT COUNT(*) FROM optimization_results WHERE project_id = %s", (project_id,))
                    else:
                        conn.close()
                        return 0
                    
                    result = cursor.fetchone()
                    conn.close()
                    return result[0] if result else 0
                conn.close()
        except Exception as e:
            st.warning(f"Could not count {step_name} records: {str(e)}")
            return 0
        
        return 0

# Global instance
db_helper = DatabaseHelper()