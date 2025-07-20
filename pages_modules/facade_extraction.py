"""
Step 4: Integrated BIM Data Extraction for BIPV Analysis
Handles both window elements and wall self-shading data upload
"""
import streamlit as st
import pandas as pd
from database_manager import BIPVDatabaseManager
from utils.consolidated_data_manager import ConsolidatedDataManager
from utils.session_state_standardizer import BIPVSessionStateManager


# Initialize database manager
db_manager = BIPVDatabaseManager()
consolidated_manager = ConsolidatedDataManager()

def get_orientation_from_azimuth(azimuth):
    """Convert azimuth degrees to cardinal direction"""
    if pd.isna(azimuth):
        return "Unknown"
    
    azimuth = float(azimuth)
    if azimuth < 0:
        azimuth += 360
    azimuth = azimuth % 360
    
    if azimuth <= 45 or azimuth > 315:
        return "North"
    elif azimuth <= 135:
        return "East"
    elif azimuth <= 225:
        return "South"
    else:
        return "West"

def save_walls_data_to_database(project_id, walls_df, progress_callback=None):
    """Save wall data to building_walls table with progress tracking"""
    conn = db_manager.get_connection()
    if not conn:
        return False
        
    try:
        with conn.cursor() as cursor:
            # Delete existing wall data for this project
            cursor.execute("DELETE FROM building_walls WHERE project_id = %s", (project_id,))
            
            total_walls = len(walls_df)
            
            # Insert new wall data with progress tracking
            for idx, (_, row) in enumerate(walls_df.iterrows()):
                # Calculate wall height from area and length if available
                length = float(row.get('Length (m)', 0)) if pd.notna(row.get('Length (m)')) else 0
                area = float(row.get('Area (m²)', 0)) if pd.notna(row.get('Area (m²)')) else 0
                height = area / length if length > 0 else 3.0  # Calculate or default to 3m
                
                cursor.execute("""
                    INSERT INTO building_walls 
                    (project_id, element_id, name, wall_type, level, area, azimuth, orientation, height)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    project_id,
                    str(row.get('ElementId', '')),
                    str(row.get('Name', '')),
                    str(row.get('Wall Type', 'Generic Wall')),
                    str(row.get('Level', '')),
                    area,
                    float(row.get('Azimuth (°)', 0)) if pd.notna(row.get('Azimuth (°)')) else None,
                    get_orientation_from_azimuth(row.get('Azimuth (°)')),
                    height
                ))
                
                # Update progress if callback provided
                if progress_callback and (idx % 10 == 0 or idx == total_walls - 1):
                    progress = int((idx + 1) / total_walls * 100)
                    progress_callback(progress, f"Saving wall element {idx + 1}/{total_walls}")
            
            conn.commit()
            return True
            
    except Exception as e:
        conn.rollback()
        st.error(f"Error saving wall data: {e}")
        return False
    finally:
        conn.close()


def save_windows_data_to_database(project_id, windows_df, progress_callback=None):
    """Save windows data to building_elements table"""
    conn = db_manager.get_connection()
    if not conn:
        return False
        
    try:
        with conn.cursor() as cursor:
            # Delete existing window data for this project
            cursor.execute("DELETE FROM building_elements WHERE project_id = %s", (project_id,))
            
            total_windows = len(windows_df)
            
            # Insert new window data
            for idx, (_, row) in enumerate(windows_df.iterrows()):
                cursor.execute("""
                    INSERT INTO building_elements 
                    (project_id, element_id, element_type, family, building_level, wall_element_id, azimuth, glass_area, orientation, pv_suitable)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    project_id,
                    str(row.get('ElementId', '')),
                    str(row.get('Category', 'Windows')),  # Map Category to element_type
                    str(row.get('Family', '')),
                    str(row.get('Level', '')),  # Map Level to building_level
                    str(row.get('HostWallId', '')),  # Map HostWallId to wall_element_id
                    float(row.get('Azimuth (°)', 0)) if pd.notna(row.get('Azimuth (°)')) else None,
                    float(row.get('Glass Area (m²)', 1.5)) if pd.notna(row.get('Glass Area (m²)')) else 1.5,
                    get_orientation_from_azimuth(row.get('Azimuth (°)')),
                    False  # Will be updated after radiation analysis
                ))
                
                # Update progress if callback provided
                if progress_callback and (idx % 10 == 0 or idx == total_windows - 1):
                    progress = int((idx + 1) / total_windows * 100)
                    progress_callback(progress, f"Saving window element {idx + 1}/{total_windows}")
            
            conn.commit()
            return True
            
    except Exception as e:
        conn.rollback()
        st.error(f"Error saving window data: {e}")
        return False
    finally:
        conn.close()


