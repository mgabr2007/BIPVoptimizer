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
from utils.session_state_standardizer import BIPVSessionStateManager
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
    
    # Wall data info - already uploaded in Step 4
    st.subheader("🏗️ Building Walls Data")
    st.info("📋 **Wall data is automatically retrieved from Step 4 upload** - No additional upload needed here.")
    
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
    
    # Check for existing analysis
    existing_data = db_manager.get_radiation_analysis_data(project_id)
    has_existing_analysis = existing_data and existing_data.get('element_radiation')
    
    # Check data availability for analysis
    st.subheader("🔍 Data Availability Check")
    
    # Show current project info
    project_name = st.session_state.get('project_data', {}).get('project_name', 'Unknown')
    st.info(f"🆔 **Current Project**: {project_name} (ID: {project_id})")
    
    conn = db_manager.get_connection()
    walls_available = False
    total_building_elements = 0
    wall_count = 0
    
    if conn:
        try:
            with conn.cursor() as cursor:
                # Check wall data from Step 5 upload
                try:
                    cursor.execute("""
                        SELECT COUNT(*) FROM building_walls WHERE project_id = %s
                    """, (project_id,))
                    result = cursor.fetchone()
                    wall_count = result[0] if result else 0
                    walls_available = wall_count > 0
                except Exception as e:
                    st.error(f"Error checking wall data: {e}")
                    walls_available = False
                
                # Check window elements from Step 4 upload  
                try:
                    cursor.execute("""
                        SELECT COUNT(*) FROM building_elements 
                        WHERE project_id = %s
                    """, (project_id,))
                    result = cursor.fetchone()
                    total_building_elements = result[0] if result else 0
                except Exception as e:
                    st.error(f"Error checking window elements: {e}")
                    total_building_elements = 0
                
                # If no data found, show available projects with data
                if total_building_elements == 0:
                    try:
                        cursor.execute("""
                            SELECT be.project_id, p.project_name, COUNT(be.id) as window_count
                            FROM building_elements be
                            JOIN projects p ON be.project_id = p.id
                            GROUP BY be.project_id, p.project_name
                            ORDER BY be.project_id DESC
                            LIMIT 5
                        """)
                        window_projects = cursor.fetchall()
                        
                        if window_projects:
                            with st.expander("🔍 **Available Projects with Window Data**", expanded=True):
                                st.write("**Projects with Window Data:**")
                                for proj_id, proj_name, count in window_projects:
                                    st.write(f"- Project {proj_id}: {proj_name} ({count:,} windows)")
                                
                                # Option to switch to latest project with data
                                latest_window_project = window_projects[0][0]
                                latest_project_name = window_projects[0][1]
                                
                                st.success(f"💡 **Recommendation**: Switch to Project {latest_window_project} ({latest_project_name}) with {window_projects[0][2]:,} windows")
                                
                                if st.button(f"🔄 Switch to Project {latest_window_project}", key="switch_to_window_project"):
                                    st.session_state.project_id = latest_window_project
                                    # Update project data in session state
                                    if 'project_data' not in st.session_state:
                                        st.session_state.project_data = {}
                                    st.session_state.project_data['project_id'] = latest_window_project
                                    st.session_state.project_data['project_name'] = latest_project_name
                                    st.success(f"✅ Switched to project {latest_window_project}")
                                    st.rerun()
                    except Exception as e:
                        st.warning(f"Could not retrieve project data: {e}")
                    
        except Exception as e:
            st.error(f"Database connection error: {e}")
            walls_available = False
            total_building_elements = 0
        finally:
            conn.close()
    
    # Debug information
    st.info(f"📊 **Found**: {total_building_elements:,} window elements, {wall_count:,} wall elements")
    
    # Show requirements status clearly
    st.subheader("📋 Analysis Requirements Status")
    col1, col2 = st.columns(2)
    with col1:
        if total_building_elements > 0:
            st.success(f"✅ Window Elements: {total_building_elements:,} available")
        else:
            st.error("❌ Window Elements: Missing - Go to Step 4 first")
    with col2:
        if walls_available:
            st.success(f"✅ Wall Data: {wall_count} walls available")  
        else:
            st.error("❌ Wall Data: Missing - Upload walls CSV above")
            
    # Clear instructions based on what's missing
    if total_building_elements == 0:
        st.warning("🚨 **CRITICAL**: No window elements found! You must complete Step 4 (Facade Extraction) first to upload window data before proceeding to Step 5.")
        st.markdown("**Next Steps:**")
        st.markdown("1. Go back to **Step 4: Facade & Window Extraction**")
        st.markdown("2. Upload your window/glass areas CSV file")  
        st.markdown("3. Return to Step 5 and upload wall data")
        st.markdown("4. Run radiation analysis")
    elif not walls_available:
        st.warning("Upload wall data above to enable radiation analysis with self-shading calculations.")
    
    col1, col2 = st.columns(2)
    with col1:
        # Check both wall data and window elements for button activation
        can_run_analysis = walls_available and total_building_elements > 0
        
        if can_run_analysis:
            if st.button("▶️ Run Advanced Analysis", type="primary", key="run_advanced_analysis"):
                run_advanced_analysis(project_id, precision, include_shading, apply_corrections)
        else:
            # Determine what's missing
            if not walls_available and total_building_elements == 0:
                help_text = "Upload window elements (Step 4) and wall data first"
            elif not walls_available:
                help_text = "Upload wall data first to enable analysis"
            elif total_building_elements == 0:
                help_text = "Upload window elements in Step 4 first"
            else:
                help_text = "Missing required data"
                
            st.button("▶️ Run Advanced Analysis", type="primary", key="run_advanced_analysis", 
                     disabled=True, help=help_text)
    
    with col2:
        if st.button("🔄 Reset Analysis", key="reset_analysis"):
            reset_analysis(project_id)
    
    # Display existing results if available
    display_existing_results(project_id)
    
    # Reset the flag after displaying results
    if 'analysis_just_completed' in st.session_state:
        del st.session_state['analysis_just_completed']

