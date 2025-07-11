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
    
    ### Quick Start Guide
    
    **1. Project Setup** - Select location and configure project settings  
    **2. Historical Data** - Upload energy consumption data (see sample below)  
    **3. Weather Analysis** - Generate TMY solar data for your location  
    **4. Building Data** - Upload BIM window elements (see Dynamo script below)  
    **5. Analysis Steps** - Complete radiation, PV specs, yield calculations  
    **6. Results** - View optimization results and download reports
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
    
    # Ready to start section
    st.markdown("---")
    st.success("""
    **Ready to begin your BIPV analysis?**
    
    Click **Step 1: Project Setup** in the sidebar to start your analysis. 
    Use the sample files above as templates for your data uploads.
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