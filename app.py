"""
BIPV Optimizer - Clean Application Entry Point
No project selector, minimal sidebar interface
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

# Initialize completion flags
completion_flags = [
    'setup_completed', 'historical_completed', 'weather_completed', 
    'building_elements_completed', 'radiation_completed', 'pv_specs_completed',
    'yield_demand_completed', 'optimization_completed', 'financial_completed'
]

for flag in completion_flags:
    if flag not in st.session_state:
        st.session_state[flag] = False


def main():
    """Main application entry point"""
    # Clean sidebar starting from loading the project
    st.sidebar.markdown("### Loading the project")
    
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
    
    # Only show current project info if available
    if 'project_data' in st.session_state and st.session_state.project_data:
        project_name = st.session_state.project_data.get('project_name', 'Unnamed Project')
        st.sidebar.markdown(f"**Current Project:** {project_name}")
        st.sidebar.markdown("---")
    
    # Main content area - render current step without top navigation
    current_step = st.session_state.current_step
    
    # Render the actual step content
    try:
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
        else:
            st.error(f"Unknown step: {current_step}")
    except Exception as e:
        st.error(f"Error rendering step '{current_step}': {str(e)}")
        st.info("Please try navigating to a different step.")
    
    # Add bottom navigation to every page
    st.markdown("---")
    render_bottom_navigation(workflow_steps, current_step)


def render_bottom_navigation(workflow_steps, current_step):
    """Render navigation buttons at the bottom of each page"""
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        # Find current step index
        current_index = next((i for i, (key, _, _) in enumerate(workflow_steps) if key == current_step), 0)
        if current_index > 0:
            prev_step = workflow_steps[current_index - 1]
            if st.button(f"← {prev_step[1]}", key="bottom_prev_step", use_container_width=True):
                st.session_state.current_step = prev_step[0]
                st.rerun()
    
    with col2:
        st.markdown(f"<h4 style='text-align: center;'>Step {current_index + 1} of {len(workflow_steps)}</h4>", unsafe_allow_html=True)
    
    with col3:
        if current_index < len(workflow_steps) - 1:
            next_step = workflow_steps[current_index + 1]
            if st.button(f"{next_step[1]} →", key="bottom_next_step", use_container_width=True):
                st.session_state.current_step = next_step[0]
                st.rerun()


if __name__ == "__main__":
    main()