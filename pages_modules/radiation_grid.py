"""
Radiation & Shading Grid Analysis page for BIPV Optimizer
ADVANCED DATABASE-DRIVEN ANALYSIS - Sophisticated calculations without pandas
"""

import streamlit as st
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from database_manager import db_manager, BIPVDatabaseManager
from services.advanced_radiation_analyzer import AdvancedRadiationAnalyzer
import time

def render_radiation_grid():
    """Render the radiation and shading grid analysis module - DATABASE-DRIVEN ONLY."""
    
    st.header("☀️ Step 5: Solar Radiation & Shading Analysis")
    st.markdown("**Advanced Database-Driven Analysis** - Sophisticated calculations with database persistence")
    
    # Data validation
    if 'project_id' not in st.session_state:
        st.error("⚠️ No project selected. Please complete Step 1 (Project Setup) first.")
        return
        
    project_id = st.session_state.project_id
    
    # Check dependencies
    if not check_dependencies():
        return
    
    # Analysis precision selection - based on user's calculation details
    st.subheader("📊 Analysis Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        precision = st.selectbox(
            "Calculation Precision",
            ["Hourly", "Daily Peak", "Monthly Average", "Yearly Average"],
            index=1,  # Default to Daily Peak
            help="Hourly: 4,015 calculations per element | Daily Peak: 365 calculations | Monthly: 12 calculations | Yearly: 4 calculations"
        )
    
    with col2:
        include_shading = st.checkbox(
            "Include Geometric Shading",
            value=True,
            help="Calculate precise shadows from building walls"
        )
    
    # Show calculation details based on precision
    calculation_details = {
        "Hourly": "⏰ **4,015 calculations per element** (11 hours × 365 days)",
        "Daily Peak": "☀️ **365 calculations per element** (noon × 365 days)",
        "Monthly Average": "📅 **12 calculations per element** (monthly representatives)",
        "Yearly Average": "📊 **4 calculations per element** (seasonal representatives)"
    }
    
    st.info(calculation_details[precision])
    
    # Advanced analysis options
    apply_corrections = st.checkbox(
        "Apply Orientation Corrections",
        value=True,
        help="Apply physics-based orientation corrections for realistic radiation values"
    )
    
    # Analysis interface
    col1, col2 = st.columns(2)
    with col1:
        if st.button("▶️ Run Advanced Analysis", type="primary", key="run_advanced_analysis"):
            run_advanced_analysis(project_id, precision, include_shading, apply_corrections)
    
    with col2:
        if st.button("🔄 Reset Analysis", key="reset_analysis"):
            reset_analysis(project_id)
    
    # Display existing results if available
    display_existing_results(project_id)

def check_dependencies():
    """Check if required data is available for radiation analysis."""
    
    # Check building elements
    if 'building_elements' not in st.session_state:
        st.error("⚠️ No building elements found. Please complete Step 4 (Facade Extraction) first.")
        return False
    
    # Check weather data
    weather_data = st.session_state.project_data.get('weather_analysis', {})
    tmy_data = weather_data.get('tmy_data', weather_data.get('hourly_data', []))
    
    if not tmy_data:
        st.error("⚠️ No TMY weather data available. Please complete Step 3 (Weather & Environment) first.")
        return False
    
    return True

def run_advanced_analysis(project_id, precision, include_shading, apply_corrections):
    """Run advanced database-driven radiation analysis with sophisticated calculations."""
    
    try:
        st.subheader("🔄 Advanced Radiation Analysis")
        
        # Initialize advanced analyzer
        analyzer = AdvancedRadiationAnalyzer(project_id)
        
        # Get suitable elements
        suitable_elements = analyzer.get_suitable_elements()
        
        if not suitable_elements:
            st.error("❌ No suitable building elements found for radiation analysis")
            return
        
        st.success(f"✅ Found {len(suitable_elements)} suitable elements for analysis")
        
        # Get weather data
        weather_data = st.session_state.project_data.get('weather_analysis', {})
        tmy_data = weather_data.get('tmy_data', weather_data.get('hourly_data', []))
        
        if not tmy_data:
            st.error("No TMY data available for analysis")
            return
        
        # Get project coordinates
        coordinates = st.session_state.project_data.get('coordinates', {})
        latitude = coordinates.get('lat', 52.52)
        longitude = coordinates.get('lng', 13.405)
        
        # Create progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Progress callback function
        def update_progress(message, current, total):
            progress = int((current / total) * 100) if total > 0 else 0
            progress_bar.progress(progress)
            status_text.text(f"{message} ({current}/{total})")
        
        # Show calculation details
        st.info(f"🔬 **Analysis Details**: {precision} precision with {len(suitable_elements)} elements")
        
        # Run advanced analysis with all sophisticated calculations
        success = analyzer.run_advanced_analysis(
            tmy_data=tmy_data,
            latitude=latitude,
            longitude=longitude,
            precision=precision,
            include_shading=include_shading,
            apply_corrections=apply_corrections,
            progress_callback=update_progress
        )
        
        if success:
            st.success("✅ Advanced analysis completed successfully!")
            progress_bar.progress(100)
            status_text.text("Analysis complete")
            
            # Update session state
            st.session_state.radiation_completed = True
            st.session_state.step5_completed = True
            
            # Display results immediately
            display_existing_results(project_id)
        else:
            st.error("❌ Analysis failed. Please check the logs.")
        
    except Exception as e:
        st.error(f"❌ Database analysis error: {str(e)}")
        import traceback
        st.error(f"Detailed error: {traceback.format_exc()}")

