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
from services.ultra_fast_radiation_analyzer import UltraFastRadiationAnalyzer
from utils.session_state_standardizer import BIPVSessionStateManager
import time

def render_radiation_grid():
    """Render the radiation and shading grid analysis module - DATABASE-DRIVEN ONLY."""
    
    # Enhanced header with visual branding
    st.markdown("""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 2rem; border-radius: 10px; margin-bottom: 2rem;">
        <h1 style="color: white; margin: 0; text-align: center;">☀️ Step 5: Solar Radiation & Shading Analysis</h1>
        <p style="color: #e6f3ff; margin: 0.5rem 0 0 0; text-align: center; font-size: 1.1em;">
            Analyzing Selected Window Types from Step 4 with High-Performance Computing
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Get current project ID from database - centralized architecture
    from services.io import get_current_project_id
    
    # Get project_id with improved error handling
    project_id = None
    
    try:
        project_id = get_current_project_id()
        if project_id:
            # Ensure project_id is set in session state for radiation analysis
            st.session_state.project_id = project_id
            if 'project_data' not in st.session_state:
                st.session_state.project_data = {}
            st.session_state.project_data['project_id'] = project_id
    except Exception as e:
        st.warning(f"Could not retrieve project ID: {str(e)}")
    
    # If no project_id found, try fallback methods
    if not project_id:
        try:
            # Try from session state first
            if hasattr(st.session_state, 'project_id') and st.session_state.project_id:
                project_id = st.session_state.project_id
                st.info(f"Using project ID from session: {project_id}")
            elif hasattr(st.session_state, 'project_data') and isinstance(st.session_state.project_data, dict):
                if 'project_id' in st.session_state.project_data:
                    project_id = st.session_state.project_data['project_id']
                    st.info(f"Using project ID from session data: {project_id}")
            
            # If still no project_id, check database for existing projects
            if not project_id:
                conn = db_manager.get_connection()
                if conn:
                    with conn.cursor() as cursor:
                        # Get the most recent project
                        cursor.execute("SELECT id, project_name FROM projects ORDER BY created_at DESC LIMIT 1")
                        result = cursor.fetchone()
                        if result:
                            project_id = result[0]
                            project_name = result[1]
                            
                            # Set session state for future calls
                            st.session_state.project_id = project_id
                            if not hasattr(st.session_state, 'project_data'):
                                st.session_state.project_data = {}
                            st.session_state.project_data['project_id'] = project_id
                            st.session_state.project_data['project_name'] = project_name
                            
                            st.success(f"✅ Using most recent project: {project_name} (ID: {project_id})")
                        else:
                            st.error("⚠️ No projects found in database. Please complete Step 1 first.")
                            return
                    conn.close()
                else:
                    st.error("⚠️ Database connection failed.")
                    return
        except Exception as fallback_error:
            st.error(f"⚠️ Could not recover project data: {str(fallback_error)}")
            return
    
    if not project_id:
        st.error("⚠️ No project ID found. Please complete Step 1 (Project Setup) first.")
        return
    
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
            st.markdown("**🎯 Calculation Precision for Selected Windows**")
            
            # Show facade orientation configuration
            try:
                conn = db_manager.get_connection()
                if conn:
                    with conn.cursor() as cursor:
                        cursor.execute("SELECT include_north_facade FROM projects WHERE id = %s", (project_id,))
                        result = cursor.fetchone()
                        include_north = result[0] if result else False
                        
                        if include_north:
                            st.info("📍 **All orientations** (N/S/E/W) - North facades included")
                        else:
                            st.info("📍 **Optimal orientations** (S/E/W only) - North facades excluded")
                    conn.close()
            except Exception:
                st.info("📍 **Default:** South/East/West orientations only")
            
            # New calculation precision radio buttons
            calc_precision = st.radio(
                "Solar Calculation Mode",
                ["Simple", "Advanced", "Auto"],
                index=2,  # Default to Auto
                help="Analysis method for selected window types from Step 4 | Simple: DNI-only (5-15% lower accuracy, 3x faster) | Advanced: Full GHI+DNI+DHI model (research-grade) | Auto: Smart data-based selection",
                horizontal=True
            )
            
            # Info text explaining accuracy vs speed tradeoffs
            precision_info = {
                "Simple": ("🟢 **Fast Processing** - DNI-only calculations, 3x faster but 5-15% lower accuracy", "simple"),
                "Advanced": ("🔴 **Research Grade** - Full GHI+DNI+DHI POA model, maximum accuracy but slower", "advanced"), 
                "Auto": ("🟡 **Intelligent** - Automatically selects best method based on available TMY data", "auto")
            }
            info_text, calc_mode = precision_info[calc_precision]
            st.markdown(info_text)
            
            # Analysis Speed vs Accuracy Slider
            st.markdown("**⚡ Performance Settings**")
            speed_accuracy = st.slider(
                "Analysis Speed vs Accuracy",
                min_value=1, max_value=5, value=3,
                help="1=Maximum Speed | 3=Balanced | 5=Maximum Accuracy"
            )
            
            # Map slider to precision level
            if speed_accuracy <= 2:
                precision = "Yearly Average"
                if calc_precision == "Auto":
                    calc_mode = "simple"
            elif speed_accuracy == 3:
                precision = "Monthly Average"  
            elif speed_accuracy == 4:
                precision = "Daily Peak"
            else:
                precision = "Hourly"
                if calc_precision == "Auto":
                    calc_mode = "advanced"
            
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
            st.markdown("**🏗️ Shading Analysis for Selected Windows**")
            include_shading = st.checkbox(
                "Include Geometric Shading",
                value=True,
                help="Calculate precise shadows from building walls on selected window types"
            )
            if include_shading:
                st.success("✅ 3D shadow calculations enabled")
            else:
                st.info("ℹ️ No shading calculations")
        
        with config_col3:
            st.markdown("**🧭 Physics Corrections for Selected Windows**")
            apply_corrections = st.checkbox(
                "Apply Orientation Corrections",
                value=True,
                help="Apply physics-based orientation corrections for realistic radiation values on selected window types"
            )
            if apply_corrections:
                st.success("✅ Physics-based corrections active")
            else:
                st.info("ℹ️ Basic calculations only")
    
    # Enhanced calculation overview with visual metrics
    st.markdown("---")
    st.markdown("### 📊 Analysis Scope & Calculations for Selected Window Types")
    
    calculation_details = {
        "Hourly": {"calculations": 4015, "icon": "⏰", "description": "11 hours × 365 days", "accuracy": "Maximum"},
        "Daily Peak": {"calculations": 365, "icon": "☀️", "description": "noon × 365 days", "accuracy": "High"},
        "Monthly Average": {"calculations": 12, "icon": "📅", "description": "monthly representatives", "accuracy": "Good"},
        "Yearly Average": {"calculations": 4, "icon": "📊", "description": "seasonal representatives", "accuracy": "Basic"}
    }
    
    details = calculation_details[precision]
    
    # Simple processing mode indicator (compact)
    mode_text = "Optimized Vectorized" if use_optimized else "Standard Sequential"
    st.info(f"🔄 **{mode_text} Processing** • {details['accuracy']} accuracy • {details['icon']} {details['description']}")
    
    # Data readiness information
    st.markdown("---")
    st.markdown("### 📋 Selected Window Types Analysis Status")
    
    with st.expander("📊 Data Sources & Analysis Flow for Selected Windows", expanded=False):
        st.markdown("""
        **Step 4 Data**: Selected window types from BIM extraction and historical filtering
        - Window glass areas, orientations, and building levels for chosen window families
        - Wall geometry for self-shading calculations on selected windows
        
        **Step 3 Data**: TMY weather data for radiation calculations
        - Hourly solar irradiance values (DNI, GHI)
        - Temperature and atmospheric conditions
        
        **Analysis Output**: Hourly radiation values for each selected window element
        - Direct and diffuse radiation components
        - Self-shading corrections applied to selected window types only
        """)
    
    st.info("💡 **Note**: Window types are selected in Step 4 based on historical significance. This step performs radiation analysis only on the selected window types suitable for BIPV installation.")
    
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
                # Check wall data from Step 4 upload
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
                
                # Check window elements from Step 4 upload (only selected types)
                try:
                    cursor.execute("""
                        SELECT COUNT(*) FROM building_elements 
                        WHERE project_id = %s AND pv_suitable = true
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
    st.info(f"📊 **Found**: {total_building_elements:,} selected window elements (from Step 4), {wall_count:,} wall elements")
    
    # Show requirements status clearly
    st.subheader("📋 Selected Window Types Analysis Requirements")
    col1, col2 = st.columns(2)
    with col1:
        if total_building_elements > 0:
            st.success(f"✅ Window Elements: {total_building_elements:,} selected for analysis (from Step 4)")
        else:
            st.error("❌ Window Elements: Missing - Go to Step 4 and select window types first")
    with col2:
        if walls_available:
            st.success(f"✅ Wall Data: {wall_count} walls available")  
        else:
            st.error("❌ Wall Data: Missing - Upload walls CSV in Step 4")
            
    # Clear instructions based on what's missing
    if total_building_elements == 0:
        st.warning("🚨 **CRITICAL**: No selected window elements found! You must complete Step 4 (Facade Extraction) and select window types suitable for BIPV installation.")
        st.markdown("**Next Steps:**")
        st.markdown("1. Go back to **Step 4: Facade & Window Extraction**")
        st.markdown("2. Upload your window/glass areas CSV file")  
        st.markdown("3. Select window types that can be replaced (historical significance filtering)")
        st.markdown("4. Upload wall data CSV file in Step 4")
        st.markdown("5. Run radiation analysis on selected window types")
    elif not walls_available:
        st.warning("Upload wall data in Step 4 (Facade Extraction) to enable radiation analysis with self-shading calculations on selected windows.")
    
    col1, col2 = st.columns(2)
    with col1:
        # Check both wall data and window elements for button activation
        can_run_analysis = walls_available and total_building_elements > 0
        
        if can_run_analysis:
            if st.button("▶️ Run Radiation Analysis on Selected Windows", type="primary", key="run_radiation_analysis"):
                # Import the execution flow
                from services.step5_execution_flow import Step5ExecutionFlow
                
                # Create progress indicators
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Initialize execution flow
                executor = Step5ExecutionFlow()
                executor.set_progress_callbacks(progress_bar, status_text)
                
                # Configure analysis based on user settings
                analysis_config = {
                    'precision': precision,
                    'apply_corrections': apply_corrections,
                    'include_shading': include_shading,
                    'calculation_mode': calc_mode,
                    'analysis_type': 'ultra_fast' if (use_optimized and precision == "Yearly Average") else 'optimized' if use_optimized else 'advanced'
                }
                
                # Show analysis type info
                if analysis_config['analysis_type'] == 'ultra_fast':
                    st.info("⚡ **Ultra-Fast Analysis** - Processing selected window types in 10-15 seconds")
                elif analysis_config['analysis_type'] == 'optimized':
                    st.info("🚀 **High-Performance Analysis** - Processing selected window types in 3-5 minutes")
                else:
                    st.info("🔬 **Research-Grade Analysis** - Maximum accuracy for selected window types, longer processing time")
                
                # Execute the complete analysis flow
                with st.spinner("Running comprehensive radiation analysis on selected window types..."):
                    execution_result = executor.run_complete_analysis(project_id, analysis_config)
                
                # Process execution results
                if execution_result['success']:
                    # Show success message with performance metrics
                    metrics = execution_result.get('performance_metrics', {})
                    elements_count = metrics.get('elements_processed', 0)
                    total_time = metrics.get('total_execution_time', 0)
                    calc_per_sec = metrics.get('calculations_per_second', 0)
                    
                    analysis_type_name = {
                        'ultra_fast': 'Ultra-Fast',
                        'optimized': 'High-Performance', 
                        'advanced': 'Research-Grade'
                    }.get(execution_result['analysis_type'], 'Standard')
                    
                    st.success(f"✅ **{analysis_type_name} Analysis Complete!**\n"
                             f"- Elements: {elements_count:,}\n"
                             f"- Total Time: {total_time:.1f} seconds\n"
                             f"- Method: {precision}\n" + 
                             (f"- Speed: {calc_per_sec:.0f} calculations/second" if calc_per_sec > 0 else ""))
                    
                    # Show validation summary
                    validation_summary = execution_result.get('validation_summary', {})
                    suitable_elements = validation_summary.get('suitable_elements', 0)
                    total_elements = validation_summary.get('total_elements', 0)
                    
                    if suitable_elements and total_elements:
                        suitability_rate = (suitable_elements / total_elements) * 100
                        st.info(f"📊 **Analysis Summary**: {suitable_elements:,} suitable elements ({suitability_rate:.1f}% suitability rate)")
                    
                    progress_bar.progress(1.0)
                    status_text.text("Analysis completed successfully!")
                    
                    # Trigger page refresh to show results
                    st.rerun()
                    
                else:
                    # Show error message
                    error_msg = execution_result.get('error', 'Unknown error occurred')
                    st.error(f"❌ **Analysis Failed**: {error_msg}")
                    
                    # Show validation errors if available
                    if 'validation_errors' in execution_result:
                        st.error("**Validation Errors:**")
                        for error in execution_result['validation_errors']:
                            st.error(f"- {error}")
                    
                    # Show warnings if available
                    if 'validation_warnings' in execution_result:
                        st.warning("**Warnings:**")
                        for warning in execution_result['validation_warnings']:
                            st.warning(f"- {warning}")
                    
                    # Show traceback for debugging if available
                    if 'traceback' in execution_result:
                        with st.expander("🔍 Debug Information", expanded=False):
                            st.code(execution_result['traceback'])
                    
                    progress_bar.progress(0)
                    status_text.text("Analysis failed")
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
    
    from services.io import get_current_project_id
    
    # Get project_id with proper error handling
    project_id = None
    try:
        project_id = get_current_project_id()
    except Exception as e:
        st.warning(f"Could not retrieve project ID from dependencies check: {str(e)}")
    
    # Enhanced project detection with debugging info
    if not project_id:
        st.error("⚠️ No project ID found. Please complete Step 1 (Project Setup) first.")
        
        # Show available projects with data for debugging
        conn = db_manager.get_connection()
        if conn:
            try:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT p.id, p.project_name, COUNT(be.id) as elements
                        FROM projects p
                        LEFT JOIN building_elements be ON p.id = be.project_id
                        GROUP BY p.id, p.project_name
                        HAVING COUNT(be.id) > 0
                        ORDER BY COUNT(be.id) DESC
                        LIMIT 3
                    """)
                    available_projects = cursor.fetchall()
                    
                    if available_projects:
                        st.info("💡 **Available projects with data:** " + 
                               ", ".join([f"{name} ({count} elements)" for _, name, count in available_projects]))
                        st.info("👉 Use the Project Selector in the sidebar to switch to a project with uploaded data.")
                conn.close()
            except:
                pass
        return False
    
    st.info(f"🎯 **Current Project:** {project_id}")
    
    # Check building elements in database
    conn = db_manager.get_connection()
    if conn:
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM building_elements WHERE project_id = %s", (project_id,))
                element_count = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM building_walls WHERE project_id = %s", (project_id,))
                wall_count = cursor.fetchone()[0]
                
                if element_count == 0:
                    st.error(f"⚠️ No building elements found in project {project_id}. Please complete Step 4 (Facade Extraction) first.")
                    
                    # Show which projects have data
                    cursor.execute("""
                        SELECT p.project_name, COUNT(be.id) as elements
                        FROM projects p
                        JOIN building_elements be ON p.id = be.project_id
                        GROUP BY p.project_name
                        ORDER BY COUNT(be.id) DESC
                        LIMIT 3
                    """)
                    projects_with_data = cursor.fetchall()
                    
                    if projects_with_data:
                        st.info("💡 **Projects with uploaded data:** " + 
                               ", ".join([f"{name} ({count})" for name, count in projects_with_data]))
                    
                    return False
                else:
                    st.success(f"✅ Found {element_count:,} building elements in database")
                    if wall_count > 0:
                        st.success(f"✅ Found {wall_count:,} wall elements for self-shading analysis")
                    
        except Exception as e:
            st.error(f"❌ Error checking building elements: {str(e)}")
            return False
        finally:
            conn.close()
    else:
        st.error("❌ Database connection failed")
        return False
    
    # Check weather data from database
    from utils.database_helper import DatabaseHelper
    db_helper = DatabaseHelper()
    weather_data = db_helper.get_step_data("3")
    
    if not weather_data or not weather_data.get('tmy_data'):
        st.error("⚠️ No TMY weather data available. Please complete Step 3 (Weather & Environment) first.")
        return False
    else:
        tmy_data = weather_data.get('tmy_data', [])
        if isinstance(tmy_data, list) and len(tmy_data) > 0:
            st.success(f"✅ TMY weather data available ({len(tmy_data):,} hourly records)")
        else:
            st.error("⚠️ TMY weather data is invalid. Please regenerate in Step 3.")
            return False
    
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

def run_advanced_analysis(project_id, precision, include_shading, apply_corrections, calculation_mode="auto"):
    """Run advanced database-driven radiation analysis with sophisticated calculations."""
    
    try:
        # Initialize session state to prevent saving errors
        if 'project_data' not in st.session_state:
            st.session_state.project_data = {}
            
        # Clear previous radiation calculations silently
        clear_radiation_data(project_id)
        
        # Initialize advanced analyzer - use OptimizedRadiationAnalyzer instead
        from services.optimized_radiation_analyzer import OptimizedRadiationAnalyzer
        analyzer = OptimizedRadiationAnalyzer()
        
        # Get building elements with error handling
        try:
            # Use database manager to check elements
            from database_manager import BIPVDatabaseManager
            db_manager = BIPVDatabaseManager()
            conn = db_manager.get_connection()
            
            if conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT COUNT(*) FROM building_elements 
                        WHERE project_id = %s
                    """, (project_id,))
                    result = cursor.fetchone()
                    element_count = result[0] if result else 0
                    
                    if element_count == 0:
                        st.error("❌ No building elements found for radiation analysis")
                        return
                        
                    st.success(f"✅ Found {element_count:,} building elements for analysis")
                conn.close()
            else:
                st.error("❌ Database connection failed")
                return
            
        except Exception as e:
            st.error(f"Error getting suitable elements: {e}")
            # Try to get all elements if suitable filtering fails
            try:
                from database_manager import BIPVDatabaseManager
                db_manager = BIPVDatabaseManager()
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
        
        # Get weather data from database
        from utils.database_helper import DatabaseHelper
        db_helper = DatabaseHelper()
        weather_data = db_helper.get_step_data("3")
        
        if not weather_data or not weather_data.get('tmy_data'):
            st.error("No TMY data available for analysis - please complete Step 3 first")
            return
        
        tmy_data = weather_data.get('tmy_data', [])
        
        # Get project coordinates from database
        project_data = db_helper.get_step_data("1") 
        coordinates = project_data.get('coordinates', {}) if project_data else {}
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
        
        # Run optimized radiation analysis with calculation mode
        analysis_results = analyzer.analyze_radiation_optimized(
            project_id=project_id,
            precision=precision,
            apply_corrections=apply_corrections,
            include_shading=include_shading,
            calculation_mode=calculation_mode
        )
        
        # Check if analysis was successful
        success = analysis_results and not analysis_results.get('error', False)
        
        if success:
            st.success("✅ Advanced analysis completed successfully!")
            progress_bar.progress(100)
            status_text.text("Analysis complete")
            
            # Update session state with results
            if 'project_data' not in st.session_state:
                st.session_state.project_data = {}
            
            st.session_state.project_data['radiation_data'] = analysis_results.get('element_radiation', {})
            st.session_state.radiation_completed = True
            st.session_state.step5_completed = True
            st.session_state.analysis_just_completed = True
            
            # Show completion metrics
            total_elements = analysis_results.get('total_elements', 0)
            calc_time = analysis_results.get('calculation_time', 0)
            st.info(f"📊 **Results**: {total_elements:,} elements analyzed in {calc_time:.1f} seconds")
            
            # Trigger page refresh to show results
            st.rerun()
            
        else:
            error_msg = analysis_results.get('error', 'Unknown error') if analysis_results else 'Analysis failed'
            st.error(f"❌ Analysis failed: {error_msg}")
        
    except Exception as e:
        st.error(f"❌ Advanced precision analysis error: {str(e)}")
        st.warning("💡 **Troubleshooting**: Try refreshing the page or switching to Simple precision mode")
        import traceback
        st.error(f"Debug info: project_id={project_id}, calculation_mode={calculation_mode}")
        st.error(f"Detailed error: {traceback.format_exc()}")
        # Reset progress indicators if they exist
        try:
            progress_bar = st.progress(0)
            status_text = st.empty()
            status_text.text("Analysis failed")
        except:
            pass  # Ignore errors resetting UI elements

