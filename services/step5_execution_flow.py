"""
Step 5 Execution Flow - Comprehensive Radiation Analysis Orchestrator
Complete execution pipeline with progress tracking, error handling, and result processing
"""

import streamlit as st
import time
import traceback
from typing import Dict, Any, Optional, Callable
from datetime import datetime
from database_manager import BIPVDatabaseManager
import numpy as np

class Step5ExecutionFlow:
    """Complete execution flow orchestrator for Step 5 radiation analysis."""
    
    def __init__(self):
        """Initialize the execution flow."""
        self.db_manager = BIPVDatabaseManager()
        self.current_analysis = None
        self.progress_callback = None
        self.status_callback = None
        
    def set_progress_callbacks(self, progress_bar, status_text):
        """Set UI progress callbacks."""
        self.progress_callback = progress_bar
        self.status_callback = status_text
        
    def update_progress(self, message: str, progress: Optional[float] = None):
        """Update progress indicators."""
        if self.status_callback:
            self.status_callback.text(message)
        if self.progress_callback and progress is not None:
            self.progress_callback.progress(min(max(progress, 0.0), 1.0))
            
    def validate_prerequisites(self, project_id: int) -> Dict[str, Any]:
        """Validate all prerequisites for radiation analysis."""
        validation_result = {
            'valid': False,
            'errors': [],
            'warnings': [],
            'data_summary': {}
        }
        
        try:
            conn = self.db_manager.get_connection()
            if not conn:
                validation_result['errors'].append("Database connection failed")
                return validation_result
                
            with conn.cursor() as cursor:
                # Check building elements
                cursor.execute("""
                    SELECT COUNT(*) as count,
                           COUNT(CASE WHEN orientation IN ('South', 'East', 'West', 'SE', 'SW') THEN 1 END) as suitable
                    FROM building_elements 
                    WHERE project_id = %s
                """, (project_id,))
                element_stats = cursor.fetchone()
                
                if not element_stats or element_stats[0] == 0:
                    validation_result['errors'].append("No building elements found - complete Step 4 first")
                    return validation_result
                    
                validation_result['data_summary']['total_elements'] = element_stats[0]
                validation_result['data_summary']['suitable_elements'] = element_stats[1]
                
                # Check wall data for shading calculations
                cursor.execute("SELECT COUNT(*) FROM building_walls WHERE project_id = %s", (project_id,))
                wall_count = cursor.fetchone()[0]
                validation_result['data_summary']['wall_count'] = wall_count
                
                if wall_count == 0:
                    validation_result['warnings'].append("No wall data available - self-shading calculations disabled")
                
                # Check TMY data
                cursor.execute("""
                    SELECT tmy_data FROM weather_analysis 
                    WHERE project_id = %s AND tmy_data IS NOT NULL
                    ORDER BY created_at DESC LIMIT 1
                """, (project_id,))
                tmy_result = cursor.fetchone()
                
                if not tmy_result:
                    validation_result['errors'].append("No TMY weather data found - complete Step 3 first")
                    return validation_result
                    
                tmy_data = tmy_result[0]
                if isinstance(tmy_data, list) and len(tmy_data) > 0:
                    validation_result['data_summary']['tmy_records'] = len(tmy_data)
                else:
                    validation_result['errors'].append("Invalid TMY data format")
                    return validation_result
                
                # Check project coordinates
                cursor.execute("""
                    SELECT latitude, longitude FROM projects WHERE id = %s
                """, (project_id,))
                coord_result = cursor.fetchone()
                
                if not coord_result or coord_result[0] is None:
                    validation_result['errors'].append("Project coordinates missing - complete Step 1 first")
                    return validation_result
                    
                validation_result['data_summary']['coordinates'] = {
                    'latitude': coord_result[0],
                    'longitude': coord_result[1]
                }
                
            conn.close()
            
            # If we get here, validation passed
            validation_result['valid'] = True
            return validation_result
            
        except Exception as e:
            validation_result['errors'].append(f"Validation error: {str(e)}")
            return validation_result
    
    def clear_previous_analysis(self, project_id: int) -> bool:
        """Clear any previous radiation analysis data."""
        try:
            self.update_progress("Clearing previous analysis data...", 0.1)
            
            conn = self.db_manager.get_connection()
            if not conn:
                return False
                
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM element_radiation WHERE project_id = %s", (project_id,))
                cursor.execute("DELETE FROM radiation_analysis WHERE project_id = %s", (project_id,))
                conn.commit()
                
            conn.close()
            return True
            
        except Exception as e:
            st.error(f"Error clearing previous data: {str(e)}")
            return False
    
    def execute_ultra_fast_analysis(self, project_id: int, config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute ultra-fast radiation analysis (10-15 second target)."""
        try:
            from services.ultra_fast_radiation_analyzer import UltraFastRadiationAnalyzer
            
            self.update_progress("Initializing ultra-fast analyzer...", 0.15)
            analyzer = UltraFastRadiationAnalyzer()
            
            # Configure analysis parameters
            analysis_config = {
                'precision': 'simple',
                'apply_corrections': config.get('apply_corrections', True),
                'include_shading': config.get('include_shading', True),
                'calculation_mode': 'yearly_average'
            }
            
            self.update_progress("Starting ultra-fast radiation calculations...", 0.20)
            
            # Execute analysis with progress tracking
            results = analyzer.analyze_project_radiation(
                project_id=project_id,
                precision=analysis_config['precision'],
                apply_corrections=analysis_config['apply_corrections'],
                include_shading=analysis_config['include_shading'],
                progress_bar=self.progress_callback,
                status_text=self.status_callback
            )
            
            if results and not results.get('error'):
                self.update_progress("Ultra-fast analysis completed!", 1.0)
                return {
                    'success': True,
                    'results': results,
                    'analysis_type': 'ultra_fast',
                    'performance_metrics': {
                        'total_time': results.get('calculation_time', 0),
                        'elements_processed': results.get('total_elements', 0),
                        'calculations_per_second': results.get('calculations_per_second', 0)
                    }
                }
            else:
                return {
                    'success': False,
                    'error': results.get('error', 'Ultra-fast analysis failed'),
                    'analysis_type': 'ultra_fast'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f"Ultra-fast analysis exception: {str(e)}",
                'analysis_type': 'ultra_fast',
                'traceback': traceback.format_exc()
            }
    
    def execute_optimized_analysis(self, project_id: int, config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute optimized radiation analysis (3-5 minute target)."""
        try:
            from services.optimized_radiation_analyzer import OptimizedRadiationAnalyzer
            
            self.update_progress("Initializing optimized analyzer...", 0.15)
            analyzer = OptimizedRadiationAnalyzer()
            
            # Configure analysis parameters
            precision = config.get('precision', 'Daily Peak')
            analysis_config = {
                'precision': precision,
                'apply_corrections': config.get('apply_corrections', True),
                'include_shading': config.get('include_shading', True),
                'calculation_mode': config.get('calculation_mode', 'auto')
            }
            
            self.update_progress("Starting optimized radiation calculations...", 0.20)
            
            # Execute analysis
            results = analyzer.analyze_radiation_optimized(
                project_id=project_id,
                precision=analysis_config['precision'],
                apply_corrections=analysis_config['apply_corrections'],
                include_shading=analysis_config['include_shading'],
                calculation_mode=analysis_config['calculation_mode']
            )
            
            if results and not results.get('error'):
                self.update_progress("Optimized analysis completed!", 1.0)
                return {
                    'success': True,
                    'results': results,
                    'analysis_type': 'optimized',
                    'performance_metrics': {
                        'total_time': results.get('calculation_time', 0),
                        'elements_processed': results.get('total_elements', 0),
                        'calculations_per_second': results.get('performance_metrics', {}).get('calculations_per_second', 0)
                    }
                }
            else:
                return {
                    'success': False,
                    'error': results.get('error', 'Optimized analysis failed'),
                    'analysis_type': 'optimized'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f"Optimized analysis exception: {str(e)}",
                'analysis_type': 'optimized',
                'traceback': traceback.format_exc()
            }
    
    def execute_advanced_analysis(self, project_id: int, config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute advanced research-grade radiation analysis."""
        try:
            from services.advanced_radiation_analyzer import AdvancedRadiationAnalyzer
            
            self.update_progress("Initializing advanced analyzer...", 0.15)
            analyzer = AdvancedRadiationAnalyzer(project_id)
            
            # Configure analysis parameters for maximum accuracy
            analysis_config = {
                'precision': config.get('precision', 'Hourly'),
                'apply_corrections': True,
                'include_shading': True,
                'calculation_mode': 'advanced',
                'environmental_factors': True,
                'detailed_logging': True
            }
            
            self.update_progress("Starting advanced radiation calculations...", 0.20)
            
            # Execute analysis with comprehensive calculations
            results = analyzer.analyze_radiation_detailed(
                precision=analysis_config['precision'],
                apply_corrections=analysis_config['apply_corrections'],
                include_shading=analysis_config['include_shading']
            )
            
            if results and not results.get('error'):
                self.update_progress("Advanced analysis completed!", 1.0)
                return {
                    'success': True,
                    'results': results,
                    'analysis_type': 'advanced',
                    'performance_metrics': {
                        'total_time': results.get('calculation_time', 0),
                        'elements_processed': results.get('total_elements', 0),
                        'accuracy_level': 'research_grade'
                    }
                }
            else:
                return {
                    'success': False,
                    'error': results.get('error', 'Advanced analysis failed'),
                    'analysis_type': 'advanced'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f"Advanced analysis exception: {str(e)}",
                'analysis_type': 'advanced',
                'traceback': traceback.format_exc()
            }
    
    def save_results_to_database(self, project_id: int, results: Dict[str, Any]) -> bool:
        """Save analysis results to database."""
        try:
            self.update_progress("Saving results to database...", 0.95)
            
            success = self.db_manager.save_radiation_analysis(
                project_id=project_id,
                radiation_data=results.get('results', {})
            )
            
            return success
            
        except Exception as e:
            st.error(f"Error saving results: {str(e)}")
            return False
    
    def update_session_state(self, project_id: int, results: Dict[str, Any]):
        """Update Streamlit session state with results."""
        try:
            if 'project_data' not in st.session_state:
                st.session_state.project_data = {}
            
            # Save radiation data
            if results.get('success') and results.get('results'):
                analysis_results = results['results']
                st.session_state.project_data['radiation_data'] = analysis_results.get('element_radiation', {})
                st.session_state.radiation_completed = True
                st.session_state.step5_completed = True
                st.session_state.analysis_just_completed = True
                
                # Save performance metrics
                st.session_state.radiation_performance = results.get('performance_metrics', {})
                
        except Exception as e:
            st.warning(f"Warning: Could not update session state: {str(e)}")
    
    def run_complete_analysis(self, project_id: int, analysis_config: Dict[str, Any]) -> Dict[str, Any]:
        """Run the complete Step 5 radiation analysis execution flow."""
        
        start_time = time.time()
        
        try:
            # Step 1: Validate prerequisites
            self.update_progress("Validating prerequisites...", 0.05)
            validation = self.validate_prerequisites(project_id)
            
            if not validation['valid']:
                return {
                    'success': False,
                    'error': "Prerequisites validation failed",
                    'validation_errors': validation['errors'],
                    'validation_warnings': validation['warnings']
                }
            
            # Step 2: Clear previous analysis
            if not self.clear_previous_analysis(project_id):
                return {
                    'success': False,
                    'error': "Failed to clear previous analysis data"
                }
            
            # Step 3: Determine analysis type and execute
            analysis_type = analysis_config.get('analysis_type', 'optimized')
            precision = analysis_config.get('precision', 'Daily Peak')
            
            if analysis_type == 'ultra_fast' or (analysis_type == 'optimized' and precision == 'Yearly Average'):
                results = self.execute_ultra_fast_analysis(project_id, analysis_config)
            elif analysis_type == 'advanced' or precision == 'Hourly':
                results = self.execute_advanced_analysis(project_id, analysis_config)
            else:
                results = self.execute_optimized_analysis(project_id, analysis_config)
            
            # Step 4: Process results
            if results['success']:
                # Save to database
                if self.save_results_to_database(project_id, results):
                    # Update session state
                    self.update_session_state(project_id, results)
                    
                    # Calculate total execution time
                    total_time = time.time() - start_time
                    
                    return {
                        'success': True,
                        'analysis_type': results['analysis_type'],
                        'performance_metrics': {
                            **results.get('performance_metrics', {}),
                            'total_execution_time': total_time,
                            'elements_processed': results.get('results', {}).get('total_elements', 0)
                        },
                        'validation_summary': validation['data_summary'],
                        'message': f"Analysis completed successfully in {total_time:.1f} seconds"
                    }
                else:
                    return {
                        'success': False,
                        'error': "Analysis completed but failed to save results"
                    }
            else:
                return results
                
        except Exception as e:
            return {
                'success': False,
                'error': f"Execution flow error: {str(e)}",
                'traceback': traceback.format_exc()
            }