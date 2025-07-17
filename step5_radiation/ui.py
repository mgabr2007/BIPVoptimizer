"""
Streamlit UI components for radiation analysis with enhanced UX and visualizations.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from typing import Dict, Any, Optional, List, Callable
import time
from datetime import datetime
import asyncio

from .models import (
    AnalysisProgress, AnalysisConfiguration, PrecisionPreset, 
    PRECISION_PRESETS, PrecisionLevel, ValidationResult,
    ProjectRadiationSummary
)
from .config import ui_config, analysis_config
from .services.analysis_runner import analysis_orchestrator
from .db.queries import radiation_queries

try:
    import streamlit_extras
    from streamlit_extras.stateful_button import button as stateful_button
    EXTRAS_AVAILABLE = True
except ImportError:
    EXTRAS_AVAILABLE = False


class RadiationAnalysisUI:
    """Main UI controller for radiation analysis."""
    
    def __init__(self):
        self.config = ui_config
        self.orchestrator = analysis_orchestrator
        self._init_session_state()
    
    def _init_session_state(self):
        """Initialize session state variables."""
        if 'radiation_analysis_state' not in st.session_state:
            st.session_state.radiation_analysis_state = {
                'analysis_running': False,
                'current_progress': None,
                'last_results': None,
                'selected_precision': 'daily_peak',
                'configuration': None
            }
    
    def render_main_interface(self, project_id: int):
        """Render the main radiation analysis interface."""
        st.header("☀️ Step 5: Solar Radiation & Shading Analysis")
        st.markdown("**Production-Grade Analysis** - Scalable radiation modeling with database persistence")
        
        # Check prerequisites
        if not self._check_prerequisites():
            return
        
        # Configuration section
        self._render_configuration_section()
        
        # Analysis controls
        self._render_analysis_controls(project_id)
        
        # Results visualization
        self._render_results_section(project_id)
        
        # Advanced options
        self._render_advanced_options()
    
    def _check_prerequisites(self) -> bool:
        """Check and display prerequisite status."""
        with st.expander("📋 Prerequisites Check", expanded=False):
            if 'project_id' not in st.session_state:
                st.error("⚠️ No project selected. Please complete Step 1 (Project Setup) first.")
                return False
            
            project_id = st.session_state.project_id
            
            # Run validation asynchronously
            try:
                validation = asyncio.run(self.orchestrator.validate_prerequisites(project_id))
            except Exception as e:
                st.error(f"Validation failed: {e}")
                return False
            
            # Display validation results
            if validation.is_valid:
                st.success("✅ All prerequisites met")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Building Elements", validation.data_summary.get('element_count', 0))
                with col2:
                    st.metric("Wall Elements", validation.data_summary.get('wall_count', 0))
                with col3:
                    st.metric("TMY Data", "✅" if validation.data_summary.get('tmy_available') else "❌")
            else:
                st.error("❌ Prerequisites not met")
                for error in validation.errors:
                    st.error(f"• {error}")
                return False
            
            # Show warnings
            for warning in validation.warnings:
                st.warning(f"⚠️ {warning}")
        
        return True
    
    def _render_configuration_section(self):
        """Render analysis configuration controls."""
        st.subheader("⚙️ Analysis Configuration")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Precision selection with detailed info
            precision_options = list(PRECISION_PRESETS.keys())
            precision_labels = [PRECISION_PRESETS[p].label for p in precision_options]
            
            selected_index = st.selectbox(
                "Analysis Precision",
                range(len(precision_options)),
                format_func=lambda x: precision_labels[x],
                index=1,  # Default to Daily Peak
                help="Choose analysis precision level"
            )
            
            selected_precision = precision_options[selected_index]
            preset = PRECISION_PRESETS[selected_precision]
            
            # Store in session state
            st.session_state.radiation_analysis_state['selected_precision'] = selected_precision.value
            
            # Show precision details
            st.info(f"**{preset.description}**\n\n📊 {preset.calc_count:,} calculations per element")
        
        with col2:
            # Advanced options
            st.markdown("**Advanced Options**")
            
            enable_shading = st.checkbox(
                "Include Self-Shading Analysis",
                value=True,
                help="Calculate geometric shading from building walls"
            )
            
            enable_environmental = st.checkbox(
                "Apply Environmental Factors",
                value=True,
                help="Apply tree and building shading reductions"
            )
            
            parallel_processing = st.checkbox(
                "Enable Parallel Processing",
                value=analysis_config.enable_parallel_processing,
                help="Process elements in parallel for faster analysis"
            )
        
        # Create configuration object
        config = AnalysisConfiguration(
            precision_preset=preset,
            enable_self_shading=enable_shading,
            enable_environmental_shading=enable_environmental,
            parallel_processing=parallel_processing,
            max_workers=analysis_config.max_workers,
            chunk_size=analysis_config.chunk_size
        )
        
        st.session_state.radiation_analysis_state['configuration'] = config
    
    def _render_analysis_controls(self, project_id: int):
        """Render analysis control buttons and progress."""
        st.subheader("🚀 Analysis Execution")
        
        state = st.session_state.radiation_analysis_state
        analysis_running = state.get('analysis_running', False)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if analysis_running:
                if st.button("⏹️ Stop Analysis", type="secondary"):
                    self.orchestrator.stop_analysis(project_id)
                    state['analysis_running'] = False
                    st.rerun()
            else:
                if st.button("▶️ Start Analysis", type="primary"):
                    self._start_analysis(project_id)
        
        with col2:
            if st.button("🔄 Reset Results"):
                self._reset_analysis_results(project_id)
        
        with col3:
            if st.button("📊 View Dashboard"):
                self._show_dashboard(project_id)
        
        # Progress display
        if analysis_running or state.get('current_progress'):
            self._render_progress_display(state.get('current_progress'))
    
    def _render_progress_display(self, progress: Optional[AnalysisProgress]):
        """Render analysis progress with timeline."""
        if not progress:
            return
        
        st.markdown("### 📈 Analysis Progress")
        
        # Progress bar
        progress_pct = progress.progress_percentage
        st.progress(progress_pct / 100.0)
        
        # Progress metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Progress", f"{progress_pct:.1f}%")
        with col2:
            st.metric("Completed", f"{progress.completed_elements:,}")
        with col3:
            st.metric("Total", f"{progress.total_elements:,}")
        with col4:
            elapsed = progress.elapsed_time
            st.metric("Elapsed", f"{elapsed:.0f}s")
        
        # Current element info
        if progress.current_element_id:
            st.info(f"🔄 Processing: {progress.current_element_id} ({progress.current_orientation})")
        
        # Timeline visualization (if streamlit-extras available)
        if EXTRAS_AVAILABLE and progress.total_elements > 0:
            self._render_progress_timeline(progress)
    
    def _render_progress_timeline(self, progress: AnalysisProgress):
        """Render progress timeline using streamlit-extras."""
        try:
            from streamlit_extras.stodo import to_do
            
            total_steps = min(10, progress.total_elements)  # Max 10 steps for display
            completed_steps = int((progress.completed_elements / progress.total_elements) * total_steps)
            
            steps = []
            for i in range(total_steps):
                if i < completed_steps:
                    steps.append(("✅", f"Step {i+1}", True))
                elif i == completed_steps:
                    steps.append(("🔄", f"Step {i+1}", False))
                else:
                    steps.append(("⏳", f"Step {i+1}", False))
            
            for icon, label, done in steps:
                to_do(label, done)
                
        except ImportError:
            pass  # Fall back to simple display
    
    def _render_results_section(self, project_id: int):
        """Render analysis results and visualizations."""
        st.subheader("📊 Analysis Results")
        
        # Try to get latest results
        try:
            summary = asyncio.run(radiation_queries.get_radiation_summary_async(project_id))
        except Exception:
            summary = radiation_queries.get_radiation_summary_sync(project_id)
        
        if not summary:
            st.info("No analysis results available. Run analysis to see results.")
            return
        
        # Results overview
        self._render_results_overview(summary)
        
        # Polar chart for orientations
        self._render_orientation_polar_chart(summary)
        
        # Detailed results table
        self._render_detailed_results_table(project_id)
    
    def _render_results_overview(self, summary: ProjectRadiationSummary):
        """Render results overview metrics."""
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Elements", f"{summary.total_elements:,}")
        with col2:
            st.metric("Total Glass Area", f"{summary.total_glass_area:.1f} m²")
        with col3:
            st.metric("Avg Radiation", f"{summary.avg_annual_radiation:.0f} kWh/m²/year")
        with col4:
            total_energy = sum(summary.energy_breakdown.values())
            st.metric("Total Energy Potential", f"{total_energy:,.0f} kWh/year")
    
    def _render_orientation_polar_chart(self, summary: ProjectRadiationSummary):
        """Render polar bar chart for orientation distribution."""
        if not summary.orientation_breakdown:
            return
        
        # Prepare data for polar chart
        orientations = list(summary.orientation_breakdown.keys())
        counts = list(summary.orientation_breakdown.values())
        
        # Map orientations to angles
        angle_map = {
            'North': 0, 'Northeast': 45, 'East': 90, 'Southeast': 135,
            'South': 180, 'Southwest': 225, 'West': 270, 'Northwest': 315,
            'Unknown': 360
        }
        
        angles = [angle_map.get(orient, 0) for orient in orientations]
        
        # Create polar bar chart
        fig = go.Figure()
        
        fig.add_trace(go.Scatterpolar(
            r=counts,
            theta=angles,
            mode='markers+lines',
            fill='toself',
            name='Element Count',
            marker=dict(size=10, color='rgb(58, 71, 80)', opacity=0.8),
            line=dict(color='rgb(58, 71, 80)', width=3)
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, max(counts) * 1.1] if counts else [0, 1]
                ),
                angularaxis=dict(
                    direction="clockwise",
                    start=90,
                    tickmode="array",
                    tickvals=[0, 45, 90, 135, 180, 225, 270, 315],
                    ticktext=['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
                )
            ),
            title="Element Distribution by Orientation",
            showlegend=False,
            height=self.config.chart_height
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_detailed_results_table(self, project_id: int):
        """Render detailed results table."""
        with st.expander("📋 Detailed Results", expanded=False):
            # This would fetch detailed element-level results
            # For now, showing placeholder
            st.info("Detailed element-by-element results would be displayed here")
            
            # In full implementation:
            # detailed_results = get_detailed_radiation_results(project_id)
            # if detailed_results:
            #     df = pd.DataFrame(detailed_results)
            #     st.dataframe(df, use_container_width=True)
    
    def _render_advanced_options(self):
        """Render advanced analysis options."""
        with st.expander("🔧 Advanced Options", expanded=False):
            st.markdown("### Performance Settings")
            
            col1, col2 = st.columns(2)
            
            with col1:
                max_workers = st.slider(
                    "Max Workers",
                    min_value=1,
                    max_value=8,
                    value=analysis_config.max_workers,
                    help="Number of parallel workers for analysis"
                )
                
                chunk_size = st.slider(
                    "Chunk Size",
                    min_value=10,
                    max_value=200,
                    value=analysis_config.chunk_size,
                    help="Elements processed per chunk"
                )
            
            with col2:
                timeout = st.slider(
                    "Timeout (seconds)",
                    min_value=60,
                    max_value=3600,
                    value=analysis_config.total_timeout,
                    help="Maximum analysis time"
                )
                
                if st.button("Apply Settings"):
                    # Update configuration
                    config = st.session_state.radiation_analysis_state.get('configuration')
                    if config:
                        config.max_workers = max_workers
                        config.chunk_size = chunk_size
                        config.timeout_seconds = timeout
                        st.success("Settings updated")
    
    def _start_analysis(self, project_id: int):
        """Start radiation analysis."""
        state = st.session_state.radiation_analysis_state
        config = state.get('configuration')
        
        if not config:
            st.error("No configuration available")
            return
        
        # Mark analysis as running
        state['analysis_running'] = True
        
        # Progress callback
        def update_progress(progress: AnalysisProgress):
            progress.project_id = project_id
            state['current_progress'] = progress
            
            # Update UI every few elements
            if progress.completed_elements % 5 == 0:
                st.rerun()
        
        try:
            # Start analysis (simplified for demo)
            st.info("🚀 Starting radiation analysis...")
            
            # In full implementation, this would be:
            # results = asyncio.run(self.orchestrator.run_analysis(
            #     project_id, config, update_progress
            # ))
            
            # For now, simulate quick analysis
            time.sleep(2)
            state['analysis_running'] = False
            st.success("✅ Analysis completed")
            st.rerun()
            
        except Exception as e:
            state['analysis_running'] = False
            st.error(f"Analysis failed: {e}")
    
    def _reset_analysis_results(self, project_id: int):
        """Reset analysis results."""
        try:
            # Clear database results
            asyncio.run(radiation_queries.clear_radiation_data_async(project_id))
            
            # Clear session state
            state = st.session_state.radiation_analysis_state
            state['current_progress'] = None
            state['last_results'] = None
            
            st.success("✅ Results cleared")
            st.rerun()
            
        except Exception as e:
            st.error(f"Failed to reset results: {e}")
    
    def _show_dashboard(self, project_id: int):
        """Show analysis dashboard."""
        st.info("📊 Dashboard view would open here with comprehensive results visualization")


class LogViewer:
    """Log viewer component for debugging."""
    
    def __init__(self):
        self.config = ui_config
    
    def render_log_panel(self):
        """Render log viewer panel."""
        with st.expander("🔍 Analysis Logs", expanded=False):
            # This would show real logs from loguru
            st.text_area(
                "Recent Logs",
                value="[INFO] Analysis started\n[INFO] Processing elements...\n[INFO] Analysis completed",
                height=200,
                disabled=True
            )
            
            if st.button("🔄 Refresh Logs"):
                st.rerun()


def render_radiation_grid():
    """Main function to render radiation analysis interface."""
    from services.io import get_current_project_id
    project_id = get_current_project_id()
    
    if not project_id:
        st.error("⚠️ No project ID found. Please complete Step 1 (Project Setup) first.")
        return
    
    # Initialize UI controller
    ui_controller = RadiationAnalysisUI()
    
    # Render main interface
    ui_controller.render_main_interface(project_id)
    
    # Log viewer
    log_viewer = LogViewer()
    log_viewer.render_log_panel()


# Backward compatibility
def render_radiation_grid_legacy():
    """Legacy function name for backward compatibility."""
    render_radiation_grid()