def render_facade_extraction():
    """Render facade extraction page with proper project data loading"""
    
    # Ensure project data is loaded from database
    from services.io import get_current_project_id, ensure_project_data_loaded
    
    if not ensure_project_data_loaded():
        st.error("Please complete Step 1: Project Setup first.")
        return
    
    project_id = get_current_project_id()
    if not project_id:
        st.error("Project ID not found. Please complete Step 1 first.")
        return
    
    st.header("Step 4: Integrated BIM Data Extraction")
    st.markdown("Upload both window elements and wall self-shading data for comprehensive BIPV analysis.")
    
    # Data Usage Information
    with st.expander("📊 How This Integrated Data Will Be Used", expanded=False):
        st.markdown("""
        ### Integrated BIM Data Flow Through BIPV Analysis:
        
        **Windows & Glass Areas Data:**
        - **Element IDs** → Unique identification for radiation calculations and BIPV system tracking
        - **Orientations & Azimuth** → Solar exposure calculations for each window element
        - **Glass Areas** → Surface area for BIPV glass replacement and energy yield calculations
        - **Host Wall Relationships** → Connection between windows and their supporting walls
        
        **Wall Self-Shading Data:**
        - **Wall Element IDs** → Geometric definition of building surfaces for shadow calculations
        - **Wall Orientations & Dimensions** → Precise geometric self-shading analysis
        - **Building Levels** → Multi-story shading effects and height-dependent solar access
        - **Wall-Window Relationships** → Accurate shadow casting on adjacent window elements
        
        **Integrated Analysis Benefits:**
        - **Step 5 (Radiation)**: Uses both datasets for precise geometric self-shading calculations
        - **Step 6 (PV Specification)**: Window data for BIPV glass sizing and coverage analysis
        - **Step 7-8 (Optimization)**: Combined data for realistic building-specific performance modeling
        - **Step 10 (Reporting)**: Complete building geometry documentation with authentic data relationships
        """)
    
    # Check prerequisites - use centralized project ID function
    
    # Get current project ID from database
    from services.io import get_current_project_id
    project_id = get_current_project_id()
    
    # Debug information
    if st.checkbox("Show Debug Info", key="debug_step4"):
        st.write("**Debug Information:**")
        st.write(f"- Project name: {st.session_state.get('project_name')}")
        st.write(f"- Database project_id: {project_id}")
        st.write(f"- Setup complete: {st.session_state.get('project_data', {}).get('setup_complete')}")
    
    if not project_id:
        st.error("❌ No project ID found. Please complete Step 1: Project Setup first.")
        st.info("💡 **Tip:** Make sure to click 'Save Project Configuration' in Step 1 to generate a project ID.")
        return
    
    project_name = st.session_state.get('project_name', 'Unnamed')
    st.info(f"📋 Current Project: **{project_name}** (ID: {project_id})")
    
    # BIM Data Upload Interface
    st.subheader("🏢 Step 1: Window & Glass Areas Data Upload")
    
    windows_upload_col1, windows_upload_col2 = st.columns([1, 1])
    
    with windows_upload_col1:
        st.markdown("""
        **Required Window Data Fields:**
        - `ElementId`: Unique window identifier
        - `Category`: Window category (Windows)
        - `Family`: Window family type
        - `Level`: Building floor level
        - `HostWallId`: Parent wall element ID
        - `Azimuth (°)`: Window orientation in degrees
        - `Glass Area (m²)`: Glass surface area for BIPV
        """)
    
    with windows_upload_col2:
        windows_file = st.file_uploader(
            "📁 Upload Windows & Glass Areas CSV",
            type=['csv'],
            key="windows_csv_upload",
            help="Upload BIM-extracted window elements with glass areas for BIPV analysis"
        )
    
    # Process Windows CSV Upload
    windows_uploaded = False
    windows_element_count = 0
    
    if windows_file is not None:
        try:
            # Read and process CSV
            windows_df = pd.read_csv(windows_file)
            
            # Validate record count
            if len(windows_df) == 0:
                st.error("❌ **CSV File Contains Zero Records**")
                st.error("The uploaded CSV file is empty or contains only headers. Please upload a file with actual building element data.")
                return
            
            # Display summary metrics only
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Windows", len(windows_df))
            with col2:
                if 'Glass Area (m²)' in windows_df.columns:
                    total_glass = windows_df['Glass Area (m²)'].sum()
                    st.metric("Total Glass Area", f"{total_glass:.1f} m²")
                else:
                    st.metric("Total Glass Area", "N/A")
            with col3:
                if 'Level' in windows_df.columns:
                    levels = windows_df['Level'].nunique()
                    st.metric("Building Levels", levels)
                else:
                    st.metric("Building Levels", "N/A")
            with col4:
                if 'Family' in windows_df.columns:
                    families = windows_df['Family'].nunique()
                    st.metric("Window Types", families)
                else:
                    st.metric("Window Types", "N/A")
            
            # Save to database
            if st.button("💾 Save Windows Data", key="save_windows_data"):
                # Create progress bar
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                try:
                    total_elements = len(windows_df)
                    
                    # Step 1: Initialize database save
                    status_text.text(f"Initializing database save for {total_elements} window elements...")
                    progress_bar.progress(5)
                    
                    # Step 2: Prepare data processing
                    status_text.text("Preparing window data for database insertion...")
                    progress_bar.progress(10)
                    
                    # Step 3: Process elements batch by batch with progress tracking
                    status_text.text(f"Processing {total_elements} window elements...")
                    progress_bar.progress(15)
                    
                    # Step 4: Save to database with detailed progress
                    status_text.text("Saving window elements to database...")
                    progress_bar.progress(20)
                    
                    # Create progress callback function for windows
                    def update_window_progress(progress, message):
                        progress_bar.progress(progress)
                        status_text.text(message)
                    
                    # Call database save with progress callback
                    if db_manager.save_building_elements_with_progress(project_id, windows_df, update_window_progress):
                        status_text.text("Database save completed!")
                        progress_bar.progress(60)
                        progress_bar.progress(60)
                        status_text.text("Updating consolidated data manager...")
                        
                        # Step 3: Update consolidated data manager with correct step reference
                        # Safe glass area calculation with field name validation
                        glass_area_total = 0
                        if 'Glass Area (m²)' in windows_df.columns:
                            glass_area_total = windows_df['Glass Area (m²)'].sum()
                        
                        facade_data_to_save = {
                            'building_elements': windows_df.to_dict('records'),
                            'element_count': len(windows_df),
                            'glass_area_total': glass_area_total,
                            'extraction_complete': True
                        }
                        consolidated_manager.save_step_data('4', facade_data_to_save)
                        progress_bar.progress(80)
                        
                        # Step 4: Update session state with validation
                        status_text.text("Updating session state...")
                        # Ensure project_data exists in session state
                        if 'project_data' not in st.session_state:
                            st.session_state.project_data = {}
                        
                        st.session_state.project_data['building_elements'] = windows_df.to_dict('records')
                        st.session_state.project_data['element_count'] = len(windows_df)
                        st.session_state.project_data['extraction_complete'] = True
                        st.session_state['facade_completed'] = True
                        
                        # Step 5: Standardize element IDs
                        status_text.text("Standardizing element IDs...")
                        BIPVSessionStateManager.standardize_element_ids()
                        progress_bar.progress(100)
                        
                        # Complete
                        status_text.text("✅ Window data saved successfully!")
                        windows_uploaded = True
                        windows_element_count = len(windows_df)
                        
                        # Ensure project context is set for Step 5
                        st.session_state.project_id = project_id
                        st.session_state.step4_completed = True
                        
                        # Force refresh to show updated status
                        st.rerun()
                    else:
                        progress_bar.progress(100)
                        status_text.text("❌ Failed to save window data")
                        st.error("❌ Failed to save window data")
                        
                except Exception as e:
                    progress_bar.progress(100)
                    status_text.text(f"❌ Error: {str(e)}")
                    st.error(f"❌ Error saving window data: {str(e)}")
                    
        except Exception as e:
            st.error(f"Error processing windows CSV: {str(e)}")
    
    # Check if windows data already exists - only if project_id is defined
    if not windows_uploaded and 'project_id' in locals() and project_id:
        conn = db_manager.get_connection()
        if conn:
            try:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT COUNT(*) FROM building_elements WHERE project_id = %s", (project_id,))
                    windows_element_count = cursor.fetchone()[0]
                    windows_uploaded = windows_element_count > 0
            except Exception as e:
                st.error(f"Error checking existing windows data: {e}")
            finally:
                conn.close()
    
    # Wall Data Upload Section
    st.subheader("🧱 Step 2: Wall Self-Shading Data Upload")
    
    walls_upload_col1, walls_upload_col2 = st.columns([1, 1])
    
    with walls_upload_col1:
        st.markdown("""
        **Required Wall Data Fields:**
        - `ElementId`: Unique wall identifier
        - `Wall Type`: Wall construction type
        - `Level`: Building floor level
        - `Length (m)`: Wall length in meters
        - `Area (m²)`: Wall surface area
        - `Azimuth (°)`: Wall orientation in degrees
        - `OriX, OriY, OriZ`: Wall normal vectors
        """)
    
    with walls_upload_col2:
        walls_file = st.file_uploader(
            "📁 Upload Wall Self-Shading CSV", 
            type=['csv'],
            key="walls_csv_upload",
            help="Upload BIM-extracted wall elements for geometric self-shading calculations"
        )
    
    # Process Walls CSV Upload
    walls_uploaded = False
    wall_element_count = 0
    
    if walls_file is not None:
        try:
            # Read and process CSV
            walls_df = pd.read_csv(walls_file)
            
            # Validate record count
            if len(walls_df) == 0:
                st.error("❌ **CSV File Contains Zero Records**")
                st.error("The uploaded walls CSV file is empty or contains only headers. Please upload a file with actual wall element data.")
                return
            
            # Display summary metrics only
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Walls", len(walls_df))
            with col2:
                if 'Area (m²)' in walls_df.columns:
                    total_area = walls_df['Area (m²)'].sum()
                    st.metric("Total Wall Area", f"{total_area:.0f} m²")
                else:
                    st.metric("Total Wall Area", "N/A")
            with col3:
                if 'Level' in walls_df.columns:
                    levels = walls_df['Level'].nunique()
                    st.metric("Building Levels", levels)
                else:
                    st.metric("Building Levels", "N/A")
            with col4:
                if 'Azimuth (°)' in walls_df.columns:
                    orientations = walls_df['Azimuth (°)'].apply(get_orientation_from_azimuth).value_counts()
                    st.metric("Orientations", len(orientations))
                else:
                    st.metric("Orientations", "N/A")
            
            # Save to database
            if st.button("💾 Save Wall Data", key="save_walls_data"):
                # Create progress bar
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                try:
                    total_walls = len(walls_df)
                    
                    # Step 1: Initialize database save
                    status_text.text(f"Initializing database save for {total_walls} wall elements...")
                    progress_bar.progress(5)
                    
                    # Step 2: Process orientations
                    status_text.text(f"Processing orientations for {total_walls} wall elements...")
                    progress_bar.progress(15)
                    
                    # Step 3: Prepare database insertion
                    status_text.text("Preparing wall data for database insertion...")
                    progress_bar.progress(25)
                    
                    # Step 4: Save to database with detailed progress
                    status_text.text("Saving wall elements to database...")
                    progress_bar.progress(30)
                    
                    # Create progress callback function
                    def update_wall_progress(progress, message):
                        progress_bar.progress(progress)
                        status_text.text(message)
                    
                    if save_walls_data_to_database(project_id, walls_df, update_wall_progress):
                        status_text.text("Database save completed!")
                        progress_bar.progress(80)
                        progress_bar.progress(80)
                        status_text.text("Updating wall data status...")
                        
                        walls_uploaded = True
                        wall_element_count = len(walls_df)
                        progress_bar.progress(100)
                        
                        # Complete
                        status_text.text("✅ Wall data saved successfully!")
                        
                        # Ensure project context is set for Step 5
                        st.session_state.project_id = project_id
                        st.session_state.step4_completed = True
                        
                        # Force refresh to show updated status
                        st.rerun()
                    else:
                        progress_bar.progress(100)
                        status_text.text("❌ Failed to save wall data")
                        st.error("❌ Failed to save wall data")
                        
                except Exception as e:
                    progress_bar.progress(100)
                    status_text.text(f"❌ Error: {str(e)}")
                    st.error(f"❌ Error saving wall data: {str(e)}")
                    
        except Exception as e:
            st.error(f"Error processing walls CSV: {str(e)}")
    
    # Check if wall data already exists - only if project_id is defined
    if not walls_uploaded and 'project_id' in locals() and project_id:
        conn = db_manager.get_connection()
        if conn:
            try:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT COUNT(*) FROM building_walls WHERE project_id = %s", (project_id,))
                    wall_element_count = cursor.fetchone()[0]
                    walls_uploaded = wall_element_count > 0
            except Exception as e:
                st.error(f"Error checking existing wall data: {e}")
            finally:
                conn.close()
    
    # Combined Status & Navigation
    st.subheader("📋 Integrated BIM Data Status")
    
    col1, col2 = st.columns(2)
    with col1:
        if windows_uploaded:
            st.success(f"✅ Window Elements: {windows_element_count:,} uploaded")
        else:
            st.error("❌ Window Elements: Not uploaded")
    with col2:
        if walls_uploaded:
            st.success(f"✅ Wall Elements: {wall_element_count:,} uploaded")
        else:
            st.error("❌ Wall Elements: Not uploaded")
    
    # Data relationships analysis and Step 5 readiness
    if windows_uploaded and walls_uploaded:
        st.success("🔗 **Step 5 Ready**: Both window and wall data uploaded successfully!")
        st.info("✅ **Step 5 Integration Confirmed**: Radiation analysis can now access your building geometry data for self-shading calculations")
        
        # Provide navigation guidance
        with st.expander("📋 What happens next in Step 5", expanded=False):
            st.markdown(f"""
            **Your uploaded data is now available for radiation analysis:**
            - **{windows_element_count:,} Window Elements**: Ready for BIPV suitability analysis
            - **{wall_element_count:,} Wall Elements**: Ready for self-shading calculations
            
            **Step 5 will use this data to:**
            - Calculate solar radiation on each window element
            - Apply wall-based self-shading corrections
            - Determine BIPV potential for each window
            - Generate comprehensive radiation grid analysis
            
            **Project Context**: Your data is saved to Project ID {project_id}
            """)
    elif windows_uploaded:
        st.warning("⚠️ **Partial Upload**: Windows uploaded, but walls data needed for complete self-shading analysis")
    elif walls_uploaded:
        st.warning("⚠️ **Partial Upload**: Walls uploaded, but windows data needed for radiation analysis")
        st.markdown("""
        **Next Steps:**
        1. **Step 5 (Radiation Analysis)**: Will use both datasets for precise geometric self-shading calculations
        2. **Window-Wall Relationships**: System will match windows to their host walls for accurate shadow analysis
        3. **Building Geometry**: Complete 3D building model ready for solar radiation calculations
        """)
        
        # Show data relationships
        with st.expander("🔍 Data Relationship Analysis", expanded=False):
            conn = db_manager.get_connection()
            if conn:
                try:
                    with conn.cursor() as cursor:
                        # Get window-wall relationships
                        cursor.execute("""
                            SELECT 
                                COUNT(DISTINCT be.element_id) as windows,
                                COUNT(DISTINCT be.host_wall_id) as unique_host_walls,
                                COUNT(DISTINCT bw.element_id) as available_walls
                            FROM building_elements be
                            LEFT JOIN building_walls bw ON be.host_wall_id = bw.element_id AND be.project_id = bw.project_id
                            WHERE be.project_id = %s
                        """, (project_id,))
                        
                        result = cursor.fetchone()
                        if result:
                            windows, host_walls, available_walls = result
                            
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Windows", windows)
                            with col2:
                                st.metric("Host Walls Referenced", host_walls)
                            with col3:
                                st.metric("Available Wall Elements", available_walls)
                                
                            # Calculate relationship coverage
                            if host_walls > 0:
                                coverage = (available_walls / host_walls) * 100 if host_walls > 0 else 0
                                st.metric("Wall-Window Relationship Coverage", f"{coverage:.1f}%")
                                
                except Exception as e:
                    st.error(f"Error analyzing relationships: {e}")
                finally:
                    conn.close()
    
    elif windows_uploaded:
        st.warning("⚠️ **Partial Upload**: Window data uploaded, but wall data is still needed for complete analysis")
    elif walls_uploaded:
        st.warning("⚠️ **Partial Upload**: Wall data uploaded, but window data is still needed for complete analysis")
    else:
        st.info("📋 **Ready to Upload**: Please upload both window and wall CSV files to proceed")
    
    # Navigation
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        if st.button("← Weather Environment", key="step4_prev_btn", use_container_width=True):
            st.session_state.current_step = 'weather_environment'
            st.rerun()
    
    with col2:
        # Remove duplicate step number display - handled by global navigation
        pass
    
    with col3:
        if st.button("Radiation Grid →", key="step4_next_btn", use_container_width=True):
            st.session_state.current_step = 'radiation_grid'
            st.rerun()


