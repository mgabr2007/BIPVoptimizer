"""
BIPV Optimizer - Clean Application Entry Point
No project selector, minimal sidebar interface
"""

import streamlit as st
import os

# Enhanced page configuration with SEO optimization
st.set_page_config(
    page_title="BIPV Optimizer - Building Integrated Photovoltaics Analysis Platform",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://www.researchgate.net/profile/Mostafa-Gabr-4',
        'Report a bug': None,
        'About': """
        # BIPV Optimizer
        
        Advanced Building-Integrated Photovoltaics optimization platform for comprehensive solar energy system analysis.
        
        **Developed by:** Mostafa Gabr  
        **Institution:** Technische Universität Berlin  
        **Research Focus:** Building-Integrated Photovoltaics Optimization
        """
    }
)

# Inject Open Graph meta tags for social media sharing
st.markdown("""
<meta property="og:title" content="BIPV Optimizer – Building Integrated Photovoltaics Analysis Platform">
<meta property="og:description" content="An AI-powered tool to evaluate, optimize, and visualize BIPV deployment scenarios for retrofitting educational buildings.">
<meta property="og:type" content="website">
<meta property="og:url" content="https://bipv-optimizer.replit.app/">
<meta property="og:site_name" content="BIPV Optimizer">
<meta property="og:locale" content="en_US">

<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="BIPV Optimizer – Building Integrated Photovoltaics Analysis Platform">
<meta name="twitter:description" content="An AI-powered tool to evaluate, optimize, and visualize BIPV deployment scenarios for retrofitting educational buildings.">
<meta name="twitter:url" content="https://bipv-optimizer.replit.app/">

<style>
    .main-header {
        font-size: 2.5rem;
        color: #2E8B57;
        text-align: center;
        margin-bottom: 2rem;
    }
</style>

<script>
// Auto-scroll to top functionality for step navigation
function scrollToTop() {
    window.scrollTo({
        top: 0,
        behavior: 'smooth'
    });
}

// Listen for step changes and scroll to top
document.addEventListener('DOMContentLoaded', function() {
    // Monitor for step navigation buttons
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.type === 'childList') {
                // Check if page content changed (step navigation occurred)
                const buttons = document.querySelectorAll('button[kind="primary"]');
                buttons.forEach(button => {
                    if (button.innerText.includes('Continue to Step') || 
                        button.innerText.includes('Next Step') ||
                        button.innerText.includes('Finish')) {
                        button.addEventListener('click', function() {
                            setTimeout(scrollToTop, 100);
                        });
                    }
                });
            }
        });
    });
    
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
});

// Also scroll to top on page load if URL fragment indicates step change
window.addEventListener('load', function() {
    if (window.location.hash || document.referrer.includes('step')) {
        setTimeout(scrollToTop, 200);
    }
});
</script>

<style>
    /* Comprehensive Yellow Theme Styling */
    .stApp {
        background: linear-gradient(135deg, #FFFEF7 0%, #FFF8DC 100%);
        color: #2F2F2F;
    }
    
    .stApp > header {
        background-color: #FFD700;
        border-bottom: 3px solid #FFA500;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background: linear-gradient(180deg, #FFD700 0%, #FFA500 100%);
    }
    
    .css-1lcbmhc {
        background: linear-gradient(180deg, #FFD700 0%, #FFA500 100%);
        border-right: 3px solid #DAA520;
    }
    
    /* Main content area */
    .main .block-container {
        background-color: rgba(255, 250, 205, 0.3);
        border-radius: 15px;
        padding: 2rem;
        box-shadow: 0 4px 20px rgba(255, 215, 0, 0.1);
    }
    
    /* Headers and titles */
    h1, h2, h3, h4, h5, h6 {
        color: #B8860B !important;
        text-shadow: 1px 1px 2px rgba(255, 215, 0, 0.3);
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(45deg, #FFD700, #FFA500);
        color: #2F2F2F;
        border: 2px solid #DAA520;
        border-radius: 10px;
        font-weight: bold;
        box-shadow: 0 4px 8px rgba(255, 165, 0, 0.3);
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        background: linear-gradient(45deg, #FFA500, #FF8C00);
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(255, 165, 0, 0.4);
    }
    
    /* Metrics */
    [data-testid="metric-container"] {
        background: linear-gradient(135deg, #FFFACD, #FFE4B5);
        border: 2px solid #FFD700;
        border-radius: 10px;
        padding: 1rem;
        box-shadow: 0 2px 8px rgba(255, 215, 0, 0.2);
    }
    
    [data-testid="metric-container"] > div > div {
        color: #B8860B !important;
    }
    
    /* Info boxes */
    .stInfo {
        background: linear-gradient(135deg, #FFE4B5, #FFFACD);
        border-left: 4px solid #FFD700;
        color: #2F2F2F;
    }
    
    .stSuccess {
        background: linear-gradient(135deg, #F0FFBF, #ADFF2F);
        border-left: 4px solid #9ACD32;
        color: #2F2F2F;
    }
    
    .stWarning {
        background: linear-gradient(135deg, #FFE4B5, #FFDAB9);
        border-left: 4px solid #FF8C00;
        color: #2F2F2F;
    }
    
    .stError {
        background: linear-gradient(135deg, #FFE4E1, #FFA07A);
        border-left: 4px solid #FF6347;
        color: #2F2F2F;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background: linear-gradient(45deg, #FFD700, #FFA500);
        color: #2F2F2F;
        border-radius: 5px;
        border: 1px solid #DAA520;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        background: linear-gradient(45deg, #FFD700, #FFA500);
        border-radius: 10px;
        padding: 5px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: rgba(255, 255, 255, 0.8);
        color: #2F2F2F;
        border-radius: 5px;
        margin: 2px;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(45deg, #FFFF00, #FFD700);
        color: #2F2F2F;
        font-weight: bold;
    }
    
    /* Progress bar */
    .stProgress > div > div > div {
        background: linear-gradient(45deg, #FFD700, #FFA500);
    }
    
    /* Selectbox and inputs */
    .stSelectbox > div > div {
        background-color: #FFFACD;
        border: 2px solid #FFD700;
        border-radius: 8px;
    }
    
    .stNumberInput > div > div {
        background-color: #FFFACD;
        border: 2px solid #FFD700;
        border-radius: 8px;
    }
    
    .stTextInput > div > div {
        background-color: #FFFACD;
        border: 2px solid #FFD700;
        border-radius: 8px;
    }
    
    /* Slider */
    .stSlider > div > div > div {
        background: linear-gradient(45deg, #FFD700, #FFA500);
    }
    
    /* Checkbox */
    .stCheckbox > label > div {
        background-color: #FFD700;
        border: 2px solid #FFA500;
    }
    
    /* DataFrame styling */
    .stDataFrame {
        border: 2px solid #FFD700;
        border-radius: 10px;
        overflow: hidden;
    }
    
    /* Custom emoji and icon styling */
    .emoji-icon {
        filter: sepia(100%) saturate(200%) hue-rotate(45deg) brightness(1.2);
    }
    
    /* Navigation styling */
    .nav-button {
        background: linear-gradient(45deg, #FFD700, #FFA500) !important;
        color: #2F2F2F !important;
        border: 2px solid #DAA520 !important;
        border-radius: 25px !important;
        padding: 0.5rem 2rem !important;
        font-weight: bold !important;
        margin: 0.5rem !important;
        box-shadow: 0 4px 12px rgba(255, 165, 0, 0.3) !important;
    }
    
    /* Sidebar text styling */
    .sidebar .markdown-text-container {
        color: #2F2F2F;
        text-shadow: 1px 1px 2px rgba(255, 255, 255, 0.5);
    }
    
    /* Custom yellow gradient backgrounds for containers */
    .yellow-container {
        background: linear-gradient(135deg, #FFFACD 0%, #FFE4B5 50%, #FFD700 100%);
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
        border: 2px solid #FFA500;
        box-shadow: 0 4px 16px rgba(255, 215, 0, 0.2);
    }
    
    /* Icon coloring */
    .st-emotion-cache-1v0mbdj > img {
        filter: sepia(100%) saturate(200%) hue-rotate(45deg) brightness(1.1);
    }
</style>

<script type="application/ld+json">
{
    "@context": "https://schema.org",
    "@type": "SoftwareApplication",
    "name": "BIPV Optimizer",
    "description": "An AI-powered tool to evaluate, optimize, and visualize BIPV deployment scenarios for retrofitting educational buildings.",
    "applicationCategory": "Engineering Software",
    "operatingSystem": "Web Browser",
    "author": {
        "@type": "Person",
        "name": "Mostafa Gabr",
        "affiliation": {
            "@type": "Organization",
            "name": "Technische Universität Berlin"
        }
    }
}
</script>
""", unsafe_allow_html=True)