def reset_analysis(project_id):
    """Reset radiation analysis for the project."""
    
    try:
        # Clear database
        from database_manager import BIPVDatabaseManager
        db_manager = BIPVDatabaseManager()
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
        
        # COMPREHENSIVE RADIATION ANALYSIS MATRIX
        st.markdown("""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 1.5rem; border-radius: 10px; margin: 1rem 0;">
            <h2 style="text-align: center; margin-bottom: 0.5rem; color: white;">📊 Comprehensive Radiation Analysis Matrix</h2>
            <p style="text-align: center; margin: 0; color: #e6f3ff;">Complete overview of radiation analysis results and performance metrics</p>
        </div>
        """, unsafe_allow_html=True)
        
        element_radiation = radiation_data['element_radiation']
        total_elements = len(element_radiation)
        
        # Calculate all statistics for comprehensive matrix
        successful_elements = len([r for r in element_radiation if float(r['annual_radiation'] or 0) > 0])
        failed_elements = total_elements - successful_elements
        completion_rate = (successful_elements / total_elements) * 100 if total_elements > 0 else 0
        
        # Radiation statistics with safe decimal handling
        radiation_values_safe = [float(r['annual_radiation']) if r['annual_radiation'] else 0.0 for r in element_radiation]
        avg_radiation = sum(radiation_values_safe) / total_elements if total_elements > 0 else 0
        max_radiation = max(radiation_values_safe) if radiation_values_safe else 0
        min_radiation = min(radiation_values_safe) if radiation_values_safe else 0
        radiation_range = max_radiation - min_radiation
        
        # Performance categorization
        excellent_elements = len([r for r in element_radiation if float(r['annual_radiation'] or 0) > 1200])
        good_elements = len([r for r in element_radiation if 800 <= float(r['annual_radiation'] or 0) <= 1200])
        poor_elements = len([r for r in element_radiation if 0 < float(r['annual_radiation'] or 0) < 800])
        bipv_suitable = excellent_elements + good_elements
        
        # Orientation distribution and performance
        orientation_data = {}
        for element in element_radiation:
            orientation = element.get('orientation', 'Unknown')
            radiation = float(element['annual_radiation'] or 0)
            
            if orientation not in orientation_data:
                orientation_data[orientation] = {'count': 0, 'radiations': [], 'avg': 0}
            
            orientation_data[orientation]['count'] += 1
            if radiation > 0:
                orientation_data[orientation]['radiations'].append(radiation)
        
        # Calculate averages for each orientation
        for orient, data in orientation_data.items():
            if data['radiations']:
                data['avg'] = sum(data['radiations']) / len(data['radiations'])
        
        # MATRIX DISPLAY - ROW 1: Progress & Completion
        st.markdown("**📈 Analysis Progress & Completion Status**")
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("Total Elements", f"{total_elements:,}")
        with col2:
            st.metric("Successfully Analyzed", f"{successful_elements:,}")
        with col3:
            st.metric("Completion Rate", f"{completion_rate:.1f}%")
        with col4:
            st.metric("Failed Analysis", f"{failed_elements:,}")
        with col5:
            processing_time_est = total_elements * 0.2  # Estimate 0.2 seconds per element
            st.metric("Est. Processing Time", f"{processing_time_est:.0f}s")
        
        # MATRIX DISPLAY - ROW 2: Radiation Performance Statistics  
        st.markdown("**☀️ Radiation Performance Statistics**")
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("Average Radiation", f"{avg_radiation:.0f} kWh/m²/year")
        with col2:
            st.metric("Peak Performance", f"{max_radiation:.0f} kWh/m²/year")
        with col3:
            st.metric("Minimum Performance", f"{min_radiation:.0f} kWh/m²/year")
        with col4:
            st.metric("Performance Range", f"{radiation_range:.0f} kWh/m²/year")
        with col5:
            # Calculate standard deviation
            if radiation_values_safe:
                variance = sum([(r - avg_radiation)**2 for r in radiation_values_safe]) / len(radiation_values_safe)
                std_dev = variance**0.5
            else:
                std_dev = 0
            st.metric("Standard Deviation", f"{std_dev:.0f} kWh/m²/year")
        
        # MATRIX DISPLAY - ROW 3: BIPV Suitability Categories
        st.markdown("**🎯 BIPV Suitability Categories**")
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            excellent_pct = (excellent_elements / total_elements) * 100 if total_elements > 0 else 0
            st.metric("Excellent (>1200)", f"{excellent_elements:,}", delta=f"{excellent_pct:.1f}%")
        with col2:
            good_pct = (good_elements / total_elements) * 100 if total_elements > 0 else 0
            st.metric("Good (800-1200)", f"{good_elements:,}", delta=f"{good_pct:.1f}%")
        with col3:
            poor_pct = (poor_elements / total_elements) * 100 if total_elements > 0 else 0
            st.metric("Poor (<800)", f"{poor_elements:,}", delta=f"{poor_pct:.1f}%")
        with col4:
            suitable_pct = (bipv_suitable / total_elements) * 100 if total_elements > 0 else 0
            st.metric("BIPV Suitable Total", f"{bipv_suitable:,}", delta=f"{suitable_pct:.1f}%")
        with col5:
            # Estimate potential capacity (15% efficiency assumption)
            avg_glass_area = 1.8  # Estimated average from BIM data
            potential_capacity = (bipv_suitable * avg_radiation * avg_glass_area * 0.15) / 1000
            st.metric("Est. Potential Capacity", f"{potential_capacity:.0f} kW")
        
        # MATRIX DISPLAY - ROW 4: Orientation Performance Matrix
        st.markdown("**🧭 Orientation Performance Matrix**")
        if orientation_data:
            # Create columns based on number of orientations (max 6 for layout)
            num_orientations = min(len(orientation_data), 6)
            orientation_cols = st.columns(num_orientations)
            
            sorted_orientations = sorted(orientation_data.items(), key=lambda x: x[1]['avg'], reverse=True)
            
            for i, (orientation, data) in enumerate(sorted_orientations[:num_orientations]):
                with orientation_cols[i]:
                    orientation_label = orientation if orientation and orientation.strip() else f"Direction {i+1}"
                    count_pct = (data['count'] / total_elements) * 100
                    st.metric(
                        f"{orientation_label}",
                        f"{data['count']:,} elements",
                        delta=f"{data['avg']:.0f} kWh/m²/year"
                    )
                    st.caption(f"{count_pct:.1f}% of total | Avg radiation")
        
        # MATRIX DISPLAY - ROW 5: Economic & Energy Potential
        st.markdown("**💰 Economic & Energy Potential Matrix**")
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            # Estimate annual energy yield (kWh/year)
            annual_yield = bipv_suitable * avg_radiation * avg_glass_area * 0.15
            st.metric("Est. Annual Yield", f"{annual_yield:,.0f} kWh/year")
        with col2:
            # Estimate annual cost savings (€0.30/kWh)
            annual_savings = annual_yield * 0.30
            st.metric("Est. Annual Savings", f"€{annual_savings:,.0f}")
        with col3:
            # Estimate system cost (€3,500/kW)
            system_cost = potential_capacity * 3500
            st.metric("Est. System Cost", f"€{system_cost:,.0f}")
        with col4:
            # Estimate payback period
            payback_years = system_cost / annual_savings if annual_savings > 0 else 0
            st.metric("Est. Payback Period", f"{payback_years:.1f} years")
        with col5:
            # Estimate CO2 savings (0.5 kg CO2/kWh grid avoided)
            co2_savings = annual_yield * 0.5 / 1000  # Convert to tonnes
            st.metric("Est. CO2 Savings", f"{co2_savings:.1f} tonnes/year")
        
        # Enhanced radiation distribution with multiple visualizations
        st.markdown("### 📈 Radiation Distribution Analysis")
        
        radiation_values = [float(r['annual_radiation']) if r['annual_radiation'] else 0.0 for r in element_radiation]
        
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
                orientation_data[orientation].append(float(element['annual_radiation']) if element['annual_radiation'] else 0.0)
            
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
                        
                        # Ensure all values are float for multiplication
                        annual_radiation = float(element['annual_radiation']) if element['annual_radiation'] else 0.0
                        potential_yield = annual_radiation * glass_area * 0.15  # 15% efficiency
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
        
        # Navigation - Single Continue Button  
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("⚡ Continue to Step 6: BIPV Panel Specifications →", type="primary", key="nav_step6"):
                st.query_params['step'] = 'pv_specification'
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
        try:
            if 'conn' in locals() and conn:
                conn.close()
        except:
            pass  # Ignore connection close errors

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