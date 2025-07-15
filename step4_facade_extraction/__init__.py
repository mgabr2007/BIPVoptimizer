"""
Step 4 Facade Extraction - Production-grade BIPV building data processing module.
"""

from .models import WindowRecord, WallRecord, ProcessingResult, OrientationType
from .config import get_config, save_config, reset_config
from .processing import DataProcessor, ParallelProcessor, merge_building_data
from .database import BulkDatabaseOperations, DataAccessLayer
from .validators import DataFrameValidator, FileValidator
from .ui import (
    ProgressTracker, ConfigurableRulesEditor, DataVisualization,
    FileUploadInterface, LogViewerInterface, LanguageSelector,
    render_performance_metrics
)
from .logging_utils import get_logger, log_operation, setup_error_monitoring

__version__ = "1.0.0"
__author__ = "BIPV Optimizer Team"

# Main facade extraction function
def render_facade_extraction(project_id: int) -> None:
    """
    Main function to render the enhanced facade extraction interface.
    
    Args:
        project_id: Current project ID for data processing
    """
    import streamlit as st
    from .ui import FileUploadInterface, ProgressTracker, DataVisualization, LogViewerInterface
    from .processing import DataProcessor
    from .database import BulkDatabaseOperations, DataAccessLayer
    
    # Initialize components
    config = get_config()
    logger = get_logger(project_id, "step4_facade")
    
    # UI Components
    upload_interface = FileUploadInterface(project_id)
    progress_tracker = ProgressTracker()
    data_viz = DataVisualization()
    log_viewer = LogViewerInterface()
    
    # Data processing components
    processor = DataProcessor(project_id)
    db_ops = BulkDatabaseOperations(project_id)
    data_access = DataAccessLayer(project_id)
    
    # Render main interface
    st.header("Step 4: Enhanced Facade Extraction")
    st.markdown("Production-grade BIM data processing with comprehensive validation and performance optimization.")
    
    # Configuration panel
    if config.ui.enable_debug_mode:
        with st.expander("🔧 Configuration & Debug", expanded=False):
            st.json(config.dict())
    
    # Show existing data
    window_count, wall_count = data_access.get_project_elements_count(project_id)
    
    if window_count > 0 or wall_count > 0:
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Existing Windows", f"{window_count:,}")
        with col2:
            st.metric("Existing Walls", f"{wall_count:,}")
    
    # File upload sections
    st.subheader("📤 Data Upload")
    
    # Windows upload
    with st.container():
        st.markdown("#### Window Elements")
        window_file = upload_interface.render_upload_section("windows", window_count)
        
        if window_file:
            if st.button("🔍 Process Windows", key="process_windows"):
                progress_tracker.create_progress_bar("windows", "Processing Window Data")
                
                def window_progress(msg, current, total):
                    progress_tracker.update_progress("windows", current, total, msg)
                
                result = processor.process_csv_file(
                    "windows.csv", window_file, "windows", window_progress
                )
                
                if result.success:
                    progress_tracker.complete_progress("windows", "Windows processed successfully")
                    render_performance_metrics(result)
                else:
                    st.error("Window processing failed")
                    for error in result.errors:
                        st.error(error)
    
    # Walls upload
    with st.container():
        st.markdown("#### Wall Elements")
        wall_file = upload_interface.render_upload_section("walls", wall_count)
        
        if wall_file:
            if st.button("🔍 Process Walls", key="process_walls"):
                progress_tracker.create_progress_bar("walls", "Processing Wall Data")
                
                def wall_progress(msg, current, total):
                    progress_tracker.update_progress("walls", current, total, msg)
                
                result = processor.process_csv_file(
                    "walls.csv", wall_file, "walls", wall_progress
                )
                
                if result.success:
                    progress_tracker.complete_progress("walls", "Walls processed successfully")
                    render_performance_metrics(result)
                else:
                    st.error("Wall processing failed")
                    for error in result.errors:
                        st.error(error)
    
    # Data visualization
    if window_count > 0:
        st.subheader("📊 Data Analysis")
        
        # Note: In a full implementation, you would load actual data here
        st.info("Data visualization will show orientation distribution, building levels, and PV suitability analysis")
    
    # Log viewer
    log_viewer.render_log_panel(project_id)


# Backward compatibility
from pages_modules.facade_extraction import render_facade_extraction as legacy_render

__all__ = [
    'WindowRecord', 'WallRecord', 'ProcessingResult', 'OrientationType',
    'get_config', 'save_config', 'reset_config',
    'DataProcessor', 'ParallelProcessor', 'merge_building_data',
    'BulkDatabaseOperations', 'DataAccessLayer',
    'DataFrameValidator', 'FileValidator',
    'ProgressTracker', 'ConfigurableRulesEditor', 'DataVisualization',
    'FileUploadInterface', 'LogViewerInterface', 'LanguageSelector',
    'render_performance_metrics', 'render_facade_extraction',
    'get_logger', 'log_operation', 'setup_error_monitoring'
]