"""
Database State Manager for BIPV Optimizer
Replaces all session state usage with database-driven state management
"""

import json
from datetime import datetime
from database_manager import BIPVDatabaseManager
import streamlit as st

class DatabaseStateManager:
    def __init__(self):
        self.db_manager = BIPVDatabaseManager()
    
    def get_current_project_id(self):
        """Get current project ID using centralized method"""
        from services.io import get_current_project_id
        return get_current_project_id()
    
    def save_step_completion(self, step_name, completion_data=None):
        """Save step completion status to database"""
        project_id = self.get_current_project_id()
        if not project_id:
            return False
        
        conn = self.db_manager.get_connection()
        if not conn:
            return False
        
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    INSERT INTO step_completions (project_id, step_name, completed_at, completion_data)
                    VALUES (%s, %s, CURRENT_TIMESTAMP, %s)
                    ON CONFLICT (project_id, step_name) 
                    DO UPDATE SET completed_at = CURRENT_TIMESTAMP, completion_data = EXCLUDED.completion_data
                """, (project_id, step_name, json.dumps(completion_data) if completion_data else None))
                
                conn.commit()
                return True
        except Exception as e:
            st.error(f"Error saving step completion: {str(e)}")
            return False
        finally:
            conn.close()
    
    def is_step_completed(self, step_name):
        """Check if step is completed"""
        project_id = self.get_current_project_id()
        if not project_id:
            return False
        
        conn = self.db_manager.get_connection()
        if not conn:
            return False
        
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT completion_data FROM step_completions 
                    WHERE project_id = %s AND step_name = %s
                """, (project_id, step_name))
                
                result = cursor.fetchone()
                return result is not None
        except Exception:
            return False
        finally:
            conn.close()
    
    def get_step_data(self, step_name):
        """Get step data from database"""
        project_id = self.get_current_project_id()
        if not project_id:
            return None
        
        # Route to appropriate database method based on step
        if step_name == 'project_setup':
            return self.db_manager.get_project_by_id(project_id)
        elif step_name == 'historical_data':
            return self._get_historical_data(project_id)
        elif step_name == 'weather_environment':
            return self._get_weather_data(project_id)
        elif step_name == 'facade_extraction':
            return self._get_building_elements(project_id)
        elif step_name == 'radiation_grid':
            return self._get_radiation_data(project_id)
        elif step_name == 'pv_specification':
            return self.db_manager.get_pv_specifications(project_id)
        elif step_name == 'yield_demand':
            return self._get_yield_demand_data(project_id)
        elif step_name == 'optimization':
            return self._get_optimization_data(project_id)
        elif step_name == 'financial_analysis':
            return self._get_financial_data(project_id)
        else:
            return None
    
    def _get_historical_data(self, project_id):
        """Get historical data from database"""
        conn = self.db_manager.get_connection()
        if not conn:
            return None
        
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT * FROM energy_analysis 
                    WHERE project_id = %s
                    ORDER BY created_at DESC LIMIT 1
                """, (project_id,))
                
                result = cursor.fetchone()
                if result:
                    return {
                        'annual_demand': result[2],
                        'self_consumption_rate': result[3],
                        'energy_yield_per_m2': result[4]
                    }
                return None
        except Exception:
            return None
        finally:
            conn.close()
    
    def _get_weather_data(self, project_id):
        """Get weather data from database"""
        conn = self.db_manager.get_connection()
        if not conn:
            return None
        
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT weather_data FROM weather_data 
                    WHERE project_id = %s
                    ORDER BY created_at DESC LIMIT 1
                """, (project_id,))
                
                result = cursor.fetchone()
                if result and result[0]:
                    return json.loads(result[0])
                return None
        except Exception:
            return None
        finally:
            conn.close()
    
    def _get_building_elements(self, project_id):
        """Get building elements from database"""
        conn = self.db_manager.get_connection()
        if not conn:
            return None
        
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT element_id, element_type, glass_area, orientation, azimuth, level
                    FROM building_elements 
                    WHERE project_id = %s
                """, (project_id,))
                
                results = cursor.fetchall()
                if results:
                    return [
                        {
                            'element_id': row[0],
                            'element_type': row[1],
                            'glass_area': row[2],
                            'orientation': row[3],
                            'azimuth': row[4],
                            'level': row[5]
                        }
                        for row in results
                    ]
                return None
        except Exception:
            return None
        finally:
            conn.close()
    
    def _get_radiation_data(self, project_id):
        """Get radiation analysis data from database"""
        conn = self.db_manager.get_connection()
        if not conn:
            return None
        
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT element_id, annual_radiation, monthly_radiation
                    FROM element_radiation 
                    WHERE project_id = %s
                """, (project_id,))
                
                results = cursor.fetchall()
                if results:
                    return {
                        row[0]: {
                            'annual_radiation': row[1],
                            'monthly_radiation': json.loads(row[2]) if row[2] else {}
                        }
                        for row in results
                    }
                return None
        except Exception:
            return None
        finally:
            conn.close()
    
    def _get_yield_demand_data(self, project_id):
        """Get yield vs demand data from database"""
        # This would typically be derived from PV specifications and historical data
        pv_specs = self.db_manager.get_pv_specifications(project_id)
        historical = self._get_historical_data(project_id)
        
        if pv_specs and historical:
            return {
                'pv_specifications': pv_specs,
                'historical_data': historical,
                'energy_balance': self._calculate_energy_balance(pv_specs, historical)
            }
        return None
    
    def _get_optimization_data(self, project_id):
        """Get optimization results from database"""
        conn = self.db_manager.get_connection()
        if not conn:
            return None
        
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT optimization_results FROM optimization_results 
                    WHERE project_id = %s
                    ORDER BY created_at DESC LIMIT 1
                """, (project_id,))
                
                result = cursor.fetchone()
                if result and result[0]:
                    return json.loads(result[0])
                return None
        except Exception:
            return None
        finally:
            conn.close()
    
    def _get_financial_data(self, project_id):
        """Get financial analysis data from database"""
        conn = self.db_manager.get_connection()
        if not conn:
            return None
        
        try:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT * FROM financial_analysis 
                    WHERE project_id = %s
                    ORDER BY created_at DESC LIMIT 1
                """, (project_id,))
                
                result = cursor.fetchone()
                if result:
                    return {
                        'npv': result[2],
                        'irr': result[3],
                        'payback_period': result[4],
                        'total_investment': result[5],
                        'annual_savings': result[6]
                    }
                return None
        except Exception:
            return None
        finally:
            conn.close()
    
    def _calculate_energy_balance(self, pv_specs, historical_data):
        """Calculate energy balance from PV specs and historical data"""
        # Simple calculation - this would be more sophisticated in practice
        if isinstance(pv_specs, dict) and 'bipv_specifications' in pv_specs:
            total_annual_generation = sum(
                spec.get('annual_energy_kwh', 0) 
                for spec in pv_specs['bipv_specifications']
            )
            annual_demand = historical_data.get('annual_demand', 0)
            
            return {
                'total_generation': total_annual_generation,
                'total_demand': annual_demand,
                'net_import': max(0, annual_demand - total_annual_generation),
                'excess_generation': max(0, total_annual_generation - annual_demand)
            }
        return {}
    
    def get_current_step(self):
        """Get current workflow step from database or URL params"""
        # Check URL parameters first
        query_params = st.query_params
        if 'step' in query_params:
            return query_params['step']
        
        # Default to welcome if no step specified
        return 'welcome'
    
    def set_current_step(self, step_name):
        """Set current workflow step"""
        st.query_params['step'] = step_name

# Create global instance
db_state_manager = DatabaseStateManager()