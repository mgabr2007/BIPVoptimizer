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
    # Sidebar navigation
    st.sidebar.title("🏢 BIPV Optimizer")
    
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
        # Always allow welcome and project setup
        if step_key in ['welcome', 'project_setup']:
            return True
        
        # For development and testing, make all steps available initially
        # Users can navigate freely but will see dependency warnings in each step
        return True
    
    # Render navigation buttons with better spacing
    for i, (step_key, step_name, description) in enumerate(workflow_steps):
        is_current = st.session_state.current_step == step_key
        
        if is_current:
            st.sidebar.markdown(f"**▶️ {step_name}**")
            st.sidebar.caption(f"*Current: {description}*")
        else:
            if st.sidebar.button(step_name, key=f"nav_{step_key}_{i}", use_container_width=True):
                st.session_state.current_step = step_key
                st.rerun()
            st.sidebar.caption(description)
        
        # Add small spacing between buttons
        if i < len(workflow_steps) - 1:
            st.sidebar.write("")
    
    st.sidebar.markdown("---")
    
    # Project info display (simplified)
    if 'project_data' in st.session_state and st.session_state.project_data:
        project_name = st.session_state.project_data.get('project_name', 'New Project')
        st.sidebar.markdown(f"**Project:** {project_name}")
    
    # Main content area - render current step
    current_step = st.session_state.current_step
    
    # Add step navigation within main content
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        # Find current step index
        current_index = next((i for i, (key, _, _) in enumerate(workflow_steps) if key == current_step), 0)
        if current_index > 0:
            prev_step = workflow_steps[current_index - 1]
            if st.button(f"← {prev_step[1]}", key="prev_step"):
                st.session_state.current_step = prev_step[0]
                st.rerun()
    
    with col2:
        st.markdown(f"<h3 style='text-align: center;'>Step {current_index + 1} of {len(workflow_steps)}</h3>", unsafe_allow_html=True)
    
    with col3:
        if current_index < len(workflow_steps) - 1:
            next_step = workflow_steps[current_index + 1]
            if st.button(f"{next_step[1]} →", key="next_step"):
                st.session_state.current_step = next_step[0]
                st.rerun()
    
    st.markdown("---")
    
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


if __name__ == "__main__":
    main()