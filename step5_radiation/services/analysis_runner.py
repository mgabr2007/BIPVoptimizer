"""
Orchestration service for radiation analysis with callbacks and progress tracking.
"""

import asyncio
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Optional, Callable, Union
from contextlib import asynccontextmanager
import logging
from datetime import datetime

from ..models import (
    ElementRadiationResult, AnalysisProgress, AnalysisConfiguration,
    ValidationResult, PrecisionPreset, TMYData, WallShadingData
)
from ..config import analysis_config, ERROR_MESSAGES
from ..db.queries import radiation_queries, execute_with_fallback
from services.advanced_radiation_analyzer import AdvancedRadiationAnalyzer

logger = logging.getLogger(__name__)


class ProgressCallback:
    """Progress tracking callback system."""
    
    def __init__(self, total_elements: int, update_interval: int = 5):
        self.total_elements = total_elements
        self.update_interval = update_interval
        self.processed_count = 0
        self.last_update = 0
        self.callbacks: List[Callable] = []
        self.start_time = time.time()
    
    def add_callback(self, callback: Callable[[AnalysisProgress], None]):
        """Add progress update callback."""
        self.callbacks.append(callback)
    
    def update(self, element_id: str, orientation: str, area: float):
        """Update progress and trigger callbacks if needed."""
        self.processed_count += 1
        
        if (self.processed_count - self.last_update) >= self.update_interval or self.processed_count == self.total_elements:
            progress = AnalysisProgress(
                project_id=0,  # Will be set by caller
                total_elements=self.total_elements,
                completed_elements=self.processed_count,
                current_element_id=element_id,
                current_orientation=orientation,
                current_area=area
            )
            
            for callback in self.callbacks:
                try:
                    callback(progress)
                except Exception as e:
                    logger.warning(f"Progress callback failed: {e}")
            
            self.last_update = self.processed_count


