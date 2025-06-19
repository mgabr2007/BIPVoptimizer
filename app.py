import streamlit as st
import sys
import os

# Add modules directory to path (but remove workspace root to avoid numpy conflicts)
modules_path = os.path.join(os.path.dirname(__file__), 'modules')
utils_path = os.path.join(os.path.dirname(__file__), 'utils')

if modules_path not in sys.path:
    sys.path.insert(0, modules_path)
if utils_path not in sys.path:
    sys.path.insert(0, utils_path)

# Remove workspace root from sys.path to prevent numpy import conflicts
workspace_root = os.path.dirname(__file__)
if workspace_root in sys.path:
    sys.path.remove(workspace_root)

# Import all modules
from project_setup import render_project_setup
from historical_data import render_historical_data
from weather_environment import render_weather_environment
from facade_extraction import render_facade_extraction
from radiation_grid import render_radiation_grid
from pv_specification import render_pv_specification
from yield_demand import render_yield_demand
from optimization import render_optimization
from financial_analysis import render_financial_analysis
from visualization_3d import render_3d_visualization
from reporting import render_reporting

def main():
    st.set_page_config(
        page_title="BIPV Analysis Platform",
        page_icon="🏢",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    st.title("🏢 Building Integrated Photovoltaics (BIPV) Analysis Platform")
    st.markdown("---")
    
    # Initialize session state for workflow progress
    if 'workflow_step' not in st.session_state:
        st.session_state.workflow_step = 1
    if 'project_data' not in st.session_state:
        st.session_state.project_data = {}
    if 'checkpoints' not in st.session_state:
        st.session_state.checkpoints = {}
    
    # Sidebar navigation
    st.sidebar.title("Workflow Navigation")
    
    steps = [
        "1. Project Setup",
        "2. Historical Data & AI Model",
        "3. Weather & Environment",
        "4. Facade & Window Extraction",
        "5. Radiation & Shading Grid",
        "6. PV Panel Specification",
        "7. Yield vs. Demand Calculation",
        "8. Optimization",
        "9. Financial & Environmental Analysis",
        "10. 3D Visualization",
        "11. Reporting & Export"
    ]
    
    # Progress indicator
    st.sidebar.progress(st.session_state.workflow_step / len(steps))
    st.sidebar.markdown(f"**Step {st.session_state.workflow_step} of {len(steps)}**")
    
    # Step selection
    selected_step = st.sidebar.selectbox("Go to Step:", steps, index=st.session_state.workflow_step-1)
    st.session_state.workflow_step = steps.index(selected_step) + 1
    
    # Checkpoint management
    st.sidebar.markdown("---")
    st.sidebar.markdown("**Checkpoints**")
    if st.sidebar.button("Save Checkpoint"):
        st.session_state.checkpoints[st.session_state.workflow_step] = st.session_state.project_data.copy()
        st.sidebar.success(f"Checkpoint saved at Step {st.session_state.workflow_step}")
    
    if st.session_state.checkpoints and st.sidebar.button("Load Last Checkpoint"):
        last_checkpoint = max(st.session_state.checkpoints.keys())
        st.session_state.project_data = st.session_state.checkpoints[last_checkpoint].copy()
        st.session_state.workflow_step = last_checkpoint
        st.sidebar.success(f"Loaded checkpoint from Step {last_checkpoint}")
        st.rerun()
    
    # Main content area
    if st.session_state.workflow_step == 1:
        render_project_setup()
    elif st.session_state.workflow_step == 2:
        render_historical_data()
    elif st.session_state.workflow_step == 3:
        render_weather_environment()
    elif st.session_state.workflow_step == 4:
        render_facade_extraction()
    elif st.session_state.workflow_step == 5:
        render_radiation_grid()
    elif st.session_state.workflow_step == 6:
        render_pv_specification()
    elif st.session_state.workflow_step == 7:
        render_yield_demand()
    elif st.session_state.workflow_step == 8:
        render_optimization()
    elif st.session_state.workflow_step == 9:
        render_financial_analysis()
    elif st.session_state.workflow_step == 10:
        render_3d_visualization()
    elif st.session_state.workflow_step == 11:
        render_reporting()
    
    # Navigation buttons
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        if st.session_state.workflow_step > 1:
            if st.button("⬅️ Previous Step"):
                st.session_state.workflow_step -= 1
                st.rerun()
    
    with col3:
        if st.session_state.workflow_step < len(steps):
            if st.button("Next Step ➡️"):
                st.session_state.workflow_step += 1
                st.rerun()

if __name__ == "__main__":
    main()
