"""
Facade and Window Extraction page for BIPV Optimizer
"""
import streamlit as st
from services.io import parse_csv_content, save_building_elements, save_project_data


def render_facade_extraction():
    """Render the facade and window extraction module."""
    st.header("Step 4: BIM Model Facade & Window Extraction")
    st.markdown("Extract building geometry and window elements from BIM models for BIPV analysis.")
    
    # Check prerequisites
    if not st.session_state.get('project_data', {}).get('setup_complete'):
        st.error("Please complete Step 1: Project Setup first.")
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
            content = uploaded_csv.getvalue().decode('utf-8-sig')
            headers, data = parse_csv_content(content)
            
            # Clean headers
            headers = [h.strip().replace('\ufeff', '') for h in headers]
            
            # Process building elements
            windows = []
            total_glass_area = 0
            suitable_elements = 0
            
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
            
            for row in data:
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
                        else:
                            # Convert to float if provided as strings
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
                                'element_id': element_id,
                                'wall_hosted_id': host_wall_id,
                                'element_type': 'Window',
                                'category': category,
                                'family': family,
                                'level': level,
                                'orientation': orientation,
                                'azimuth': azimuth,
                                'glass_area': glass_area,
                                'window_area': window_area,
                                'window_width': window_width,
                                'window_height': window_height,
                                'suitable': suitable,
                                'pv_suitable': suitable
                            })
                    except (ValueError, TypeError):
                        continue
            
            # Store processed data
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
            
            # Save to database
            if 'project_id' in st.session_state:
                success = save_building_elements(st.session_state.project_id, windows)
                save_project_data(st.session_state.project_data)
                if success:
                    st.success(f"Saved {len(windows)} building elements to database")
            
            st.success(f"BIM data processed successfully! Analyzed {len(windows)} building elements.")
            
            # Display results
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Elements", len(windows))
            with col2:
                st.metric("Suitable Elements", suitable_elements)
            with col3:
                st.metric("Total Window Area", f"{total_glass_area:.1f} m²")
            with col4:
                suitability_rate = (suitable_elements / len(windows)) * 100 if windows else 0
                st.metric("Suitability Rate", f"{suitability_rate:.1f}%")
            
            # Orientation distribution
            st.subheader("Orientation Distribution")
            orientation_stats = {}
            for window in windows:
                orient = window['orientation']
                orientation_stats[orient] = orientation_stats.get(orient, 0) + 1
            
            st.bar_chart(orientation_stats)
            
            if st.button("Continue to Step 5: Radiation Analysis", key="continue_radiation"):
                st.session_state.current_step = 'radiation_grid'
                st.rerun()
                
        except Exception as e:
            st.error(f"Error processing CSV file: {str(e)}")
    
    else:
        st.info("Please upload a CSV file with BIM-extracted window data to continue.")
    
    # Display existing data if available
    if st.session_state.project_data.get('extraction_complete'):
        st.success("BIM extraction complete! You can proceed to Step 5: Radiation Analysis.")