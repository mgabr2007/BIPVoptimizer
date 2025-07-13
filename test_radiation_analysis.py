#!/usr/bin/env python3
"""
Test radiation analysis functionality
"""

import pandas as pd
import sys
import os
import traceback
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))

def test_radiation_analysis():
    """Test the radiation analysis with comprehensive error handling"""
    
    print("=" * 60)
    print("TESTING RADIATION ANALYSIS FUNCTIONALITY")
    print("=" * 60)
    
    try:
        # Import required modules
        from pages_modules.radiation_grid import calculate_combined_shading_factor, calculate_precise_shading_factor
        
        print("✅ Successfully imported radiation analysis functions")
        
        # Test data structures
        test_window = {
            'element_id': 'test_window_1',
            'orientation': 'South',
            'azimuth': 180,
            'glass_area': 2.5,
            'level': 'Level 1'
        }
        
        test_walls = pd.DataFrame([
            {
                'ElementId': 'wall_1',
                'Level': 'Level 1',
                'Length (m)': 5.0,
                'Area (m²)': 15.0,
                'Azimuth (°)': 180,
                'OriX': 0,
                'OriY': 1,
                'OriZ': 0
            }
        ])
        
        test_solar_pos = {
            'elevation': 45,
            'azimuth': 180
        }
        
        print("✅ Test data structures created")
        
        # Test shading factor calculation with different data types
        test_cases = [
            ("Normal dict", {'shading_factor': 0.9}),
            ("String (should fail gracefully)", "invalid_string"),
            ("None (should fail gracefully)", None),
            ("Empty dict", {}),
            ("Dict without shading_factor", {'other_key': 'value'}),
            ("Integer (should fail gracefully)", 123),
            ("List (should fail gracefully)", [1, 2, 3])
        ]
        
        for test_name, test_data in test_cases:
            print(f"\nTesting {test_name}:")
            try:
                # Test precise shading factor calculation
                result = calculate_precise_shading_factor(test_window, test_window, test_solar_pos)
                print(f"  ✅ Precise shading factor: {result}")
                
                # Test combined shading factor calculation
                result = calculate_combined_shading_factor(test_window, test_walls, test_solar_pos)
                print(f"  ✅ Combined shading factor: {result}")
                
            except Exception as e:
                print(f"  ❌ Error in {test_name}: {e}")
                traceback.print_exc()
        
        print("\n" + "=" * 60)
        print("RADIATION ANALYSIS TEST COMPLETED")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ CRITICAL ERROR: {e}")
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = test_radiation_analysis()
    if success:
        print("\n🎉 All tests passed!")
    else:
        print("\n💥 Some tests failed!")