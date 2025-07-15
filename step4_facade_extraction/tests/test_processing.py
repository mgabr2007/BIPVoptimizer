"""
Unit tests for data processing functions.
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch
from step4_facade_extraction.processing import DataProcessor
from step4_facade_extraction.models import OrientationType, WindowRecord, WallRecord


class TestDataProcessor:
    """Test cases for DataProcessor class."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.processor = DataProcessor(project_id=1)
    
    def test_orientation_from_azimuth(self):
        """Test azimuth to orientation conversion."""
        test_cases = [
            (0, OrientationType.NORTH),
            (45, OrientationType.NORTH),
            (90, OrientationType.EAST),
            (135, OrientationType.SOUTH),
            (180, OrientationType.SOUTH),
            (225, OrientationType.SOUTH),
            (270, OrientationType.WEST),
            (315, OrientationType.NORTH),
            (360, OrientationType.NORTH),
            (-45, OrientationType.NORTH),  # Should handle negative values
            (np.nan, OrientationType.UNKNOWN)  # Should handle NaN
        ]
        
        for azimuth, expected in test_cases:
            result = self.processor.get_orientation_from_azimuth(azimuth)
            assert result == expected, f"Azimuth {azimuth} should map to {expected}, got {result}"
    
    def test_pv_suitability_determination(self):
        """Test PV suitability logic."""
        # Test suitable case
        assert self.processor.determine_pv_suitability(
            OrientationType.SOUTH, 5.0, "Window Family"
        ) == True
        
        # Test unsuitable orientation
        assert self.processor.determine_pv_suitability(
            OrientationType.NORTH, 5.0, "Window Family"
        ) == False
        
        # Test too small area
        assert self.processor.determine_pv_suitability(
            OrientationType.SOUTH, 0.1, "Window Family"
        ) == False
        
        # Test too large area
        assert self.processor.determine_pv_suitability(
            OrientationType.SOUTH, 150.0, "Window Family"
        ) == False
        
        # Test excluded family
        assert self.processor.determine_pv_suitability(
            OrientationType.SOUTH, 5.0, "Roof Window"
        ) == False
    
    def test_detect_csv_encoding(self):
        """Test CSV encoding detection."""
        # UTF-8 content
        utf8_content = "ElementId,Family\nW001,Window".encode('utf-8')
        assert self.processor.detect_csv_encoding(utf8_content) == 'utf-8'
        
        # Latin-1 content with special characters
        latin1_content = "ElementId,Family\nW001,Fenêtre".encode('latin-1')
        result = self.processor.detect_csv_encoding(latin1_content)
        assert result in ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']
    
    def test_process_window_chunk(self):
        """Test window chunk processing."""
        # Create test DataFrame
        test_data = {
            'ElementId': ['W001', 'W002', 'W003'],
            'Family': ['Casement', 'Fixed', 'Sliding'],
            'Glass Area (m²)': [2.5, 1.8, 3.2],
            'Azimuth (°)': [180, 90, 270],
            'Level': ['01', '02', '01'],
            'HostWallId': ['Wall001', 'Wall002', 'Wall003']
        }
        df = pd.DataFrame(test_data)
        
        windows, errors = self.processor.process_window_chunk(df)
        
        assert len(windows) == 3
        assert len(errors) == 0
        assert all(isinstance(w, WindowRecord) for w in windows)
        assert windows[0].element_id == 'W001'
        assert windows[0].orientation == OrientationType.SOUTH
        assert windows[0].pv_suitable == True
    
    def test_process_wall_chunk(self):
        """Test wall chunk processing."""
        # Create test DataFrame
        test_data = {
            'ElementId': ['Wall001', 'Wall002'],
            'Wall Type': ['Exterior', 'Interior'],
            'Length (m)': [10.0, 8.0],
            'Area (m²)': [30.0, 24.0],
            'Azimuth (°)': [180, 90],
            'Level': ['01', '01']
        }
        df = pd.DataFrame(test_data)
        
        walls, errors = self.processor.process_wall_chunk(df)
        
        assert len(walls) == 2
        assert len(errors) == 0
        assert all(isinstance(w, WallRecord) for w in walls)
        assert walls[0].element_id == 'Wall001'
        assert walls[0].orientation == OrientationType.SOUTH


class TestDataValidation:
    """Test cases for data validation."""
    
    def test_window_data_validation(self):
        """Test window data validation."""
        from step4_facade_extraction.validators import DataFrameValidator
        
        validator = DataFrameValidator()
        
        # Valid data
        valid_data = {
            'ElementId': ['W001', 'W002'],
            'Family': ['Casement', 'Fixed'],
            'Glass Area (m²)': [2.5, 1.8],
            'Azimuth (°)': [180, 90]
        }
        df = pd.DataFrame(valid_data)
        
        is_valid, errors = validator.validate_window_data(df)
        assert is_valid == True
        assert len(errors) == 0
    
    def test_wall_data_validation(self):
        """Test wall data validation."""
        from step4_facade_extraction.validators import DataFrameValidator
        
        validator = DataFrameValidator()
        
        # Valid data
        valid_data = {
            'ElementId': ['Wall001', 'Wall002'],
            'Wall Type': ['Exterior', 'Interior'],
            'Length (m)': [10.0, 8.0],
            'Area (m²)': [30.0, 24.0],
            'Azimuth (°)': [180, 90]
        }
        df = pd.DataFrame(valid_data)
        
        is_valid, errors = validator.validate_wall_data(df)
        assert is_valid == True
        assert len(errors) == 0


@pytest.fixture
def sample_window_data():
    """Sample window data for testing."""
    return {
        'ElementId': ['W001', 'W002', 'W003', 'W004'],
        'Family': ['Casement', 'Fixed', 'Sliding', 'Awning'],
        'Glass Area (m²)': [2.5, 1.8, 3.2, 0.8],
        'Azimuth (°)': [180, 90, 270, 45],
        'Level': ['01', '02', '01', '03']
    }


@pytest.fixture
def sample_wall_data():
    """Sample wall data for testing."""
    return {
        'ElementId': ['Wall001', 'Wall002', 'Wall003'],
        'Wall Type': ['Exterior', 'Interior', 'Exterior'],
        'Length (m)': [10.0, 8.0, 12.0],
        'Area (m²)': [30.0, 24.0, 36.0],
        'Azimuth (°)': [180, 90, 270]
    }


def test_integration_window_processing(sample_window_data):
    """Integration test for complete window processing."""
    processor = DataProcessor(project_id=1)
    df = pd.DataFrame(sample_window_data)
    
    # Convert to CSV bytes for processing
    csv_buffer = df.to_csv(index=False).encode('utf-8')
    
    result = processor.process_csv_file(
        "test_windows.csv", csv_buffer, "windows"
    )
    
    assert result.success == True
    assert result.total_elements == 4
    assert result.processed_elements == 4
    assert result.suitable_elements > 0  # At least some should be suitable


def test_integration_wall_processing(sample_wall_data):
    """Integration test for complete wall processing."""
    processor = DataProcessor(project_id=1)
    df = pd.DataFrame(sample_wall_data)
    
    # Convert to CSV bytes for processing
    csv_buffer = df.to_csv(index=False).encode('utf-8')
    
    result = processor.process_csv_file(
        "test_walls.csv", csv_buffer, "walls"
    )
    
    assert result.success == True
    assert result.total_elements == 3
    assert result.processed_elements == 3