def check_dependencies():
    """Check if required data is available for radiation analysis."""
    
    project_id = st.session_state.get('project_id')
    if not project_id:
        st.error("⚠️ No project ID found. Please complete Step 1 (Project Setup) first.")
        return False
    
    # Check building elements in database
    conn = db_manager.get_connection()
    if conn:
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM building_elements WHERE project_id = %s", (project_id,))
                element_count = cursor.fetchone()[0]
                
                if element_count == 0:
                    st.error("⚠️ No building elements found. Please complete Step 4 (Facade Extraction) first.")
                    return False
                else:
                    st.success(f"✅ Found {element_count:,} building elements in database")
                    
        except Exception as e:
            st.error(f"❌ Error checking building elements: {str(e)}")
            return False
        finally:
            conn.close()
    else:
        st.error("❌ Database connection failed")
        return False
    
    # Check weather data  
    weather_data = st.session_state.get('project_data', {}).get('weather_analysis', {})
    tmy_data = weather_data.get('tmy_data', weather_data.get('hourly_data', []))
    
    if not tmy_data:
        st.error("⚠️ No TMY weather data available. Please complete Step 3 (Weather & Environment) first.")
        return False
    else:
        st.success("✅ TMY weather data available")
    
    return True

def clear_radiation_data(project_id):
    """Clear previous radiation analysis data for the project"""
    try:
        from database_manager import BIPVDatabaseManager
        db_manager = BIPVDatabaseManager()
        conn = db_manager.get_connection()
        
        if conn:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM element_radiation WHERE project_id = %s", (project_id,))
                cursor.execute("DELETE FROM radiation_analysis WHERE project_id = %s", (project_id,))
                conn.commit()
            conn.close()
            return True
    except Exception as e:
        st.warning(f"Error clearing radiation data: {str(e)}")
        return False

