"""
Welcome page for BIPV Optimizer
"""
import streamlit as st
import uuid
import datetime
from utils.color_schemes import get_emoji, create_colored_html, YELLOW_SCHEME
from services.database_state_manager import db_state_manager
from pages_modules.logo_assets import SCIKIT_LEARN_LOGO, PVLIB_LOGO


def render_welcome():
    """Render the welcome and introduction page"""
    
    # Main banner with enhanced styling
    st.markdown("""
    <div style="background: linear-gradient(135deg, #2E8B57 0%, #228B22 50%, #32CD32 100%); 
                padding: 30px 20px; border-radius: 15px; text-align: center; margin-bottom: 30px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
        <h1 style="color: white; margin: 0; font-size: 2.5em; font-weight: 700;">
            ☀️ BIPV Optimizer Platform
        </h1>
        <p style="color: #e6ffe6; font-size: 1.2em; margin: 10px 0 0 0; font-weight: 400;">
            Building-Integrated Photovoltaics Analysis & Optimization
        </p>
        <p style="color: #ccffcc; font-size: 0.95em; margin: 8px 0 0 0;">
            Research Platform | Technische Universität Berlin
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Introduction section with better formatting
    col1, col2 = st.columns([3, 2])
    
    with col1:
        st.markdown("""
        ### 🏢 What is BIPV?
        
        **Building-Integrated Photovoltaics (BIPV)** replaces conventional windows with semi-transparent 
        photovoltaic glass that generates electricity while maintaining natural lighting. This platform 
        analyzes building geometry to identify suitable window types for BIPV installation, considering 
        historical significance and architectural constraints.
        
        **Intelligent Window Selection:** Project configuration allows analysis of optimal orientations 
        (South/East/West) or all orientations including North-facing facades based on your building's 
        specific requirements.
        """)
    
    with col2:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    padding: 25px; border-radius: 12px; color: white; margin-top: 20px;">
            <h4 style="color: white; margin-top: 0;">🎯 Platform Capabilities</h4>
            <ul style="margin: 0; padding-left: 20px;">
                <li>AI-powered energy prediction</li>
                <li>Multi-objective optimization</li>
                <li>Real TMY weather data</li>
                <li>25-year financial analysis</li>
                <li>ISO/ASHRAE compliance</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    
    # Key Features with enhanced visual cards
    st.markdown("---")
    st.markdown("### ⚡ Key Platform Features")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div style="background: #f0f7ff; padding: 20px; border-radius: 10px; border-left: 4px solid #2196F3; height: 180px;">
            <h4 style="color: #1976D2; margin-top: 0;">🤖 AI-Powered Analysis</h4>
            <p style="margin: 0; font-size: 0.9em;">Machine learning for energy demand prediction using RandomForestRegressor with R² performance tracking</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="background: #fff3e0; padding: 20px; border-radius: 10px; border-left: 4px solid #FF9800; height: 180px;">
            <h4 style="color: #F57C00; margin-top: 0;">🧬 Multi-Objective Optimization</h4>
            <p style="margin: 0; font-size: 0.9em;">NSGA-II genetic algorithms optimize cost, energy yield, and ROI for optimal BIPV placement</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div style="background: #e8f5e9; padding: 20px; border-radius: 10px; border-left: 4px solid #4CAF50; height: 180px;">
            <h4 style="color: #388E3C; margin-top: 0;">☁️ Real Weather Data</h4>
            <p style="margin: 0; font-size: 0.9em;">ISO 15927-4 compliant TMY generation from actual meteorological stations with multi-source validation</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div style="background: #fce4ec; padding: 20px; border-radius: 10px; border-left: 4px solid #E91E63; height: 180px;">
            <h4 style="color: #C2185B; margin-top: 0;">🏗️ BIM Integration</h4>
            <p style="margin: 0; font-size: 0.9em;">Direct Revit model processing with Dynamo scripts for accurate building element extraction</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div style="background: #f3e5f5; padding: 20px; border-radius: 10px; border-left: 4px solid #9C27B0; height: 180px;">
            <h4 style="color: #7B1FA2; margin-top: 0;">💰 Financial Modeling</h4>
            <p style="margin: 0; font-size: 0.9em;">Comprehensive 25-year NPV, IRR, payback analysis with sensitivity testing and cash flow projections</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div style="background: #e0f2f1; padding: 20px; border-radius: 10px; border-left: 4px solid #009688; height: 180px;">
            <h4 style="color: #00796B; margin-top: 0;">✅ Standards Compliance</h4>
            <p style="margin: 0; font-size: 0.9em;">ISO 15927-4, ASHRAE 90.1, IEC 61853 certified methodologies for research-grade accuracy</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Complete 11-Step Workflow with enhanced visual presentation
    st.markdown("---")
    st.markdown("### 🔄 Complete 11-Step Analysis Workflow")
    
    st.markdown("""
    <div style="background: linear-gradient(to right, #f8f9fa, #e9ecef); padding: 25px; border-radius: 12px; margin: 20px 0;">
    """, unsafe_allow_html=True)
    
    # Display workflow steps in organized sections
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **📍 Steps 1-6: Setup & Analysis**
        
        **1. Project Setup**  
        🗺️ Location selection and project configuration
        
        **2. Historical Data**  
        📊 Energy consumption analysis and AI model training
        
        **3. Weather Integration**  
        ☁️ TMY data generation and climate analysis
        
        **4. Window Selection**  
        🪟 BIM extraction and window type filtering for BIPV suitability
        
        **5. Radiation Analysis**  
        ☀️ Solar irradiance and shading calculations for selected windows
        
        **6. PV Specification**  
        ⚡ BIPV technology selection for selected window types
        """)
    
    with col2:
        st.markdown("""
        **📈 Steps 7-11: Optimization & Results**
        
        **7. Yield vs Demand**  
        📉 Energy balance analysis for selected windows
        
        **8. Optimization**  
        🧬 Multi-objective genetic algorithm optimization
        
        **9. Financial Analysis**  
        💰 Economic viability analysis for selected windows
        
        **10. Reporting**  
        📄 Comprehensive analysis reports and data export
        
        **11. AI Consultation** ✨  
        🤖 Expert analysis and optimization recommendations
        """)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Sample Files Section with enhanced styling
    st.markdown("---")
    st.markdown("### 📁 Sample Files for Your Analysis")
    st.markdown("Download these templates to get started with your BIPV analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div style="background: #e3f2fd; padding: 20px; border-radius: 10px; margin-bottom: 15px;">
            <h4 style="color: #1565C0; margin-top: 0;">📊 Historical Energy Data Sample</h4>
        </div>
        """, unsafe_allow_html=True)
        
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
            label="📥 Download Sample Energy Data",
            data=csv_data,
            file_name="Sample_Building_Energy_Data.csv",
            mime="text/csv",
            help="Use this as a template for your building's historical energy consumption data",
            use_container_width=True
        )
    
    with col2:
        st.markdown("""
        <div style="background: #f3e5f5; padding: 20px; border-radius: 10px; margin-bottom: 15px;">
            <h4 style="color: #6A1B9A; margin-top: 0;">🔧 Building Elements Extraction</h4>
        </div>
        """, unsafe_allow_html=True)
        
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
            label="📥 Download Dynamo Script",
            data=dyn_data,
            file_name="Extract_Window_Metadata.dyn",
            mime="application/json",
            help="Revit Dynamo script to extract building window data for BIPV analysis",
            use_container_width=True
        )
    
    # External Dependencies section with improved tabs
    st.markdown("---")
    st.markdown("### 🔧 External Dependencies & Technologies")
    
    st.markdown("""
    <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
        The BIPV Optimizer platform is built on a comprehensive stack of leading technologies and external services 
        to ensure professional-grade analysis and reliable data sources.
    </div>
    """, unsafe_allow_html=True)
    
    # Create tabs for different dependency categories
    dep_tab1, dep_tab2, dep_tab3, dep_tab4 = st.tabs([
        "🧮 Core Framework", "🔬 Scientific Computing", "🗄️ Data & APIs", "📊 Visualization & Reports"
    ])
    
    with dep_tab1:
        st.markdown("""
        #### Web Framework & Data Processing
        
        - **Streamlit (1.46.0+)** - Interactive web application framework with enhanced UI components
        - **Pandas (2.0.3)** - High-performance data manipulation and analysis
        - **NumPy (1.24.4)** - Fundamental package for scientific computing with stable version compatibility
        - **PostgreSQL (16)** - Robust relational database for comprehensive data persistence
        
        #### Data Validation & Quality Assurance
        
        - **Pydantic (2.11.7+)** - Data validation using Python type annotations
        - **Pandera (0.25.0+)** - Statistical data testing toolkit for DataFrame validation
        - **Great Expectations (0.18.22+)** - Data quality validation and monitoring framework
        - **Loguru (0.7.3+)** - Advanced logging with structured output for debugging
        """)
    
    with dep_tab2:
        st.markdown("""
        #### Solar Energy & Optimization
        
        - **pvlib (0.13.0+)** - Professional solar position and irradiance modeling for BIPV analysis
        - **DEAP (1.4.3+)** - Distributed Evolutionary Algorithms (NSGA-II genetic optimization)
        - **scikit-learn (1.7.0+)** - Machine learning library with RandomForestRegressor for demand prediction
        
        #### Weather & Environmental Analysis
        
        - **pytz (2025.2+)** - Comprehensive world timezone definitions and conversions
        - **ISO 15927-4** - International standards compliance for climatic data analysis
        - **ASHRAE 90.1** - Energy standards for building design and analysis
        - **IEC 61853** - PV module performance testing and energy rating standards
        """)
    
    with dep_tab3:
        st.markdown("""
        #### External Data Sources
        
        **Weather & Climate Data:**
        - **OpenWeatherMap API** - Global weather data and meteorological forecasting
        - **TU Berlin Climate Portal** - Academic-grade meteorological data for Germany
        
        **Electricity Market Data:**
        - **German SMARD** - Official electricity market data (Germany)
        - **UK Ofgem** - UK electricity rates and grid information
        - **US EIA** - U.S. Energy Information Administration data
        - **EU Eurostat** - European Union statistical data for energy markets
        
        #### AI & Research Integration
        
        - **Perplexity AI** - Advanced AI for research consultation and academic literature analysis
        - **Web Scraping Tools** - Trafilatura & BeautifulSoup4 for data extraction
        """)
    
    with dep_tab4:
        st.markdown("""
        #### Interactive Visualization
        
        - **Plotly (6.1.2+)** - Professional interactive charts and 3D visualizations
        - **Folium (0.20.0+)** - Interactive maps and geographical analysis
        - **Streamlit-Folium (0.25.0+)** - Seamless integration of Folium maps in Streamlit
        - **Kaleido (1.0.0+)** - Static image export for scientific publications
        
        #### Report Generation & Export
        
        - **ReportLab (4.4.3+)** - PDF generation with professional formatting
        - **python-docx (1.2.0+)** - Microsoft Word document creation for comprehensive reports
        - **openpyxl (3.1.5+)** - Excel spreadsheet processing and export capabilities
        - **Streamlit-Extras (0.7.5+)** - Extended Streamlit components for enhanced reporting
        """)

    # Important notes section with better formatting
    st.markdown("---")
    st.markdown("""
    <div style="background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%); 
                padding: 25px; border-radius: 12px; border-left: 5px solid #ffc107;">
        <h4 style="color: #856404; margin-top: 0;">⚠️ Important Workflow Requirements</h4>
        <ul style="color: #856404; margin: 0;">
            <li><strong>Step 1 (Project Setup)</strong> - Configure facade orientation analysis (optimal S/E/W or all orientations including North)</li>
            <li><strong>Step 4 (Window Selection) is MANDATORY</strong> - Window type filtering for BIPV suitability is required before radiation analysis</li>
            <li><strong>Historical significance filtering</strong> - Some windows cannot be replaced due to heritage constraints</li>
            <li><strong>Sequential workflow</strong> - Each step builds on previous results; complete steps in order for accurate analysis</li>
            <li><strong>Use sample files above</strong> as templates for your data uploads to ensure compatibility</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # Ready to start section with enhanced CTA
    st.markdown("---")
    st.markdown("### 🚀 Ready to Start Your BIPV Analysis?")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("""
        <div style="text-align: center; margin-bottom: 20px;">
            <p style="font-size: 1.05em; color: #555;">
                Begin your comprehensive BIPV analysis with a new project. Each analysis creates a unique project ID 
                for independent calculations and data persistence.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
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
    
    # Powered by section with technology logos
    st.markdown("---")
    st.markdown("### 🚀 Powered by Leading Technologies")
    
    st.markdown("""
    <div style="text-align: center; margin: 25px 0; background: linear-gradient(to right, #f8f9fa, #e9ecef); 
                padding: 20px; border-radius: 10px;">
        <h4 style="margin-bottom: 25px; color: #2E8B57;">Key Scientific Computing Libraries</h4>
    </div>
    """, unsafe_allow_html=True)
    
    # Display the three main technology logos in columns ordered by workflow usage
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Step 2: scikit-learn for AI model training and demand prediction
        st.markdown(f"""
        <div style="background: white; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); 
                    padding: 30px 20px; text-align: center; height: 180px; display: flex; align-items: center; 
                    justify-content: center; margin-bottom: 15px;">
            <img src="{SCIKIT_LEARN_LOGO}" width="140" style="max-width: 100%; height: auto;">
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div style="text-align: center; padding: 15px; background: linear-gradient(135deg, #FF9A56 0%, #FF6B6B 100%); 
                    border-radius: 8px; color: white;">
            <strong style="font-size: 1.1em;">scikit-learn</strong><br>
            <small>Machine Learning & AI Prediction</small><br>
            <small style="opacity: 0.9;">Step 2: Energy Demand Forecasting</small>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        # Steps 3,5,6,7: pvlib for solar energy modeling
        st.markdown(f"""
        <div style="background: white; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); 
                    padding: 30px 20px; text-align: center; height: 180px; display: flex; align-items: center; 
                    justify-content: center; margin-bottom: 15px;">
            <img src="{PVLIB_LOGO}" width="140" style="max-width: 100%; height: auto;">
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div style="text-align: center; padding: 15px; background: linear-gradient(135deg, #56CCF2 0%, #2F80ED 100%); 
                    border-radius: 8px; color: white;">
            <strong style="font-size: 1.1em;">pvlib</strong><br>
            <small>Solar Energy Modeling & Analysis</small><br>
            <small style="opacity: 0.9;">Steps 3,5,6,7: Solar Radiation & PV</small>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        # Step 8: DEAP for multi-objective optimization
        st.markdown("""
        <div style="background: white; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); 
                    padding: 30px 20px; text-align: center; height: 180px; display: flex; align-items: center; 
                    justify-content: center; margin-bottom: 15px;">
            <div>
                <div style="font-size: 3em; margin-bottom: 5px;">🧬</div>
                <div style="font-size: 1.6em; font-weight: bold; color: #764ba2;">DEAP</div>
                <div style="font-size: 0.9em; color: #666;">Evolutionary Algorithms</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div style="text-align: center; padding: 15px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    border-radius: 8px; color: white;">
            <strong style="font-size: 1.1em;">DEAP</strong><br>
            <small>Distributed Evolutionary Algorithms (NSGA-II)</small><br>
            <small style="opacity: 0.9;">Step 8: Multi-Objective Optimization</small>
        </div>
        """, unsafe_allow_html=True)
    
    
    # Research attribution (footer) with enhanced design
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; padding: 25px; background: linear-gradient(135deg, #f0f2f6 0%, #e6e9ef 100%); 
                border-radius: 10px; margin-top: 30px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);">
        <h4 style="color: #2E8B57; margin-top: 0;">🎓 Academic Research Platform</h4>
        <p style="margin: 10px 0; color: #555;">
            <strong>Developed by Mostafa Gabr, PhD Candidate</strong><br>
            Technische Universität Berlin | Faculty of Architecture
        </p>
        <p style="margin: 10px 0;">
            <a href="https://www.researchgate.net/profile/Mostafa-Gabr-4" target="_blank" 
               style="color: #2E8B57; text-decoration: none; font-weight: 500;">
                📚 ResearchGate Profile →
            </a>
        </p>
        <p style="margin: 15px 0 0 0; font-size: 0.85em; color: #777;">
            Platform Version: 2.0 | Last Updated: October 2025
        </p>
    </div>
    """, unsafe_allow_html=True)
