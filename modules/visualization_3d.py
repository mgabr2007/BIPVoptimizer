import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

def create_building_geometry():
    """Create basic 3D building geometry for visualization."""
    # Simplified building geometry - in real implementation this would come from BIM
    
    # Building envelope (rectangular)
    building_width = 30
    building_depth = 20
    building_height = 40
    
    # Define building faces
    faces = {
        'South': {
            'vertices': [
                [0, 0, 0], [building_width, 0, 0], 
                [building_width, 0, building_height], [0, 0, building_height]
            ],
            'normal': [0, -1, 0],
            'azimuth': 180
        },
        'North': {
            'vertices': [
                [building_width, building_depth, 0], [0, building_depth, 0], 
                [0, building_depth, building_height], [building_width, building_depth, building_height]
            ],
            'normal': [0, 1, 0],
            'azimuth': 0
        },
        'East': {
            'vertices': [
                [building_width, 0, 0], [building_width, building_depth, 0], 
                [building_width, building_depth, building_height], [building_width, 0, building_height]
            ],
            'normal': [1, 0, 0],
            'azimuth': 90
        },
        'West': {
            'vertices': [
                [0, building_depth, 0], [0, 0, 0], 
                [0, 0, building_height], [0, building_depth, building_height]
            ],
            'normal': [-1, 0, 0],
            'azimuth': 270
        }
    }
    
    return faces, building_width, building_depth, building_height

def create_pv_panel_geometry(x_center, y_center, z_center, width, height, orientation, panel_count_h, panel_count_v):
    """Create geometry for PV panels on a facade."""
    panels = []
    
    # Panel dimensions
    panel_spacing = 0.05  # 5cm spacing
    total_width = panel_count_h * width + (panel_count_h - 1) * panel_spacing
    total_height = panel_count_v * height + (panel_count_v - 1) * panel_spacing
    
    # Starting position (center of panel array)
    start_x = x_center - total_width / 2
    start_z = z_center - total_height / 2
    
    for i in range(panel_count_h):
        for j in range(panel_count_v):
            # Calculate panel position
            panel_x = start_x + i * (width + panel_spacing)
            panel_z = start_z + j * (height + panel_spacing)
            
            # Create panel vertices based on orientation
            if orientation == 'South':
                vertices = [
                    [panel_x, y_center, panel_z],
                    [panel_x + width, y_center, panel_z],
                    [panel_x + width, y_center, panel_z + height],
                    [panel_x, y_center, panel_z + height]
                ]
            elif orientation == 'North':
                vertices = [
                    [panel_x + width, y_center, panel_z],
                    [panel_x, y_center, panel_z],
                    [panel_x, y_center, panel_z + height],
                    [panel_x + width, y_center, panel_z + height]
                ]
            elif orientation == 'East':
                vertices = [
                    [x_center, panel_x, panel_z],
                    [x_center, panel_x + width, panel_z],
                    [x_center, panel_x + width, panel_z + height],
                    [x_center, panel_x, panel_z + height]
                ]
            elif orientation == 'West':
                vertices = [
                    [x_center, panel_x + width, panel_z],
                    [x_center, panel_x, panel_z],
                    [x_center, panel_x, panel_z + height],
                    [x_center, panel_x + width, panel_z + height]
                ]
            else:
                continue
            
            panels.append({
                'vertices': vertices,
                'orientation': orientation,
                'panel_id': f"{orientation}_{i}_{j}"
            })
    
    return panels

def create_mesh3d_from_vertices(vertices, color='blue', opacity=0.7, name='Surface'):
    """Create a Plotly Mesh3d object from vertices."""
    if len(vertices) != 4:
        return None
    
    # Extract coordinates
    x = [v[0] for v in vertices]
    y = [v[1] for v in vertices]
    z = [v[2] for v in vertices]
    
    # Define triangles for a rectangular face (2 triangles)
    i = [0, 0]  # First vertex of each triangle
    j = [1, 2]  # Second vertex of each triangle  
    k = [2, 3]  # Third vertex of each triangle
    
    return go.Mesh3d(
        x=x, y=y, z=z,
        i=i, j=j, k=k,
        color=color,
        opacity=opacity,
        name=name,
        showscale=False
    )

