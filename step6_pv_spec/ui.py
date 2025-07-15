"""
Streamlit UI components for PV specification with enhanced UX and visualizations.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from typing import Dict, Any, Optional, List, Tuple
import json
from datetime import datetime
import asyncio
from io import BytesIO
import base64

from .models import (
    PanelSpecification, ElementPVSpecification, BuildingElement,
    RadiationRecord, ProjectPVSummary, SpecificationConfiguration
)
from .services.spec_calculator import spec_calculator
from .services.panel_catalog import panel_catalog_manager, get_default_panels
from .db.queries import execute_with_fallback, specification_queries, project_data_queries
from .config import ui_config, spec_config, PANEL_TYPE_FILTERS

try:
    import streamlit_extras
    from streamlit_extras.stateful_button import button as stateful_button
    from streamlit_extras.stodo import to_do
    from streamlit_extras.metric_cards import style_metric_cards
    EXTRAS_AVAILABLE = True
except ImportError:
    EXTRAS_AVAILABLE = False


class PVSpecificationUI:
    """Main UI controller for PV specification module."""
    
    def __init__(self):
        self.config = ui_config
        self.spec_config = spec_config
        self.catalog_manager = panel_catalog_manager
        self.calculator = spec_calculator
        self._init_session_state()
    
    def _init_session_state(self):
        """Initialize session state variables."""
        if 'pv_spec_state' not in st.session_state:
            st.session_state.pv_spec_state = {
                'selected_panel': None,
                'custom_panel': None,
                'coverage_factor': self.spec_config.default_coverage_factor,
                'performance_ratio': self.spec_config.default_performance_ratio,
                'panel_type_filter': 'all',
                'specifications': [],
                'calculation_metrics': None,
                'show_advanced': False
            }
    
    def render_main_interface(self, project_id: int):
        """Render the main PV specification interface."""
        st.header("⚡ Step 6: BIPV Panel Specification & Layout")
        st.markdown("**Production-Grade Calculator** - Vectorized calculations with database persistence")
        
        # Check prerequisites
        if not self._check_prerequisites(project_id):
            return
        
        # Render interface sections using accordion approach
        self._render_panel_selection_section()
        self._render_customization_section()
        self._render_calculation_controls(project_id)
        self._render_results_section(project_id)
        
        # Export options
        self._render_export_section(project_id)
    
    def _check_prerequisites(self, project_id: int) -> bool:
        """Check and display prerequisite status."""
        with st.expander("📋 Prerequisites Check", expanded=False):
            # Check building elements
            try:
                elements_data = asyncio.run(
                    specification_queries.get_building_elements_with_radiation_async(project_id)
                )
            except Exception:
                elements_data = specification_queries.get_building_elements_with_radiation_sync(project_id)
            
            if not elements_data:
                st.error("⚠️ No building elements with radiation data found. Complete Steps 4 and 5 first.")
                return False
            
            # Display status
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Building Elements", len(elements_data))
            
            with col2:
                elements_with_radiation = len([e for e in elements_data if e.get('annual_radiation')])
                st.metric("With Radiation Data", elements_with_radiation)
            
            with col3:
                suitable_elements = len([e for e in elements_data if e.get('pv_suitable', True)])
                st.metric("PV Suitable", suitable_elements)
            
            if elements_with_radiation == 0:
                st.warning("⚠️ No radiation analysis data found. Complete Step 5 first.")
                return False
            
            st.success("✅ All prerequisites met")
        
        return True
    
    def _render_panel_selection_section(self):
        """Render panel selection with filtering."""
        if EXTRAS_AVAILABLE:
            with st.expander("🔧 Panel Selection", expanded=True):
                self._render_panel_selection_content()
        else:
            st.subheader("🔧 Panel Selection")
            self._render_panel_selection_content()
    
    def _render_panel_selection_content(self):
        """Render panel selection content."""
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Panel type filter
            panel_type_options = ['all', 'opaque', 'semi_transparent']
            panel_type_labels = ['All Types', 'Opaque Panels', 'Semi-Transparent Panels']
            
            type_index = st.selectbox(
                "Panel Type Filter",
                range(len(panel_type_options)),
                format_func=lambda x: panel_type_labels[x],
                help="Filter panels by transparency type"
            )
            
            selected_type = panel_type_options[type_index]
            st.session_state.pv_spec_state['panel_type_filter'] = selected_type
        
        with col2:
            # Advanced panel management
            if st.button("📝 Manage Catalog"):
                self._show_catalog_management_dialog()
        
        # Get panels based on filter
        try:
            if selected_type == 'all':
                panels = asyncio.run(self.catalog_manager.get_all_panels_async())
            else:
                panels = asyncio.run(self.catalog_manager.get_panels_by_type_async(selected_type))
            
            if not panels:
                panels = get_default_panels()
                st.warning("Using default panels. Database connection may be unavailable.")
        
        except Exception as e:
            st.error(f"Failed to load panels: {e}")
            panels = get_default_panels()
        
        # Panel selection interface
        if panels:
            self._render_panel_grid(panels)
        else:
            st.error("No panels available")
    
    def _render_panel_grid(self, panels: List[PanelSpecification]):
        """Render interactive panel selection grid."""
        # Create panel comparison table
        panel_data = []
        for panel in panels:
            panel_data.append({
                'Name': panel.name,
                'Manufacturer': panel.manufacturer,
                'Type': panel.panel_type.replace('_', ' ').title(),
                'Efficiency': f"{panel.efficiency:.1%}",
                'Transparency': f"{panel.transparency:.1%}",
                'Power Density': f"{panel.power_density:.0f} W/m²",
                'Cost': f"€{panel.cost_per_m2:.0f}/m²",
                'Select': False
            })
        
        panel_df = pd.DataFrame(panel_data)
        
        # Interactive selection
        st.markdown("**Available BIPV Panels:**")
        
        # Use columns for better layout
        for i, panel in enumerate(panels):
            col1, col2, col3, col4 = st.columns([3, 2, 2, 1])
            
            with col1:
                st.markdown(f"**{panel.name}**")
                st.caption(f"by {panel.manufacturer}")
            
            with col2:
                st.metric("Efficiency", f"{panel.efficiency:.1%}")
            
            with col3:
                st.metric("Cost", f"€{panel.cost_per_m2:.0f}/m²")
            
            with col4:
                if st.button("Select", key=f"select_{i}"):
                    st.session_state.pv_spec_state['selected_panel'] = panel
                    st.success(f"Selected: {panel.name}")
                    st.rerun()
        
        # Show selected panel info
        selected_panel = st.session_state.pv_spec_state.get('selected_panel')
        if selected_panel:
            st.info(f"✅ Selected: **{selected_panel.name}** by {selected_panel.manufacturer}")
    
    def _render_customization_section(self):
        """Render panel customization options."""
        if EXTRAS_AVAILABLE:
            with st.expander("⚙️ Panel Customization", expanded=False):
                self._render_customization_content()
        else:
            st.subheader("⚙️ Panel Customization")
            self._render_customization_content()
    
    def _render_customization_content(self):
        """Render customization content."""
        selected_panel = st.session_state.pv_spec_state.get('selected_panel')
        
        if not selected_panel:
            st.warning("Please select a panel first")
            return
        
        st.markdown(f"**Customizing: {selected_panel.name}**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # System parameters
            st.markdown("**System Parameters**")
            
            coverage_factor = st.slider(
                "Panel Coverage Factor",
                min_value=self.spec_config.min_coverage_factor,
                max_value=self.spec_config.max_coverage_factor,
                value=st.session_state.pv_spec_state['coverage_factor'],
                step=0.05,
                format="%.1%",
                help="Percentage of glass area covered by PV panels"
            )
            
            performance_ratio = st.slider(
                "System Performance Ratio",
                min_value=self.spec_config.min_performance_ratio,
                max_value=self.spec_config.max_performance_ratio,
                value=st.session_state.pv_spec_state['performance_ratio'],
                step=0.05,
                format="%.1%",
                help="Overall system efficiency factor"
            )
            
            # Store in session state
            st.session_state.pv_spec_state['coverage_factor'] = coverage_factor
            st.session_state.pv_spec_state['performance_ratio'] = performance_ratio
        
        with col2:
            # Panel modifications
            st.markdown("**Panel Modifications**")
            
            custom_efficiency = st.number_input(
                "Custom Efficiency (%)",
                min_value=2.0,
                max_value=25.0,
                value=selected_panel.efficiency * 100,
                step=0.1,
                help="Override panel efficiency"
            )
            
            custom_cost = st.number_input(
                "Custom Cost (€/m²)",
                min_value=50.0,
                max_value=1000.0,
                value=selected_panel.cost_per_m2,
                step=10.0,
                help="Override panel cost"
            )
            
            if st.button("Apply Modifications"):
                # Create custom panel
                custom_panel = PanelSpecification(
                    id=selected_panel.id,
                    name=f"{selected_panel.name} (Custom)",
                    manufacturer=selected_panel.manufacturer,
                    panel_type=selected_panel.panel_type,
                    efficiency=custom_efficiency / 100,
                    transparency=selected_panel.transparency,
                    power_density=selected_panel.power_density,
                    cost_per_m2=custom_cost,
                    glass_thickness=selected_panel.glass_thickness,
                    u_value=selected_panel.u_value,
                    glass_weight=selected_panel.glass_weight,
                    performance_ratio=selected_panel.performance_ratio
                )
                
                st.session_state.pv_spec_state['custom_panel'] = custom_panel
                st.success("🔧 Custom panel created")
    
    def _render_calculation_controls(self, project_id: int):
        """Render calculation controls and status."""
        if EXTRAS_AVAILABLE:
            with st.expander("🚀 Calculation & Analysis", expanded=True):
                self._render_calculation_content(project_id)
        else:
            st.subheader("🚀 Calculation & Analysis")
            self._render_calculation_content(project_id)
    
    def _render_calculation_content(self, project_id: int):
        """Render calculation content."""
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("▶️ Calculate Specifications", type="primary"):
                self._run_specification_calculation(project_id)
        
        with col2:
            if st.button("🔄 Recalculate"):
                self._run_specification_calculation(project_id, force_recalculate=True)
        
        with col3:
            if st.button("📊 Show Dashboard"):
                self._show_specification_dashboard(project_id)
        
        # Show calculation metrics
        metrics = st.session_state.pv_spec_state.get('calculation_metrics')
        if metrics:
            self._display_calculation_metrics(metrics)
    
    def _run_specification_calculation(self, project_id: int, force_recalculate: bool = False):
        """Run PV specification calculation."""
        panel = st.session_state.pv_spec_state.get('custom_panel') or st.session_state.pv_spec_state.get('selected_panel')
        
        if not panel:
            st.error("Please select a panel first")
            return
        
        with st.spinner("Calculating PV specifications..."):
            try:
                # Get building elements and radiation data
                elements_data = asyncio.run(
                    specification_queries.get_building_elements_with_radiation_async(project_id)
                )
                
                # Convert to model objects
                elements = []
                radiation_records = []
                
                for data in elements_data:
                    if data.get('pv_suitable', True) and data.get('annual_radiation'):
                        element = BuildingElement(
                            element_id=data['element_id'],
                            project_id=project_id,
                            orientation=data['orientation'],
                            azimuth=data.get('azimuth', 0),
                            glass_area=data['glass_area'],
                            pv_suitable=data.get('pv_suitable', True)
                        )
                        elements.append(element)
                        
                        radiation = RadiationRecord(
                            element_id=data['element_id'],
                            project_id=project_id,
                            annual_radiation=data['annual_radiation'],
                            shading_factor=data.get('shading_factor', 1.0)
                        )
                        radiation_records.append(radiation)
                
                if not elements:
                    st.error("No suitable elements found for calculation")
                    return
                
                # Run calculation
                specifications, metrics = self.calculator.calculate_specifications(
                    elements=elements,
                    radiation_data=radiation_records,
                    panel_spec=panel,
                    coverage_factor=st.session_state.pv_spec_state['coverage_factor'],
                    performance_ratio=st.session_state.pv_spec_state['performance_ratio']
                )
                
                if specifications:
                    # Store results
                    st.session_state.pv_spec_state['specifications'] = specifications
                    st.session_state.pv_spec_state['calculation_metrics'] = metrics
                    
                    # Save to database
                    asyncio.run(specification_queries.bulk_upsert_specifications_async(specifications))
                    
                    st.success(f"✅ Calculated specifications for {len(specifications)} elements")
                    st.rerun()
                else:
                    st.error("Calculation failed - no specifications generated")
                
            except Exception as e:
                st.error(f"Calculation failed: {e}")
    
    def _display_calculation_metrics(self, metrics):
        """Display calculation performance metrics."""
        st.markdown("**Calculation Performance:**")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Elements Processed", f"{metrics.processed_elements:,}")
        
        with col2:
            st.metric("Calculation Time", f"{metrics.calculation_time:.2f}s")
        
        with col3:
            st.metric("Method Used", metrics.method_used.title())
        
        with col4:
            success_rate = (metrics.processed_elements / metrics.total_elements * 100) if metrics.total_elements > 0 else 0
            st.metric("Success Rate", f"{success_rate:.1f}%")
    
    def _render_results_section(self, project_id: int):
        """Render calculation results and visualizations."""
        if EXTRAS_AVAILABLE:
            with st.expander("📊 Results & Analysis", expanded=True):
                self._render_results_content(project_id)
        else:
            st.subheader("📊 Results & Analysis")
            self._render_results_content(project_id)
    
    def _render_results_content(self, project_id: int):
        """Render results content."""
        specifications = st.session_state.pv_spec_state.get('specifications', [])
        
        if not specifications:
            st.info("No calculation results available. Run analysis to see results.")
            return
        
        # Summary metrics
        self._render_summary_metrics(specifications)
        
        # Interactive visualizations
        self._render_treemap_visualization(specifications)
        
        # Detailed results table
        self._render_detailed_results_table(specifications)
    
    def _render_summary_metrics(self, specifications: List[ElementPVSpecification]):
        """Render summary metrics cards."""
        if not specifications:
            return
        
        # Calculate totals
        total_power = sum(spec.system_power for spec in specifications)
        total_energy = sum(spec.annual_energy for spec in specifications)
        total_cost = sum(spec.total_cost for spec in specifications)
        total_area = sum(spec.effective_area for spec in specifications)
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total System Power", f"{total_power:.1f} kW")
        
        with col2:
            st.metric("Annual Energy Generation", f"{total_energy:,.0f} kWh")
        
        with col3:
            st.metric("Total System Cost", f"€{total_cost:,.0f}")
        
        with col4:
            st.metric("Effective Panel Area", f"{total_area:.1f} m²")
        
        # Style metric cards if available
        if EXTRAS_AVAILABLE:
            style_metric_cards()
    
    def _render_treemap_visualization(self, specifications: List[ElementPVSpecification]):
        """Render interactive treemap of cost vs capacity by orientation."""
        if not specifications:
            return
        
        st.markdown("**System Distribution by Orientation**")
        
        # Prepare data for treemap
        df = pd.DataFrame([spec.dict() for spec in specifications])
        
        # Aggregate by orientation
        orientation_agg = df.groupby('orientation').agg({
            'system_power': 'sum',
            'total_cost': 'sum',
            'annual_energy': 'sum',
            'element_id': 'count'
        }).reset_index()
        
        orientation_agg.columns = ['Orientation', 'Power_kW', 'Cost_EUR', 'Energy_kWh', 'Count']
        
        # Create treemap
        fig = px.treemap(
            orientation_agg,
            path=['Orientation'],
            values='Power_kW',
            color='Cost_EUR',
            color_continuous_scale='Viridis',
            title="System Distribution (Size = Power, Color = Cost)",
            hover_data={'Energy_kWh': ':,.0f', 'Count': True}
        )
        
        fig.update_layout(height=self.config.chart_height)
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_detailed_results_table(self, specifications: List[ElementPVSpecification]):
        """Render detailed results table."""
        st.markdown("**Detailed Element Specifications**")
        
        # Convert to DataFrame
        df = pd.DataFrame([spec.dict() for spec in specifications])
        
        # Select and format columns
        display_columns = [
            'element_id', 'orientation', 'glass_area', 'effective_area',
            'system_power', 'annual_energy', 'specific_yield', 'total_cost', 'cost_per_wp'
        ]
        
        display_df = df[display_columns].copy()
        
        # Format numerical columns
        display_df['glass_area'] = display_df['glass_area'].round(2)
        display_df['effective_area'] = display_df['effective_area'].round(2)
        display_df['system_power'] = display_df['system_power'].round(3)
        display_df['annual_energy'] = display_df['annual_energy'].round(0)
        display_df['specific_yield'] = display_df['specific_yield'].round(0)
        display_df['total_cost'] = display_df['total_cost'].round(0)
        display_df['cost_per_wp'] = display_df['cost_per_wp'].round(2)
        
        # Rename columns for display
        display_df.columns = [
            'Element ID', 'Orientation', 'Glass Area (m²)', 'Effective Area (m²)',
            'System Power (kW)', 'Annual Energy (kWh)', 'Specific Yield (kWh/kW)',
            'Total Cost (€)', 'Cost per Wp (€)'
        ]
        
        st.dataframe(display_df, use_container_width=True, height=400)
    
    def _render_export_section(self, project_id: int):
        """Render export options."""
        if EXTRAS_AVAILABLE:
            with st.expander("📤 Export & API", expanded=False):
                self._render_export_content(project_id)
        else:
            st.subheader("📤 Export & API")
            self._render_export_content(project_id)
    
    def _render_export_content(self, project_id: int):
        """Render export content."""
        specifications = st.session_state.pv_spec_state.get('specifications', [])
        
        if not specifications:
            st.info("No data available for export")
            return
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # CSV Export
            if st.button("📄 Download CSV"):
                csv_data = self._generate_csv_export(specifications)
                st.download_button(
                    label="📄 Download Specifications CSV",
                    data=csv_data,
                    file_name=f"pv_specifications_{project_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
        
        with col2:
            # Excel Export
            if self.config.enable_excel_export and st.button("📊 Download Excel"):
                excel_data = self._generate_excel_export(specifications, project_id)
                st.download_button(
                    label="📊 Download Specifications Excel",
                    data=excel_data,
                    file_name=f"pv_specifications_{project_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        
        with col3:
            # JSON Export
            if st.button("🔗 Generate JSON"):
                json_data = self._generate_json_export(specifications)
                st.download_button(
                    label="🔗 Download JSON Data",
                    data=json_data,
                    file_name=f"pv_specifications_{project_id}.json",
                    mime="application/json"
                )
    
    def _generate_csv_export(self, specifications: List[ElementPVSpecification]) -> bytes:
        """Generate CSV export data."""
        df = pd.DataFrame([spec.dict() for spec in specifications])
        
        # Select relevant columns
        export_columns = [
            'element_id', 'orientation', 'glass_area', 'panel_coverage',
            'effective_area', 'system_power', 'annual_radiation', 'annual_energy',
            'specific_yield', 'total_cost', 'cost_per_wp'
        ]
        
        export_df = df[export_columns]
        
        # Generate CSV with BOM for proper Excel handling
        csv_buffer = BytesIO()
        csv_data = export_df.to_csv(index=False, encoding=self.config.csv_encoding)
        csv_buffer.write(csv_data.encode(self.config.csv_encoding))
        
        return csv_buffer.getvalue()
    
    def _generate_excel_export(self, specifications: List[ElementPVSpecification], project_id: int) -> bytes:
        """Generate Excel export with multiple sheets."""
        from io import BytesIO
        import pandas as pd
        
        excel_buffer = BytesIO()
        
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            # Specifications sheet
            spec_df = pd.DataFrame([spec.dict() for spec in specifications])
            spec_df.to_excel(writer, sheet_name='Specifications', index=False)
            
            # Summary sheet
            summary_data = self._calculate_export_summary(specifications)
            summary_df = pd.DataFrame([summary_data])
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
            
            # Orientation breakdown
            orientation_df = self._calculate_orientation_breakdown(specifications)
            orientation_df.to_excel(writer, sheet_name='Orientation_Breakdown', index=False)
        
        return excel_buffer.getvalue()
    
    def _generate_json_export(self, specifications: List[ElementPVSpecification]) -> str:
        """Generate JSON export data."""
        export_data = {
            'specifications': [spec.dict() for spec in specifications],
            'summary': self._calculate_export_summary(specifications),
            'exported_at': datetime.now().isoformat(),
            'total_elements': len(specifications)
        }
        
        return json.dumps(export_data, indent=2, default=str)
    
    def _calculate_export_summary(self, specifications: List[ElementPVSpecification]) -> Dict[str, Any]:
        """Calculate summary statistics for export."""
        if not specifications:
            return {}
        
        return {
            'total_elements': len(specifications),
            'total_system_power_kw': sum(spec.system_power for spec in specifications),
            'total_annual_energy_kwh': sum(spec.annual_energy for spec in specifications),
            'total_system_cost_eur': sum(spec.total_cost for spec in specifications),
            'total_effective_area_m2': sum(spec.effective_area for spec in specifications),
            'avg_specific_yield_kwh_kw': sum(spec.specific_yield * spec.system_power for spec in specifications) / sum(spec.system_power for spec in specifications),
            'avg_cost_per_wp_eur': sum(spec.cost_per_wp * spec.system_power for spec in specifications) / sum(spec.system_power for spec in specifications)
        }
    
    def _calculate_orientation_breakdown(self, specifications: List[ElementPVSpecification]) -> pd.DataFrame:
        """Calculate orientation breakdown for export."""
        df = pd.DataFrame([spec.dict() for spec in specifications])
        
        breakdown = df.groupby('orientation').agg({
            'element_id': 'count',
            'system_power': ['sum', 'mean'],
            'annual_energy': ['sum', 'mean'],
            'total_cost': ['sum', 'mean'],
            'specific_yield': 'mean',
            'cost_per_wp': 'mean'
        }).round(2)
        
        # Flatten column names
        breakdown.columns = ['_'.join(col).strip() for col in breakdown.columns]
        breakdown = breakdown.reset_index()
        
        return breakdown
    
    def _show_catalog_management_dialog(self):
        """Show panel catalog management interface."""
        st.markdown("### 📝 Panel Catalog Management")
        
        # This would open a dialog for CRUD operations
        # Implementation would include add/edit/delete functionality
        st.info("Catalog management interface would be implemented here with CRUD operations")
    
    def _show_specification_dashboard(self, project_id: int):
        """Show comprehensive specification dashboard."""
        st.markdown("### 📊 Specification Dashboard")
        
        # This would show a comprehensive dashboard
        # Implementation would include advanced visualizations and analytics
        st.info("Advanced dashboard would be implemented here with comprehensive analytics")


def render_pv_specification():
    """Main function to render PV specification interface."""
    if 'project_id' not in st.session_state:
        st.error("⚠️ No project selected. Please complete Step 1 first.")
        return
    
    project_id = st.session_state.project_id
    
    # Initialize UI controller
    ui_controller = PVSpecificationUI()
    
    # Render main interface
    ui_controller.render_main_interface(project_id)


# Backward compatibility
def render_pv_specification_legacy():
    """Legacy function name for backward compatibility."""
    render_pv_specification()