"""
Welcome page for BIPV Optimizer
"""
import streamlit as st
import uuid
import datetime
from utils.color_schemes import get_emoji, create_colored_html, YELLOW_SCHEME
from services.database_state_manager import db_state_manager


def render_welcome():
    """Render the welcome and introduction page"""
    
    # Main banner
    st.markdown("""
    <div style="background: linear-gradient(135deg, #2E8B57 0%, #228B22 50%, #32CD32 100%); 
                padding: 20px; border-radius: 10px; text-align: center; margin-bottom: 20px;">
        <h1 style="color: white; margin: 0; font-size: 2.2em;">
            BIPV Optimizer Platform
        </h1>
        <p style="color: white; font-size: 1.1em; margin: 5px 0 0 0;">
            Building-Integrated Photovoltaics Analysis & Optimization
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    ### What is BIPV?
    
    **Building-Integrated Photovoltaics (BIPV)** replaces conventional windows with semi-transparent 
    photovoltaic glass that generates electricity while maintaining natural lighting.
    
    ### Key Platform Features
    
    • **AI-Powered Analysis** - Machine learning for energy demand prediction  
    • **Multi-Objective Optimization** - Genetic algorithms for optimal BIPV placement  
    • **Real Weather Data** - TMY generation from actual meteorological stations  
    • **BIM Integration** - Direct Revit model processing with Dynamo scripts  
    • **Financial Modeling** - 25-year NPV, IRR, and payback analysis  
    • **Standards Compliance** - ISO 15927-4, ASHRAE 90.1, IEC 61853  
    
    ### Complete 11-Step Analysis Workflow
    
    **1. Project Setup** - Location selection and project configuration  
    **2. Historical Data** - Energy consumption analysis and AI model training  
    **3. Weather Integration** - TMY data generation and climate analysis  
    **4. BIM Extraction** - Building geometry and window element analysis  
    **5. Radiation Analysis** - Solar irradiance and shading calculations  
    **6. PV Specification** - BIPV technology selection and system design  
    **7. Yield vs Demand** - Energy balance and grid interaction analysis  
    **8. Optimization** - Multi-objective genetic algorithm optimization  
    **9. Financial Analysis** - Economic viability and investment analysis  
    **10. Reporting** - Comprehensive analysis reports and data export  
    **11. AI Consultation** - Expert analysis and optimization recommendations
    """)
    
    # Sample Files Section
    st.markdown("---")
    st.subheader("📁 Sample Files for Your Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Historical Energy Data Sample**")
        st.info("""
        **For Step 2 - Historical Data Upload**
        
        Required CSV format with columns:
        - Date (YYYY-MM-DD)
        - Consumption (kWh)
        - Temperature, Humidity, Solar_Irradiance, Occupancy (optional)
        """)
        
        # Download sample energy data
        with open("attached_assets/TUB_H_Building_EnergyWeather_Occupancy_1752240159032.csv", "r") as f:
            csv_data = f.read()
        
        st.download_button(
            label="📊 Download Sample Energy Data",
            data=csv_data,
            file_name="Sample_Building_Energy_Data.csv",
            mime="text/csv",
            help="Use this as a template for your building's historical energy consumption data"
        )
    
    with col2:
        st.markdown("**Building Elements Extraction**")
        st.info("""
        **For Step 4 - BIM Data Upload**
        
        Dynamo script to extract window elements from Revit:
        - Element IDs and orientations
        - Glass areas and dimensions
        - Building levels and wall relationships
        """)
        
        # Download Dynamo script
        with open("attached_assets/get windowMetadata_1752240238047.dyn", "r") as f:
            dyn_data = f.read()
        
        st.download_button(
            label="🔧 Download Dynamo Script",
            data=dyn_data,
            file_name="Extract_Window_Metadata.dyn",
            mime="application/json",
            help="Revit Dynamo script to extract building window data for BIPV analysis"
        )
    
    # Important notes section
    st.markdown("---")
    st.warning("""
    **Important Workflow Requirements:**
    
    • **Step 4 (BIM Extraction) is MANDATORY** - All subsequent analysis steps require building element data
    • **Steps must be completed in sequence** - Each step builds on previous results
    • **Use sample files above** as templates for your data uploads
    """)
    
    # Ready to start section
    st.markdown("---")
    st.markdown("### 🚀 Start Your BIPV Analysis")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        if st.button("🔬 Start New Analysis", key="start_analysis_btn", use_container_width=True, type="primary"):
            # Generate unique project name with timestamp
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            project_name = f"BIPV_Analysis_{timestamp}"
            
            # Create initial project record in database
            from services.io import save_project_data
            
            initial_project_data = {
                'project_name': project_name,
                'location': 'TBD',
                'coordinates': {'lat': 0, 'lon': 0},
                'timezone': 'UTC',
                'currency': 'EUR',
                'setup_complete': False,
                'weather_api_choice': 'auto',
                'location_method': 'map',
                'search_radius': 500
            }
            
            # Save to database and get project ID
            project_id = save_project_data(initial_project_data)
            
            if project_id:
                # Clear any existing project session state to ensure clean start
                if 'project_data' in st.session_state:
                    del st.session_state.project_data
                if 'project_id' in st.session_state:
                    del st.session_state.project_id
                if 'project_name' in st.session_state:
                    del st.session_state.project_name
                
                # Set the new project as current
                st.session_state.project_id = project_id
                st.session_state.project_name = project_name
                st.session_state.project_data = initial_project_data
                st.session_state.project_data['project_id'] = project_id
                
                # Save project data to database state manager
                db_state_manager.save_step_data('project_setup', initial_project_data)
                
                # Navigate to Step 1 using query parameters
                st.query_params['step'] = 'project_setup'
                
                # Success message and redirect
                st.success(f"✅ New project created: **{project_name}** (ID: {project_id})")
                st.info("📋 Redirecting to Step 1: Project Setup...")
                st.rerun()
            else:
                st.error("Failed to create project in database. Please try again.")
    
    st.markdown("""
    <div style="text-align: center; margin-top: 10px; color: #666; font-size: 0.9em;">
        Each analysis creates a unique project ID for independent calculations
    </div>
    """, unsafe_allow_html=True)
    
    # Research attribution (footer)
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; padding: 10px; background-color: #f0f2f6; border-radius: 5px; margin-top: 20px;">
        <small>
        <strong>Research Platform</strong><br>
        Developed by Mostafa Gabr | Technische Universität Berlin<br>
        <a href="https://www.researchgate.net/profile/Mostafa-Gabr-4" target="_blank">ResearchGate Profile</a>
        </small>
    </div>
    """, unsafe_allow_html=True)