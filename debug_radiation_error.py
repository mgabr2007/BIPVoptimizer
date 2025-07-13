#!/usr/bin/env python3
"""
Debug radiation analysis error comprehensively
"""

import pandas as pd
import sys
import os
import traceback
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))

def debug_radiation_error():
    """Debug the exact error in radiation analysis"""
    
    print("=" * 60)
    print("DEBUGGING RADIATION ANALYSIS ERROR")
    print("=" * 60)
    
    try:
        # Import the render function directly
        from pages_modules.radiation_grid import render_radiation_grid
        
        # Set up mock session state
        import streamlit as st
        
        # Mock building elements
        test_elements = [
            {
                'element_id': 'test_1',
                'Element ID': 'test_1',
                'orientation': 'South',
                'azimuth': 180,
                'glass_area': 2.5,
                'pv_suitable': True,
                'level': 'Level 1'
            }
        ]
        
        # Mock TMY data - fixed array lengths
        data_length = 100
        tmy_data = pd.DataFrame({
            'datetime': pd.date_range('2023-01-01', periods=data_length, freq='H'),
            'GHI': [500] * data_length,
            'DNI': [400] * data_length,
            'DHI': [100] * data_length,
            'day_of_year': [1] * data_length,
            'hour': (list(range(24)) * (data_length // 24 + 1))[:data_length]  # Proper cycling
        })
        
        # Mock weather analysis
        weather_analysis = {
            'tmy_data': tmy_data,
            'annual_ghi': 1500,
            'temperature': 20
        }
        
        # Mock project data
        project_data = {
            'project_name': 'Test Project',
            'location': 'Berlin, Germany',
            'latitude': 52.5,
            'longitude': 13.4,
            'weather_analysis': weather_analysis
        }
        
        # Set up session state
        if 'building_elements' not in st.session_state:
            st.session_state.building_elements = pd.DataFrame(test_elements)
        if 'project_data' not in st.session_state:
            st.session_state.project_data = project_data
        if 'weather_analysis' not in st.session_state:
            st.session_state.weather_analysis = weather_analysis
        
        print("✅ Mock data created successfully")
        
        # Try to call the render function
        print("🔍 Attempting to run render_radiation_grid...")
        render_radiation_grid()
        print("✅ render_radiation_grid completed successfully!")
        
    except Exception as e:
        print(f"❌ ERROR in render_radiation_grid: {e}")
        print("\nFull traceback:")
        traceback.print_exc()
        
        # Try to identify the exact line causing the error
        print("\n🔍 Analyzing error location...")
        tb = traceback.format_exc()
        lines = tb.split('\n')
        for i, line in enumerate(lines):
            if "'str' object has no attribute 'get'" in line:
                print(f"Error at line {i}: {line}")
                if i > 0:
                    print(f"Previous line: {lines[i-1]}")
                if i < len(lines) - 1:
                    print(f"Next line: {lines[i+1]}")
                break
        
        return False
    
    return True

if __name__ == "__main__":
    success = debug_radiation_error()
    if success:
        print("\n🎉 DEBUG COMPLETED - No errors found!")
    else:
        print("\n💥 DEBUG FAILED - Error identified!")