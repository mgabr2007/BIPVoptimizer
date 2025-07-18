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
    
    /* Ensure Streamlit messages are always visible */
    .stAlert {
        display: block !important;
        visibility: visible !important;
        opacity: 1 !important;
        z-index: 999 !important;
        margin: 1rem 0 !important;
    }
    
    div[data-testid="stAlert"] {
        display: block !important;
        visibility: visible !important;
        opacity: 1 !important;
        z-index: 999 !important;
        margin: 1rem 0 !important;
    }
    
    /* Success messages - green */
    div[data-testid="stAlert"][data-baseweb="notification"] {
        background-color: #d4edda !important;
        border-color: #c3e6cb !important;
        color: #155724 !important;
    }
    
    /* Ensure alert content is visible */
    .stAlert > div {
        display: block !important;
        visibility: visible !important;
    }
    
    /* Hide ONLY download progress bars, not all alerts */
    .stProgress {
        display: none !important;
    }
    
    /* Hide Streamlit footer and branding */
    .stApp > footer {
        display: none !important;
    }
    
    /* Hide "Made with Streamlit" footer */
    footer[data-testid="stFooter"] {
        display: none !important;
    }
    
    /* Hide download status bars */
    .download-content {
        display: none !important;
    }
    
    /* Clean up file download interface */
    [data-testid="stFileDownloadButton"] + div {
        display: none !important;
    }
</style>

<script>
// Enhanced auto-scroll to banner functionality for all navigation
function scrollToTop() {
    // First try to find the page banner/header (step title with icon)
    const bannerSelectors = [
        'h1[style*="text-align: center"]',  // Main step titles
        'h1[style*="text-align:center"]',   // Main step titles (no space)
        '.step-header',                     // Custom step headers
        '[class*="step-title"]',           // Step title classes
        'div[style*="text-align: center"] h1', // Centered div with h1
        'div[style*="text-align:center"] h1',  // Centered div with h1 (no space)
        '[data-testid*="stMarkdown"] h1',   // Streamlit markdown h1
        '.main div:first-child h1',         // First h1 in main content
        'h1:first-of-type',                // First h1 on page
        '.main h1',                        // H1 in main content
        '.stMarkdown h1:first-child'       // First h1 in markdown
    ];
    
    let bannerElement = null;
    for (const selector of bannerSelectors) {
        bannerElement = document.querySelector(selector);
        if (bannerElement) break;
    }
    
    if (bannerElement) {
        // Scroll to banner with some offset to show it clearly
        const bannerRect = bannerElement.getBoundingClientRect();
        const scrollTop = window.pageYOffset + bannerRect.top - 30; // 30px offset above banner
        
        window.scrollTo({
            top: Math.max(0, scrollTop),
            behavior: 'smooth'
        });
        
        // Debug: Log which banner was found (can be removed in production)
        console.log('Scrolling to banner:', bannerElement.textContent, 'using selector:', bannerElement.tagName);
    } else {
        // Try to find any element with step numbers (like "2 HISTORICAL DATA")
        const stepElements = document.querySelectorAll('*');
        let stepBanner = null;
        
        for (const element of stepElements) {
            const text = element.textContent || '';
            if (text.match(/^\d+\s+[A-Z\s]+$/) && element.tagName === 'H1') {
                stepBanner = element;
                break;
            }
        }
        
        if (stepBanner) {
            const stepRect = stepBanner.getBoundingClientRect();
            const scrollTop = window.pageYOffset + stepRect.top - 30;
            window.scrollTo({
                top: Math.max(0, scrollTop),
                behavior: 'smooth'
            });
            console.log('Scrolling to step banner:', stepBanner.textContent);
        } else {
            // Final fallback to top if no banner found
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
            console.log('No banner found, scrolling to top');
        }
    }
    
    // Also scroll the main content container if needed
    const mainContainer = document.querySelector('.main');
    if (mainContainer) {
        // For Streamlit, usually just scrolling the window is sufficient
        // but we'll add a small delay to ensure it works
        setTimeout(() => {
            if (bannerElement) {
                bannerElement.scrollIntoView({ 
                    behavior: 'smooth', 
                    block: 'start',
                    inline: 'nearest'
                });
            }
        }, 100);
    }
}

