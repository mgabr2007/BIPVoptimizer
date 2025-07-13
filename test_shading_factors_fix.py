#!/usr/bin/env python3
"""
Test shading factors fix for 'str' object has no attribute 'get' error
"""

import pandas as pd
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))

from pages_modules.radiation_grid import generate_radiation_grid
from datetime import datetime
import time

def test_shading_factors_fix():
    """Test that shading factors handle different data types correctly"""
    
    print("=" * 60)
    print("TESTING SHADING FACTORS FIX")
    print("=" * 60)
    
    # Create test elements
    test_elements = pd.DataFrame([
        {
            'element_id': 'element_test_1',
            'Element ID': 'element_test_1',
            'element_type': 'Window',
            'orientation': 'South',
            'glass_area': 2.5,
            'azimuth': 180.0,
            'tilt': 90.0,
            'level': 'Level 1',
            'pv_suitable': True
        },
        {
            'element_id': 'element_test_2',
            'Element ID': 'element_test_2',
            'element_type': 'Window',
            'orientation': 'East',
            'glass_area': 3.0,
            'azimuth': 90.0,
            'tilt': 90.0,
            'level': 'Level 2',
            'pv_suitable': True
        }
    ])
    
    print(f"Test elements: {len(test_elements)}")
    
    # Create test TMY data
    tmy_data = pd.DataFrame({
        'datetime': pd.date_range('2023-01-01', periods=100, freq='H'),
        'GHI': [500] * 100,
        'DNI': [400] * 100,
        'DHI': [100] * 100,
        'Temperature': [20] * 100
    })
    
    print(f"TMY data shape: {tmy_data.shape}")
    
    # Test 1: None shading factors (should work)
    print("\n--- Test 1: None shading factors ---")
    try:
        start_time = time.time()
        result1 = generate_radiation_grid(
            suitable_elements=test_elements,
            tmy_data=tmy_data,
            latitude=52.5,
            longitude=13.4,
            shading_factors=None,
            walls_data=None
        )
        end_time = time.time()
        
        print(f"✅ SUCCESS: None shading factors - {len(result1)} results in {end_time - start_time:.2f}s")
        
    except Exception as e:
        print(f"❌ FAILED: None shading factors - Error: {e}")
        return False
    
    # Test 2: String shading factors (should not crash)
    print("\n--- Test 2: String shading factors ---")
    try:
        start_time = time.time()
        result2 = generate_radiation_grid(
            suitable_elements=test_elements,
            tmy_data=tmy_data,
            latitude=52.5,
            longitude=13.4,
            shading_factors="invalid_string",  # This should not crash
            walls_data=None
        )
        end_time = time.time()
        
        print(f"✅ SUCCESS: String shading factors handled - {len(result2)} results in {end_time - start_time:.2f}s")
        
    except Exception as e:
        print(f"❌ FAILED: String shading factors - Error: {e}")
        return False
    
    # Test 3: Dict shading factors (should work)
    print("\n--- Test 3: Dict shading factors ---")
    try:
        start_time = time.time()
        result3 = generate_radiation_grid(
            suitable_elements=test_elements,
            tmy_data=tmy_data,
            latitude=52.5,
            longitude=13.4,
            shading_factors={'10': {'shading_factor': 0.9}},  # Valid dict
            walls_data=None
        )
        end_time = time.time()
        
        print(f"✅ SUCCESS: Dict shading factors - {len(result3)} results in {end_time - start_time:.2f}s")
        
    except Exception as e:
        print(f"❌ FAILED: Dict shading factors - Error: {e}")
        return False
    
    # Test 4: Invalid dict shading factors (should not crash)
    print("\n--- Test 4: Invalid dict shading factors ---")
    try:
        start_time = time.time()
        result4 = generate_radiation_grid(
            suitable_elements=test_elements,
            tmy_data=tmy_data,
            latitude=52.5,
            longitude=13.4,
            shading_factors={'invalid': 'data'},  # Invalid dict structure
            walls_data=None
        )
        end_time = time.time()
        
        print(f"✅ SUCCESS: Invalid dict shading factors handled - {len(result4)} results in {end_time - start_time:.2f}s")
        
    except Exception as e:
        print(f"❌ FAILED: Invalid dict shading factors - Error: {e}")
        return False
    
    print("\n🎉 All shading factors tests PASSED!")
    return True

if __name__ == "__main__":
    success = test_shading_factors_fix()
    if success:
        print("\n💥 Shading factors fix test PASSED!")
    else:
        print("\n💥 Shading factors fix test FAILED!")
        sys.exit(1)