def run_advanced_analysis(project_id, precision, include_shading, apply_corrections):
    """Run advanced database-driven radiation analysis with sophisticated calculations."""
    
    try:
        # Clear previous radiation calculations silently
        clear_radiation_data(project_id)
        
        # Initialize advanced analyzer
        analyzer = AdvancedRadiationAnalyzer(project_id)
        
        # Get suitable elements with error handling
        try:
            suitable_elements = analyzer.get_suitable_elements()
            
            if not suitable_elements:
                st.error("❌ No suitable building elements found for radiation analysis")
                return
                
            st.success(f"✅ Found {len(suitable_elements):,} suitable elements for analysis")
            
        except Exception as e:
            st.error(f"Error getting suitable elements: {e}")
            # Try to get all elements if suitable filtering fails
            try:
                conn = db_manager.get_connection()
                if conn:
                    with conn.cursor() as cursor:
                        cursor.execute("""
                            SELECT COUNT(*) FROM building_elements WHERE project_id = %s
                        """, (project_id,))
                        result = cursor.fetchone()
                        element_count = result[0] if result else 0
                        
                        if element_count > 0:
                            st.warning(f"Found {element_count:,} total elements, but filtering failed. Using all elements.")
                        else:
                            st.error("❌ No building elements found in database for this project")
                            return
                    conn.close()
                else:
                    st.error("❌ Database connection failed")
                    return
            except Exception as e2:
                st.error(f"❌ Critical error checking elements: {e2}")
                return
        
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
            st.session_state.analysis_just_completed = True
            
            # Don't display results here - they will be shown below to avoid duplication
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
        
        # Progress Matrix
        st.subheader("📈 Analysis Progress Matrix")
        
        # Calculate statistics for progress matrix
        successful_elements = len([r for r in element_radiation if r['annual_radiation'] > 0])
        failed_elements = total_elements - successful_elements
        
        # Calculate orientation distribution
        orientation_counts = {}
        for element in element_radiation:
            orientation = element.get('orientation', 'Unknown')
            orientation_counts[orientation] = orientation_counts.get(orientation, 0) + 1
        
        # Progress matrix display
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Elements", f"{total_elements:,}")
        with col2:
            st.metric("Successfully Analyzed", f"{successful_elements:,}", delta=f"{(successful_elements/total_elements)*100:.1f}%")
        with col3:
            st.metric("Failed Analysis", f"{failed_elements:,}", delta=f"{(failed_elements/total_elements)*100:.1f}%" if failed_elements > 0 else "0%")
        with col4:
            completion_rate = (successful_elements / total_elements) * 100 if total_elements > 0 else 0
            st.metric("Completion Rate", f"{completion_rate:.1f}%")
        
        # Orientation breakdown
        st.subheader("🧭 Orientation Distribution")
        if orientation_counts:
            orientation_cols = st.columns(len(orientation_counts))
            for i, (orientation, count) in enumerate(orientation_counts.items()):
                with orientation_cols[i]:
                    percentage = (count / total_elements) * 100
                    st.metric(f"{orientation}", f"{count:,}", delta=f"{percentage:.1f}%")
        
        # Summary statistics
        st.subheader("☀️ Radiation Statistics")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            avg_radiation = sum(r['annual_radiation'] for r in element_radiation) / total_elements
            st.metric("Average Radiation", f"{avg_radiation:.0f} kWh/m²/year")
        with col2:
            max_radiation = max(r['annual_radiation'] for r in element_radiation)
            st.metric("Maximum Radiation", f"{max_radiation:.0f} kWh/m²/year")
        with col3:
            min_radiation = min(r['annual_radiation'] for r in element_radiation) if element_radiation else 0
            st.metric("Minimum Radiation", f"{min_radiation:.0f} kWh/m²/year")
        with col4:
            # Calculate suitable elements (>200 kWh/m²/year threshold)
            suitable_radiation = len([r for r in element_radiation if r['annual_radiation'] > 200])
            st.metric("High Performance Elements", f"{suitable_radiation:,}", delta=f"{(suitable_radiation/total_elements)*100:.1f}%")
        
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
        # Use timestamp to ensure unique key
        import time
        unique_key = f"radiation_distribution_chart_{project_id}_{int(time.time())}"
        st.plotly_chart(fig, use_container_width=True, key=unique_key)
        
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
        # Use timestamp for unique button key
        import time
        unique_button_key = f"continue_pv_spec_{project_id}_{int(time.time())}"
        if st.button("Continue to Step 6: PV Specification", key=unique_button_key):
            st.session_state.current_step = 'pv_specification'
            st.session_state.scroll_to_top = True
            st.rerun()
        
    except Exception as e:
        st.error(f"❌ Error displaying results: {str(e)}")

def save_walls_data_to_database(project_id, walls_df):
    """Save wall data to database for shading calculations."""
    try:
        conn = db_manager.get_connection()
        if not conn:
            return False
            
        with conn.cursor() as cursor:
            # Create walls table if it doesn't exist
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS building_walls (
                    id SERIAL PRIMARY KEY,
                    project_id INTEGER REFERENCES projects(id),
                    element_id VARCHAR(100),
                    wall_type VARCHAR(100),
                    orientation VARCHAR(20),
                    azimuth DECIMAL(10,2),
                    height DECIMAL(10,2),
                    level VARCHAR(50),
                    area DECIMAL(10,2),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Clear existing wall data for this project
            cursor.execute("DELETE FROM building_walls WHERE project_id = %s", (project_id,))
            
            # Insert new wall data using actual CSV column names
            for idx, row in walls_df.iterrows():
                # Extract wall height from Area and Length if available
                length = float(row.get('Length (m)', 0))
                area = float(row.get('Area (m²)', 0))
                height = area / length if length > 0 else 3.0  # Calculate height or default to 3m
                
                # Get orientation from azimuth
                azimuth = float(row.get('Azimuth (°)', 0))
                orientation = get_orientation_from_azimuth(azimuth)
                
                cursor.execute("""
                    INSERT INTO building_walls 
                    (project_id, element_id, wall_type, orientation, azimuth, height, level, area)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    project_id,
                    str(row.get('ElementId', f'wall_{idx}')),
                    str(row.get('Wall Type', 'Generic Wall')),
                    orientation,
                    azimuth,
                    height,
                    str(row.get('Level', '')),
                    area
                ))
            
            conn.commit()
            return True
            
    except Exception as e:
        st.error(f"Error saving wall data: {str(e)}")
        return False
    finally:
        if conn:
            conn.close()

def get_orientation_from_azimuth(azimuth):
    """Convert azimuth angle to orientation direction"""
    azimuth = azimuth % 360  # Normalize to 0-360
    if 315 <= azimuth or azimuth < 45:
        return "North"
    elif 45 <= azimuth < 135:
        return "East"
    elif 135 <= azimuth < 225:
        return "South"
    elif 225 <= azimuth < 315:
        return "West"
    else:
        return "Unknown"