// Listen for all button clicks and page changes
document.addEventListener('DOMContentLoaded', function() {
    // Monitor for any navigation buttons
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.type === 'childList') {
                // Find all navigation buttons and attach scroll functionality
                const allButtons = document.querySelectorAll('button');
                allButtons.forEach(button => {
                    const buttonText = button.innerText || button.textContent || '';
                    if (buttonText.includes('Continue to Step') || 
                        buttonText.includes('Next Step') ||
                        buttonText.includes('Previous Step') ||
                        buttonText.includes('→') ||
                        buttonText.includes('←') ||
                        buttonText.includes('Finish') ||
                        buttonText.includes('Start') ||
                        buttonText.includes('Begin') ||
                        buttonText.includes('Step') ||
                        buttonText.includes('Calculate') ||
                        buttonText.includes('Generate') ||
                        buttonText.includes('Upload') ||
                        buttonText.includes('Download') ||
                        buttonText.includes('Analyze') ||
                        buttonText.includes('Continue') ||
                        buttonText.includes('Process') ||
                        buttonText.includes('Save') ||
                        buttonText.includes('Load') ||
                        buttonText.includes('New') ||
                        buttonText.includes('Reset') ||
                        buttonText.includes('Complete') ||
                        buttonText.includes('Fetch') ||
                        buttonText.includes('Run') ||
                        buttonText.includes('Execute') ||
                        buttonText.includes('Optimize') ||
                        buttonText.includes('Submit') ||
                        button.closest('.stButton') ||
                        button.closest('[data-testid="stButton"]')) {
                        
                        // Remove existing listeners to prevent duplicates
                        button.removeEventListener('click', handleNavClick);
                        // Add click handler
                        button.addEventListener('click', handleNavClick);
                    }
                });
            }
        });
    });
    
    function handleNavClick() {
        // Immediate scroll for instant feedback
        scrollToTop();
        // Additional scroll after potential content change
        setTimeout(scrollToTop, 50);
        setTimeout(scrollToTop, 150);
        setTimeout(scrollToTop, 300);
    }
    
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
    
    // Initial setup for existing buttons
    handleNavClick();
});

// Scroll to top on any page change or rerun
window.addEventListener('load', scrollToTop);
window.addEventListener('beforeunload', scrollToTop);

// Handle Streamlit reruns and auto-scroll for any major content changes
setInterval(function() {
    const buttons = document.querySelectorAll('button');
    let hasNavButton = false;
    buttons.forEach(button => {
        const text = button.innerText || button.textContent || '';
        if (text.includes('→') || text.includes('←') || text.includes('Continue') || 
            text.includes('Step') || text.includes('Calculate') || text.includes('Generate') ||
            text.includes('Upload') || text.includes('Download') || text.includes('Analyze') ||
            text.includes('Process') || text.includes('Save') || text.includes('Load') ||
            text.includes('New') || text.includes('Reset') || text.includes('Complete') ||
            text.includes('Fetch') || text.includes('Run') || text.includes('Execute') ||
            text.includes('Optimize') || text.includes('Submit') || text.includes('Start') ||
            text.includes('Finish') || text.includes('Begin')) {
            hasNavButton = true;
            // Ensure click handler is attached
            button.removeEventListener('click', handleGlobalNavClick);
            button.addEventListener('click', handleGlobalNavClick);
        }
    });
    
    // Auto-scroll if user seems to be navigating (scroll position > 100px and nav buttons exist)
    if (hasNavButton && window.scrollY > 100) {
        // Check if content has changed recently (indicates page transition)
        const currentContent = document.querySelector('.main').innerHTML.length;
        if (window.lastContentLength && currentContent !== window.lastContentLength) {
            scrollToTop();
        }
        window.lastContentLength = currentContent;
    }
}, 500);

// Global navigation click handler
function handleGlobalNavClick() {
    scrollToTop();
    setTimeout(scrollToTop, 100);
    setTimeout(scrollToTop, 300);
    setTimeout(scrollToTop, 500);
}

// Universal button click handler - make ALL buttons scroll to top
document.addEventListener('click', function(event) {
    // Check if clicked element is a button or inside a button
    const button = event.target.closest('button') || 
                   event.target.closest('.stButton button') ||
                   event.target.closest('[data-testid="stButton"] button');
    
    if (button) {
        // Small delay to allow Streamlit to process the click first
        setTimeout(function() {
            scrollToTop();
        }, 10);
        
        // Additional scrolls to handle page transitions
        setTimeout(scrollToTop, 100);
        setTimeout(scrollToTop, 300);
        setTimeout(scrollToTop, 600);
    }
}, true); // Use capture phase to catch all button clicks
</script>