def save_windows_data_to_database(project_id, windows_df, progress_callback=None):
    """Save windows data to building_elements table"""
    conn = db_manager.get_connection()
    if not conn:
        return False
        
    try:
        with conn.cursor() as cursor:
            # Delete existing window data for this project
            cursor.execute("DELETE FROM building_elements WHERE project_id = %s", (project_id,))
            
            total_windows = len(windows_df)
            
            # Insert new window data
            for idx, (_, row) in enumerate(windows_df.iterrows()):
                cursor.execute("""
                    INSERT INTO building_elements 
                    (project_id, element_id, element_type, family, building_level, wall_element_id, azimuth, glass_area, orientation, pv_suitable)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    project_id,
                    str(row.get('ElementId', '')),
                    str(row.get('Category', 'Windows')),  # Map Category to element_type
                    str(row.get('Family', '')),
                    str(row.get('Level', '')),  # Map Level to building_level
                    str(row.get('HostWallId', '')),  # Map HostWallId to wall_element_id
                    float(row.get('Azimuth (°)', 0)) if pd.notna(row.get('Azimuth (°)')) else None,
                    float(row.get('Glass Area (m²)', 1.5)) if pd.notna(row.get('Glass Area (m²)')) else 1.5,
                    get_orientation_from_azimuth(row.get('Azimuth (°)')),
                    False  # Will be updated after radiation analysis
                ))
                
                # Update progress if callback provided
                if progress_callback and (idx % 10 == 0 or idx == total_windows - 1):
                    progress = int((idx + 1) / total_windows * 100)
                    progress_callback(progress, f"Saving window element {idx + 1}/{total_windows}")
            
            conn.commit()
            return True
            
    except Exception as e:
        conn.rollback()
        st.error(f"Error saving window data: {e}")
        return False
    finally:
        conn.close()


def render_facade_extraction():
    """Main render function for facade extraction module"""
    
    # Import required functions
    from services.io import get_current_project_id, ensure_project_data_loaded
    
    # Check if project setup is complete
    if not ensure_project_data_loaded():
        st.error("Please complete Step 1: Project Setup first.")
        return
    
    project_id = get_current_project_id()
    if not project_id:
        st.error("Project ID not found. Please complete Step 1 first.")
        return
    
    st.header("Step 4: Integrated BIM Data Extraction")
    st.markdown("Upload both window elements and wall self-shading data for comprehensive BIPV analysis.")
    
    # Data Usage Information
    with st.expander("📊 How This Data Will Be Used", expanded=False):
        st.markdown("""
        ### BIM Data Flow Through BIPV Analysis:
        
        **Windows & Glass Areas:**
        - Element IDs → Unique identification for radiation calculations
        - Orientations → Solar exposure calculations
        - Glass Areas → BIPV glass replacement sizing
        
        **Wall Self-Shading:**
        - Wall geometries → Shadow calculations
        - Multi-story effects → Height-dependent analysis
        """)
    
    project_name = st.session_state.get('project_name', 'Unnamed')
    st.info(f"📋 Current Project: **{project_name}** (ID: {project_id})")
    
    # Windows Upload Section
    st.subheader("🏢 Window Elements Upload")
    
    windows_file = st.file_uploader(
        "📁 Upload Windows CSV",
        type=['csv'],
        key="windows_csv_upload",
        help="Upload BIM-extracted window elements"
    )
    
    if windows_file is not None:
        if st.button("💾 Save Windows Data", key="save_windows", use_container_width=True):
            try:
                windows_df = pd.read_csv(windows_file)
                
                # Simple processing without progress callback
                success = save_windows_data_to_database(project_id, windows_df)
                
                if success:
                    st.success(f"Successfully processed {len(windows_df)} window elements")
                    st.rerun()
                else:
                    st.error("Failed to save windows data")
                    
            except Exception as e:
                st.error(f"Error processing windows file: {e}")
    
    # Walls Upload Section
    st.markdown("---")
    st.subheader("🏗️ Wall Self-Shading Data Upload")
    
    walls_file = st.file_uploader(
        "📁 Upload Walls CSV",
        type=['csv'],
        key="walls_csv_upload",
        help="Upload BIM-extracted wall elements for self-shading calculations"
    )
    
    if walls_file is not None:
        if st.button("💾 Save Walls Data", key="save_walls", use_container_width=True):
            try:
                walls_df = pd.read_csv(walls_file)
                
                # Simple processing without progress callback
                success = save_walls_data_to_database(project_id, walls_df)
                
                if success:
                    st.success(f"Successfully processed {len(walls_df)} wall elements")
                    st.rerun()
                else:
                    st.error("Failed to save walls data")
                    
            except Exception as e:
                st.error(f"Error processing walls file: {e}")
    
    # Check data status for both windows and walls
    conn = db_manager.get_connection()
    windows_uploaded = False
    walls_uploaded = False
    
    if conn:
        try:
            with conn.cursor() as cursor:
                # Check windows data
                cursor.execute("SELECT COUNT(*) FROM building_elements WHERE project_id = %s", (project_id,))
                windows_count = cursor.fetchone()[0]
                windows_uploaded = windows_count > 0
                
                # Check walls data
                cursor.execute("SELECT COUNT(*) FROM building_walls WHERE project_id = %s", (project_id,))
                walls_count = cursor.fetchone()[0]
                walls_uploaded = walls_count > 0
                
        except Exception as e:
            st.error(f"Error checking data status: {e}")
        finally:
            conn.close()
    
    # Combined Status display
    st.markdown("---")
    st.subheader("📊 Upload Status")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if windows_uploaded:
            st.success("✅ Window data uploaded successfully")
        else:
            st.warning("⚠️ Window data needed")
    
    with col2:
        if walls_uploaded:
            st.success("✅ Wall data uploaded successfully") 
        else:
            st.warning("⚠️ Wall data needed")
    
    # Overall completion status
    if windows_uploaded and walls_uploaded:
        st.success("🎉 **Complete BIM Data**: Both window and wall data uploaded successfully!")
        st.info("💡 **Ready for Step 5**: Radiation analysis can now use authentic building geometry for self-shading calculations")
    elif windows_uploaded:
        st.warning("⚠️ **Partial Upload**: Window data uploaded, but wall data is still needed for complete analysis")
    elif walls_uploaded:
        st.warning("⚠️ **Partial Upload**: Wall data uploaded, but window data is still needed for complete analysis")
    else:
        st.info("📋 **Ready to Upload**: Please upload both window and wall CSV files to proceed")
    
    # Navigation
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        if st.button("← Weather Environment", key="step4_prev", use_container_width=True):
            st.session_state.current_step = 'weather_environment'
            st.rerun()
    
    with col3:
        if st.button("Radiation Grid →", key="step4_next", use_container_width=True):
            st.session_state.current_step = 'radiation_grid'
            st.rerun()