def visualize_radiation_heatmap(faces, radiation_data):
    """Create 3D visualization with radiation intensity heatmap."""
    fig = go.Figure()
    
    # Building faces with radiation coloring
    for orientation, face_data in faces.items():
        # Get radiation data for this orientation
        orientation_radiation = radiation_data[radiation_data['orientation'] == orientation]
        
        if len(orientation_radiation) > 0:
            avg_radiation = orientation_radiation['corrected_annual_irradiation'].mean()
            
            # Color based on radiation intensity
            if avg_radiation > 1400:
                color = 'red'
                opacity = 0.8
            elif avg_radiation > 1200:
                color = 'orange'
                opacity = 0.7
            elif avg_radiation > 1000:
                color = 'yellow'
                opacity = 0.6
            else:
                color = 'lightblue'
                opacity = 0.5
            
            mesh = create_mesh3d_from_vertices(
                face_data['vertices'], 
                color=color, 
                opacity=opacity,
                name=f"{orientation} ({avg_radiation:.0f} kWh/m²)"
            )
            
            if mesh:
                fig.add_trace(mesh)
    
    # Configure layout
    fig.update_layout(
        title="Building Facade Radiation Analysis",
        scene=dict(
            xaxis_title="X (m)",
            yaxis_title="Y (m)",
            zaxis_title="Z (m)",
            camera=dict(
                eye=dict(x=1.5, y=1.5, z=1.2)
            ),
            aspectmode='data'
        ),
        width=800,
        height=600
    )
    
    return fig

def visualize_pv_installation(selected_solution, pv_specs, radiation_data):
    """Create 3D visualization of selected PV installation."""
    
    # Get building geometry
    faces, building_width, building_depth, building_height = create_building_geometry()
    
    fig = go.Figure()
    
    # Add building structure (wireframe)
    for orientation, face_data in faces.items():
        vertices = face_data['vertices']
        
        # Add building face outline
        x_outline = [v[0] for v in vertices] + [vertices[0][0]]
        y_outline = [v[1] for v in vertices] + [vertices[0][1]]
        z_outline = [v[2] for v in vertices] + [vertices[0][2]]
        
        fig.add_trace(go.Scatter3d(
            x=x_outline,
            y=y_outline,
            z=z_outline,
            mode='lines',
            line=dict(color='gray', width=3),
            name=f"Building {orientation}",
            showlegend=False
        ))
    
    # Add selected PV systems
    selection_mask = selected_solution['selection_mask']
    selected_specs = pv_specs[selection_mask]
    
    panel_width = 1.65  # Standard panel width
    panel_height = 1.00  # Standard panel height
    
    for _, system in selected_specs.iterrows():
        orientation = system['orientation']
        
        if orientation not in faces:
            continue
        
        # Get face center for PV placement
        face_vertices = faces[orientation]['vertices']
        face_center_x = np.mean([v[0] for v in face_vertices])
        face_center_y = np.mean([v[1] for v in face_vertices])
        face_center_z = np.mean([v[2] for v in face_vertices])
        
        # Create PV panels
        panels = create_pv_panel_geometry(
            face_center_x, face_center_y, face_center_z,
            panel_width, panel_height, orientation,
            system['panels_horizontal'], system['panels_vertical']
        )
        
        # Add PV panels to visualization
        for panel in panels:
            mesh = create_mesh3d_from_vertices(
                panel['vertices'],
                color='darkblue',
                opacity=0.9,
                name=f"PV Panel {orientation}"
            )
            
            if mesh:
                fig.add_trace(mesh)
    
    # Configure layout
    fig.update_layout(
        title=f"3D PV Installation Visualization - {selected_solution['solution_id']}",
        scene=dict(
            xaxis_title="X (m)",
            yaxis_title="Y (m)",
            zaxis_title="Z (m)",
            camera=dict(
                eye=dict(x=1.8, y=1.8, z=1.5)
            ),
            aspectmode='data'
        ),
        width=900,
        height=700
    )
    
    return fig

