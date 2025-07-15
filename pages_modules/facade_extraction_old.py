"""
Step 4: Integrated BIM Data Extraction for BIPV Analysis
Handles both window elements and wall self-shading data upload
"""
import streamlit as st
import pandas as pd
from database_manager import BIPVDatabaseManager
from utils.consolidated_data_manager import ConsolidatedDataManager
from utils.navigation import render_bottom_navigation



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

def save_walls_data_to_database(project_id, walls_df):
    """Save wall data to building_walls table"""
    conn = db_manager.get_connection()
    if not conn:
        return False
        
    try:
        with conn.cursor() as cursor:
            # Delete existing wall data for this project
            cursor.execute("DELETE FROM building_walls WHERE project_id = %s", (project_id,))
            
            # Insert new wall data
            for _, row in walls_df.iterrows():
                cursor.execute("""
                    INSERT INTO building_walls 
                    (project_id, element_id, name, wall_type, level, length_m, area_m2, volume_m3, 
                     ori_x, ori_y, ori_z, azimuth, orientation)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    project_id,
                    str(row.get('ElementId', '')),
                    str(row.get('Name', '')),
                    str(row.get('Wall Type', '')),
                    str(row.get('Level', '')),
                    float(row.get('Length (m)', 0)) if pd.notna(row.get('Length (m)')) else None,
                    float(row.get('Area (m²)', 0)) if pd.notna(row.get('Area (m²)')) else None,
                    float(row.get('Volume (m³)', 0)) if pd.notna(row.get('Volume (m³)')) else None,
                    float(row.get('OriX', 0)) if pd.notna(row.get('OriX')) else None,
                    float(row.get('OriY', 0)) if pd.notna(row.get('OriY')) else None,
                    float(row.get('OriZ', 0)) if pd.notna(row.get('OriZ')) else None,
                    float(row.get('Azimuth (°)', 0)) if pd.notna(row.get('Azimuth (°)')) else None,
                    get_orientation_from_azimuth(row.get('Azimuth (°)'))
                ))
            
            conn.commit()
            return True
            
    except Exception as e:
        conn.rollback()
        st.error(f"Error saving wall data: {e}")
        return False
    finally:
        conn.close()

def render_facade_extraction():
    """Render the integrated BIM data extraction module."""
    
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
    
    # Check prerequisites
    if not st.session_state.get('project_data', {}).get('setup_complete'):
        st.error("❌ Please complete Step 1: Project Setup first.")
        return
    
    # Get current project ID
    project_data = st.session_state.get('project_data', {})
    project_id = project_data.get('project_id')
    
    if not project_id:
        st.error("❌ No project ID found. Please complete Step 1: Project Setup first.")
        return
    
    st.info(f"📋 Current Project: **{project_data.get('project_name', 'Unnamed')}** (ID: {project_id})")
    
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
            
            # Display preview
            st.markdown("### 🔍 Windows Data Preview")
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
                    
            # Display sample rows
            st.dataframe(windows_df.head(), use_container_width=True)
            
            # Save to database
            if st.button("💾 Save Windows Data", key="save_windows_data"):
                if db_manager.save_building_elements(project_id, windows_df):
                    st.success("✅ Window data saved successfully!")
                    windows_uploaded = True
                    windows_element_count = len(windows_df)
                    
                    # Update consolidated data manager
                    consolidated_manager.save_step_data(project_id, 'facade_extraction', {
                        'building_elements': windows_df.to_dict('records'),
                        'element_count': len(windows_df),
                        'glass_area_total': windows_df['Glass Area (m²)'].sum() if 'Glass Area (m²)' in windows_df.columns else 0
                    })
                    
                    # Force refresh to show updated status
                    st.rerun()
                else:
                    st.error("❌ Failed to save window data")
                    
        except Exception as e:
            st.error(f"Error processing windows CSV: {str(e)}")
    
    # Check if windows data already exists
    conn = db_manager.get_connection()
    if conn and not windows_uploaded:
        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM building_elements WHERE project_id = %s", (project_id,))
                windows_element_count = cursor.fetchone()[0]
                windows_uploaded = windows_element_count > 0
        except:
            pass
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
            
            # Display preview
            st.markdown("### 🔍 Wall Data Preview")
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
                    
            # Display sample rows
            st.dataframe(walls_df.head(), use_container_width=True)
            
            # Save to database
            if st.button("💾 Save Wall Data", key="save_walls_data"):
                if save_walls_data_to_database(project_id, walls_df):
                    st.success("✅ Wall data saved successfully!")
                    walls_uploaded = True
                    wall_element_count = len(walls_df)
                    # Force refresh to show updated status
                    st.rerun()
                else:
                    st.error("❌ Failed to save wall data")
                    
        except Exception as e:
            st.error(f"Error processing walls CSV: {str(e)}")
    
    # Check if wall data already exists
    if conn and not walls_uploaded:
        conn = db_manager.get_connection()
        if conn:
            try:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT COUNT(*) FROM building_walls WHERE project_id = %s", (project_id,))
                    wall_element_count = cursor.fetchone()[0]
                    walls_uploaded = wall_element_count > 0
            except:
                pass
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
    
    # Data relationships analysis
    if windows_uploaded and walls_uploaded:
        st.success("🔗 **Ready for Step 5**: Both window and wall data uploaded successfully!")
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
    render_bottom_navigation(['Welcome', 'Project Setup', 'Historical Data', 'Weather Environment', 'Facade Extraction'], 'Facade Extraction')
        try:
            with open(dynamo_file_path, 'rb') as f:
                dynamo_content = f.read()
            
            st.download_button(
                label="Download Dynamo Script (.dyn)",
                data=dynamo_content,
                file_name="get_windowMetadata.dyn",
                mime="application/octet-stream",
                help="🔧 Download this Dynamo script to extract window and facade element data from Revit models. Run in Dynamo for Revit to export ElementId, Category, Family, Type, Level, HostWallId, Orientations (X,Y,Z), Azimuth, and Glass Area data to CSV format.",
                key="download_dynamo"
            )
        except FileNotFoundError:
            st.error("Dynamo script file not found.")
    
    # CSV file upload
    st.subheader("Upload BIM-Extracted CSV Data")
    
    uploaded_csv = st.file_uploader(
        "Select BIM CSV file",
        type=['csv'],
        help="📁 Upload CSV file containing window and facade element data extracted from your BIM model using the Dynamo script. Required columns: ElementId, Category, Family, Type, Level, HostWallId, OriX, OriY, OriZ, Azimuth (°), Glass Area (m²). This data is essential for all subsequent BIPV analysis steps.",
        key="bim_csv_upload"
    )
    
    if uploaded_csv is not None:
        try:
            # Check if this file was already processed to prevent reprocessing on any page rerun
            current_file_name = uploaded_csv.name
            last_processed_file = st.session_state.get('last_processed_file', '')
            processing_complete = st.session_state.get('step4_processing_complete', False)
            
            # Only process if it's a new file OR data hasn't been processed yet
            if (current_file_name != last_processed_file or not processing_complete):
                
                # Use spinner instead of progress bar to avoid interface fading
                with st.spinner("Processing CSV file..."):
                    content = uploaded_csv.getvalue().decode('utf-8-sig')
                    headers, data = parse_csv_content(content)
                    
                    # Clean headers
                    headers = [h.strip().replace('\ufeff', '') for h in headers]
                    
                    # Mark this file as processed
                    st.session_state.last_processed_file = current_file_name
                
                # Initialize variables at the top level
                windows = []
                facade_data = {}
                suitable_elements = 0
                total_glass_area = 0
                
                # Check if this specific file was already processed to avoid duplication
                if (st.session_state.get('step4_processing_complete', False) and 
                    current_file_name == last_processed_file):
                    st.info("CSV data already processed. Displaying existing results.")
                    # Display existing data without reprocessing
                    if 'building_elements' in st.session_state:
                        windows = st.session_state.building_elements.to_dict('records')
                        facade_data = st.session_state.project_data.get('facade_data', {})
                        suitable_elements = facade_data.get('suitable_elements', 0)
                        total_glass_area = facade_data.get('total_glass_area', 0)
                        # Skip to display results
                        st.success(f"BIM data processed successfully! Analyzed {len(windows)} building elements.")
                    else:
                        st.warning("No processed data found. Please re-upload the CSV file.")
                        return
                else:
                    # Process building elements with enhanced progress tracking
                    total_rows = len(data)
                    
                    # Create prominent progress section
                    st.subheader("🔄 Processing BIM Elements")
                    progress_container = st.container()
                    
                    with progress_container:
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            progress_bar = st.progress(0)
                        with col2:
                            progress_percentage = st.empty()
                        
                        status_text = st.empty()
                        element_progress = st.empty()
                        
                    st.markdown("---")
                
                    def get_orientation_from_azimuth(azimuth):
                        azimuth = float(azimuth) % 360
                        if 315 <= azimuth or azimuth < 45:
                            return "North (315-45°)"
                        elif 45 <= azimuth < 135:
                            return "East (45-135°)"
                        elif 135 <= azimuth < 225:
                            return "South (135-225°)"
                        elif 225 <= azimuth < 315:
                            return "West (225-315°)"
                        return "Unknown"
                
                    # Process elements with enhanced progress tracking
                    for i, row in enumerate(data):
                        # Update progress indicators with enhanced visibility
                        percentage_complete = int(100 * i / total_rows)
                        progress_bar.progress(percentage_complete)
                        progress_percentage.markdown(f"**{percentage_complete}%**")
                        status_text.text(f"Processing element {i+1} of {total_rows}")
                        
                        if len(row) >= len(headers):
                            try:
                                element_data = dict(zip(headers, row))
                                
                                element_id = str(element_data.get('ElementId', '')).strip()
                                host_wall_id = str(element_data.get('HostWallId', '')).strip()
                                category = element_data.get('Category', '').strip()
                                family = element_data.get('Family', '').strip()
                                level = element_data.get('Level', '').strip()
                                azimuth = float(element_data.get('Azimuth (°)', 0))
                                glass_area = float(element_data.get('Glass Area (m²)', 0))
                                
                                # Show current element being processed with color coding
                                element_progress.markdown(f"🏢 **{element_id}** | {category} | {level}")
                            
                                # Extract window dimensions if available
                                window_width = element_data.get('Width (m)', element_data.get('Window Width', element_data.get('width', None)))
                                window_height = element_data.get('Height (m)', element_data.get('Window Height', element_data.get('height', None)))
                                
                                # Calculate dimensions from glass area if not provided
                                if window_width is None or window_height is None:
                                    if glass_area > 0:
                                        # Estimate dimensions based on typical window aspect ratios
                                        if 'arched' in family.lower() or 'arch' in family.lower():
                                            # Arched windows typically wider than tall
                                            aspect_ratio = 1.2  # width/height
                                            window_height = (glass_area / aspect_ratio) ** 0.5
                                            window_width = glass_area / window_height
                                        elif 'casement' in family.lower():
                                            # Casement windows typically taller than wide
                                            aspect_ratio = 0.8  # width/height
                                            window_height = (glass_area / aspect_ratio) ** 0.5
                                            window_width = glass_area / window_height
                                        else:
                                            # Standard rectangular windows
                                            aspect_ratio = 1.0  # square-ish
                                            window_height = (glass_area / aspect_ratio) ** 0.5
                                            window_width = glass_area / window_height
                                    else:
                                        # Default dimensions for windows with no area data
                                        window_width = 1.2
                                        window_height = 1.5
                                
                                # Convert to float if provided as strings
                                if window_width is None or window_height is None:
                                    window_width = float(window_width) if window_width else 1.2
                                    window_height = float(window_height) if window_height else 1.5
                                
                                orientation = get_orientation_from_azimuth(azimuth)
                                
                                is_window = category.lower() in ['windows', 'window', 'curtain wall', 'curtainwall', 'glazing']
                                
                                if is_window:
                                    window_area = glass_area if glass_area > 0 else window_width * window_height
                                    
                                    # PV suitability scoring
                                    suitable = False
                                    if orientation in ["South (135-225°)", "East (45-135°)", "West (225-315°)"]:
                                        suitable = True
                                
                                    if suitable:
                                        suitable_elements += 1
                                    
                                    total_glass_area += window_area
                                
                                windows.append({
                                    'ElementId': element_id,  # Keep original BIM column name
                                    'element_id': element_id,  # Also store with standard name
                                    'HostWallId': host_wall_id,
                                    'wall_hosted_id': host_wall_id,
                                    'element_type': 'Window',
                                    'Category': category,
                                    'category': category,
                                    'Family': family,
                                    'family': family,
                                    'Level': level,
                                    'level': level,
                                    'orientation': orientation,
                                    'azimuth': azimuth,
                                    'tilt': 90,  # Windows are typically vertical
                                    'glass_area': glass_area,
                                    'area': glass_area,  # For radiation calculations
                                    'window_area': window_area,
                                    'window_width': window_width,
                                    'window_height': window_height,
                                    'suitable': suitable,
                                    'pv_suitable': suitable
                                })
                            except (ValueError, TypeError):
                                continue
                    
                    # Complete progress tracking with immediate cleanup and display
                    progress_bar.progress(100)
                    progress_container.empty()  # Clear progress immediately
                    
                    # Store essential data for immediate display (minimal operations)
                    facade_data = {
                        'total_elements': len(windows),
                        'suitable_elements': suitable_elements,
                        'total_glass_area': total_glass_area,
                        'total_window_area': total_glass_area,
                        'windows': windows,
                        'csv_processed': True
                    }
                
                    st.session_state.project_data['facade_data'] = facade_data
                    st.session_state.project_data['extraction_complete'] = True
                    st.session_state.step4_processing_complete = True
                    st.session_state.last_processed_file = current_file_name
                    
                    # Show immediate completion message
                    st.success(f"✅ Processing complete! Analyzed {len(windows)} building elements with {suitable_elements} suitable for BIPV.")
            
            else:
                # File already processed, just display existing results without reprocessing
                if 'building_elements' in st.session_state:
                    windows = st.session_state.building_elements.to_dict('records')
                    facade_data = st.session_state.project_data.get('facade_data', {})
                    suitable_elements = facade_data.get('suitable_elements', 0)
                    total_glass_area = facade_data.get('total_glass_area', 0)
                else:
                    st.warning("No processed data found. Please re-upload the CSV file.")
                    return
            
            # Display results
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Elements", len(windows))
            with col2:
                st.metric("Suitable Elements", suitable_elements, 
                         help="Elements that meet BIPV suitability criteria - click the info section below for details")
            with col3:
                st.metric("Total Window Area", f"{total_glass_area:.1f} m²")
            with col4:
                suitability_rate = (suitable_elements / len(windows)) * 100 if windows else 0
                st.metric("Suitability Rate", f"{suitability_rate:.1f}%")
            
            # BIPV Suitability Criteria Explanation
            with st.expander("🔍 BIPV Suitability Criteria - What Makes Elements 'Suitable'?", expanded=False):
                st.markdown("""
                ### BIPV Suitability Assessment Criteria
                
                The system evaluates each building element against specific criteria to determine if it's suitable for BIPV installation:
                
                #### ✅ **Suitable Elements** (Selected for BIPV):
                **Orientation Requirements:**
                - **South-facing (135-225°)**: Optimal solar exposure in Northern Hemisphere
                - **East-facing (45-135°)**: Good morning solar capture
                - **West-facing (225-315°)**: Good afternoon solar capture
                
                **Technical Requirements:**
                - All window and glazing elements regardless of area size
                - Structural compatibility for BIPV glass replacement
                - Access for installation and maintenance
                
                #### ❌ **Non-Suitable Elements** (Excluded from BIPV):
                **Orientation Limitations:**
                - **North-facing (315-45°)**: Poor solar performance (only 30% of south-facing efficiency)
                - Limited annual solar radiation (900 kWh/m² vs 1800 kWh/m² for south)
                
                **Why North Windows Are Excluded:**
                - Low energy production makes investment uneconomical
                - Poor return on investment (ROI)
                - Higher cost per kWh generated
                - Focus resources on high-performing orientations for maximum impact
                
                #### 📊 **Performance Comparison by Orientation:**
                - **South**: 1800 kWh/m²/year (100% - Optimal)
                - **East/West**: 1400 kWh/m²/year (78% - Good)
                - **North**: 900 kWh/m²/year (50% - Poor)
                
                #### 💡 **Why This Filtering Matters:**
                1. **Economic Efficiency**: Focus investment on high-performing elements
                2. **Maximum ROI**: Prioritize elements with best solar exposure
                3. **System Optimization**: Ensure optimal energy production per euro invested
                4. **Implementation Strategy**: Phase installation starting with best-performing orientations
                
                **Result**: Your BIPV system will only include the most economically viable window elements, maximizing energy production and financial returns.
                """)
            
            # Orientation distribution
            st.subheader("Orientation Distribution")
            orientation_stats = {}
            for window in windows:
                orient = window['orientation']
                orientation_stats[orient] = orientation_stats.get(orient, 0) + 1
            
            st.bar_chart(orientation_stats)
            
            # Background data saving (after UI display is complete)
            if st.session_state.get('step4_processing_complete') and not st.session_state.get('step4_data_saved', False):
                try:
                    # Store building elements DataFrame
                    import pandas as pd
                    building_elements_df = pd.DataFrame(windows)
                    st.session_state.building_elements = building_elements_df
                    st.session_state.building_elements_completed = True
                    
                    # Save to consolidated data manager
                    from database_manager import ConsolidatedDataManager
                    consolidated_manager = ConsolidatedDataManager()
                    step4_data = {
                        'building_elements': windows,
                        'facade_data': st.session_state.project_data['facade_data'],
                        'elements': windows,
                        'extraction_complete': True
                    }
                    consolidated_manager.save_step4_data(step4_data)
                    
                    # Database save using helper
                    db_helper.save_step_data("building_elements", windows)
                    
                    # Database save for building elements with detailed debugging
                    if 'project_id' in st.session_state:
                        from database_manager import db_manager
                        project_id = st.session_state.project_id
                        
                        st.write(f"**Debug**: Attempting to save {len(windows)} elements to database for project {project_id}")
                        st.write(f"**Debug**: Sample element data: {windows[0] if windows else 'No elements'}")
                        
                        success = db_manager.save_building_elements(project_id, windows)
                        if success:
                            st.success(f"✅ Successfully saved {len(windows)} building elements to database for project {project_id}")
                            
                            # Verify the save worked
                            from psycopg2.extras import RealDictCursor
                            conn = db_manager.get_connection()
                            if conn:
                                try:
                                    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                                        cursor.execute("SELECT COUNT(*) as count FROM building_elements WHERE project_id = %s", (project_id,))
                                        result = cursor.fetchone()
                                        st.write(f"**Verification**: Database now contains {result['count']} elements for project {project_id}")
                                except Exception as e:
                                    st.error(f"Verification failed: {e}")
                                finally:
                                    conn.close()
                        else:
                            st.error("❌ Failed to save building elements to database")
                        
                        # Save project data
                        db_manager.save_project(st.session_state.project_data)
                    else:
                        st.warning("⚠️ No project_id found in session state - cannot save to database")
                    
                    st.session_state.step4_data_saved = True
                except Exception as e:
                    pass  # Continue silently if background save fails
            
            # Add step-specific download button
            st.markdown("---")
            st.markdown("### 📄 Step 4 Analysis Report")
            st.markdown("Download detailed BIM facade and window extraction analysis report:")
            
            from utils.individual_step_reports import create_step_download_button
            create_step_download_button(4, "Facade Extraction", "Download BIM Analysis Report")
            
            st.markdown("---")
            
            if st.button("Continue to Step 5: Radiation Analysis", key="continue_radiation"):
                st.session_state.current_step = 'radiation_grid'
                st.session_state.scroll_to_top = True
                st.rerun()
                
        except Exception as e:
            st.error(f"Error processing CSV file: {str(e)}")
    
    else:
        st.info("Please upload a CSV file with BIM-extracted window data to continue.")
    
    # Display existing data if available
    if st.session_state.project_data.get('extraction_complete'):
        st.success("BIM extraction complete! You can proceed to Step 5: Radiation Analysis.")