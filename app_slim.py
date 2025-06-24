"""
BIPV Optimizer - Slim Application Entry Point
Refactored modular architecture with clean separation of concerns
"""
import streamlit as st
import os

# Import page modules
from pages.welcome import render_welcome
from pages.project_setup import render_project_setup
# TODO: Import remaining page modules as they are created

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
        elif step_key in ['radiation_grid', 'pv_specification', 'yield_demand', 'optimization', 'financial_analysis', 'reporting']:
            return project_data.get('extraction_complete', False)
        
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
        # TODO: Import and call render_historical_data()
        st.header("Step 2: Historical Data Analysis")
        st.info("This step is being refactored. Please use the original app.py for now.")
    elif current_step == 'weather_environment':
        # TODO: Import and call render_weather_environment()
        st.header("Step 3: Weather & Environment Integration")
        st.info("This step is being refactored. Please use the original app.py for now.")
    elif current_step == 'facade_extraction':
        # TODO: Import and call render_facade_extraction()
        st.header("Step 4: Facade & Window Extraction")
        st.info("This step is being refactored. Please use the original app.py for now.")
    elif current_step == 'radiation_grid':
        # TODO: Import and call render_radiation_grid()
        st.header("Step 5: Radiation & Shading Analysis")
        st.info("This step is being refactored. Please use the original app.py for now.")
    elif current_step == 'pv_specification':
        # TODO: Import and call render_pv_specification()
        st.header("Step 6: PV Specification & Layout")
        st.info("This step is being refactored. Please use the original app.py for now.")
    elif current_step == 'yield_demand':
        # TODO: Import and call render_yield_demand()
        st.header("Step 7: Yield vs Demand Analysis")
        st.info("This step is being refactored. Please use the original app.py for now.")
    elif current_step == 'optimization':
        # TODO: Import and call render_optimization()
        st.header("Step 8: Multi-Objective Optimization")
        st.info("This step is being refactored. Please use the original app.py for now.")
    elif current_step == 'financial_analysis':
        # TODO: Import and call render_financial_analysis()
        st.header("Step 9: Financial & Environmental Analysis")
        st.info("This step is being refactored. Please use the original app.py for now.")
    elif current_step == 'reporting':
        # TODO: Import and call render_reporting()
        st.header("Step 10: Reporting & Export")
        st.info("This step is being refactored. Please use the original app.py for now.")


if __name__ == "__main__":
    main()