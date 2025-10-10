"""
Data validation utilities using Pandera for facade extraction.
"""

import pandas as pd
import pandera as pa
from pandera import Check
from pandera.api.pandas import Column, DataFrameSchema
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from .models import ValidationError, WindowRecord, WallRecord
from .logging_utils import get_logger


class DataFrameValidator:
    """Validator for CSV data using Pandera schemas."""
    
    def __init__(self, project_id: Optional[int] = None):
        self.logger = get_logger(project_id)
        self.errors: List[ValidationError] = []
    
    @property
    def window_schema(self) -> DataFrameSchema:
        """Schema for window/glazing elements CSV."""
        return DataFrameSchema({
            "ElementId": Column(pa.String, nullable=False, 
                              checks=[Check.str_length(min_value=1, max_value=50)]),
            "Family": Column(pa.String, nullable=False,
                           checks=[Check.str_length(min_value=1, max_value=100)]),
            "Glass Area (m²)": Column(pa.Float, nullable=False,
                                    checks=[Check.greater_than_or_equal_to(0),
                                           Check.less_than_or_equal_to(100)]),
            "Azimuth (°)": Column(pa.Float, nullable=False,
                                checks=[Check.greater_than_or_equal_to(0),
                                       Check.less_than(360)]),
            "Level": Column(pa.String, nullable=True),
            "HostWallId": Column(pa.String, nullable=True),
            "Window Width (m)": Column(pa.Float, nullable=True,
                                     checks=[Check.greater_than(0)]),
            "Window Height (m)": Column(pa.Float, nullable=True,
                                      checks=[Check.greater_than(0)])
        }, strict=False)  # Allow additional columns
    
    @property
    def wall_schema(self) -> DataFrameSchema:
        """Schema for wall elements CSV."""
        return DataFrameSchema({
            "ElementId": Column(pa.String, nullable=False,
                              checks=[Check.str_length(min_value=1, max_value=50)]),
            "Wall Type": Column(pa.String, nullable=False,
                              checks=[Check.str_length(min_value=1, max_value=100)]),
            "Level": Column(pa.String, nullable=True),
            "Length (m)": Column(pa.Float, nullable=False,
                               checks=[Check.greater_than(0)]),
            "Area (m²)": Column(pa.Float, nullable=False,
                              checks=[Check.greater_than(0)]),
            "Azimuth (°)": Column(pa.Float, nullable=False,
                                checks=[Check.greater_than_or_equal_to(0),
                                       Check.less_than(360)])
        }, strict=False)
    
    def validate_csv_headers(self, df: pd.DataFrame, expected_type: str) -> Tuple[bool, List[str]]:
        """Validate CSV headers before full validation."""
        missing_columns = []
        
        if expected_type == "windows":
            required_columns = ["ElementId", "Family", "Glass Area (m²)", "Azimuth (°)"]
        elif expected_type == "walls":
            required_columns = ["ElementId", "Wall Type", "Length (m)", "Area (m²)", "Azimuth (°)"]
        else:
            return False, ["Unknown data type"]
        
        for col in required_columns:
            if col not in df.columns:
                missing_columns.append(col)
        
        return len(missing_columns) == 0, missing_columns
    
    def detect_units(self, df: pd.DataFrame, column: str) -> Dict[str, Any]:
        """Detect and suggest unit conversions."""
        if column not in df.columns:
            return {"needs_conversion": False}
        
        values = df[column].dropna()
        if len(values) == 0:
            return {"needs_conversion": False}
        
        # Check for angle units (radians vs degrees)
        if "azimuth" in column.lower() or "angle" in column.lower():
            max_val = values.max()
            if max_val <= 2 * np.pi:  # Likely radians
                return {
                    "needs_conversion": True,
                    "detected_unit": "radians",
                    "target_unit": "degrees",
                    "conversion_factor": 180 / np.pi
                }
        
        # Check for area units (cm² vs m²)
        if "area" in column.lower():
            median_val = values.median()
            if median_val > 10000:  # Likely cm²
                return {
                    "needs_conversion": True,
                    "detected_unit": "cm²",
                    "target_unit": "m²",
                    "conversion_factor": 0.0001
                }
        
        return {"needs_conversion": False}
    
    def check_duplicates(self, df: pd.DataFrame, column: str = "ElementId") -> List[str]:
        """Check for duplicate ElementIds."""
        if column not in df.columns:
            return []
        
        duplicates = df[df.duplicated(subset=[column], keep=False)][column].tolist()
        return list(set(duplicates))
    
    def validate_window_data(self, df: pd.DataFrame) -> Tuple[bool, List[ValidationError]]:
        """Validate window/glazing data."""
        self.errors = []
        
        try:
            # Basic header validation
            is_valid, missing_cols = self.validate_csv_headers(df, "windows")
            if not is_valid:
                for col in missing_cols:
                    self.errors.append(ValidationError(
                        row_number=0,
                        column=col,
                        error_message=f"Required column '{col}' is missing",
                        suggested_fix=f"Add column '{col}' to your CSV file"
                    ))
                return False, self.errors
            
            # Check for duplicates
            duplicates = self.check_duplicates(df, "ElementId")
            if duplicates:
                self.errors.append(ValidationError(
                    row_number=0,
                    column="ElementId",
                    error_message=f"Duplicate ElementIds found: {duplicates[:5]}{'...' if len(duplicates) > 5 else ''}",
                    suggested_fix="Ensure all ElementIds are unique"
                ))
            
            # Validate against schema
            try:
                self.window_schema.validate(df, lazy=True)
            except pa.errors.SchemaErrors as e:
                for error in e.failure_cases.itertuples():
                    self.errors.append(ValidationError(
                        row_number=error.index if hasattr(error, 'index') else 0,
                        column=error.column if hasattr(error, 'column') else "unknown",
                        error_message=str(error.failure_case) if hasattr(error, 'failure_case') else str(error),
                        suggested_fix="Check data format and ranges"
                    ))
            
            # Check unit conversions
            for col in ["Azimuth (°)", "Glass Area (m²)"]:
                if col in df.columns:
                    unit_info = self.detect_units(df, col)
                    if unit_info["needs_conversion"]:
                        self.errors.append(ValidationError(
                            row_number=0,
                            column=col,
                            error_message=f"Values appear to be in {unit_info['detected_unit']}, expected {unit_info['target_unit']}",
                            suggested_fix=f"Multiply values by {unit_info['conversion_factor']}"
                        ))
            
            return len(self.errors) == 0, self.errors
            
        except Exception as e:
            self.logger.error(f"Validation error: {str(e)}")
            self.errors.append(ValidationError(
                row_number=0,
                column="general",
                error_message=f"Validation failed: {str(e)}",
                suggested_fix="Check file format and structure"
            ))
            return False, self.errors
    
    def validate_wall_data(self, df: pd.DataFrame) -> Tuple[bool, List[ValidationError]]:
        """Validate wall data."""
        self.errors = []
        
        try:
            # Basic header validation
            is_valid, missing_cols = self.validate_csv_headers(df, "walls")
            if not is_valid:
                for col in missing_cols:
                    self.errors.append(ValidationError(
                        row_number=0,
                        column=col,
                        error_message=f"Required column '{col}' is missing",
                        suggested_fix=f"Add column '{col}' to your CSV file"
                    ))
                return False, self.errors
            
            # Check for duplicates
            duplicates = self.check_duplicates(df, "ElementId")
            if duplicates:
                self.errors.append(ValidationError(
                    row_number=0,
                    column="ElementId",
                    error_message=f"Duplicate ElementIds found: {duplicates[:5]}{'...' if len(duplicates) > 5 else ''}",
                    suggested_fix="Ensure all ElementIds are unique"
                ))
            
            # Validate against schema
            try:
                self.wall_schema.validate(df, lazy=True)
            except pa.errors.SchemaErrors as e:
                for error in e.failure_cases.itertuples():
                    self.errors.append(ValidationError(
                        row_number=error.index if hasattr(error, 'index') else 0,
                        column=error.column if hasattr(error, 'column') else "unknown",
                        error_message=str(error.failure_case) if hasattr(error, 'failure_case') else str(error),
                        suggested_fix="Check data format and ranges"
                    ))
            
            # Validate calculated height
            if "Length (m)" in df.columns and "Area (m²)" in df.columns:
                for idx, row in df.iterrows():
                    if pd.notna(row["Length (m)"]) and pd.notna(row["Area (m²)"]):
                        if row["Length (m)"] > 0:
                            height = row["Area (m²)"] / row["Length (m)"]
                            if height > 50:  # Unreasonably tall wall
                                self.errors.append(ValidationError(
                                    row_number=idx,
                                    column="calculated_height",
                                    error_message=f"Calculated wall height ({height:.1f}m) seems too tall",
                                    suggested_fix="Check area and length values"
                                ))
            
            return len(self.errors) == 0, self.errors
            
        except Exception as e:
            self.logger.error(f"Wall validation error: {str(e)}")
            self.errors.append(ValidationError(
                row_number=0,
                column="general",
                error_message=f"Validation failed: {str(e)}",
                suggested_fix="Check file format and structure"
            ))
            return False, self.errors


