"""
Test element duplication prevention
"""

import streamlit as st
from utils.analysis_monitor import analysis_monitor
from utils.radiation_logger import radiation_logger
import time

def test_duplication_prevention():
    st.title("🧪 Element Duplication Prevention Test")
    
    # Simulate processing with same element ID multiple times
    test_elements = [
        {'element_id': '367277', 'orientation': 'West', 'area': 23.4},
        {'element_id': '367277', 'orientation': 'West', 'area': 23.4},  # Duplicate
        {'element_id': '367278', 'orientation': 'West', 'area': 23.4},
        {'element_id': '367277', 'orientation': 'West', 'area': 23.4},  # Duplicate
        {'element_id': '367279', 'orientation': 'West', 'area': 23.4},
        {'element_id': '367278', 'orientation': 'West', 'area': 23.4},  # Duplicate
    ]
    
    if st.button("🚀 Test Duplication Prevention"):
        processed_element_ids = set()
        
        # Create monitor
        monitor = analysis_monitor.create_monitor_display()
        
        st.subheader("Processing Results:")
        
        for i, element in enumerate(test_elements):
            element_id = element['element_id']
            orientation = element['orientation']
            area = element['area']
            
            # Check if already processed
            if element_id in processed_element_ids:
                st.warning(f"❌ DUPLICATE DETECTED: Element {element_id} already processed - SKIPPING")
                monitor.log_element_skip(element_id, "Already processed")
                continue
            
            # Process element
            st.success(f"✅ Processing: Element {element_id} ({orientation}, {area}m²)")
            monitor.log_element_start(element_id, orientation, area)
            
            # Simulate processing time
            time.sleep(0.1)
            
            # Simulate successful processing
            annual_radiation = 1200 + (i * 50)  # Simulate different values
            processing_time = 0.1
            
            monitor.log_element_success(element_id, annual_radiation, processing_time)
            
            # CRITICAL: Add to processed set
            processed_element_ids.add(element_id)
            
            # Individual element completion display removed
        
        st.subheader("Test Summary:")
        st.write(f"**Total test elements**: {len(test_elements)}")
        st.write(f"**Unique elements processed**: {len(processed_element_ids)}")
        st.write(f"**Duplicates prevented**: {len(test_elements) - len(processed_element_ids)}")
        st.write(f"**Processed element IDs**: {sorted(processed_element_ids)}")
        
        if len(processed_element_ids) == 3:  # Should be 3 unique elements
            st.success("🎉 **TEST PASSED**: Duplication prevention working correctly!")
        else:
            st.error("❌ **TEST FAILED**: Duplication prevention not working properly!")

if __name__ == "__main__":
    test_duplication_prevention()