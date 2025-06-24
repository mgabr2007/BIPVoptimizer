"""
BIPV Optimizer - Slim Application Entry Point
Refactored modular architecture with clean separation of concerns
"""
import streamlit as st
import os

# Import page modules
from pages.welcome import render_welcome
from pages.project_setup import render_project_setup
from pages.historical_data import render_historical_data
from pages.weather_environment import render_weather_environment
from pages.facade_extraction import render_facade_extraction
from pages.radiation_grid import render_radiation_grid
from pages.pv_specification import render_pv_specification
from pages.yield_demand import render_yield_demand
from pages.optimization import render_optimization
from pages.financial_analysis import render_financial_analysis
from pages.reporting import render_reporting

# Import services
from services.io import list_projects

# Import project selector
from project_selector import render_project_selector

# Page configuration
st.set_page_config(
    page_title="BIPV Optimizer",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'current_step' not in st.session_state:
    st.session_state.current_step = 'welcome'

if 'project_data' not in st.session_state:
    st.session_state.project_data = {}


def main():
    """Main application entry point"""
    # Sidebar navigation
    st.sidebar.title("🏢 BIPV Optimizer")
    
    # Project selector
    render_project_selector()
    
    st.sidebar.markdown("---")
    
    # Navigation menu
    st.sidebar.subheader("📋 Analysis Workflow")
    
    # Define workflow steps
    workflow_steps = [
        ("welcome", "🏠 Welcome", "Introduction to BIPV optimization"),
        ("project_setup", "1️⃣ Project Setup", "Location and configuration"),
        ("historical_data", "2️⃣ Historical Data", "Energy consumption analysis"),
        ("weather_environment", "3️⃣ Weather Integration", "TMY and climate data"),
        ("facade_extraction", "4️⃣ BIM Extraction", "Building geometry analysis"),
        ("radiation_grid", "5️⃣ Radiation Analysis", "Solar irradiance modeling"),
        ("pv_specification", "6️⃣ PV Specification", "Technology selection"),
        ("yield_demand", "7️⃣ Yield vs Demand", "Energy balance analysis"),
        ("optimization", "8️⃣ Optimization", "Multi-objective optimization"),
        ("financial_analysis", "9️⃣ Financial Analysis", "Economic viability"),
        ("reporting", "🔟 Reporting", "Results and export")
    ]
    
    # Check step dependencies
    def check_step_availability(step_key):
        """Check if a step is available based on previous completions"""
        if step_key in ['welcome', 'project_setup']:
            return True
        
        project_data = st.session_state.get('project_data', {})
        
        if step_key == 'historical_data':
            return project_data.get('setup_complete', False)
        elif step_key == 'weather_environment':
            return project_data.get('setup_complete', False)
        elif step_key == 'facade_extraction':
            return project_data.get('setup_complete', False)
        elif step_key == 'radiation_grid':
            return st.session_state.get('building_elements_completed', False) and st.session_state.get('weather_completed', False)
        elif step_key == 'pv_specification':
            return st.session_state.get('radiation_completed', False)
        elif step_key == 'yield_demand':
            return st.session_state.get('pv_specs_completed', False) and st.session_state.get('historical_completed', False)
        elif step_key == 'optimization':
            return st.session_state.get('yield_demand_completed', False)
        elif step_key == 'financial_analysis':
            return st.session_state.get('optimization_completed', False)
        elif step_key == 'reporting':
            return st.session_state.get('building_elements_completed', False)
        
        return True
    
    # Render navigation buttons
    for step_key, step_name, description in workflow_steps:
        is_available = check_step_availability(step_key)
        is_current = st.session_state.current_step == step_key
        
        if is_current:
            st.sidebar.markdown(f"**▶️ {step_name}**")
        elif is_available:
            if st.sidebar.button(step_name, key=f"nav_{step_key}"):
                st.session_state.current_step = step_key
                st.rerun()
        else:
            st.sidebar.markdown(f"🔒 {step_name} *(requires previous steps)*")
        
        st.sidebar.caption(description)
    
    st.sidebar.markdown("---")
    
    # Project info display
    if 'project_data' in st.session_state and st.session_state.project_data:
        project_name = st.session_state.project_data.get('project_name', 'Unnamed Project')
        location = st.session_state.project_data.get('location', 'No location set')
        st.sidebar.markdown(f"**Current Project:** {project_name}")
        st.sidebar.markdown(f"**Location:** {location}")
    
    # Main content area - render current step
    current_step = st.session_state.current_step
    
    if current_step == 'welcome':
        render_welcome()
    elif current_step == 'project_setup':
        render_project_setup()
    elif current_step == 'historical_data':
        render_historical_data()
    elif current_step == 'weather_environment':
        render_weather_environment()
    elif current_step == 'facade_extraction':
        render_facade_extraction()
    elif current_step == 'radiation_grid':
        render_radiation_grid()
    elif current_step == 'pv_specification':
        render_pv_specification()
    elif current_step == 'yield_demand':
        render_yield_demand()
    elif current_step == 'optimization':
        render_optimization()
    elif current_step == 'financial_analysis':
        render_financial_analysis()
    elif current_step == 'reporting':
        render_reporting()


if __name__ == "__main__":
    main()