def reset_analysis(project_id):
    """Reset radiation analysis for the project."""
    
    try:
        # Clear database
        conn = db_manager.get_connection()
        if conn:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM element_radiation WHERE project_id = %s", (project_id,))
                cursor.execute("DELETE FROM radiation_analysis WHERE project_id = %s", (project_id,))
                conn.commit()
            conn.close()
        
        # Clear session state
        if 'radiation_completed' in st.session_state:
            del st.session_state['radiation_completed']
        if 'step5_completed' in st.session_state:
            del st.session_state['step5_completed']
        
        st.success("✅ Analysis reset successfully")
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ Reset failed: {str(e)}")

def display_existing_results(project_id):
    """Display existing radiation analysis results."""
    
    try:
        # Get results from database
        radiation_data = db_manager.get_radiation_analysis_data(project_id)
        
        if not radiation_data or not radiation_data.get('element_radiation'):
            st.info("ℹ️ No radiation analysis results available. Run the analysis to generate results.")
            return
        
        st.subheader("📊 Radiation Analysis Results")
        
        element_radiation = radiation_data['element_radiation']
        total_elements = len(element_radiation)
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Elements", total_elements)
        with col2:
            avg_radiation = sum(r['annual_radiation'] for r in element_radiation) / total_elements
            st.metric("Average Radiation", f"{avg_radiation:.0f} kWh/m²/year")
        with col3:
            max_radiation = max(r['annual_radiation'] for r in element_radiation)
            st.metric("Maximum Radiation", f"{max_radiation:.0f} kWh/m²/year")
        with col4:
            min_radiation = min(r['annual_radiation'] for r in element_radiation)
            st.metric("Minimum Radiation", f"{min_radiation:.0f} kWh/m²/year")
        
        # Radiation distribution chart
        st.subheader("📈 Radiation Distribution")
        
        radiation_values = [r['annual_radiation'] for r in element_radiation]
        
        fig = px.histogram(
            x=radiation_values,
            nbins=20,
            title="Distribution of Annual Radiation Values",
            labels={'x': 'Annual Radiation (kWh/m²/year)', 'y': 'Number of Elements'}
        )
        fig.update_layout(
            xaxis_title="Annual Radiation (kWh/m²/year)",
            yaxis_title="Number of Elements"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Top performing elements
        st.subheader("🏆 Top Performing Elements")
        
        sorted_elements = sorted(element_radiation, key=lambda x: x['annual_radiation'], reverse=True)
        top_elements = sorted_elements[:10]
        
        for i, element in enumerate(top_elements, 1):
            with st.expander(f"#{i}: {element['element_id']} - {element['annual_radiation']:.0f} kWh/m²/year"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Element ID**: {element['element_id']}")
                    st.write(f"**Orientation**: {element.get('orientation', 'Unknown')}")
                    st.write(f"**Glass Area**: {element.get('glass_area', 'Unknown')} m²")
                with col2:
                    st.write(f"**Annual Radiation**: {element['annual_radiation']:.0f} kWh/m²/year")
                    st.write(f"**Building Level**: {element.get('building_level', 'Unknown')}")
                    st.write(f"**Family**: {element.get('family', 'Unknown')}")
        
        # Navigation
        st.markdown("---")
        if st.button("Continue to Step 6: PV Specification", key="continue_pv_spec"):
            st.session_state.current_step = 'pv_specification'
            st.session_state.scroll_to_top = True
            st.rerun()
        
    except Exception as e:
        st.error(f"❌ Error displaying results: {str(e)}")