<style>
    /* Comprehensive Yellow Theme Styling */
    .stApp {
        background: linear-gradient(135deg, #FFFEF7 0%, #FFF8DC 100%);
        color: #2F2F2F;
    }
    
    .stApp > header {
        display: none;
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
from pages_modules.pv_specification_unified import render_pv_specification
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



# Initialize database-driven state management
from services.database_state_manager import db_state_manager
from services.io import get_current_project_id

# Ensure database connectivity and project context
current_project_id = get_current_project_id()

# Database-driven project management
if current_project_id:
    st.sidebar.success(f"Project ID: {current_project_id}")
else:
    st.sidebar.info("No active project - start with Step 1")

# Database-driven completion tracking (no session state needed)


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
    
    # Get current step from URL parameters or default to welcome
    current_step = st.query_params.get('step', 'welcome')
    
    # Render navigation buttons for workflow steps
    for i, (step_key, step_name, description) in enumerate(workflow_steps):
        is_current = current_step == step_key
        
        if is_current:
            st.sidebar.markdown(f"**▶️ {step_name}**")
            st.sidebar.caption(f"*Current: {description}*")
        else:
            if st.sidebar.button(step_name, key=f"nav_{step_key}_{i}", use_container_width=True):
                st.query_params['step'] = step_key
                st.rerun()
            st.sidebar.caption(description)
        
        # Add small spacing between buttons
        if i < len(workflow_steps) - 1:
            st.sidebar.write("")
    
    st.sidebar.markdown("---")
    
    # Show current project info from database
    if current_project_id:
        from database_manager import db_manager
        project_data = db_manager.get_project_by_id(current_project_id)
        if project_data:
            project_name = project_data.get('project_name', 'Unnamed Project')
            st.sidebar.markdown(f"**Current Project:** {project_name}")
            
            # AI Model Performance Status from database
            historical_data = db_state_manager.get_step_data('historical_data')
            if historical_data and historical_data.get('model_r2_score') is not None:
                r2_score = historical_data['model_r2_score']
                status = historical_data.get('model_performance_status', 'Unknown')
                
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
    
    # Add compact progress indicator to sidebar
    render_compact_progress(workflow_steps, current_step)
    
    # Enhanced scroll-to-top functionality
    st.markdown("""
        <script>
        window.scrollTo({top: 0, behavior: 'smooth'});
        </script>
        """, unsafe_allow_html=True)
    
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
    from utils.individual_step_reports import create_step_download_button
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        # Find current step index
        current_index = next((i for i, (key, _, _) in enumerate(workflow_steps) if key == current_step), 0)
        if current_index > 0:
            prev_step = workflow_steps[current_index - 1]
            if st.button(f"← {prev_step[1]}", key="bottom_prev_step", use_container_width=True):
                st.query_params['step'] = prev_step[0]
                st.rerun()
    
    with col2:
        # Adjust step count to exclude welcome page from numbering
        if current_step == 'welcome':
            st.markdown(f"<h4 style='text-align: center;'>Welcome</h4>", unsafe_allow_html=True)
        else:
            step_number = current_index  # current_index already accounts for welcome at position 0
            st.markdown(f"<h4 style='text-align: center;'>Step {step_number} of 11</h4>", unsafe_allow_html=True)
    
    with col3:
        # Show download button for completed analysis steps or navigation for others
        if current_step == 'welcome':
            # Welcome page - no navigation button
            st.empty()
        elif current_step == 'reporting':
            # Last step - show new calculation button
            if st.button("🔄 New Analysis", key="bottom_new_calc", use_container_width=True):
                st.query_params['step'] = 'welcome'
                st.rerun()
        elif current_step in ['project_setup', 'historical_data', 'weather_environment', 'facade_extraction', 'radiation_grid', 'pv_specification', 'yield_demand', 'optimization', 'financial_analysis']:
            # Analysis steps - show download report button
            step_names = {
                'project_setup': ('Project Setup', 1),
                'historical_data': ('Historical Data', 2),
                'weather_environment': ('Weather Environment', 3),
                'facade_extraction': ('Facade Extraction', 4),
                'radiation_grid': ('Radiation Analysis', 5),
                'pv_specification': ('PV Specification', 6),
                'yield_demand': ('Yield vs Demand', 7),
                'optimization': ('Optimization', 8),
                'financial_analysis': ('Financial Analysis', 9)
            }
            
            if current_step in step_names:
                # Find next step for navigation
                current_index = next((i for i, (key, _, _) in enumerate(workflow_steps) if key == current_step), 0)
                if current_index < len(workflow_steps) - 1:
                    next_step = workflow_steps[current_index + 1]
                    if st.button(f"Continue →", key=f"bottom_continue_nav", use_container_width=True):
                        db_state_manager.set_current_step(next_step[0])
                        st.rerun()
                else:
                    if st.button("🎯 Complete Analysis", key=f"bottom_complete_nav", use_container_width=True):
                        db_state_manager.set_current_step('reporting')
                        st.rerun()
        elif current_step == 'ai_consultation':
            # Show finish button on the final step
            if st.button("🎯 Finish & New Calculation", key="finish_restart_bottom", use_container_width=True):
                # Clear current project context and return to welcome
                db_state_manager.set_current_step('welcome')
                st.rerun()
        else:
            # Other steps - show next navigation
            if current_index < len(workflow_steps) - 1:
                next_step = workflow_steps[current_index + 1]
                if st.button(f"{next_step[1]} →", key="bottom_next_step", use_container_width=True):
                    db_state_manager.set_current_step(next_step[0])
                    st.rerun()


if __name__ == "__main__":
    main()