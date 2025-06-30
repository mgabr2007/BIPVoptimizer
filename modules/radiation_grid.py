import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import pvlib

def calculate_solar_position(latitude, longitude, times):
    """Calculate solar position for given location and times."""
    location = pvlib.location.Location(latitude=latitude, longitude=longitude)
    solar_position = location.get_solarposition(times)
    return solar_position

def calculate_irradiance_on_surface(ghi, dni, dhi, solar_position, surface_tilt, surface_azimuth):
    """Calculate irradiance on tilted surface using pvlib."""
    try:
        # Calculate plane of array irradiance
        poa_irradiance = pvlib.irradiance.get_total_irradiance(
            surface_tilt=surface_tilt,
            surface_azimuth=surface_azimuth,
            solar_zenith=solar_position['zenith'],
            solar_azimuth=solar_position['azimuth'],
            dni=dni,
            ghi=ghi,
            dhi=dhi
        )
        return poa_irradiance['poa_global']
    except:
        # Fallback calculation if pvlib fails
        return ghi * np.cos(np.radians(surface_tilt))

def generate_radiation_grid(suitable_elements, tmy_data, latitude, longitude, shading_factors=None, walls_data=None):
    """Generate radiation grid for all suitable elements with wall-window relationship analysis."""
    
    # Convert TMY data
    tmy_df = pd.DataFrame(tmy_data)
    tmy_df['datetime'] = pd.to_datetime(tmy_df['datetime'])
    
    # Calculate solar positions
    solar_position = calculate_solar_position(latitude, longitude, tmy_df['datetime'])
    
    radiation_grid = []
    
    for _, element in suitable_elements.iterrows():
        # Calculate irradiance for this element's orientation and tilt
        surface_irradiance = calculate_irradiance_on_surface(
            ghi=tmy_df['GHI'],
            dni=tmy_df['DNI'],
            dhi=tmy_df['DHI'],
            solar_position=solar_position,
            surface_tilt=element['tilt'],
            surface_azimuth=element['azimuth']
        )
        
        # Apply shading correction if available
        if shading_factors is not None:
            hour = tmy_df['datetime'].dt.hour
            shading_correction = hour.map(
                dict(zip(range(24), [shading_factors.get(str(h), {'shading_factor': 1.0})['shading_factor'] for h in range(24)]))
            )
            surface_irradiance = surface_irradiance * shading_correction
        
        # Enhanced wall-window relationship analysis
        host_wall_id = element.get('HostWallId', element.get('wall_hosted_id', 'Unknown'))
        wall_info = {'exists': False, 'area': 0, 'level': 'Unknown', 'azimuth_match': False}
        
        # If walls data is available, find the host wall
        if walls_data is not None and host_wall_id != 'Unknown':
            matching_wall = walls_data[walls_data['ElementId'] == host_wall_id]
            if not matching_wall.empty:
                wall_row = matching_wall.iloc[0]
                wall_info = {
                    'exists': True,
                    'area': wall_row.get('Area (m²)', 0),
                    'level': wall_row.get('Level', 'Unknown'),
                    'azimuth_match': abs(wall_row.get('Azimuth (°)', 0) - element['azimuth']) < 15,
                    'wall_azimuth': wall_row.get('Azimuth (°)', 0)
                }
        
        # Calculate statistics
        element_radiation = {
            'element_id': element.get('ElementId', element.get('id', f"element_{element.name if hasattr(element, 'name') else 'unknown'}")),
            'element_type': element.get('Category', element.get('type', 'Unknown')),
            'orientation': element['orientation'],
            'area': element.get('glass_area', element.get('area', 1.5)),
            'glass_area': element.get('glass_area', element.get('area', 1.5)),
            'tilt': element['tilt'],
            'azimuth': element['azimuth'],
            'annual_irradiation': surface_irradiance.sum(),  # kWh/m²/year
            'peak_irradiance': surface_irradiance.max(),  # W/m²
            'avg_irradiance': surface_irradiance.mean(),  # W/m²
            'capacity_factor': surface_irradiance.mean() / 1000,  # Simplified capacity factor
            'monthly_irradiation': surface_irradiance.groupby(tmy_df['datetime'].dt.month).sum().to_dict(),
            'family': element.get('Family', 'Unknown'),
            'level': element.get('Level', 'Unknown'),
            'host_wall_id': host_wall_id,
            'host_wall_exists': wall_info['exists'],
            'host_wall_area': wall_info['area'],
            'host_wall_level': wall_info['level'],
            'azimuth_match_with_wall': wall_info.get('azimuth_match', False)
        }
        
        radiation_grid.append(element_radiation)
    
    return pd.DataFrame(radiation_grid)

