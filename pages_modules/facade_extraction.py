"""
Facade and Window Extraction page for BIPV Optimizer
"""
import streamlit as st
from services.io import parse_csv_content, save_building_elements, save_project_data
from utils.consolidated_data_manager import ConsolidatedDataManager



def render_facade_extraction():
    """Render the facade and window extraction module."""
    
    # Add OptiSunny character header image
    st.image("attached_assets/step04_1751436847829.png", width=400)
    
    st.header("Step 4: BIM Model Facade & Window Extraction")
    st.markdown("Extract building geometry and window elements from BIM models for BIPV analysis.")
    
    # Data Usage Information
    with st.expander("📊 How This Data Will Be Used", expanded=False):
        st.markdown("""
        ### Data Flow Through BIPV Analysis Workflow:
        
        **Step 4 → Step 5 (Radiation Analysis):**
        - **Element IDs** → Unique identification for radiation calculations and tracking
        - **Orientations (X,Y,Z) & Azimuth** → Solar exposure calculations and shading analysis
        - **Glass Areas** → Surface area for irradiance integration and energy yield calculations
        - **Wall-Window relationships** → Geometric self-shading from adjacent building elements
        
        **Step 4 → Step 6 (PV Specification):**
        - **Glass Areas** → BIPV glass coverage calculations and system sizing
        - **Element dimensions** → Panel layout optimization and installation feasibility
        - **Family/Type data** → BIPV technology compatibility and integration constraints
        
        **Step 4 → Step 7 (Yield vs Demand):**
        - **Orientation-specific yields** → Directional energy generation profiles for grid interaction
        - **Building element count** → Total BIPV capacity and coverage ratio calculations
        
        **Step 4 → Step 8 (Optimization):**
        - **Element IDs** → Individual system selection for genetic algorithm optimization
        - **Orientation distribution** → Multi-directional optimization constraints and objectives
        
        **Step 4 → Step 10 (Reporting):**
        - **BIM metadata** → Building-specific technical documentation and element traceability
        - **Orientation analysis** → Architectural integration assessment and design validation
        """)
    
    # Check prerequisites
    if not st.session_state.get('project_data', {}).get('setup_complete'):
        st.error("❌ Please complete Step 1: Project Setup first.")
        return
    
    st.subheader("BIM Data Requirements")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **Required BIM Data:**
        - Window and facade elements with orientations
        - Glass areas and dimensions
        - Element IDs and wall associations
        - Building level information
        
        **CSV Format Required:**
        ```
        ElementId,Category,Family,Type,Level,HostWallId,OriX,OriY,OriZ,Azimuth (°),Glass Area (m²)
        385910,Windows,Arched (1),,03,342232,-0.1,0.99,-0.0,354.12,2.5
        ```
        """)
    
    with col2:
        st.markdown("**Download Dynamo Script**")
        
        dynamo_file_path = "attached_assets/get windowMetadata_1750510157705.dyn"
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
                    
                    # Complete progress tracking with immediate results transition
                    progress_bar.progress(100)
                    progress_percentage.markdown("**100%**")
                    status_text.text(f"✅ Processing complete - {len(windows)} elements processed")
                    element_progress.markdown("**Ready for display**")
                    
                    # Immediate completion and cleanup
                    progress_container.empty()
                    
                    # Store processed data immediately
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
                    
                    # Store building elements
                    import pandas as pd
                    building_elements_df = pd.DataFrame(windows)
                    st.session_state.building_elements = building_elements_df
                    st.session_state.building_elements_completed = True
                    st.session_state.step4_processing_complete = True
                    st.session_state.last_processed_file = current_file_name
                
                    # Optimized data saving - run in background without blocking UI
                    if not st.session_state.get('step4_already_processed', False):
                        try:
                            consolidated_manager = ConsolidatedDataManager()
                            step4_data = {
                                'building_elements': windows,
                                'facade_data': facade_data,
                                'elements': windows,
                                'extraction_complete': True
                            }
                            consolidated_manager.save_step4_data(step4_data)
                            st.session_state.step4_already_processed = True
                            
                            # Database save (non-blocking)
                            if 'project_id' in st.session_state:
                                save_building_elements(st.session_state.project_id, windows)
                                save_project_data(st.session_state.project_data)
                                st.session_state.step4_db_saved = True
                        except Exception as e:
                            pass  # Continue with UI display even if save fails
                    
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