class RadiationAnalysisOrchestrator:
    """Main orchestrator for radiation analysis operations."""
    
    def __init__(self, analyzer: Optional[AdvancedRadiationAnalyzer] = None):
        """Initialize with dependency injection for testing."""
        self.analyzer = analyzer or AdvancedRadiationAnalyzer()
        self.config = analysis_config
        self.queries = radiation_queries
        self._active_analyses: Dict[int, bool] = {}
    
    async def validate_prerequisites(self, project_id: int) -> ValidationResult:
        """Validate that all prerequisites are met for analysis."""
        errors = []
        warnings = []
        data_summary = {}
        
        try:
            # Check for building elements
            elements = await execute_with_fallback(
                self.queries.get_suitable_elements_async,
                self.queries.get_suitable_elements_sync,
                project_id
            )
            
            if not elements:
                errors.append(ERROR_MESSAGES["no_elements"])
            else:
                data_summary["element_count"] = len(elements)
                
                # Check orientations
                orientations = set(elem.get("orientation", "Unknown") for elem in elements)
                data_summary["orientations"] = list(orientations)
                
                if "Unknown" in orientations:
                    warnings.append("Some elements have unknown orientation")
            
            # Check for wall data (for shading analysis)
            walls = await execute_with_fallback(
                self.queries.get_wall_data_async,
                self.queries.get_wall_data_sync,
                project_id
            )
            
            data_summary["wall_count"] = len(walls) if walls else 0
            
            if not walls:
                warnings.append("No wall data available - self-shading calculations will be simplified")
            
            # Check for TMY data (simplified check)
            # In real implementation, this would check the weather data table
            data_summary["tmy_available"] = True  # Assume available for now
            
            return ValidationResult(
                is_valid=len(errors) == 0,
                errors=errors,
                warnings=warnings,
                data_summary=data_summary
            )
            
        except Exception as e:
            logger.error(f"Validation failed: {e}")
            return ValidationResult(
                is_valid=False,
                errors=[f"Validation error: {str(e)}"],
                data_summary={}
            )
    
    async def run_analysis(
        self,
        project_id: int,
        configuration: AnalysisConfiguration,
        progress_callback: Optional[Callable[[AnalysisProgress], None]] = None
    ) -> List[ElementRadiationResult]:
        """Run complete radiation analysis with progress tracking."""
        
        # Mark analysis as active
        self._active_analyses[project_id] = True
        
        try:
            logger.info(f"Starting radiation analysis for project {project_id}")
            
            # Validate prerequisites
            validation = await self.validate_prerequisites(project_id)
            if not validation.is_valid:
                raise ValueError(f"Prerequisites not met: {validation.errors}")
            
            # Get elements to analyze
            elements = await execute_with_fallback(
                self.queries.get_suitable_elements_async,
                self.queries.get_suitable_elements_sync,
                project_id
            )
            
            if not elements:
                raise ValueError(ERROR_MESSAGES["no_elements"])
            
            # Get wall data for shading calculations
            walls = await execute_with_fallback(
                self.queries.get_wall_data_async,
                self.queries.get_wall_data_sync,
                project_id
            )
            
            # Setup progress tracking
            progress_tracker = ProgressCallback(
                total_elements=len(elements),
                update_interval=self.config.max_workers
            )
            
            if progress_callback:
                progress_tracker.add_callback(progress_callback)
            
            # Choose execution strategy based on configuration
            if configuration.parallel_processing and len(elements) > configuration.chunk_size:
                results = await self._run_parallel_analysis(
                    project_id, elements, walls, configuration, progress_tracker
                )
            else:
                results = await self._run_sequential_analysis(
                    project_id, elements, walls, configuration, progress_tracker
                )
            
            # Store results in database
            await self._store_results(project_id, results)
            
            logger.info(f"Completed radiation analysis for {len(results)} elements")
            return results
            
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            raise
        finally:
            # Mark analysis as inactive
            self._active_analyses[project_id] = False
    
    async def _run_parallel_analysis(
        self,
        project_id: int,
        elements: List[Dict[str, Any]],
        walls: List[Dict[str, Any]],
        configuration: AnalysisConfiguration,
        progress_tracker: ProgressCallback
    ) -> List[ElementRadiationResult]:
        """Run analysis in parallel chunks."""
        
        results = []
        chunk_size = configuration.chunk_size
        max_workers = min(configuration.max_workers, len(elements) // chunk_size + 1)
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit chunks for processing
            futures = []
            for i in range(0, len(elements), chunk_size):
                chunk = elements[i:i + chunk_size]
                future = executor.submit(
                    self._process_element_chunk,
                    project_id, chunk, walls, configuration, progress_tracker
                )
                futures.append(future)
            
            # Collect results as they complete
            for future in as_completed(futures):
                try:
                    chunk_results = future.result(timeout=configuration.timeout_seconds)
                    results.extend(chunk_results)
                except Exception as e:
                    logger.error(f"Chunk processing failed: {e}")
                    # Continue with other chunks
        
        return results
    
    async def _run_sequential_analysis(
        self,
        project_id: int,
        elements: List[Dict[str, Any]],
        walls: List[Dict[str, Any]],
        configuration: AnalysisConfiguration,
        progress_tracker: ProgressCallback
    ) -> List[ElementRadiationResult]:
        """Run analysis sequentially."""
        
        results = []
        
        for element in elements:
            try:
                # Check if analysis should continue
                if not self._active_analyses.get(project_id, False):
                    logger.info("Analysis stopped by user")
                    break
                
                result = await self._analyze_single_element(
                    project_id, element, walls, configuration
                )
                
                if result:
                    results.append(result)
                    progress_tracker.update(
                        element.get("element_id", ""),
                        element.get("orientation", ""),
                        element.get("glass_area", 0.0)
                    )
                
            except Exception as e:
                logger.warning(f"Element {element.get('element_id')} failed: {e}")
                continue
        
        return results
    
    def _process_element_chunk(
        self,
        project_id: int,
        elements: List[Dict[str, Any]],
        walls: List[Dict[str, Any]],
        configuration: AnalysisConfiguration,
        progress_tracker: ProgressCallback
    ) -> List[ElementRadiationResult]:
        """Process a chunk of elements (synchronous for thread execution)."""
        
        results = []
        
        # Note: This would be synchronous version of analysis
        # In full implementation, would call sync analyzer methods
        for element in elements:
            try:
                # Placeholder for actual analysis
                # In real implementation: result = self.analyzer.analyze_element_sync(...)
                
                result = ElementRadiationResult(
                    element_id=element.get("element_id", ""),
                    project_id=project_id,
                    orientation=element.get("orientation", "Unknown"),
                    azimuth=element.get("azimuth", 0.0),
                    glass_area=element.get("glass_area", 0.0),
                    annual_radiation=self._calculate_placeholder_radiation(element),
                    shading_factor=self._calculate_shading_factor(element, walls)
                )
                
                results.append(result)
                progress_tracker.update(
                    element.get("element_id", ""),
                    element.get("orientation", ""),
                    element.get("glass_area", 0.0)
                )
                
            except Exception as e:
                logger.warning(f"Element {element.get('element_id')} failed: {e}")
                continue
        
        return results
    
    async def _analyze_single_element(
        self,
        project_id: int,
        element: Dict[str, Any],
        walls: List[Dict[str, Any]],
        configuration: AnalysisConfiguration
    ) -> Optional[ElementRadiationResult]:
        """Analyze a single building element."""
        
        try:
            # In full implementation, this would call the actual analyzer
            # For now, using simplified calculation
            
            annual_radiation = self._calculate_placeholder_radiation(element)
            shading_factor = self._calculate_shading_factor(element, walls)
            
            return ElementRadiationResult(
                element_id=element.get("element_id", ""),
                project_id=project_id,
                orientation=element.get("orientation", "Unknown"),
                azimuth=element.get("azimuth", 0.0),
                glass_area=element.get("glass_area", 0.0),
                annual_radiation=annual_radiation,
                shading_factor=shading_factor
            )
            
        except Exception as e:
            logger.error(f"Single element analysis failed: {e}")
            return None
    
    def _calculate_placeholder_radiation(self, element: Dict[str, Any]) -> float:
        """Calculate placeholder radiation based on orientation."""
        orientation = element.get("orientation", "Unknown").lower()
        azimuth = element.get("azimuth", 0.0)
        
        # Simple orientation-based calculation
        base_radiation = 1200.0  # kWh/m²/year baseline
        
        if orientation == "south":
            return base_radiation * 1.0
        elif orientation in ["southeast", "southwest"]:
            return base_radiation * 0.85
        elif orientation in ["east", "west"]:
            return base_radiation * 0.70
        elif orientation == "north":
            return base_radiation * 0.30
        else:
            # Use azimuth for unknown orientations
            if 135 <= azimuth <= 225:  # South-facing
                return base_radiation * 0.90
            else:
                return base_radiation * 0.60
    
    def _calculate_shading_factor(self, element: Dict[str, Any], walls: List[Dict[str, Any]]) -> float:
        """Calculate shading factor based on nearby walls."""
        if not walls:
            return 1.0  # No shading data available
        
        # Simple placeholder calculation
        # In real implementation, would use geometric analysis
        base_factor = 0.95  # 5% reduction for general shading
        
        # Additional reduction based on wall proximity (simplified)
        element_level = element.get("level", "00")
        nearby_walls = [w for w in walls if w.get("level") == element_level]
        
        if len(nearby_walls) > 3:
            base_factor *= 0.90  # Additional 10% reduction for dense walls
        
        return base_factor
    
    async def _store_results(self, project_id: int, results: List[ElementRadiationResult]):
        """Store analysis results in database."""
        if not results:
            return
        
        try:
            # Use bulk upsert for efficiency
            metrics = await execute_with_fallback(
                self.queries.bulk_upsert_radiation_results_async,
                self.queries.bulk_upsert_radiation_results_sync,
                results
            )
            
            if metrics.success:
                logger.info(f"Stored {metrics.rows_affected} radiation results in {metrics.execution_time:.2f}s")
            else:
                logger.error(f"Failed to store results: {metrics.error_message}")
                
        except Exception as e:
            logger.error(f"Storage failed: {e}")
            raise
    
    def stop_analysis(self, project_id: int):
        """Stop active analysis for a project."""
        self._active_analyses[project_id] = False
        logger.info(f"Stopped analysis for project {project_id}")
    
    def is_analysis_active(self, project_id: int) -> bool:
        """Check if analysis is currently active for a project."""
        return self._active_analyses.get(project_id, False)


# Global orchestrator instance
analysis_orchestrator = RadiationAnalysisOrchestrator()