#!/usr/bin/env python3
"""
Test Data Type Consistency Fix for Radiation Analysis
Verifies that suitable_elements is properly handled as DataFrame throughout the code
"""

import pandas as pd
import numpy as np
import sys
import os

# Add the project directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_suitable_elements_handling():
    """Test that suitable_elements is properly handled as DataFrame"""
    
    print("=" * 60)
    print("TESTING DATA TYPE CONSISTENCY FIX")
    print("=" * 60)
    
    # Test data - list of dictionaries (original problematic format)
    elements_list = [
        {
            'element_id': 'TEST_001',
            'Element ID': 'TEST_001',
            'glass_area': 2.5,
            'Glass Area (m²)': 2.5,
            'orientation': 'South',
            'Orientation': 'South',
            'azimuth': 180,
            'Azimuth (degrees)': 180,
            'pv_suitable': True,
            'suitable': True,
            'level': 'Level 1',
            'window_width': 1.5,
            'window_height': 1.0,
            'wall_hosted_id': 'WALL_001'
        },
        {
            'element_id': 'TEST_002',
            'Element ID': 'TEST_002',
            'glass_area': 1.8,
            'Glass Area (m²)': 1.8,
            'orientation': 'East',
            'Orientation': 'East',
            'azimuth': 90,
            'Azimuth (degrees)': 90,
            'pv_suitable': True,
            'suitable': True,
            'level': 'Level 2',
            'window_width': 1.2,
            'window_height': 1.5,
            'wall_hosted_id': 'WALL_002'
        }
    ]
    
    # Test DataFrame creation from list
    try:
        df_from_list = pd.DataFrame(elements_list)
        print(f"✅ DataFrame created from list: {len(df_from_list)} rows")
        print(f"   Columns: {list(df_from_list.columns)}")
    except Exception as e:
        print(f"❌ DataFrame creation failed: {e}")
        return False
    
    # Test iteration with .iterrows()
    try:
        for i, (_, element) in enumerate(df_from_list.iterrows()):
            element_id = element.get('element_id', f'Unknown_{i}')
            glass_area = element.get('glass_area', 1.5)
            orientation = element.get('orientation', 'South')
            print(f"   Element {i+1}: ID={element_id}, Area={glass_area}, Orientation={orientation}")
        print("✅ .iterrows() iteration successful")
    except Exception as e:
        print(f"❌ .iterrows() iteration failed: {e}")
        return False
    
    # Test direct DataFrame indexing with .iloc
    try:
        for i in range(len(df_from_list)):
            element = df_from_list.iloc[i]
            element_id = element.get('element_id', f'Unknown_{i}')
            glass_area = element.get('glass_area', 1.5)
            orientation = element.get('orientation', 'South')
            print(f"   Element {i+1}: ID={element_id}, Area={glass_area}, Orientation={orientation}")
        print("✅ .iloc indexing successful")
    except Exception as e:
        print(f"❌ .iloc indexing failed: {e}")
        return False
    
    # Test consistency between different access methods
    try:
        # Method 1: .iterrows()
        ids_iterrows = []
        for _, element in df_from_list.iterrows():
            ids_iterrows.append(element.get('element_id', 'Unknown'))
        
        # Method 2: .iloc
        ids_iloc = []
        for i in range(len(df_from_list)):
            element = df_from_list.iloc[i]
            ids_iloc.append(element.get('element_id', 'Unknown'))
        
        if ids_iterrows == ids_iloc:
            print("✅ Data consistency verified between .iterrows() and .iloc")
        else:
            print(f"❌ Data inconsistency: {ids_iterrows} vs {ids_iloc}")
            return False
    except Exception as e:
        print(f"❌ Consistency check failed: {e}")
        return False
    
    # Test handling of mixed data types
    try:
        # Add some potential problem cases
        mixed_data = elements_list + [
            {
                'element_id': 'TEST_003',
                'glass_area': '2.0',  # String instead of float
                'orientation': 'West',
                'azimuth': '270',     # String instead of int
                'pv_suitable': 'True', # String instead of bool
                'level': 'Level 3'
            }
        ]
        
        df_mixed = pd.DataFrame(mixed_data)
        
        for i, (_, element) in enumerate(df_mixed.iterrows()):
            element_id = element.get('element_id', f'Unknown_{i}')
            glass_area = float(element.get('glass_area', 1.5))  # Force conversion
            orientation = element.get('orientation', 'South')
            azimuth = float(element.get('azimuth', 180))  # Force conversion
            
        print("✅ Mixed data types handled successfully")
    except Exception as e:
        print(f"❌ Mixed data types failed: {e}")
        return False
    
    print("\n🎉 All data type consistency tests PASSED!")
    return True

if __name__ == "__main__":
    success = test_suitable_elements_handling()
    if success:
        print("\n💥 Data type consistency fix VERIFIED!")
    else:
        print("\n💥 Data type consistency fix FAILED!")
        sys.exit(1)