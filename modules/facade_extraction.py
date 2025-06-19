import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

def simulate_revit_extraction():
    """Simulate facade and window extraction from Revit models."""
    # This would normally use pythonnet + Revit API
    # For now, we'll simulate the extraction process
    
    facades = []
    windows = []
    
    # Generate sample facade data
    orientations = ['North', 'South', 'East', 'West']
    
    for i, orientation in enumerate(orientations):
        # Main facade
        facade = {
            'id': f'FACADE_{i+1:03d}',
            'type': 'Wall',
            'orientation': orientation,
            'area': np.random.uniform(100, 300),
            'height': np.random.uniform(8, 15),
            'width': np.random.uniform(15, 25),
            'tilt': 90,  # Vertical walls
            'azimuth': i * 90,  # 0=North, 90=East, 180=South, 270=West
            'pv_suitable': orientation in ['South', 'East', 'West'],
            'material': 'Concrete',
            'floor_level': np.random.randint(1, 6)
        }
        facades.append(facade)
        
        # Generate windows for this facade
        num_windows = np.random.randint(3, 8)
        for j in range(num_windows):
            window = {
                'id': f'WIN_{i+1:03d}_{j+1:02d}',
                'facade_id': facade['id'],
                'type': 'Window',
                'orientation': orientation,
                'area': np.random.uniform(2, 8),
                'height': np.random.uniform(1.2, 2.5),
                'width': np.random.uniform(1.0, 3.0),
                'tilt': 90,
                'azimuth': i * 90,
                'pv_suitable': True,  # Windows can be replaced with PV
                'glazing_type': np.random.choice(['Double', 'Triple']),
                'frame_material': np.random.choice(['Aluminum', 'Wood', 'UPVC'])
            }
            windows.append(window)
    
    return pd.DataFrame(facades), pd.DataFrame(windows)

def filter_pv_suitable_elements(facades_df, windows_df):
    """Filter elements suitable for PV installation."""
    
    # Filter criteria for PV suitability
    suitable_facades = facades_df[
        (facades_df['pv_suitable'] == True) &
        (facades_df['area'] >= 20) &  # Minimum area for PV installation
        (facades_df['orientation'].isin(['South', 'East', 'West']))
    ].copy()
    
    suitable_windows = windows_df[
        (windows_df['pv_suitable'] == True) &
        (windows_df['area'] >= 2) &  # Minimum window area
        (windows_df['orientation'].isin(['South', 'East', 'West']))
    ].copy()
    
    return suitable_facades, suitable_windows

def calculate_element_geometry(df):
    """Calculate additional geometry metadata for elements."""
    df = df.copy()
    
    # Calculate aspect ratio
    df['aspect_ratio'] = df['width'] / df['height']
    
    # Calculate orientation factor (South = 1.0, East/West = 0.8, North = 0.3)
    orientation_factors = {'South': 1.0, 'East': 0.8, 'West': 0.8, 'North': 0.3}
    df['orientation_factor'] = df['orientation'].map(orientation_factors)
    
    # Calculate effective area (considering orientation)
    df['effective_area'] = df['area'] * df['orientation_factor']
    
    # Estimate installation complexity
    df['complexity'] = pd.cut(df['area'], bins=[0, 10, 50, 200, float('inf')], 
                             labels=['Simple', 'Moderate', 'Complex', 'Very Complex'])
    
    return df