def apply_orientation_corrections(radiation_df):
    """Apply orientation and tilt corrections to radiation calculations."""
    
    # Orientation factor corrections (relative to south-facing)
    orientation_corrections = {
        'South': 1.0,
        'Southwest': 0.95,
        'Southeast': 0.95,
        'West': 0.85,
        'East': 0.85,
        'Northwest': 0.70,
        'Northeast': 0.70,
        'North': 0.50
    }
    
    # Apply corrections
    radiation_df = radiation_df.copy()
    radiation_df['orientation_correction'] = radiation_df['orientation'].map(
        lambda x: orientation_corrections.get(x, 0.8)
    )
    
    # Tilt factor corrections (optimal tilt varies by latitude)
    def tilt_correction(tilt, latitude):
        optimal_tilt = abs(latitude)  # Simplified optimal tilt
        tilt_diff = abs(tilt - optimal_tilt)
        return max(0.7, 1 - (tilt_diff / 90) * 0.3)  # Max 30% loss at 90° from optimal
    
    radiation_df['tilt_correction'] = radiation_df.apply(
        lambda row: tilt_correction(row['tilt'], 40), axis=1  # Using default latitude
    )
    
    # Apply corrections to irradiation values
    radiation_df['corrected_annual_irradiation'] = (
        radiation_df['annual_irradiation'] * 
        radiation_df['orientation_correction'] * 
        radiation_df['tilt_correction']
    )
    
    return radiation_df