class FileValidator:
    """File-level validation utilities."""
    
    def __init__(self):
        self.logger = get_logger()
    
    def validate_file_size(self, file_size: int, max_size_mb: int = 50) -> bool:
        """Validate file size."""
        max_size_bytes = max_size_mb * 1024 * 1024
        return file_size <= max_size_bytes
    
    def validate_file_extension(self, filename: str, allowed_extensions: List[str] = None) -> bool:
        """Validate file extension."""
        if allowed_extensions is None:
            allowed_extensions = [".csv"]
        
        return any(filename.lower().endswith(ext) for ext in allowed_extensions)
    
    def validate_mime_type(self, mime_type: str, allowed_types: List[str] = None) -> bool:
        """Validate MIME type."""
        if allowed_types is None:
            allowed_types = ["text/csv", "application/csv"]
        
        return mime_type in allowed_types
    
    def scan_for_malware(self, file_content: bytes) -> bool:
        """Placeholder for malware scanning."""
        # TODO: Implement actual malware scanning
        # For now, just check for suspicious patterns
        suspicious_patterns = [b"<script", b"javascript:", b"eval("]
        
        for pattern in suspicious_patterns:
            if pattern in file_content:
                self.logger.warning(f"Suspicious pattern detected: {pattern}")
                return False
        
        return True


def validate_locale_numbers(df: pd.DataFrame, numeric_columns: List[str]) -> pd.DataFrame:
    """Convert locale-aware numbers (comma decimal separators)."""
    for col in numeric_columns:
        if col in df.columns:
            # Convert comma decimal separators to dots
            df[col] = df[col].astype(str).str.replace(',', '.', regex=False)
            try:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            except Exception:
                pass  # Keep original values if conversion fails
    
    return df