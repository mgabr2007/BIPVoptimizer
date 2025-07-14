"""
Radiation & Shading Grid Analysis page for BIPV Optimizer
DATABASE-DRIVEN ONLY - No pandas DataFrames
"""

import streamlit as st
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from database_manager import db_manager, BIPVDatabaseManager
from services.radiation_analysis_service_clean import DatabaseRadiationAnalyzer
import time

def render_radiation_grid():
    """Render the radiation and shading grid analysis module - DATABASE-DRIVEN ONLY."""
    
    st.header("☀️ Step 5: Solar Radiation & Shading Analysis")
    st.markdown("**Database-Driven Analysis** - Direct database operations for optimal performance")
    
    # Data validation
    if 'project_id' not in st.session_state:
        st.error("⚠️ No project selected. Please complete Step 1 (Project Setup) first.")
        return
        
    project_id = st.session_state.project_id
    
    # Check dependencies
    if not check_dependencies():
        return
    
    # Method Selection - DATABASE ONLY
    st.subheader("📊 Analysis Method")
    st.info("**Database-Driven Analysis**: Direct database operations for element processing, radiation calculations, and data storage. No pandas DataFrames used.")
    
    # Database-driven analysis interface
    col1, col2 = st.columns(2)
    with col1:
        if st.button("▶️ Run Database Analysis", type="primary", key="run_database_analysis"):
            run_database_analysis(project_id)
    
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

def run_database_analysis(project_id):
    """Run database-driven radiation analysis."""
    
    try:
        st.subheader("🔄 Database-Driven Radiation Analysis")
        
        # Initialize database analyzer
        analyzer = DatabaseRadiationAnalyzer(project_id)
        
        # Get suitable elements
        suitable_elements = analyzer.get_suitable_elements()
        
        if not suitable_elements:
            st.error("❌ No suitable building elements found for radiation analysis")
            return
        
        st.success(f"✅ Found {len(suitable_elements)} suitable elements for analysis")
        
        # Get weather data
        weather_data = st.session_state.project_data.get('weather_analysis', {})
        tmy_data = weather_data.get('tmy_data', weather_data.get('hourly_data', []))
        
        project_data = st.session_state.project_data
        latitude = project_data.get('latitude', 52.5)
        longitude = project_data.get('longitude', 13.4)
        
        # Create progress tracking
        progress_container = st.container()
        with progress_container:
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                processed_metric = st.metric("Processed", "0")
            with col2:
                success_metric = st.metric("Success", "0")
            with col3:
                errors_metric = st.metric("Errors", "0")
            with col4:
                skipped_metric = st.metric("Skipped", "0")
            
            progress_bar = st.progress(0)
            log_container = st.container()
        
        # Progress tracking variables
        processed_count = 0
        success_count = 0
        error_count = 0
        skipped_count = 0
        
        # Process elements
        total_elements = len(suitable_elements)
        radiation_results = []
        
        with log_container:
            log_area = st.empty()
            log_messages = []
            
            def update_progress_log(message, current_count):
                timestamp = datetime.now().strftime("%H:%M:%S")
                log_messages.append(f"[{timestamp}] {message}")
                
                # Keep only last 8 messages
                if len(log_messages) > 8:
                    log_messages.pop(0)
                
                # Update progress display
                progress_bar.progress(current_count / total_elements)
                processed_metric.metric("Processed", str(current_count))
                success_metric.metric("Success", str(success_count))
                errors_metric.metric("Errors", str(error_count))
                skipped_metric.metric("Skipped", str(skipped_count))
                
                # Update log display
                log_area.text("\n".join(log_messages))
        
        # Start analysis
        update_progress_log("Starting database-driven radiation analysis...", 0)
        
        for i, element in enumerate(suitable_elements):
            try:
                element_id = element['element_id']
                orientation = element['orientation']
                glass_area = element['glass_area']
                
                update_progress_log(f"Processing {element_id} ({orientation}, {glass_area}m²)", i)
                
                # Calculate radiation for this element
                radiation_data = analyzer.calculate_element_radiation(element, tmy_data, latitude, longitude)
                
                if radiation_data:
                    radiation_results.append({
                        'element_id': element_id,
                        'annual_radiation': radiation_data['annual_radiation'],
                        'peak_irradiance': radiation_data['peak_irradiance'],
                        'orientation_multiplier': radiation_data.get('orientation_multiplier', 1.0)
                    })
                    success_count += 1
                    update_progress_log(f"✅ {element_id}: {radiation_data['annual_radiation']:.0f} kWh/m²/year", i + 1)
                else:
                    skipped_count += 1
                    update_progress_log(f"⚠️ {element_id}: Skipped (no radiation data)", i + 1)
                
                processed_count += 1
                
            except Exception as e:
                error_count += 1
                update_progress_log(f"❌ {element_id}: Error - {str(e)[:50]}", i + 1)
                processed_count += 1
        
        # Save results to database
        if radiation_results:
            update_progress_log("Saving results to database...", total_elements)
            
            success = analyzer.save_radiation_results(radiation_results)
            
            if success:
                update_progress_log(f"✅ Successfully saved {len(radiation_results)} radiation results", total_elements)
                st.success(f"✅ Analysis completed! Processed {processed_count} elements, {success_count} successful calculations")
                
                # Update session state
                st.session_state.radiation_completed = True
                st.session_state.step5_completed = True
                
            else:
                st.error("❌ Failed to save radiation results to database")
        else:
            st.error("❌ No radiation results to save")
        
        # Clear progress after completion
        progress_container.empty()
        
    except Exception as e:
        st.error(f"❌ Database analysis error: {str(e)}")

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