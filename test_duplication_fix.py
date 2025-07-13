#!/usr/bin/env python3
"""
Test Element Duplication Prevention Fix
"""

import streamlit as st
import pandas as pd
import time
from datetime import datetime
from pages_modules.radiation_grid import generate_radiation_grid
from utils.analysis_monitor import AnalysisMonitor
from utils.radiation_logger import RadiationLogger
from utils.database_helper import DatabaseHelper

# Mock session state for testing
class MockSessionState:
    def __init__(self):
        self.data = {}
    
    def __getitem__(self, key):
        return self.data[key]
    
    def __setitem__(self, key, value):
        self.data[key] = value
        
    def __contains__(self, key):
        return key in self.data
    
    def get(self, key, default=None):
        return self.data.get(key, default)

def test_duplication_prevention():
    """Test that element duplication is prevented"""
    print("=" * 60)
    print("TESTING ELEMENT DUPLICATION PREVENTION")
    print("=" * 60)
    
    # Initialize mock session state
    st.session_state = MockSessionState()
    st.session_state.project_id = 1
    
    # Create test elements with some duplicates
    test_elements = [
        {
            'element_id': 'element_367277',  # This is the one from user's evidence
            'orientation': 'South',
            'azimuth': 180,
            'tilt': 90,
            'area': 2.5,
            'level': '01',
            'width': 1.5,
            'height': 1.7,
            'wall_hosted_id': 'wall_123'
        },
        {
            'element_id': 'element_367278',
            'orientation': 'East',
            'azimuth': 90,
            'tilt': 90,
            'area': 3.0,
            'level': '02',
            'width': 1.8,
            'height': 1.7,
            'wall_hosted_id': 'wall_124'
        },
        {
            'element_id': 'element_367279',
            'orientation': 'West',
            'azimuth': 270,
            'tilt': 90,
            'area': 2.8,
            'level': '01',
            'width': 1.6,
            'height': 1.8,
            'wall_hosted_id': 'wall_125'
        }
    ]
    
    # Create simple TMY data
    dates = pd.date_range('2023-01-01', periods=48, freq='H')
    tmy_data = pd.DataFrame({
        'Date': dates,
        'GHI': [500 + i * 10 for i in range(48)],
        'DNI': [700 + i * 5 for i in range(48)],
        'DHI': [200 + i * 3 for i in range(48)],
        'Temperature': [20 + i * 0.1 for i in range(48)]
    })
    
    print(f"Test elements: {len(test_elements)}")
    print(f"Element IDs: {[e['element_id'] for e in test_elements]}")
    print(f"TMY data shape: {tmy_data.shape}")
    
    # Initialize monitoring
    monitor = AnalysisMonitor()
    db_helper = DatabaseHelper()
    
    # Clear any existing processed elements
    if hasattr(st.session_state, 'processed_element_ids'):
        del st.session_state.processed_element_ids
    
    try:
        # Convert elements to DataFrame as expected by the function
        test_elements_df = pd.DataFrame(test_elements)
        
        # Process elements
        start_time = time.time()
        results = generate_radiation_grid(
            test_elements_df,
            tmy_data,
            52.5,  # Berlin latitude
            13.4,  # Berlin longitude
            shading_factors=None,
            walls_data=None
        )
        end_time = time.time()
        
        print(f"\nProcessing completed in {end_time - start_time:.2f} seconds")
        print(f"Results count: {len(results)}")
        print(f"Results type: {type(results)}")
        
        # Handle DataFrame results
        if isinstance(results, pd.DataFrame):
            if not results.empty:
                print(f"Results columns: {list(results.columns)}")
                print(f"First result: {results.iloc[0].to_dict()}")
                processed_ids = results['element_id'].tolist() if 'element_id' in results.columns else []
            else:
                processed_ids = []
        elif isinstance(results, list) and results:
            if isinstance(results[0], dict):
                processed_ids = [r['element_id'] for r in results]
            else:
                processed_ids = [str(r) for r in results]
        else:
            processed_ids = []
            
        print(f"Processed IDs: {processed_ids}")
        
        # Test for duplicates
        unique_ids = set(processed_ids)
        if len(processed_ids) != len(unique_ids):
            print("❌ ERROR: Duplicate elements found!")
            duplicates = [x for x in processed_ids if processed_ids.count(x) > 1]
            print(f"Duplicates: {duplicates}")
        else:
            print("✅ SUCCESS: No duplicate elements found")
        
        # Check monitoring data
        try:
            monitor_data = monitor.get_summary()
            print(f"\nMonitoring Summary:")
            print(f"- Elements started: {monitor_data.get('elements_started', 'N/A')}")
            print(f"- Elements completed: {monitor_data.get('elements_completed', 'N/A')}")
            print(f"- Elements failed: {monitor_data.get('elements_failed', 'N/A')}")
            print(f"- Total processing time: {monitor_data.get('total_processing_time', 0):.2f}s")
        except Exception as e:
            print(f"Monitoring data unavailable: {e}")
        
        # Test database logging
        try:
            outcomes = db_helper.get_radiation_outcomes(limit=10)
            print(f"\nDatabase outcomes: {len(outcomes)}")
        except Exception as e:
            print(f"Database outcomes unavailable: {e}")
        
        return len(processed_ids) == len(unique_ids)
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_duplication_prevention()
    if success:
        print("\n🎉 Element duplication prevention test PASSED!")
    else:
        print("\n💥 Element duplication prevention test FAILED!")