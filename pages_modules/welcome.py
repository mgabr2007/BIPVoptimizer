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
    photovoltaic glass that generates electricity while maintaining natural lighting. This platform 
    analyzes building geometry to identify suitable window types for BIPV installation, considering 
    historical significance and architectural constraints. Project configuration allows analysis of 
    optimal orientations (South/East/West) or all orientations including North-facing facades.
    
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
    **4. Window Selection** - BIM extraction and window type filtering for BIPV suitability  
    **5. Radiation Analysis** - Solar irradiance and shading calculations for selected windows  
    **6. PV Specification** - BIPV technology selection for selected window types  
    **7. Yield vs Demand** - Energy balance analysis for selected windows  
    **8. Optimization** - Multi-objective genetic algorithm optimization  
    **9. Financial Analysis** - Economic viability analysis for selected windows  
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
        **For Step 4 - Window Selection & BIM Data Upload**
        
        Dynamo script to extract window elements from Revit:
        - Element IDs and orientations
        - Glass areas and window family types
        - Building levels and wall relationships
        - Window type filtering for BIPV suitability
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
    
    # External Dependencies section
    st.markdown("---")
    st.subheader("🔧 External Dependencies & Technologies")
    
    st.markdown("""
    The BIPV Optimizer platform is built on a comprehensive stack of leading technologies and external services 
    to ensure professional-grade analysis and reliable data sources:
    """)
    
    # Create tabs for different dependency categories
    dep_tab1, dep_tab2, dep_tab3, dep_tab4 = st.tabs([
        "🧮 Core Framework", "🔬 Scientific Computing", "🗄️ Data & APIs", "📊 Visualization & Reports"
    ])
    
    with dep_tab1:
        st.markdown("""
        **Web Framework & Data Processing:**
        - **Streamlit** - Interactive web application framework
        - **Pandas** - High-performance data manipulation and analysis
        - **NumPy** - Fundamental package for scientific computing
        - **PostgreSQL** - Robust relational database for data persistence
        
        **Data Validation & Quality:**
        - **Pydantic** - Data validation using Python type annotations
        - **Pandera** - Statistical data testing toolkit
        - **Great Expectations** - Data quality and validation framework
        """)
    
    with dep_tab2:
        st.markdown("""
        **Solar Energy & Optimization:**
        - **pvlib** - Professional solar position and irradiance modeling
        - **DEAP** - Distributed Evolutionary Algorithms (NSGA-II genetic optimization)
        - **scikit-learn** - Machine learning library for demand prediction models
        
        **Weather & Environmental:**
        - **pytz** - World timezone definitions and conversions
        - **ISO 15927-4** - International standards for climatic data
        """)
    
    with dep_tab3:
        st.markdown("""
        **External Data Sources:**
        - **OpenWeatherMap API** - Global weather data and forecasting
        - **TU Berlin Climate Portal** - Academic-grade meteorological data for Germany
        - **German SMARD** - Official electricity market data (Germany)
        - **UK Ofgem** - UK electricity rates and grid information
        - **US EIA** - U.S. Energy Information Administration data
        - **EU Eurostat** - European Union statistical data
        
        **AI & Research Integration:**
        - **Perplexity AI** - Advanced AI for research consultation and literature analysis
        """)
    
    with dep_tab4:
        st.markdown("""
        **Interactive Visualization:**
        - **Plotly** - Professional interactive charts and 3D visualizations
        - **Folium** - Interactive maps and geographical analysis
        - **Kaleido** - Static image export for scientific publications
        
        **Report Generation:**
        - **ReportLab** - PDF generation with professional formatting
        - **python-docx** - Microsoft Word document creation
        - **openpyxl** - Excel spreadsheet processing and export
        """)

    # Important notes section
    st.markdown("---")
    st.warning("""
    **Important Workflow Requirements:**
    
    • **Step 1 (Project Setup)** - Configure facade orientation analysis (optimal S/E/W or all orientations)
    • **Step 4 (Window Selection) is MANDATORY** - Window type filtering for BIPV suitability is required
    • **Historical significance filtering** - Some windows cannot be replaced due to heritage constraints
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
    
    # Powered by section
    st.markdown("---")
    st.markdown("### 🚀 Powered by Leading Technologies")
    
    st.markdown("""
    <div style="text-align: center; margin: 20px 0; background-color: #f8f9fa; padding: 20px; border-radius: 10px;">
        <h4 style="margin-bottom: 25px; color: #2E8B57;">Key Scientific Computing Libraries</h4>
    </div>
    """, unsafe_allow_html=True)
    
    # Display the three main technology logos in columns
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        st.image("attached_assets/pvlib_powered_logo_horiz.png", 
                caption="Professional solar position and irradiance modeling", 
                use_container_width=True)
        st.markdown("""
        <div style="text-align: center; margin-top: 10px; padding: 10px; background: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <strong>pvlib</strong><br>
            <small style="color: #666;">Solar Energy Modeling & Analysis</small>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.image("attached_assets/scikit_learn_logo.png", 
                caption="Machine learning library for demand prediction models", 
                use_container_width=True)
        st.markdown("""
        <div style="text-align: center; margin-top: 10px; padding: 10px; background: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <strong>scikit-learn</strong><br>
            <small style="color: #666;">Machine Learning & AI Prediction</small>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        # Since DEAP doesn't have a logo, create a custom text-based design
        st.markdown("""
        <div style="text-align: center; padding: 40px 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    border-radius: 10px; margin-bottom: 10px; color: white;">
            <div style="font-size: 2.5em; margin-bottom: 10px;">🧬</div>
            <div style="font-size: 1.5em; font-weight: bold;">DEAP</div>
            <div style="font-size: 0.9em; opacity: 0.9;">Evolutionary Algorithms</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("""
        <div style="text-align: center; margin-top: 10px; padding: 10px; background: white; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <strong>DEAP</strong><br>
            <small style="color: #666;">Distributed Evolutionary Algorithms (NSGA-II)</small>
        </div>
        """, unsafe_allow_html=True)
    
    # Additional supporting technologies section
    st.markdown("""
    <div style="text-align: center; margin: 30px 0 20px 0; background-color: #f8f9fa; padding: 20px; border-radius: 10px;">
        <h5 style="margin-bottom: 15px; color: #2E8B57;">Supporting Technologies & APIs</h5>
        
        <div style="display: flex; flex-wrap: wrap; justify-content: center; gap: 12px; align-items: center; margin: 20px 0;">
            <div style="display: flex; align-items: center; background: white; padding: 6px 10px; border-radius: 6px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); font-size: 0.85em;">
                <span style="margin-right: 6px;">🎯</span><strong>Streamlit</strong>
            </div>
            <div style="display: flex; align-items: center; background: white; padding: 6px 10px; border-radius: 6px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); font-size: 0.85em;">
                <span style="margin-right: 6px;">🐼</span><strong>Pandas</strong>
            </div>
            <div style="display: flex; align-items: center; background: white; padding: 6px 10px; border-radius: 6px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); font-size: 0.85em;">
                <span style="margin-right: 6px;">🔢</span><strong>NumPy</strong>
            </div>
            <div style="display: flex; align-items: center; background: white; padding: 6px 10px; border-radius: 6px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); font-size: 0.85em;">
                <span style="margin-right: 6px;">🗄️</span><strong>PostgreSQL</strong>
            </div>
            <div style="display: flex; align-items: center; background: white; padding: 6px 10px; border-radius: 6px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); font-size: 0.85em;">
                <span style="margin-right: 6px;">📊</span><strong>Plotly</strong>
            </div>
            <div style="display: flex; align-items: center; background: white; padding: 6px 10px; border-radius: 6px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); font-size: 0.85em;">
                <span style="margin-right: 6px;">🗺️</span><strong>Folium</strong>
            </div>
            <div style="display: flex; align-items: center; background: white; padding: 6px 10px; border-radius: 6px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); font-size: 0.85em;">
                <span style="margin-right: 6px;">🌤️</span><strong>OpenWeather API</strong>
            </div>
            <div style="display: flex; align-items: center; background: white; padding: 6px 10px; border-radius: 6px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); font-size: 0.85em;">
                <span style="margin-right: 6px;">🔮</span><strong>Perplexity AI</strong>
            </div>
            <div style="display: flex; align-items: center; background: white; padding: 6px 10px; border-radius: 6px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); font-size: 0.85em;">
                <span style="margin-right: 6px;">🏛️</span><strong>TU Berlin Portal</strong>
            </div>
        </div>
        
        <div style="margin-top: 15px; font-size: 0.85em; color: #666; font-style: italic;">
            Professional research platform integrating leading open-source and commercial technologies<br>
            for comprehensive BIPV analysis and optimization
        </div>
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