# Import page modules
from pages_modules.welcome import render_welcome
from pages_modules.project_setup import render_project_setup
from pages_modules.historical_data import render_historical_data
from pages_modules.weather_environment import render_weather_environment
from pages_modules.facade_extraction import render_facade_extraction
from pages_modules.radiation_grid import render_radiation_grid
from pages_modules.pv_specification import render_pv_specification
from pages_modules.yield_demand import render_yield_demand
from pages_modules.optimization import render_optimization
from pages_modules.financial_analysis import render_financial_analysis
from pages_modules.reporting import render_reporting
from services.perplexity_agent import render_perplexity_consultation

# Import workflow visualization
from components.workflow_visualization import (
    render_workflow_progress, 
    render_compact_progress,
    render_step_completion_tracker,
    render_milestone_tracker
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
    # Add BIPV Optimizer logo to sidebar
    st.sidebar.image("attached_assets/BIPVOptiLogoLightGreen_1751289503547.png", width=200)
    st.sidebar.markdown("---")
    
    # Define workflow steps with yellow-themed emojis
    workflow_steps = [
        ("welcome", "🌞 Welcome", "Introduction to BIPV optimization"),
        ("project_setup", "📍 Project Setup", "Location and configuration"),
        ("historical_data", "📊 Historical Data", "Energy consumption analysis"),
        ("weather_environment", "🌤️ Weather Integration", "TMY and climate data"),
        ("facade_extraction", "🏢 BIM Extraction", "Building geometry analysis"),
        ("radiation_grid", "☀️ Radiation Analysis", "Solar irradiance modeling"),
        ("pv_specification", "⚡ PV Specification", "Technology selection"),
        ("yield_demand", "🔋 Yield vs Demand", "Energy balance analysis"),
        ("optimization", "🎯 Optimization", "Multi-objective optimization"),
        ("financial_analysis", "💰 Financial Analysis", "Economic viability"),
        ("reporting", "📄 Reporting", "Results and export"),
        ("ai_consultation", "🤖 AI Consultation", "Expert analysis and recommendations")
    ]
    
    # Render navigation buttons for workflow steps
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
    
    # Show current project info if available
    if 'project_data' in st.session_state and st.session_state.project_data:
        project_name = st.session_state.project_data.get('project_name', 'Unnamed Project')
        st.sidebar.markdown(f"**Current Project:** {project_name}")
        
        # AI Model Performance Status in Sidebar
        if st.session_state.project_data.get('model_r2_score') is not None:
            r2_score = st.session_state.project_data['model_r2_score']
            status = st.session_state.project_data.get('model_performance_status', 'Unknown')
            
            if r2_score >= 0.85:
                color = "green"
                icon = "🟢"
            elif r2_score >= 0.70:
                color = "orange"
                icon = "🟡"
            else:
                color = "red"
                icon = "🔴"
            
            st.sidebar.markdown(f"""
            <div style="padding: 8px; border: 2px solid {color}; border-radius: 6px; text-align: center; background: rgba(248, 249, 250, 0.9); margin: 10px 0;">
                <strong style="font-size: 12px;">{icon} AI Model R²: {r2_score:.3f}</strong><br>
                <span style="color: {color}; font-size: 10px;">{status} Performance</span>
            </div>
            """, unsafe_allow_html=True)
    
    st.sidebar.markdown("---")
    
    # Get current step for all components
    current_step = st.session_state.current_step
    
    # Add compact progress indicator to sidebar
    render_compact_progress(workflow_steps, current_step)
    
    # Check for scroll to top flag and inject JavaScript if needed
    if st.session_state.get('scroll_to_top', False):
        st.markdown("""
        <script>
        window.scrollTo({top: 0, behavior: 'smooth'});
        </script>
        """, unsafe_allow_html=True)
        st.session_state.scroll_to_top = False
    
    # Main content area with workflow visualization
    
    # Add workflow visualization toggle
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title("🏢 BIPV Optimizer")
    with col2:
        show_workflow_vis = st.toggle("Show Workflow Progress", key="workflow_vis_toggle")
    
    # Display workflow visualization if enabled
    if show_workflow_vis:
        with st.expander("🔄 Workflow Visualization", expanded=False):
            tab1, tab2, tab3 = st.tabs(["Progress Tracker", "Milestones", "Completion Status"])
            
            with tab1:
                render_workflow_progress(workflow_steps, current_step)
            
            with tab2:
                render_milestone_tracker()
            
            with tab3:
                render_step_completion_tracker()
    
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
        elif current_step == 'ai_consultation':
            render_perplexity_consultation()
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
                st.session_state.scroll_to_top = True
                st.rerun()
    
    with col2:
        # Adjust step count to exclude welcome page from numbering
        if current_step == 'welcome':
            st.markdown(f"<h4 style='text-align: center;'>Welcome</h4>", unsafe_allow_html=True)
        else:
            step_number = current_index  # current_index already accounts for welcome at position 0
            st.markdown(f"<h4 style='text-align: center;'>Step {step_number} of 11</h4>", unsafe_allow_html=True)
    
    with col3:
        if current_index < len(workflow_steps) - 1:
            next_step = workflow_steps[current_index + 1]
            if st.button(f"{next_step[1]} →", key="bottom_next_step", use_container_width=True):
                st.session_state.current_step = next_step[0]
                st.session_state.scroll_to_top = True
                st.rerun()
        elif current_step == 'ai_consultation':
            # Show finish button on the final step
            if st.button("🎯 Finish & New Calculation", key="finish_restart_bottom", use_container_width=True):
                # Reset all session state for new calculation
                for key in list(st.session_state.keys()):
                    if key != 'current_step':
                        del st.session_state[key]
                st.session_state.current_step = 'welcome'
                st.rerun()


if __name__ == "__main__":
    main()