def render_radiation_grid():
    """Render the radiation and shading grid analysis module."""
    
    st.header("5. Radiation & Shading Grid")
    st.markdown("Generate spatial radiation analysis for PV-suitable surfaces and apply shading corrections.")
    
    # Check prerequisites
    prerequisites = ['pv_suitable_facades', 'pv_suitable_windows', 'tmy_data']
    missing = [p for p in prerequisites if p not in st.session_state.project_data]
    
    if missing:
        st.warning(f"⚠️ Missing required data: {', '.join(missing)}")
        st.info("Please complete previous steps: facade extraction and weather data.")
        return
    
    # Load data
    facades_df = pd.DataFrame(st.session_state.project_data['pv_suitable_facades'])
    windows_df = pd.DataFrame(st.session_state.project_data['pv_suitable_windows'])
    tmy_data = st.session_state.project_data['tmy_data']
    
    latitude = st.session_state.project_data.get('latitude', 40.7128)
    longitude = st.session_state.project_data.get('longitude', -74.0060)
    
    # Combine all suitable elements
    all_elements = pd.concat([facades_df, windows_df], ignore_index=True)
    
    st.subheader(f"Radiation Analysis for {len(all_elements)} Elements")
    
    # Display analysis configuration
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Location", f"{latitude:.2f}°, {longitude:.2f}°")
    with col2:
        st.metric("Total Elements", len(all_elements))
    with col3:
        st.metric("Total Area", f"{all_elements['area'].sum():.1f} m²")
    
    # Generate radiation grid
    if st.button("Generate Radiation Grid"):
        with st.spinner("Calculating solar radiation for all surfaces..."):
            try:
                # Get shading factors if available
                shading_factors = st.session_state.project_data.get('shading_factors')
                
                # Get walls data if available for wall-window relationship analysis
                walls_data = st.session_state.get('walls_data', None)
                
                # Generate radiation grid with wall-window relationships
                radiation_grid = generate_radiation_grid(
                    all_elements, tmy_data, latitude, longitude, shading_factors, walls_data
                )
                
                # Apply orientation and tilt corrections
                radiation_grid = apply_orientation_corrections(radiation_grid)
                
                # Store results
                st.session_state.project_data['radiation_grid'] = radiation_grid.to_dict()
                
                st.success("✅ Radiation analysis completed!")
                
                # Display summary statistics
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Avg Annual Irradiation", f"{radiation_grid['annual_irradiation'].mean():.0f} kWh/m²")
                with col2:
                    st.metric("Peak Irradiance", f"{radiation_grid['peak_irradiance'].max():.0f} W/m²")
                with col3:
                    st.metric("Best Element", f"{radiation_grid['annual_irradiation'].max():.0f} kWh/m²")
                with col4:
                    st.metric("Avg Capacity Factor", f"{radiation_grid['capacity_factor'].mean():.2f}")
                
            except Exception as e:
                st.error(f"❌ Error calculating radiation: {str(e)}")
                return
    
    # Display radiation results if available
    if 'radiation_grid' in st.session_state.project_data:
        radiation_df = pd.DataFrame(st.session_state.project_data['radiation_grid'])
        
        st.subheader("Radiation Analysis Results")
        
        # Radiation heatmap by orientation
        orientation_stats = radiation_df.groupby('orientation').agg({
            'annual_irradiation': 'mean',
            'corrected_annual_irradiation': 'mean',
            'element_id': 'count'
        }).reset_index()
        orientation_stats.columns = ['Orientation', 'Raw Irradiation', 'Corrected Irradiation', 'Element Count']
        
        fig_heatmap = go.Figure()
        fig_heatmap.add_trace(go.Bar(
            name='Raw Irradiation',
            x=orientation_stats['Orientation'],
            y=orientation_stats['Raw Irradiation'],
            marker_color='lightblue'
        ))
        fig_heatmap.add_trace(go.Bar(
            name='Corrected Irradiation',
            x=orientation_stats['Orientation'],
            y=orientation_stats['Corrected Irradiation'],
            marker_color='darkblue'
        ))
        fig_heatmap.update_layout(
            title='Average Annual Irradiation by Orientation',
            xaxis_title='Orientation',
            yaxis_title='Irradiation (kWh/m²/year)',
            barmode='group'
        )
        st.plotly_chart(fig_heatmap, use_container_width=True)
        
        # Individual element analysis
        st.subheader("Individual Element Performance")
        
        # Sort by performance
        top_elements = radiation_df.nlargest(10, 'corrected_annual_irradiation')
        
        fig_top = px.bar(top_elements, 
                        x='element_id', 
                        y='corrected_annual_irradiation',
                        color='orientation',
                        title='Top 10 Performing Elements',
                        labels={'corrected_annual_irradiation': 'Annual Irradiation (kWh/m²)'})
        st.plotly_chart(fig_top, use_container_width=True)
        
        # Performance distribution
        col1, col2 = st.columns(2)
        
        with col1:
            fig_dist = px.histogram(radiation_df, 
                                   x='corrected_annual_irradiation',
                                   nbins=20,
                                   title='Distribution of Annual Irradiation',
                                   labels={'corrected_annual_irradiation': 'Annual Irradiation (kWh/m²)'})
            st.plotly_chart(fig_dist, use_container_width=True)
        
        with col2:
            fig_scatter = px.scatter(radiation_df,
                                    x='area',
                                    y='corrected_annual_irradiation',
                                    color='orientation',
                                    size='area',
                                    title='Area vs Performance',
                                    labels={'area': 'Element Area (m²)',
                                           'corrected_annual_irradiation': 'Annual Irradiation (kWh/m²)'})
            st.plotly_chart(fig_scatter, use_container_width=True)
        
        # Detailed data table
        st.subheader("Detailed Radiation Data")
        
        # Select columns for display
        display_columns = ['element_id', 'element_type', 'orientation', 'area', 'tilt',
                          'annual_irradiation', 'corrected_annual_irradiation', 'capacity_factor']
        
        display_df = radiation_df[display_columns].round(2)
        display_df = display_df.sort_values('corrected_annual_irradiation', ascending=False)
        
        st.dataframe(display_df, use_container_width=True)
        
        # Monthly analysis
        st.subheader("Monthly Irradiation Patterns")
        
        # Extract monthly data for visualization
        monthly_data = []
        for _, row in radiation_df.iterrows():
            monthly_irr = row['monthly_irradiation']
            if isinstance(monthly_irr, dict):
                for month, irradiation in monthly_irr.items():
                    monthly_data.append({
                        'element_id': row['element_id'],
                        'orientation': row['orientation'],
                        'month': month,
                        'irradiation': irradiation
                    })
        
        if monthly_data:
            monthly_df = pd.DataFrame(monthly_data)
            
            # Average monthly pattern by orientation
            monthly_avg = monthly_df.groupby(['month', 'orientation'])['irradiation'].mean().reset_index()
            
            fig_monthly = px.line(monthly_avg, 
                                 x='month', 
                                 y='irradiation',
                                 color='orientation',
                                 title='Monthly Irradiation Patterns by Orientation',
                                 labels={'irradiation': 'Monthly Irradiation (kWh/m²)',
                                        'month': 'Month'})
            st.plotly_chart(fig_monthly, use_container_width=True)
        
        # Shading impact analysis
        if 'shading_factors' in st.session_state.project_data:
            st.subheader("Shading Impact Analysis")
            
            # Calculate shading losses
            radiation_df['shading_loss'] = radiation_df['annual_irradiation'] - radiation_df['corrected_annual_irradiation']
            radiation_df['shading_loss_percent'] = (radiation_df['shading_loss'] / radiation_df['annual_irradiation']) * 100
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Avg Shading Loss", f"{radiation_df['shading_loss_percent'].mean():.1f}%")
            with col2:
                st.metric("Max Shading Loss", f"{radiation_df['shading_loss_percent'].max():.1f}%")
            
            fig_shading = px.bar(radiation_df.nlargest(10, 'shading_loss_percent'),
                                x='element_id',
                                y='shading_loss_percent',
                                color='orientation',
                                title='Top 10 Elements with Highest Shading Loss',
                                labels={'shading_loss_percent': 'Shading Loss (%)'})
            st.plotly_chart(fig_shading, use_container_width=True)
        
        # Export radiation data
        st.subheader("Export Radiation Analysis")
        
        if st.button("Export Radiation Data"):
            csv_data = radiation_df.to_csv(index=False)
            st.download_button(
                label="Download Radiation Analysis CSV",
                data=csv_data,
                file_name="radiation_analysis.csv",
                mime="text/csv"
            )
        
        st.success("✅ Radiation grid analysis completed! Ready for PV specification.")
        
    else:
        st.info("👆 Please generate the radiation grid to analyze solar potential.")
        
        # Show analysis info
        with st.expander("🔧 About Radiation Analysis"):
            st.markdown("""
            **The radiation analysis will:**
            1. Calculate solar position for all hours of the year
            2. Compute plane-of-array irradiance for each surface orientation and tilt
            3. Apply shading corrections from trees/obstacles
            4. Generate annual irradiation statistics
            5. Identify best and worst performing surfaces
            6. Create monthly irradiation profiles
            
            **Key metrics calculated:**
            - Annual irradiation (kWh/m²/year)
            - Peak irradiance (W/m²)
            - Capacity factor
            - Shading losses
            - Monthly patterns
            """)