def create_performance_3d_scatter(pv_specs, radiation_data):
    """Create 3D scatter plot of PV system performance."""
    
    # Merge specifications with radiation data
    merged_data = pd.merge(pv_specs, radiation_data, on='element_id', how='inner')
    
    fig = go.Figure()
    
    # Color by orientation
    orientations = merged_data['orientation_x'].unique()
    colors = px.colors.qualitative.Set1[:len(orientations)]
    
    for i, orientation in enumerate(orientations):
        orientation_data = merged_data[merged_data['orientation_x'] == orientation]
        
        fig.add_trace(go.Scatter3d(
            x=orientation_data['system_power_kw'],
            y=orientation_data['annual_energy_kwh'],
            z=orientation_data['corrected_annual_irradiation'],
            mode='markers',
            marker=dict(
                size=orientation_data['element_area'] / 10,  # Size by area
                color=colors[i],
                opacity=0.7
            ),
            name=orientation,
            text=orientation_data['element_id'],
            hovertemplate=
            '<b>%{text}</b><br>' +
            'Power: %{x:.1f} kW<br>' +
            'Annual Energy: %{y:.0f} kWh<br>' +
            'Irradiation: %{z:.0f} kWh/m²<br>' +
            '<extra></extra>'
        ))
    
    fig.update_layout(
        title="3D Performance Analysis: Power vs Energy vs Irradiation",
        scene=dict(
            xaxis_title="System Power (kW)",
            yaxis_title="Annual Energy (kWh)",
            zaxis_title="Solar Irradiation (kWh/m²)",
            camera=dict(
                eye=dict(x=1.5, y=1.5, z=1.2)
            )
        ),
        width=900,
        height=700
    )
    
    return fig

