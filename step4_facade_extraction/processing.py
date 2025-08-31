"""
Data processing utilities for facade extraction with chunked processing and performance optimizations.
"""

import pandas as pd
import numpy as np
import hashlib
import io
from typing import List, Dict, Any, Optional, Tuple, Callable, Generator
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from .models import WindowRecord, WallRecord, ProcessingResult, OrientationType, UploadMetadata
from .config import get_config
from .validators import DataFrameValidator, FileValidator, validate_locale_numbers
from .logging_utils import get_logger, log_operation


class DataProcessor:
    """Main data processor for facade extraction with chunked processing."""
    
    def __init__(self, project_id: Optional[int] = None):
        self.config = get_config()
        self.logger = get_logger(project_id)
        self.validator = DataFrameValidator(project_id)
        self.file_validator = FileValidator()
        self.project_id = project_id
    
    def calculate_file_hash(self, file_content: bytes) -> str:
        """Calculate SHA-256 hash of file content."""
        return hashlib.sha256(file_content).hexdigest()
    
    def detect_csv_encoding(self, file_content: bytes) -> str:
        """Detect CSV file encoding using fallback sequence."""
        for encoding in self.config.processing.encoding_fallbacks:
            try:
                file_content.decode(encoding)
                return encoding
            except UnicodeDecodeError:
                continue
        
        # If all fail, use utf-8 with error handling
        return 'utf-8'
    
    def load_csv_in_chunks(self, file_content: bytes, 
                          progress_callback: Optional[Callable] = None) -> Generator[pd.DataFrame, None, None]:
        """Load CSV file in chunks for memory efficiency."""
        encoding = self.detect_csv_encoding(file_content)
        
        try:
            # Create StringIO from bytes
            text_content = file_content.decode(encoding)
            csv_buffer = io.StringIO(text_content)
            
            # Read in chunks
            chunk_size = self.config.processing.chunk_size
            chunk_number = 0
            
            for chunk in pd.read_csv(csv_buffer, chunksize=chunk_size):
                if progress_callback:
                    progress_callback(f"Processing chunk {chunk_number + 1}", chunk_number * chunk_size, None)
                
                yield chunk
                chunk_number += 1
                
        except Exception as e:
            self.logger.error(f"Error loading CSV in chunks: {str(e)}")
            raise
    
    def validate_file(self, filename: str, file_content: bytes) -> Tuple[bool, List[str]]:
        """Comprehensive file validation."""
        errors = []
        
        # File size validation
        if not self.file_validator.validate_file_size(
            len(file_content), self.config.security.max_upload_size_mb
        ):
            errors.append(f"File size exceeds {self.config.security.max_upload_size_mb}MB limit")
        
        # File extension validation
        if not self.file_validator.validate_file_extension(
            filename, self.config.processing.allowed_extensions
        ):
            errors.append(f"File extension not allowed. Allowed: {self.config.processing.allowed_extensions}")
        
        # Malware scan (if enabled)
        if self.config.security.enable_malware_scan:
            if not self.file_validator.scan_for_malware(file_content):
                errors.append("File failed security scan")
        
        return len(errors) == 0, errors
    
    def preprocess_dataframe(self, df: pd.DataFrame, data_type: str) -> pd.DataFrame:
        """Preprocess DataFrame with locale handling and cleaning."""
        # Handle locale-aware numbers
        if data_type == "windows":
            numeric_cols = ["Glass Area (m²)", "Azimuth (°)", "Window Width (m)", "Window Height (m)"]
        else:  # walls
            numeric_cols = ["Length (m)", "Area (m²)", "Azimuth (°)"]
        
        df = validate_locale_numbers(df, numeric_cols)
        
        # Clean string columns
        string_cols = df.select_dtypes(include=['object']).columns
        for col in string_cols:
            df[col] = df[col].astype(str).str.strip()
        
        # Handle missing values
        df = df.fillna({
            'Level': '00',
            'HostWallId': '',
            'Window Width (m)': None,
            'Window Height (m)': None
        })
        
        return df
    
    def get_orientation_from_azimuth(self, azimuth: float) -> OrientationType:
        """Convert azimuth to orientation using configuration."""
        if pd.isna(azimuth) or azimuth is None:
            self.logger.warning(f"Missing azimuth data, returning UNKNOWN orientation")
            return OrientationType.UNKNOWN
        
        try:
            azimuth = float(azimuth) % 360
        except (ValueError, TypeError):
            self.logger.warning(f"Invalid azimuth value: {azimuth}, returning UNKNOWN orientation")
            return OrientationType.UNKNOWN
            
        config = self.config.orientation
        
        # Check each orientation range with improved logic
        if (azimuth >= config.north_range[0] or azimuth <= config.north_range[1]):
            orientation = OrientationType.NORTH
        elif config.east_range[0] <= azimuth <= config.east_range[1]:
            orientation = OrientationType.EAST
        elif config.south_range[0] <= azimuth <= config.south_range[1]:
            orientation = OrientationType.SOUTH
        elif config.west_range[0] <= azimuth <= config.west_range[1]:
            orientation = OrientationType.WEST
        else:
            self.logger.warning(f"Azimuth {azimuth}° does not fit standard orientation ranges")
            orientation = OrientationType.UNKNOWN
            
        # Debug logging for orientation calculation
        if hasattr(self, 'debug_orientation_count'):
            self.debug_orientation_count = getattr(self, 'debug_orientation_count', 0) + 1
            if self.debug_orientation_count <= 5:  # Log first 5 calculations
                self.logger.info(f"Azimuth {azimuth}° → {orientation.value}")
        
        return orientation
    
    def determine_pv_suitability(self, orientation: OrientationType, glass_area: float, 
                                family: str) -> bool:
        """Determine PV suitability based on configuration rules."""
        rules = self.config.suitability
        
        # Check orientation
        if orientation.value not in rules.suitable_orientations:
            return False
        
        # Check glass area
        if not (rules.min_glass_area <= glass_area <= rules.max_glass_area):
            return False
        
        # Check family exclusions
        for excluded in rules.excluded_families:
            if excluded.lower() in family.lower():
                return False
        
        return True
        
    def repair_missing_orientations(self, project_id: int, selected_families_only: bool = True) -> Tuple[int, List[str]]:
        """Repair missing orientation data for existing records."""
        from .database import BulkDatabaseOperations
        
        repaired_count = 0
        errors = []
        
        try:
            db_ops = BulkDatabaseOperations(project_id)
            
            with db_ops.connection_manager.get_connection() as conn:
                with conn.cursor() as cursor:
                    # Get selected window families if respecting user selections
                    selected_families = []
                    if selected_families_only:
                        cursor.execute("""
                            SELECT selected_families FROM selected_window_types 
                            WHERE project_id = %s
                        """, (str(project_id),))
                        result = cursor.fetchone()
                        if result and result[0]:
                            selected_families = result[0]
                            self.logger.info(f"Repairing orientation data for selected families only: {selected_families}")
                        else:
                            self.logger.warning("No window type selections found, repairing all windows")
                            selected_families_only = False
                    
                    # Build query with optional family filter
                    base_query = """
                        SELECT element_id, azimuth, glass_area, family 
                        FROM building_elements 
                        WHERE project_id = %s 
                        AND (orientation IS NULL OR orientation = '') 
                        AND azimuth IS NOT NULL 
                        AND azimuth >= 0
                    """
                    params = [project_id]
                    
                    if selected_families_only and selected_families:
                        base_query += " AND family = ANY(%s)"
                        params.append(selected_families)
                    
                    cursor.execute(base_query, params)
                    records_to_fix = cursor.fetchall()
                    
                    if selected_families_only and selected_families:
                        self.logger.info(f"Found {len(records_to_fix)} records with missing orientation data in selected families")
                    else:
                        self.logger.info(f"Found {len(records_to_fix)} records with missing orientation data")
                    
                    # Update each record with calculated orientation
                    for element_id, azimuth, glass_area, family in records_to_fix:
                        try:
                            orientation = self.get_orientation_from_azimuth(azimuth)
                            
                            # Only calculate suitability for selected families
                            if selected_families_only and selected_families:
                                # For selected families, check if they meet BIPV criteria
                                pv_suitable = (
                                    family in selected_families and
                                    self.determine_pv_suitability(orientation, glass_area or 1.0, family)
                                )
                            else:
                                # For all families, use standard suitability check
                                pv_suitable = self.determine_pv_suitability(orientation, glass_area or 1.0, family)
                            
                            cursor.execute("""
                                UPDATE building_elements 
                                SET orientation = %s, pv_suitable = %s 
                                WHERE project_id = %s AND element_id = %s
                            """, (orientation.value, pv_suitable, project_id, element_id))
                            
                            repaired_count += 1
                            
                        except Exception as e:
                            errors.append(f"Element {element_id}: {str(e)}")
                    
                    # Apply final suitability rules respecting user selections
                    if selected_families_only and selected_families:
                        # Only mark selected families as suitable
                        cursor.execute("""
                            UPDATE building_elements 
                            SET pv_suitable = (
                                family = ANY(%s)
                                AND orientation IN ('South', 'East', 'West', 'Southeast', 'Southwest') 
                                AND glass_area >= %s 
                                AND glass_area <= %s
                                AND family NOT ILIKE ANY(ARRAY['%%roof%%', '%%floor%%', '%%ceiling%%'])
                            )
                            WHERE project_id = %s 
                            AND orientation IS NOT NULL 
                            AND orientation != ''
                        """, (
                            selected_families,
                            self.config.suitability.min_glass_area,
                            self.config.suitability.max_glass_area,
                            project_id
                        ))
                        
                        # Ensure non-selected families are marked as unsuitable
                        cursor.execute("""
                            UPDATE building_elements 
                            SET pv_suitable = false
                            WHERE project_id = %s 
                            AND family != ALL(%s)
                        """, (project_id, selected_families))
                        
                    else:
                        # Apply standard suitability rules to all families
                        cursor.execute("""
                            UPDATE building_elements 
                            SET pv_suitable = (
                                orientation IN ('South', 'East', 'West', 'Southeast', 'Southwest') 
                                AND glass_area >= %s 
                                AND glass_area <= %s
                                AND family NOT ILIKE ANY(ARRAY['%%roof%%', '%%floor%%', '%%ceiling%%'])
                            )
                            WHERE project_id = %s 
                            AND orientation IS NOT NULL 
                            AND orientation != ''
                        """, (
                            self.config.suitability.min_glass_area,
                            self.config.suitability.max_glass_area,
                            project_id
                        ))
                    
                    conn.commit()
                    self.logger.info(f"Successfully repaired {repaired_count} orientation records")
                    
        except Exception as e:
            errors.append(f"Database repair error: {str(e)}")
            self.logger.error(f"Failed to repair orientations: {str(e)}")
            
        return repaired_count, errors
    
    def validate_csv_data_quality(self, df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """Validate CSV data quality before processing."""
        errors = []
        warnings = []
        
        # Check required columns
        required_columns = ['ElementId', 'Glass Area (m²)', 'Azimuth (°)']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            errors.append(f"Missing required columns: {', '.join(missing_columns)}")
        
        if not errors:  # Only check data quality if columns exist
            # Check for missing azimuth data
            missing_azimuth = df['Azimuth (°)'].isna().sum()
            total_rows = len(df)
            
            if missing_azimuth > 0:
                missing_percent = (missing_azimuth / total_rows) * 100
                if missing_percent > 10:  # More than 10% missing
                    errors.append(f"Too many records with missing azimuth data: {missing_azimuth}/{total_rows} ({missing_percent:.1f}%)")
                else:
                    warnings.append(f"Some records have missing azimuth data: {missing_azimuth}/{total_rows} ({missing_percent:.1f}%)")
            
            # Check for invalid azimuth values
            invalid_azimuth = ((df['Azimuth (°)'] < 0) | (df['Azimuth (°)'] >= 360)).sum()
            if invalid_azimuth > 0:
                warnings.append(f"Found {invalid_azimuth} records with invalid azimuth values (should be 0-360°)")
            
            # Check for missing glass area
            missing_glass_area = df['Glass Area (m²)'].isna().sum()
            if missing_glass_area > 0:
                warnings.append(f"Found {missing_glass_area} records with missing glass area data")
        
        # Log warnings
        for warning in warnings:
            self.logger.warning(warning)
            
        return len(errors) == 0, errors
    
    def process_window_chunk(self, chunk: pd.DataFrame) -> Tuple[List[WindowRecord], List[str]]:
        """Process a chunk of window data."""
        windows = []
        errors = []
        
        for idx, row in chunk.iterrows():
            try:
                # Extract data with safe defaults
                element_id = str(row.get('ElementId', ''))
                if not element_id:
                    errors.append(f"Row {idx}: Missing ElementId")
                    continue
                
                family = str(row.get('Family', ''))
                glass_area = float(row.get('Glass Area (m²)', 0))
                azimuth = float(row.get('Azimuth (°)', 0))
                
                # Calculate derived values
                orientation = self.get_orientation_from_azimuth(azimuth)
                pv_suitable = self.determine_pv_suitability(orientation, glass_area, family)
                
                # Validate orientation was calculated properly
                if orientation == OrientationType.UNKNOWN and azimuth > 0:
                    self.logger.warning(f"Element {element_id}: Azimuth {azimuth}° resulted in UNKNOWN orientation")
                
                # Create window record
                window = WindowRecord(
                    element_id=element_id,
                    family=family,
                    glass_area=glass_area,
                    window_width=row.get('Window Width (m)'),
                    window_height=row.get('Window Height (m)'),
                    building_level=str(row.get('Level', '00')),
                    wall_element_id=str(row.get('HostWallId', '')),
                    azimuth=azimuth,
                    orientation=orientation,
                    pv_suitable=pv_suitable,
                    project_id=self.project_id or 0
                )
                
                # Debug: Log first few records to verify orientation storage
                if hasattr(self, 'debug_record_count'):
                    self.debug_record_count = getattr(self, 'debug_record_count', 0) + 1
                    if self.debug_record_count <= 3:
                        self.logger.info(f"Window record: ID={element_id}, Azimuth={azimuth}°, Orientation={orientation.value}, PV_Suitable={pv_suitable}")
                
                windows.append(window)
                
            except Exception as e:
                errors.append(f"Row {idx}: {str(e)}")
                continue
        
        return windows, errors
    
    def process_wall_chunk(self, chunk: pd.DataFrame) -> Tuple[List[WallRecord], List[str]]:
        """Process a chunk of wall data."""
        walls = []
        errors = []
        
        for idx, row in chunk.iterrows():
            try:
                # Extract data with safe defaults
                element_id = str(row.get('ElementId', ''))
                if not element_id:
                    errors.append(f"Row {idx}: Missing ElementId")
                    continue
                
                wall_type = str(row.get('Wall Type', ''))
                length = float(row.get('Length (m)', 0))
                area = float(row.get('Area (m²)', 0))
                azimuth = float(row.get('Azimuth (°)', 0))
                
                # Calculate derived values
                orientation = self.get_orientation_from_azimuth(azimuth)
                
                # Create wall record
                wall = WallRecord(
                    element_id=element_id,
                    wall_type=wall_type,
                    building_level=str(row.get('Level', '00')),
                    length=length,
                    area=area,
                    azimuth=azimuth,
                    orientation=orientation,
                    project_id=self.project_id or 0
                )
                
                walls.append(wall)
                
            except Exception as e:
                errors.append(f"Row {idx}: {str(e)}")
                continue
        
        return walls, errors
    
    def process_csv_file(self, filename: str, file_content: bytes, data_type: str,
                        progress_callback: Optional[Callable] = None) -> ProcessingResult:
        """Process CSV file with comprehensive validation and chunked processing."""
        
        with log_operation(self.logger, f"process_csv_file_{data_type}", filename=filename):
            start_time = time.time()
            
            # File validation
            is_valid_file, file_errors = self.validate_file(filename, file_content)
            if not is_valid_file:
                return ProcessingResult(
                    success=False,
                    errors=file_errors
                )
            
            try:
                # Load entire file first for validation
                encoding = self.detect_csv_encoding(file_content)
                df = pd.read_csv(io.BytesIO(file_content), encoding=encoding)
                
                # Preprocess DataFrame
                df = self.preprocess_dataframe(df, data_type)
                
                # Validate data structure
                if data_type == "windows":
                    is_valid_data, validation_errors = self.validator.validate_window_data(df)
                else:
                    is_valid_data, validation_errors = self.validator.validate_wall_data(df)
                
                if not is_valid_data:
                    return ProcessingResult(
                        success=False,
                        errors=[f"{e.column}: {e.error_message}" for e in validation_errors]
                    )
                
                # Process in chunks
                all_records = []
                all_errors = []
                total_rows = len(df)
                processed_rows = 0
                
                # Process data in chunks
                for chunk_start in range(0, total_rows, self.config.processing.chunk_size):
                    chunk_end = min(chunk_start + self.config.processing.chunk_size, total_rows)
                    chunk = df.iloc[chunk_start:chunk_end]
                    
                    if data_type == "windows":
                        records, errors = self.process_window_chunk(chunk)
                    else:
                        records, errors = self.process_wall_chunk(chunk)
                    
                    all_records.extend(records)
                    all_errors.extend(errors)
                    processed_rows = chunk_end
                    
                    # Update progress
                    if progress_callback:
                        progress_callback(
                            f"Processing {data_type}", processed_rows, total_rows
                        )
                
                # Calculate processing time
                processing_time = time.time() - start_time
                
                # Count suitable elements for windows
                suitable_elements = 0
                if data_type == "windows":
                    suitable_elements = sum(1 for r in all_records if r.pv_suitable)
                
                self.logger.log_data_processing(total_rows, processed_rows, len(all_errors))
                
                return ProcessingResult(
                    success=True,
                    total_elements=total_rows,
                    processed_elements=processed_rows,
                    suitable_elements=suitable_elements,
                    errors=all_errors,
                    processing_time=processing_time
                )
                
            except Exception as e:
                self.logger.error(f"CSV processing failed: {str(e)}")
                return ProcessingResult(
                    success=False,
                    errors=[f"Processing failed: {str(e)}"]
                )


class ParallelProcessor:
    """Parallel processing utilities for large datasets."""
    
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.logger = get_logger()
    
    def process_multiple_files(self, files: List[Tuple[str, bytes, str]], 
                             progress_callback: Optional[Callable] = None) -> Dict[str, ProcessingResult]:
        """Process multiple files in parallel."""
        results = {}
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all files for processing
            future_to_file = {}
            for filename, content, data_type in files:
                processor = DataProcessor()
                future = executor.submit(
                    processor.process_csv_file, filename, content, data_type, progress_callback
                )
                future_to_file[future] = filename
            
            # Collect results
            for future in as_completed(future_to_file):
                filename = future_to_file[future]
                try:
                    result = future.result()
                    results[filename] = result
                    self.logger.info(f"Completed processing {filename}")
                except Exception as e:
                    self.logger.error(f"Failed processing {filename}: {str(e)}")
                    results[filename] = ProcessingResult(
                        success=False,
                        errors=[str(e)]
                    )
        
        return results


def merge_building_data(window_results: List[WindowRecord], 
                       wall_results: List[WallRecord]) -> Dict[str, Any]:
    """Merge window and wall data for integrated analysis."""
    
    # Create lookup for walls by element ID
    wall_lookup = {wall.element_id: wall for wall in wall_results}
    
    # Find wall-window relationships
    relationships = []
    for window in window_results:
        if window.wall_element_id and window.wall_element_id in wall_lookup:
            wall = wall_lookup[window.wall_element_id]
            relationships.append({
                'window_id': window.element_id,
                'wall_id': wall.element_id,
                'window_orientation': window.orientation.value,
                'wall_orientation': wall.orientation.value,
                'wall_height': wall.height,
                'wall_area': wall.area
            })
    
    return {
        'windows': window_results,
        'walls': wall_results,
        'relationships': relationships,
        'summary': {
            'total_windows': len(window_results),
            'total_walls': len(wall_results),
            'suitable_windows': sum(1 for w in window_results if w.pv_suitable),
            'connected_pairs': len(relationships)
        }
    }