def render_facade_extraction():
    """Render the facade and window extraction module."""
    
    st.header("4. Facade & Window Extraction")
    st.markdown("Extract facade and window elements from BIM models and identify PV-suitable surfaces.")
    
    # Check if models are uploaded
    if 'lod200_model' not in st.session_state.project_data:
        st.warning("⚠️ Please upload LOD 200 BIM model in Step 1 before proceeding.")
        return
    
    st.subheader("BIM Model Analysis")
    
    # Display model information
    lod200_info = st.session_state.project_data['lod200_model']
    st.info(f"📁 Analyzing model: {lod200_info['name']} ({lod200_info['size'] / 1024 / 1024:.2f} MB)")
    
    # Extraction process
    if st.button("Extract Facades and Windows"):
        with st.spinner("Extracting building elements from Revit model..."):
            try:
                # Simulate Revit API extraction
                # In real implementation, this would use pythonnet + Revit API
                facades_df, windows_df = simulate_revit_extraction()
                
                # Store extracted data
                st.session_state.project_data['extracted_facades'] = facades_df.to_dict()
                st.session_state.project_data['extracted_windows'] = windows_df.to_dict()
                
                st.success(f"✅ Extraction complete! Found {len(facades_df)} facades and {len(windows_df)} windows.")
                
                # Display extraction summary
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Facades", len(facades_df))
                with col2:
                    st.metric("Total Windows", len(windows_df))
                with col3:
                    st.metric("Total Facade Area", f"{facades_df['area'].sum():.1f} m²")
                with col4:
                    st.metric("Total Window Area", f"{windows_df['area'].sum():.1f} m²")
                
            except Exception as e:
                st.error(f"❌ Error during extraction: {str(e)}")
                return
    
    # Display extracted elements if available
    if 'extracted_facades' in st.session_state.project_data:
        facades_df = pd.DataFrame(st.session_state.project_data['extracted_facades'])
        windows_df = pd.DataFrame(st.session_state.project_data['extracted_windows'])
        
        # Filter PV-suitable elements
        suitable_facades, suitable_windows = filter_pv_suitable_elements(facades_df, windows_df)
        
        # Calculate geometry metadata
        suitable_facades = calculate_element_geometry(suitable_facades)
        suitable_windows = calculate_element_geometry(suitable_windows)
        
        # Store filtered data
        st.session_state.project_data['pv_suitable_facades'] = suitable_facades.to_dict()
        st.session_state.project_data['pv_suitable_windows'] = suitable_windows.to_dict()
        
        st.subheader("PV-Suitable Elements")
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Suitable Facades", len(suitable_facades))
        with col2:
            st.metric("Suitable Windows", len(suitable_windows))
        with col3:
            st.metric("Available Facade Area", f"{suitable_facades['area'].sum():.1f} m²")
        with col4:
            st.metric("Available Window Area", f"{suitable_windows['area'].sum():.1f} m²")
        
        # Orientation distribution
        col1, col2 = st.columns(2)
        
        with col1:
            if len(suitable_facades) > 0:
                facade_orientation = suitable_facades.groupby('orientation')['area'].sum().reset_index()
                fig_facade_orient = px.pie(facade_orientation, values='area', names='orientation',
                                          title='Facade Area by Orientation')
                st.plotly_chart(fig_facade_orient, use_container_width=True)
        
        with col2:
            if len(suitable_windows) > 0:
                window_orientation = suitable_windows.groupby('orientation')['area'].sum().reset_index()
                fig_window_orient = px.pie(window_orientation, values='area', names='orientation',
                                          title='Window Area by Orientation')
                st.plotly_chart(fig_window_orient, use_container_width=True)
        
        # Detailed facade table
        st.subheader("Facade Elements Details")
        if len(suitable_facades) > 0:
            # Display table with key columns
            facade_display = suitable_facades[['id', 'orientation', 'area', 'height', 'width', 
                                             'effective_area', 'complexity']].round(2)
            st.dataframe(facade_display, use_container_width=True)
            
            # Area vs effective area comparison
            fig_area_comp = go.Figure()
            fig_area_comp.add_trace(go.Bar(name='Total Area', x=suitable_facades['id'], y=suitable_facades['area']))
            fig_area_comp.add_trace(go.Bar(name='Effective Area', x=suitable_facades['id'], y=suitable_facades['effective_area']))
            fig_area_comp.update_layout(title='Facade Area vs Effective Area (considering orientation)',
                                       xaxis_title='Facade ID', yaxis_title='Area (m²)')
            st.plotly_chart(fig_area_comp, use_container_width=True)
        else:
            st.warning("No suitable facades found for PV installation.")
        
        # Detailed window table
        st.subheader("Window Elements Details")
        if len(suitable_windows) > 0:
            # Display table with key columns
            window_display = suitable_windows[['id', 'facade_id', 'orientation', 'area', 
                                             'height', 'width', 'glazing_type']].round(2)
            st.dataframe(window_display, use_container_width=True)
            
            # Window size distribution
            fig_window_size = px.scatter(suitable_windows, x='width', y='height', color='orientation',
                                        size='area', hover_data=['id'],
                                        title='Window Size Distribution',
                                        labels={'width': 'Width (m)', 'height': 'Height (m)'})
            st.plotly_chart(fig_window_size, use_container_width=True)
        else:
            st.warning("No suitable windows found for PV installation.")
        
        # Installation complexity analysis
        st.subheader("Installation Complexity Analysis")
        
        if len(suitable_facades) > 0:
            complexity_summary = suitable_facades.groupby('complexity').agg({
                'id': 'count',
                'area': 'sum'
            }).reset_index()
            complexity_summary.columns = ['Complexity', 'Count', 'Total Area']
            
            col1, col2 = st.columns(2)
            with col1:
                fig_complexity_count = px.bar(complexity_summary, x='Complexity', y='Count',
                                             title='Facade Count by Installation Complexity')
                st.plotly_chart(fig_complexity_count, use_container_width=True)
            
            with col2:
                fig_complexity_area = px.bar(complexity_summary, x='Complexity', y='Total Area',
                                            title='Total Area by Installation Complexity')
                st.plotly_chart(fig_complexity_area, use_container_width=True)
        
        # Export options
        st.subheader("Export Extracted Data")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Export Facades CSV"):
                csv_facades = suitable_facades.to_csv(index=False)
                st.download_button(
                    label="Download Facades CSV",
                    data=csv_facades,
                    file_name="pv_suitable_facades.csv",
                    mime="text/csv"
                )
        
        with col2:
            if st.button("Export Windows CSV"):
                csv_windows = suitable_windows.to_csv(index=False)
                st.download_button(
                    label="Download Windows CSV",
                    data=csv_windows,
                    file_name="pv_suitable_windows.csv",
                    mime="text/csv"
                )
        
        # Summary and next steps
        st.success("✅ Facade and window extraction completed successfully!")
        
        total_pv_area = suitable_facades['area'].sum() + suitable_windows['area'].sum()
        st.info(f"📊 Total PV-suitable area: {total_pv_area:.1f} m² available for solar installation")
        
    else:
        st.info("👆 Please run the extraction process to analyze facade and window elements.")
        
        # Show extraction process info
        with st.expander("🔧 About the Extraction Process"):
            st.markdown("""
            **The extraction process will:**
            1. Connect to the uploaded Revit model using pythonnet + Revit API
            2. Identify all wall and window elements
            3. Extract geometry data (area, dimensions, orientation)
            4. Filter elements suitable for PV installation based on:
               - Minimum area requirements
               - Favorable orientations (South, East, West)
               - Structural suitability
            5. Calculate metadata for installation planning
            
            **Note:** This implementation simulates the extraction process.
            In production, it would require Revit and the appropriate API setup.
            """)
