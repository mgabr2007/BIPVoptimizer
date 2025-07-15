"""
UI components for facade extraction with enhanced UX and internationalization support.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Optional, Dict, Any, List, Callable
import time
from datetime import datetime
from .models import ProcessingResult, UploadMetadata, ValidationError
from .config import get_config
from .logging_utils import get_logger, LogViewer
from .processing import DataProcessor
from .database import BulkDatabaseOperations, DataAccessLayer


class ProgressTracker:
    """Enhanced progress tracking with multiple progress bars."""
    
    def __init__(self):
        self.progress_bars = {}
        self.status_texts = {}
        self.start_times = {}
    
    def create_progress_bar(self, key: str, title: str) -> None:
        """Create a new progress bar."""
        st.write(f"**{title}**")
        self.progress_bars[key] = st.progress(0)
        self.status_texts[key] = st.empty()
        self.start_times[key] = time.time()
    
    def update_progress(self, key: str, current: int, total: int, message: str = "") -> None:
        """Update progress bar."""
        if key in self.progress_bars:
            progress = int((current / total) * 100) if total > 0 else 0
            self.progress_bars[key].progress(progress)
            
            elapsed = time.time() - self.start_times[key]
            if total > 0 and current > 0:
                eta = (elapsed / current) * (total - current)
                self.status_texts[key].text(f"{message} ({current:,}/{total:,}) - ETA: {eta:.1f}s")
            else:
                self.status_texts[key].text(f"{message} ({current:,}/{total:,})")
    
    def complete_progress(self, key: str, message: str = "Completed") -> None:
        """Mark progress as complete."""
        if key in self.progress_bars:
            self.progress_bars[key].progress(100)
            elapsed = time.time() - self.start_times[key]
            self.status_texts[key].text(f"{message} - Completed in {elapsed:.1f}s")


class ConfigurableRulesEditor:
    """Editable suitability rules in sidebar."""
    
    def __init__(self):
        self.config = get_config()
    
    def render_suitability_rules(self) -> Dict[str, Any]:
        """Render editable suitability rules in sidebar."""
        with st.sidebar:
            st.header("🔧 BIPV Suitability Rules")
            
            with st.expander("Orientation Rules", expanded=False):
                suitable_orientations = st.multiselect(
                    "Suitable Orientations",
                    options=["North", "South", "East", "West", "Northeast", "Northwest", "Southeast", "Southwest"],
                    default=self.config.suitability.suitable_orientations,
                    help="Select orientations suitable for PV installation"
                )
            
            with st.expander("Area Constraints", expanded=False):
                min_area = st.number_input(
                    "Minimum Glass Area (m²)",
                    min_value=0.1,
                    max_value=10.0,
                    value=self.config.suitability.min_glass_area,
                    step=0.1,
                    help="Minimum window area for PV installation"
                )
                
                max_area = st.number_input(
                    "Maximum Glass Area (m²)",
                    min_value=10.0,
                    max_value=500.0,
                    value=self.config.suitability.max_glass_area,
                    step=1.0,
                    help="Maximum window area for PV installation"
                )
            
            with st.expander("Family Exclusions", expanded=False):
                excluded_families = st.text_area(
                    "Excluded Window Families (one per line)",
                    value="\n".join(self.config.suitability.excluded_families),
                    help="Window families to exclude from PV analysis"
                ).split('\n')
                excluded_families = [f.strip() for f in excluded_families if f.strip()]
            
            return {
                "suitable_orientations": suitable_orientations,
                "min_glass_area": min_area,
                "max_glass_area": max_area,
                "excluded_families": excluded_families
            }


class DataVisualization:
    """Enhanced data visualization components."""
    
    @staticmethod
    def create_polar_orientation_chart(df: pd.DataFrame, title: str) -> None:
        """Create polar histogram for orientation distribution."""
        if 'orientation' not in df.columns:
            st.warning("No orientation data available for visualization")
            return
        
        # Count orientations
        orientation_counts = df['orientation'].value_counts()
        
        # Map orientations to angles for polar plot
        angle_map = {
            'North': 0, 'Northeast': 45, 'East': 90, 'Southeast': 135,
            'South': 180, 'Southwest': 225, 'West': 270, 'Northwest': 315
        }
        
        angles = [angle_map.get(orient, 0) for orient in orientation_counts.index]
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatterpolar(
            r=orientation_counts.values,
            theta=angles,
            mode='markers+lines',
            fill='toself',
            name='Element Count',
            marker=dict(size=10, color='rgb(27, 38, 81)', opacity=0.7),
            line=dict(color='rgb(27, 38, 81)', width=2)
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(visible=True, range=[0, max(orientation_counts.values) * 1.1]),
                angularaxis=dict(direction="clockwise", start=90)
            ),
            title=f"{title} - Polar Distribution",
            showlegend=True,
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    @staticmethod
    def create_building_level_analysis(df: pd.DataFrame) -> None:
        """Create building level analysis visualization."""
        if 'building_level' not in df.columns:
            return
        
        level_stats = df.groupby('building_level').agg({
            'glass_area': ['count', 'sum', 'mean'] if 'glass_area' in df.columns else ['count'],
            'orientation': lambda x: x.value_counts().to_dict()
        }).round(2)
        
        # Flatten column names
        level_stats.columns = ['_'.join(col).strip() for col in level_stats.columns]
        
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Element Count by Level', 'Total Glass Area by Level', 
                          'Average Glass Area by Level', 'Orientation Distribution'),
            specs=[[{"type": "bar"}, {"type": "bar"}],
                   [{"type": "bar"}, {"type": "pie"}]]
        )
        
        levels = level_stats.index
        
        # Element count
        if 'glass_area_count' in level_stats.columns:
            fig.add_trace(
                go.Bar(x=levels, y=level_stats['glass_area_count'], name='Count'),
                row=1, col=1
            )
        
        # Total area
        if 'glass_area_sum' in level_stats.columns:
            fig.add_trace(
                go.Bar(x=levels, y=level_stats['glass_area_sum'], name='Total Area'),
                row=1, col=2
            )
        
        # Average area
        if 'glass_area_mean' in level_stats.columns:
            fig.add_trace(
                go.Bar(x=levels, y=level_stats['glass_area_mean'], name='Avg Area'),
                row=2, col=1
            )
        
        fig.update_layout(height=600, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)


class FileUploadInterface:
    """Enhanced file upload interface with drag-and-drop and multiple file support."""
    
    def __init__(self, project_id: Optional[int] = None):
        self.config = get_config()
        self.logger = get_logger(project_id)
        self.project_id = project_id
    
    def render_upload_section(self, data_type: str, existing_count: int = 0) -> Optional[bytes]:
        """Render enhanced upload section."""
        
        # Show existing data info
        if existing_count > 0:
            st.info(f"📁 **Existing Data**: {existing_count:,} {data_type} elements found")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"🔄 Replace {data_type.title()}", key=f"replace_{data_type}"):
                    st.session_state[f'replace_{data_type}'] = True
            with col2:
                if st.button(f"➕ Add to {data_type.title()}", key=f"add_{data_type}"):
                    st.session_state[f'add_{data_type}'] = True
        
        # Upload interface
        st.markdown(f"### 📤 Upload {data_type.title()} Data")
        
        # Required columns info
        if data_type == "windows":
            required_cols = ["ElementId", "Family", "Glass Area (m²)", "Azimuth (°)"]
            optional_cols = ["Level", "HostWallId", "Window Width (m)", "Window Height (m)"]
        else:
            required_cols = ["ElementId", "Wall Type", "Length (m)", "Area (m²)", "Azimuth (°)"]
            optional_cols = ["Level"]
        
        with st.expander("📋 Required CSV Format", expanded=False):
            st.markdown("**Required Columns:**")
            for col in required_cols:
                st.markdown(f"- `{col}`")
            
            st.markdown("**Optional Columns:**")
            for col in optional_cols:
                st.markdown(f"- `{col}`")
        
        # File uploader
        uploaded_file = st.file_uploader(
            f"Choose {data_type} CSV file",
            type=['csv'],
            key=f"{data_type}_uploader",
            help=f"Upload CSV file with {data_type} data extracted from BIM model"
        )
        
        if uploaded_file is not None:
            # File validation
            file_content = uploaded_file.read()
            
            # Show file info
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("File Size", f"{len(file_content) / 1024:.1f} KB")
            with col2:
                st.metric("Max Allowed", f"{self.config.security.max_upload_size_mb} MB")
            with col3:
                file_hash = hash(file_content)
                st.metric("File Hash", f"{file_hash:x}"[:8])
            
            return file_content
        
        return None
    
    def render_validation_results(self, errors: List[ValidationError]) -> None:
        """Render validation results with suggestions."""
        if not errors:
            st.success("✅ Data validation passed")
            return
        
        st.error(f"❌ Found {len(errors)} validation issues:")
        
        for i, error in enumerate(errors[:10]):  # Show first 10 errors
            with st.expander(f"Error {i+1}: {error.column}", expanded=False):
                st.error(error.error_message)
                if error.suggested_fix:
                    st.info(f"💡 **Suggestion**: {error.suggested_fix}")
        
        if len(errors) > 10:
            st.warning(f"... and {len(errors) - 10} more errors")


class LogViewerInterface:
    """Log viewer interface for debugging."""
    
    def __init__(self):
        self.log_viewer = LogViewer()
    
    def render_log_panel(self, project_id: Optional[int] = None) -> None:
        """Render log viewer panel."""
        with st.expander("🔍 Processing Logs", expanded=False):
            
            # Filter controls
            col1, col2, col3 = st.columns(3)
            with col1:
                show_project = st.checkbox("Filter by Project", value=project_id is not None)
                project_filter = project_id if show_project else None
            
            with col2:
                level_filter = st.selectbox(
                    "Log Level",
                    options=[None, "INFO", "WARNING", "ERROR", "DEBUG"],
                    index=0
                )
            
            with col3:
                if st.button("🔄 Refresh Logs"):
                    st.rerun()
            
            # Get filtered logs
            logs = self.log_viewer.filter_logs(project_filter, level_filter)
            
            if logs:
                # Display logs in scrollable container
                log_text = "\n".join(logs[-50:])  # Last 50 entries
                st.text_area(
                    "Recent Logs",
                    value=log_text,
                    height=300,
                    disabled=True
                )
            else:
                st.info("No logs available")


class LanguageSelector:
    """Language selection interface for i18n support."""
    
    def __init__(self):
        self.languages = {
            "en": "🇺🇸 English",
            "ar": "🇸🇦 العربية"
        }
    
    def render_language_toggle(self) -> str:
        """Render language selection toggle."""
        current_lang = st.session_state.get("lang", "en")
        
        with st.sidebar:
            selected_lang = st.selectbox(
                "Language / اللغة",
                options=list(self.languages.keys()),
                format_func=lambda x: self.languages[x],
                index=list(self.languages.keys()).index(current_lang),
                key="language_selector"
            )
            
            if selected_lang != current_lang:
                st.session_state["lang"] = selected_lang
                st.rerun()
        
        return selected_lang
    
    def get_text(self, key: str, lang: str = None) -> str:
        """Get localized text (placeholder for full i18n implementation)."""
        if lang is None:
            lang = st.session_state.get("lang", "en")
        
        # Placeholder translations
        translations = {
            "en": {
                "upload_title": "Upload Building Data",
                "processing": "Processing...",
                "completed": "Completed",
                "validation_passed": "Data validation passed",
                "validation_failed": "Data validation failed"
            },
            "ar": {
                "upload_title": "تحميل بيانات المبنى",
                "processing": "جاري المعالجة...",
                "completed": "مكتمل",
                "validation_passed": "تم التحقق من البيانات بنجاح",
                "validation_failed": "فشل التحقق من البيانات"
            }
        }
        
        return translations.get(lang, {}).get(key, key)


def render_performance_metrics(processing_result: ProcessingResult) -> None:
    """Render processing performance metrics."""
    if not processing_result.processing_time:
        return
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Processing Time", f"{processing_result.processing_time:.2f}s")
    
    with col2:
        rate = processing_result.processed_elements / processing_result.processing_time
        st.metric("Processing Rate", f"{rate:.0f} elements/s")
    
    with col3:
        success_rate = (processing_result.processed_elements - len(processing_result.errors)) / processing_result.processed_elements * 100
        st.metric("Success Rate", f"{success_rate:.1f}%")
    
    with col4:
        if processing_result.suitable_elements > 0:
            suitability_rate = processing_result.suitable_elements / processing_result.processed_elements * 100
            st.metric("PV Suitability", f"{suitability_rate:.1f}%")