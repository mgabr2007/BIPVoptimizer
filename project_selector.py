"""
Project Selector Component for BIPV Optimizer
Allows users to load previously analyzed projects from database
"""

import streamlit as st
from database_manager import db_manager
from datetime import datetime

def render_project_selector():
    """Render project selection interface"""
    
    st.sidebar.subheader("📂 Project Management")
    
    # Get list of existing projects
    projects = db_manager.list_projects()
    
    if projects:
        project_options = [f"{p['project_name']} ({p['location']})" for p in projects]
        project_options.insert(0, "➕ Create New Project")
        
        selected_option = st.sidebar.selectbox(
            "Select Project",
            options=project_options,
            key="project_selector"
        )
        
        if selected_option != "➕ Create New Project":
            # Extract project name from selection
            project_name = selected_option.split(" (")[0]
            
            if st.sidebar.button("📥 Load Project", key="load_project"):
                load_project_from_database(project_name)
                st.rerun()
            
            # Show project details
            selected_project = next((p for p in projects if p['project_name'] == project_name), None)
            if selected_project:
                st.sidebar.markdown("**Project Details:**")
                # Handle datetime objects properly
                created_date = selected_project['created_at']
                updated_date = selected_project['updated_at']
                
                if hasattr(created_date, 'strftime'):
                    created_str = created_date.strftime('%Y-%m-%d')
                else:
                    created_str = str(created_date)[:10]
                    
                if hasattr(updated_date, 'strftime'):
                    updated_str = updated_date.strftime('%Y-%m-%d')
                else:
                    updated_str = str(updated_date)[:10]
                
                st.sidebar.text(f"Created: {created_str}")
                st.sidebar.text(f"Updated: {updated_str}")
        
        # Delete project option
        if len(projects) > 0:
            st.sidebar.markdown("---")
            delete_project = st.sidebar.selectbox(
                "Delete Project",
                options=["Select project to delete..."] + [p['project_name'] for p in projects],
                key="delete_selector"
            )
            
            if delete_project != "Select project to delete...":
                if st.sidebar.button("🗑️ Delete Project", key="delete_project"):
                    if delete_project_from_database(delete_project):
                        st.sidebar.success(f"Deleted project: {delete_project}")
                        st.rerun()
    
    else:
        st.sidebar.info("No saved projects found. Create your first project!")

def load_project_from_database(project_name):
    """Load project data from database into session state"""
    
    # Get comprehensive project data
    db_data = db_manager.get_project_report_data(project_name)
    
    if not db_data:
        st.error(f"Project '{project_name}' not found in database")
        return False
    
    # Reconstruct session state from database data
    project_data = {
        'project_name': db_data['project_name'],
        'location': db_data['location'],
        'coordinates': {
            'lat': float(db_data['latitude']) if db_data['latitude'] else 0,
            'lon': float(db_data['longitude']) if db_data['longitude'] else 0
        },
        'timezone': db_data['timezone'],
        'currency': db_data['currency'],
        'setup_complete': True
    }
    
    # Add weather data if available
    if db_data.get('temperature'):
        project_data['current_weather'] = {
            'temperature': float(db_data['temperature']),
            'description': 'Loaded from database',
            'api_success': True
        }
    
    # Add radiation data if available
    if db_data.get('avg_irradiance'):
        project_data['radiation_data'] = {
            'avg_irradiance': float(db_data['avg_irradiance']),
            'peak_irradiance': float(db_data['peak_irradiance']) if db_data['peak_irradiance'] else 1000,
            'shading_factor': float(db_data['shading_factor']) if db_data['shading_factor'] else 0,
            'analysis_complete': True
        }
    
    # Add financial analysis data if available
    if db_data.get('initial_investment'):
        project_data['financial_analysis'] = {
            'initial_investment': float(db_data['initial_investment']),
            'annual_savings': float(db_data['annual_savings']) if db_data['annual_savings'] else 0,
            'npv': float(db_data['npv']) if db_data['npv'] else 0,
            'irr': float(db_data['irr']) if db_data['irr'] else 0,
            'payback_period': float(db_data['payback_period']) if db_data['payback_period'] else 0,
            'co2_savings_annual': float(db_data['co2_savings_annual']) if db_data['co2_savings_annual'] else 0,
            'co2_savings_lifetime': float(db_data['co2_savings_lifetime']) if db_data['co2_savings_lifetime'] else 0,
            'analysis_complete': True
        }
    
    # Set session state
    st.session_state.project_data = project_data
    st.session_state.project_id = db_data['project_id']
    
    # Load building elements
    if db_data.get('building_elements'):
        import pandas as pd
        building_elements_df = pd.DataFrame(db_data['building_elements'])
        st.session_state.building_elements = building_elements_df
        
        # Add to project_data for compatibility
        project_data['facade_data'] = {
            'windows': db_data['building_elements'],
            'total_elements': len(db_data['building_elements']),
            'suitable_elements': sum(1 for elem in db_data['building_elements'] if elem.get('pv_suitable')),
            'total_glass_area': sum(elem.get('glass_area', 0) for elem in db_data['building_elements'])
        }
        project_data['extraction_complete'] = True
    
    # Load PV specifications
    if db_data.get('panel_type'):
        pv_specs = {
            'panel_type': db_data['panel_type'],
            'efficiency': float(db_data['efficiency']) if db_data['efficiency'] else 0,
            'transparency': float(db_data['transparency']) if db_data['transparency'] else 0,
            'cost_per_m2': float(db_data['cost_per_m2']) if db_data['cost_per_m2'] else 0
        }
        st.session_state.pv_specs = pv_specs
    
    st.success(f"Successfully loaded project: {project_name}")
    st.info(f"Loaded {len(db_data.get('building_elements', []))} building elements")
    
    # Set workflow step to reporting for immediate access
    st.session_state.workflow_step = 10
    
    return True

def delete_project_from_database(project_name):
    """Delete project from database"""
    conn = db_manager.get_connection()
    if not conn:
        return False
    
    try:
        with conn.cursor() as cursor:
            # Get project ID
            cursor.execute("SELECT id FROM projects WHERE project_name = %s", (project_name,))
            result = cursor.fetchone()
            
            if result:
                project_id = result[0]
                # Delete project (cascade will handle related tables)
                cursor.execute("DELETE FROM projects WHERE id = %s", (project_id,))
                conn.commit()
                return True
            else:
                st.error(f"Project '{project_name}' not found")
                return False
                
    except Exception as e:
        conn.rollback()
        st.error(f"Error deleting project: {str(e)}")
        return False
    finally:
        conn.close()

def show_database_status():
    """Show database connection status in sidebar"""
    conn = db_manager.get_connection()
    if conn:
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM projects")
                project_count = cursor.fetchone()[0]
            
            st.sidebar.success(f"📊 Database Connected")
            st.sidebar.text(f"{project_count} projects stored")
            conn.close()
        except:
            st.sidebar.error("Database connection issues")
    else:
        st.sidebar.error("Database unavailable")