def render_3d_visualization():
    """Render the 3D visualization module."""
    
    st.header("10. 3D Visualization")
    st.markdown("Interactive 3D visualization of BIM facades with PV system overlays and performance analysis.")
    
    # Check prerequisites
    prerequisites = ['pv_specifications', 'radiation_grid']
    missing = [p for p in prerequisites if p not in st.session_state.project_data]
    
    if missing:
        st.warning(f"⚠️ Missing required data: {', '.join(missing)}")
        st.info("Please complete previous steps: PV specifications and radiation analysis.")
        return
    
    # Load data
    pv_specs = pd.DataFrame(st.session_state.project_data['pv_specifications'])
    radiation_data = pd.DataFrame(st.session_state.project_data['radiation_grid'])
    
    st.subheader("3D Visualization Options")
    
    # Visualization type selection
    viz_type = st.radio(
        "Select Visualization Type",
        ["Radiation Heatmap", "PV Installation Design", "Performance Analysis"],
        help="Choose the type of 3D visualization to display"
    )
    
    if viz_type == "Radiation Heatmap":
        st.subheader("Solar Radiation Heatmap")
        st.markdown("Visualize solar radiation intensity on building facades.")
        
        with st.spinner("Generating 3D radiation heatmap..."):
            try:
                # Create building geometry
                faces, _, _, _ = create_building_geometry()
                
                # Create radiation heatmap
                fig = visualize_radiation_heatmap(faces, radiation_data)
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Radiation legend
                st.markdown("**Radiation Intensity Legend:**")
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.markdown("🔴 **High (>1400 kWh/m²)**")
                with col2:
                    st.markdown("🟠 **Good (1200-1400 kWh/m²)**")
                with col3:
                    st.markdown("🟡 **Moderate (1000-1200 kWh/m²)**")
                with col4:
                    st.markdown("🔵 **Low (<1000 kWh/m²)**")
                
                # Radiation statistics
                st.subheader("Radiation Statistics by Orientation")
                
                orientation_stats = radiation_data.groupby('orientation').agg({
                    'annual_irradiation': ['mean', 'max', 'min'],
                    'corrected_annual_irradiation': ['mean', 'max', 'min'],
                    'element_id': 'count'
                }).round(0)
                
                orientation_stats.columns = ['Avg Raw', 'Max Raw', 'Min Raw', 'Avg Corrected', 'Max Corrected', 'Min Corrected', 'Elements']
                
                st.dataframe(orientation_stats, use_container_width=True)
                
            except Exception as e:
                st.error(f"❌ Error generating radiation heatmap: {str(e)}")
    
    elif viz_type == "PV Installation Design":
        st.subheader("PV Installation 3D Design")
        st.markdown("Visualize optimized PV panel placement on building facades.")
        
        # Check if optimization results are available
        if 'optimization_results' not in st.session_state.project_data:
            st.warning("⚠️ Please complete optimization analysis in Step 8 to visualize PV installations.")
            return
        
        # Load optimization results
        optimization_results = pd.DataFrame(st.session_state.project_data['optimization_results'])
        
        # Solution selection
        solution_options = optimization_results['solution_id'].tolist()
        selected_solution_id = st.selectbox(
            "Select Solution to Visualize",
            solution_options,
            help="Choose an optimized solution to view in 3D"
        )
        
        if selected_solution_id:
            selected_solution = optimization_results[optimization_results['solution_id'] == selected_solution_id].iloc[0]
            
            # Display solution info
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Selected Elements", selected_solution['selected_elements'])
            with col2:
                st.metric("Total Power", f"{selected_solution['system_power_kw']:.1f} kW")
            with col3:
                st.metric("Annual Energy", f"{selected_solution['annual_yield_kwh']:,.0f} kWh")
            with col4:
                st.metric("Installation Cost", f"${selected_solution['installation_cost']:,.0f}")
            
            with st.spinner("Generating 3D PV installation visualization..."):
                try:
                    fig = visualize_pv_installation(selected_solution, pv_specs, radiation_data)
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Installation details
                    st.subheader("Installation Details")
                    
                    if 'selected_element_ids' in selected_solution and selected_solution['selected_element_ids']:
                        selected_elements = pv_specs[pv_specs['element_id'].isin(selected_solution['selected_element_ids'])]
                        
                        # Group by orientation
                        orientation_summary = selected_elements.groupby('orientation').agg({
                            'element_id': 'count',
                            'system_power_kw': 'sum',
                            'annual_energy_kwh': 'sum',
                            'panels_count': 'sum'
                        }).reset_index()
                        
                        orientation_summary.columns = ['Orientation', 'Elements', 'Total Power (kW)', 'Annual Energy (kWh)', 'Panel Count']
                        orientation_summary = orientation_summary.round(1)
                        
                        st.dataframe(orientation_summary, use_container_width=True)
                
                except Exception as e:
                    st.error(f"❌ Error generating PV installation visualization: {str(e)}")
    
    elif viz_type == "Performance Analysis":
        st.subheader("3D Performance Analysis")
        st.markdown("Interactive 3D analysis of PV system performance metrics.")
        
        with st.spinner("Generating 3D performance visualization..."):
            try:
                fig = create_performance_3d_scatter(pv_specs, radiation_data)
                st.plotly_chart(fig, use_container_width=True)
                
                # Performance insights
                st.subheader("Performance Insights")
                
                # Best performing elements
                merged_data = pd.merge(pv_specs, radiation_data, on='element_id', how='inner')
                
                # Calculate performance score (normalized)
                merged_data['performance_score'] = (
                    merged_data['annual_energy_kwh'] / merged_data['annual_energy_kwh'].max() +
                    merged_data['corrected_annual_irradiation'] / merged_data['corrected_annual_irradiation'].max() +
                    merged_data['system_power_kw'] / merged_data['system_power_kw'].max()
                ) / 3
                
                top_performers = merged_data.nlargest(5, 'performance_score')
                
                st.markdown("**Top 5 Performing Elements:**")
                
                performance_display = top_performers[['element_id', 'orientation_x', 'system_power_kw', 
                                                    'annual_energy_kwh', 'corrected_annual_irradiation', 'performance_score']].copy()
                performance_display.columns = ['Element ID', 'Orientation', 'Power (kW)', 'Annual Energy (kWh)', 'Irradiation (kWh/m²)', 'Performance Score']
                performance_display = performance_display.round(3)
                
                st.dataframe(performance_display, use_container_width=True)
                
                # Performance by orientation
                col1, col2 = st.columns(2)
                
                with col1:
                    orientation_performance = merged_data.groupby('orientation_x').agg({
                        'performance_score': 'mean',
                        'annual_energy_kwh': 'mean',
                        'system_power_kw': 'mean'
                    }).reset_index()
                    
                    fig_perf = px.bar(
                        orientation_performance,
                        x='orientation_x',
                        y='performance_score',
                        title='Average Performance Score by Orientation',
                        labels={'performance_score': 'Performance Score', 'orientation_x': 'Orientation'}
                    )
                    st.plotly_chart(fig_perf, use_container_width=True)
                
                with col2:
                    # Power density analysis
                    merged_data['power_density'] = merged_data['system_power_kw'] / merged_data['element_area']
                    
                    fig_density = px.scatter(
                        merged_data,
                        x='element_area',
                        y='power_density',
                        color='orientation_x',
                        title='Power Density vs Element Area',
                        labels={'power_density': 'Power Density (kW/m²)', 'element_area': 'Element Area (m²)'}
                    )
                    st.plotly_chart(fig_density, use_container_width=True)
                
            except Exception as e:
                st.error(f"❌ Error generating performance analysis: {str(e)}")
    
    # Additional visualization tools
    st.subheader("Visualization Controls")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Export 3D Model Data"):
            # Create export data for 3D models
            export_data = {
                'building_geometry': create_building_geometry()[0],
                'pv_specifications': pv_specs.to_dict(),
                'radiation_data': radiation_data.to_dict()
            }
            
            import json
            json_data = json.dumps(export_data, indent=2, default=str)
            
            st.download_button(
                label="Download 3D Model JSON",
                data=json_data,
                file_name="bipv_3d_model_data.json",
                mime="application/json"
            )
    
    with col2:
        if st.button("Generate High-Resolution Images"):
            st.info("📸 High-resolution image export would be available in production version with additional plotly features.")
    
    # Visualization summary
    st.subheader("3D Visualization Summary")
    
    summary_metrics = {
        "Metric": [
            "Total Visualized Elements",
            "Orientations Covered",
            "Power Range",
            "Irradiation Range",
            "Best Performing Orientation"
        ],
        "Value": [
            f"{len(pv_specs)} elements",
            f"{len(pv_specs['orientation'].unique())} orientations",
            f"{pv_specs['system_power_kw'].min():.1f} - {pv_specs['system_power_kw'].max():.1f} kW",
            f"{radiation_data['corrected_annual_irradiation'].min():.0f} - {radiation_data['corrected_annual_irradiation'].max():.0f} kWh/m²",
            radiation_data.loc[radiation_data['corrected_annual_irradiation'].idxmax(), 'orientation']
        ]
    }
    
    st.table(summary_metrics)
    
    st.success("✅ 3D visualization completed! Ready for reporting and export.")
    
    # Additional info
    with st.expander("🔧 About 3D Visualization"):
        st.markdown("""
        **Available Visualizations:**
        1. **Radiation Heatmap**: Color-coded building facades showing solar radiation intensity
        2. **PV Installation Design**: 3D placement of optimized PV panels on building surfaces
        3. **Performance Analysis**: Interactive 3D scatter plots of system performance metrics
        
        **Features:**
        - Interactive 3D models with zoom, pan, and rotate
        - Real-time data integration from analysis modules
        - Performance-based color coding and sizing
        - Detailed hover information and tooltips
        
        **Export Options:**
        - 3D model data in JSON format
        - High-resolution image export (production version)
        - Integration with BIM software (future development)
        
        **Note**: Visualizations are based on simplified building geometry. 
        In production, full BIM integration would provide detailed architectural geometry.
        """)
