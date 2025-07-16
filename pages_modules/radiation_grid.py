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
from services.optimized_radiation_analyzer import OptimizedRadiationAnalyzer
from utils.session_state_standardizer import BIPVSessionStateManager
import time

def render_radiation_grid():
    """Render the radiation and shading grid analysis module - DATABASE-DRIVEN ONLY."""
    
    # Enhanced header with visual branding
    st.markdown("""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 2rem; border-radius: 10px; margin-bottom: 2rem;">
        <h1 style="color: white; margin: 0; text-align: center;">☀️ Step 5: Solar Radiation & Shading Analysis</h1>
        <p style="color: #e6f3ff; margin: 0.5rem 0 0 0; text-align: center; font-size: 1.1em;">
            Advanced Database-Driven Analysis with High-Performance Computing
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Data validation
    if 'project_id' not in st.session_state:
        st.error("⚠️ No project selected. Please complete Step 1 (Project Setup) first.")
        return
        
    project_id = st.session_state.project_id
    
    # Check dependencies
    if not check_dependencies():
        return
    
    # Enhanced Performance & Configuration Section
    with st.container():
        st.markdown("### ⚡ Performance & Precision Configuration")
        
        # Performance mode selection with visual indicators
        col1, col2 = st.columns([2, 1])
        with col1:
            use_optimized = st.checkbox(
                "🚀 Enable High-Performance Analysis",
                value=True,
                help="Use optimized analyzer to reduce processing time from hours to minutes"
            )
        with col2:
            if use_optimized:
                st.success("🎯 **Optimized Mode Active**")
            else:
                st.warning("⚠️ **Legacy Mode**")
        
        st.markdown("---")
        
        # Configuration grid with enhanced layout
        config_col1, config_col2, config_col3 = st.columns([1, 1, 1])
        
        with config_col1:
            st.markdown("**🎯 Precision Level**")
            precision = st.selectbox(
                "Calculation Precision",
                ["Hourly", "Daily Peak", "Monthly Average", "Yearly Average"],
                index=1,  # Default to Daily Peak
                help="Higher precision = longer processing time | Daily Peak recommended for balance",
                label_visibility="collapsed"
            )
            
            # Enhanced time estimation with visual indicators
            time_estimates = {
                "Hourly": ("15-30 minutes", "🔴", "maximum accuracy"),
                "Daily Peak": ("3-5 minutes", "🟡", "recommended balance"),
                "Monthly Average": ("30-60 seconds", "🟢", "good accuracy"),
                "Yearly Average": ("10-20 seconds", "🟢", "quick overview")
            }
            time, indicator, description = time_estimates[precision]
            st.markdown(f"{indicator} **{time}** - {description}")
        
        with config_col2:
            st.markdown("**🏗️ Shading Analysis**")
            include_shading = st.checkbox(
                "Include Geometric Shading",
                value=True,
                help="Calculate precise shadows from building walls"
            )
            if include_shading:
                st.success("✅ 3D shadow calculations enabled")
            else:
                st.info("ℹ️ No shading calculations")
        
        with config_col3:
            st.markdown("**🧭 Physics Corrections**")
            apply_corrections = st.checkbox(
                "Apply Orientation Corrections",
                value=True,
                help="Apply physics-based orientation corrections for realistic radiation values"
            )
            if apply_corrections:
                st.success("✅ Physics-based corrections active")
            else:
                st.info("ℹ️ Basic calculations only")
    
    # Enhanced calculation overview with visual metrics
    st.markdown("---")
    st.markdown("### 📊 Analysis Scope & Calculations")
    
    calculation_details = {
        "Hourly": {"calculations": 4015, "icon": "⏰", "description": "11 hours × 365 days", "accuracy": "Maximum"},
        "Daily Peak": {"calculations": 365, "icon": "☀️", "description": "noon × 365 days", "accuracy": "High"},
        "Monthly Average": {"calculations": 12, "icon": "📅", "description": "monthly representatives", "accuracy": "Good"},
        "Yearly Average": {"calculations": 4, "icon": "📊", "description": "seasonal representatives", "accuracy": "Basic"}
    }
    
    details = calculation_details[precision]
    
    # Visual calculation overview
    calc_col1, calc_col2, calc_col3, calc_col4 = st.columns(4)
    
    with calc_col1:
        st.metric(
            "Calculations per Element",
            f"{details['calculations']:,}",
            help="Number of time steps calculated for each building element"
        )
    
    with calc_col2:
        st.metric(
            "Processing Mode",
            "Vectorized" if use_optimized else "Sequential",
            help="Calculation method for performance optimization"
        )
    
    with calc_col3:
        st.metric(
            "Accuracy Level",
            details['accuracy'],
            help="Expected accuracy of radiation calculations"
        )
    
    with calc_col4:
        estimated_elements = 2000  # Default estimate
        total_calculations = details['calculations'] * estimated_elements
        st.metric(
            "Total Calculations",
            f"{total_calculations:,}",
            help="Estimated total calculations for all elements"
        )
    
    # Processing mode indicator
    if use_optimized:
        st.success(f"🚀 **Optimized Mode**: {details['icon']} {details['calculations']:,} calculations per element ({details['description']}) with vectorized processing")
    else:
        st.info(f"🔄 **Standard Mode**: {details['icon']} {details['calculations']:,} calculations per element ({details['description']})")
    
    # Wall data section with enhanced info
    st.markdown("---")
    st.markdown("### 🏗️ Building Geometry Data")
    
    with st.expander("📋 Data Sources & Requirements", expanded=False):
        st.markdown("""
        **Window Elements**: Automatically loaded from Step 4 facade extraction
        - Glass areas, orientations, and building levels
        - Used for primary radiation calculations
        
        **Wall Geometry**: Retrieved from Step 4 BIM upload  
        - Wall dimensions and orientations
        - Used for geometric self-shading calculations
        
        **Weather Data**: TMY data from Step 3
        - Hourly solar irradiance values
        - Direct Normal Irradiance (DNI) and Global Horizontal Irradiance (GHI)
        """)
    
    # Check for existing analysis
    existing_data = db_manager.get_radiation_analysis_data(project_id)
    has_existing_analysis = existing_data and existing_data.get('element_radiation')
    
    # Enhanced data availability dashboard
    st.markdown("---")
    st.markdown("### 🔍 Analysis Readiness Dashboard")
    
    # Project info with enhanced display
    project_name = st.session_state.get('project_data', {}).get('project_name', 'Unknown')
    coordinates = st.session_state.get('project_data', {}).get('coordinates', {})
    location_name = st.session_state.get('project_data', {}).get('location_name', 'Unknown Location')
    
    # Project overview card
    with st.container():
        st.markdown(f"""
        <div style="background: #f8f9fa; padding: 1rem; border-radius: 8px; border-left: 4px solid #007bff; margin-bottom: 1rem;">
            <h4 style="margin: 0; color: #495057;">📍 {project_name}</h4>
            <p style="margin: 0.5rem 0 0 0; color: #6c757d;">
                {location_name} • Project ID: {project_id}
            </p>
        </div>
        """, unsafe_allow_html=True)
    
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
                if use_optimized:
                    # Use optimized analyzer
                    analyzer = OptimizedRadiationAnalyzer()
                    st.info("🚀 **Using High-Performance Analyzer**")
                    
                    analysis_results = analyzer.analyze_radiation_optimized(
                        project_id=project_id,
                        precision=precision,
                        apply_corrections=apply_corrections,
                        include_shading=include_shading
                    )
                    
                    if analysis_results and not analysis_results.get('error'):
                        # Save to session state for persistence
                        if 'project_data' not in st.session_state:
                            st.session_state.project_data = {}
                        
                        st.session_state.project_data['radiation_data'] = analysis_results['element_radiation']
                        st.session_state['radiation_completed'] = True
                        BIPVSessionStateManager.update_step_completion('radiation', True)
                        
                        st.success(f"✅ **Optimized Analysis Complete!**\n"
                                 f"- Elements: {analysis_results['total_elements']}\n"
                                 f"- Method: {precision} (optimized)\n"
                                 f"- Time: {analysis_results['calculation_time']:.1f} seconds\n"
                                 f"- Speed: {analysis_results['performance_metrics']['calculations_per_second']:.0f} calc/sec")
                        st.rerun()
                    else:
                        st.error(f"Optimized analysis failed: {analysis_results.get('error', 'Unknown error')}")
                else:
                    # Use legacy analyzer
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
    
    # Enhanced results display
    st.markdown("---")
    display_existing_results(project_id)
    
    # Reset the flag after displaying results
    if 'analysis_just_completed' in st.session_state:
        del st.session_state['analysis_just_completed']
    
    # How This Data Will Be Used section
    st.markdown("---")
    with st.expander("📈 How This Data Will Be Used in Next Steps", expanded=False):
        st.markdown("""
        **Step 6 - BIPV Specifications:**
        - Annual radiation values determine PV panel suitability
        - Elements with >800 kWh/m²/year are prioritized for BIPV installation
        - Radiation data feeds into energy yield calculations
        
        **Step 7 - Yield vs Demand:**
        - Monthly radiation profiles calculate seasonal energy generation
        - Shading factors adjust realistic energy output
        - Building-specific radiation data ensures accurate energy balance
        
        **Step 8 - Optimization:**
        - High-radiation elements are weighted favorably in genetic algorithms
        - Orientation-specific performance influences optimal BIPV selection
        - Cost-benefit analysis uses actual radiation for ROI calculations
        
        **Step 9 - Financial Analysis:**
        - Lifetime energy generation projections based on radiation data
        - Location-specific performance affects payback period calculations
        - Environmental impact calculations use accurate energy yield estimates
        """)

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
                    # Ensure orientation label is not empty
                    orientation_label = orientation if orientation and orientation.strip() else f"Direction {i+1}"
                    st.metric(orientation_label, f"{count:,}", delta=f"{percentage:.1f}%")
        
        # Enhanced radiation statistics with visual indicators
        st.markdown("### ☀️ Radiation Performance Overview")
        
        # Calculate enhanced statistics
        avg_radiation = sum(r['annual_radiation'] for r in element_radiation) / total_elements
        max_radiation = max(r['annual_radiation'] for r in element_radiation)
        min_radiation = min(r['annual_radiation'] for r in element_radiation) if element_radiation else 0
        
        # Performance categorization
        excellent_elements = len([r for r in element_radiation if r['annual_radiation'] > 1200])
        good_elements = len([r for r in element_radiation if 800 <= r['annual_radiation'] <= 1200])
        poor_elements = len([r for r in element_radiation if r['annual_radiation'] < 800])
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric(
                "Average Radiation",
                f"{avg_radiation:.0f} kWh/m²/year",
                delta=f"Range: {max_radiation-min_radiation:.0f}",
                help="Mean annual radiation across all analyzed elements"
            )
        with col2:
            st.metric(
                "Peak Performance",
                f"{max_radiation:.0f} kWh/m²/year",
                delta=f"{excellent_elements} excellent (>1200)",
                help="Highest performing element radiation value"
            )
        with col3:
            st.metric(
                "Good Performance", 
                f"{good_elements:,} elements",
                delta=f"{(good_elements/total_elements)*100:.1f}%",
                help="Elements with 800-1200 kWh/m²/year (suitable for BIPV)"
            )
        with col4:
            # Calculate suitable elements (>200 kWh/m²/year threshold)
            suitable_radiation = len([r for r in element_radiation if r['annual_radiation'] > 200])
            st.metric("High Performance Elements", f"{suitable_radiation:,}", delta=f"{(suitable_radiation/total_elements)*100:.1f}%")
        
        # Enhanced radiation distribution with multiple visualizations
        st.markdown("### 📈 Radiation Distribution Analysis")
        
        radiation_values = [r['annual_radiation'] for r in element_radiation]
        
        # Create tabs for different chart views
        chart_tab1, chart_tab2, chart_tab3 = st.tabs(["📊 Distribution", "🧭 By Orientation", "🏢 Performance Map"])
        
        with chart_tab1:
            # Enhanced histogram with performance zones
            fig = px.histogram(
                x=radiation_values,
                nbins=30,
                title="Annual Radiation Distribution with Performance Zones",
                labels={'x': 'Annual Radiation (kWh/m²/year)', 'y': 'Number of Elements'},
                color_discrete_sequence=['#3498db']
            )
            
            # Add performance zone lines
            fig.add_vline(x=800, line_dash="dash", line_color="orange", 
                         annotation_text="Minimum BIPV Threshold")
            fig.add_vline(x=1200, line_dash="dash", line_color="green", 
                         annotation_text="Excellent Performance")
            
            fig.update_layout(
                xaxis_title="Annual Radiation (kWh/m²/year)",
                yaxis_title="Number of Elements",
                showlegend=False
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with chart_tab2:
            # Radiation by orientation
            orientation_data = {}
            for element in element_radiation:
                orientation = element.get('orientation', 'Unknown')
                if orientation not in orientation_data:
                    orientation_data[orientation] = []
                orientation_data[orientation].append(element['annual_radiation'])
            
            # Box plot by orientation
            if orientation_data:
                fig_box = go.Figure()
                for orientation, values in orientation_data.items():
                    fig_box.add_trace(go.Box(
                        y=values,
                        name=orientation,
                        boxpoints='outliers'
                    ))
                
                fig_box.update_layout(
                    title="Radiation Performance by Orientation",
                    yaxis_title="Annual Radiation (kWh/m²/year)",
                    xaxis_title="Building Orientation"
                )
                st.plotly_chart(fig_box, use_container_width=True)
        
        with chart_tab3:
            # Performance categorization pie chart
            performance_data = {
                'Excellent (>1200)': excellent_elements,
                'Good (800-1200)': good_elements,
                'Poor (<800)': poor_elements
            }
            
            fig_pie = px.pie(
                values=list(performance_data.values()),
                names=list(performance_data.keys()),
                title="Element Performance Distribution",
                color_discrete_sequence=['#2ecc71', '#f39c12', '#e74c3c']
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        
        # Enhanced top performing elements with actionable insights
        st.markdown("### 🏆 Performance Analysis & Recommendations")
        
        sorted_elements = sorted(element_radiation, key=lambda x: x['annual_radiation'], reverse=True)
        top_elements = sorted_elements[:10]
        bottom_elements = sorted_elements[-5:]
        
        # Performance insights tabs
        insight_tab1, insight_tab2, insight_tab3 = st.tabs(["🌟 Top Performers", "⚠️ Poor Performers", "📋 Summary"])
        
        with insight_tab1:
            st.markdown("**🚀 Best candidates for BIPV installation:**")
            
            for i, element in enumerate(top_elements, 1):
                # Performance indicator
                performance_level = "🟢 Excellent" if element['annual_radiation'] > 1200 else "🟡 Good"
                
                with st.expander(f"#{i}: Element {element['element_id']} - {element['annual_radiation']:.0f} kWh/m²/year {performance_level}"):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.markdown("**Element Details**")
                        st.write(f"ID: {element['element_id']}")
                        st.write(f"Orientation: {element.get('orientation', 'Unknown')}")
                        st.write(f"Glass Area: {element.get('glass_area', 'Unknown')} m²")
                    with col2:
                        st.markdown("**Performance Metrics**")
                        st.write(f"Annual Radiation: {element['annual_radiation']:.0f} kWh/m²/year")
                        st.write(f"Level: {element.get('building_level', 'Unknown')}")
                        st.write(f"Family: {element.get('family', 'Unknown')}")
                    with col3:
                        st.markdown("**BIPV Potential**")
                        # Convert glass_area to float safely
                        glass_area = element.get('glass_area', 1.5)
                        if isinstance(glass_area, str):
                            try:
                                glass_area = float(glass_area)
                            except:
                                glass_area = 1.5
                        elif hasattr(glass_area, '__float__'):  # Handle Decimal type
                            glass_area = float(glass_area)
                        
                        potential_yield = element['annual_radiation'] * glass_area * 0.15  # 15% efficiency
                        st.write(f"Est. Annual Yield: {potential_yield:.0f} kWh")
                        cost_savings = potential_yield * 0.30  # €0.30/kWh
                        st.write(f"Est. Annual Savings: €{cost_savings:.0f}")
                        st.write("✅ **Recommended for BIPV**")
        
        with insight_tab2:
            st.markdown("**⚠️ Elements requiring attention:**")
            
            for i, element in enumerate(bottom_elements, 1):
                with st.expander(f"Element {element['element_id']} - {element['annual_radiation']:.0f} kWh/m²/year"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Element ID**: {element['element_id']}")
                        st.write(f"**Orientation**: {element.get('orientation', 'Unknown')}")
                        st.write(f"**Radiation**: {element['annual_radiation']:.0f} kWh/m²/year")
                    with col2:
                        st.write("**Issues & Recommendations:**")
                        if element['annual_radiation'] < 400:
                            st.write("🔴 Very low radiation - likely north-facing")
                        elif element['annual_radiation'] < 800:
                            st.write("🟡 Below BIPV threshold - check for shading")
                        st.write("❌ Not recommended for BIPV")
        
        with insight_tab3:
            st.markdown("**📊 Analysis Summary & Next Steps:**")
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Key Findings:**")
                st.write(f"• {excellent_elements} elements (>1200 kWh/m²/year) are prime BIPV candidates")
                st.write(f"• {good_elements} elements (800-1200 kWh/m²/year) are suitable for BIPV")
                st.write(f"• {poor_elements} elements (<800 kWh/m²/year) not recommended")
                st.write(f"• Average radiation: {avg_radiation:.0f} kWh/m²/year")
                
            with col2:
                st.markdown("**Recommendations for Step 6:**")
                st.write("• Focus BIPV specifications on top performing elements")
                st.write("• Consider panel efficiency based on radiation levels")
                st.write("• Exclude poor performers from economic analysis")
                st.write("• Use orientation data for panel optimization")
        
        # Enhanced navigation with progress indicators
        st.markdown("---")
        st.markdown("### 🎯 Analysis Complete - Ready for Next Step")
        
        # Progress summary
        col1, col2, col3 = st.columns(3)
        with col1:
            st.success("✅ **Radiation Analysis Complete**")
            st.write(f"• {total_elements:,} elements analyzed")
            st.write(f"• {completion_rate:.1f}% success rate")
        with col2:
            st.info("🎯 **Ready for BIPV Specification**")
            st.write(f"• {excellent_elements + good_elements:,} elements suitable")
            st.write(f"• {avg_radiation:.0f} kWh/m²/year avg radiation")
        with col3:
            st.warning("📊 **Data Integration**")
            st.write("• Radiation data saved to database")
            st.write("• Session state updated")
        
        # Enhanced navigation button
        if st.button("🚀 Continue to Step 6: BIPV Panel Specifications", type="primary"):
            st.session_state.current_step = 'pv_specification'
            st.session_state.scroll_to_top = True
            st.success("Proceeding to BIPV specification with radiation data...")
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