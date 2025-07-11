"""
Welcome page for BIPV Optimizer
"""
import streamlit as st
from utils.color_schemes import get_emoji, create_colored_html, YELLOW_SCHEME


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
    st.success("""
    **Ready to begin your BIPV analysis?**
    
    Click **Step 1: Project Setup** in the sidebar to start your complete 11-step analysis workflow.
    """)
    
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