#!/usr/bin/env python3
"""
Final Validation Test
Simple test to verify the critical duplication prevention functionality
"""

import sys
import os
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.element_registry import get_global_registry, clear_global_registry

def test_validation():
    """Test the critical duplication prevention functionality"""
    
    print("🎯 BIPV Optimizer - Element Duplication Prevention Validation")
    print("=" * 80)
    
    # Clear registry for fresh start
    clear_global_registry()
    registry = get_global_registry()
    
    # Test critical element processing sequence
    print("\n1. Element Processing Sequence")
    print("-" * 50)
    
    # Simulate the actual workflow scenario
    elements = ["367277", "367278", "367279"]
    
    # Phase 1: Start processing
    started_elements = []
    for element_id in elements:
        success, message = registry.start_processing(element_id)
        if success:
            started_elements.append(element_id)
            print(f"✓ Started: {element_id}")
        else:
            print(f"✗ Failed to start: {element_id} - {message}")
    
    # Phase 2: Try to start again (should be blocked)
    blocked_duplicates = 0
    for element_id in elements:
        success, message = registry.start_processing(element_id)
        if not success:
            blocked_duplicates += 1
            print(f"✓ Blocked duplicate: {element_id}")
        else:
            print(f"✗ Duplicate NOT blocked: {element_id}")
    
    # Phase 3: Complete processing
    completed_elements = []
    for element_id in started_elements:
        success, message = registry.complete_processing(element_id)
        if success:
            completed_elements.append(element_id)
            print(f"✓ Completed: {element_id}")
        else:
            print(f"✗ Failed to complete: {element_id} - {message}")
    
    # Final validation
    print("\n2. Final Validation")
    print("-" * 50)
    
    print(f"✓ Elements started: {len(started_elements)}")
    print(f"✓ Duplicates blocked: {blocked_duplicates}")
    print(f"✓ Elements completed: {len(completed_elements)}")
    
    # Check registry status
    summary = registry.get_summary()
    print(f"✓ Registry summary: {summary}")
    
    # Success criteria
    all_started = len(started_elements) == 3
    all_blocked = blocked_duplicates == 3
    all_completed = len(completed_elements) == 3
    registry_clean = summary['processing'] == 0
    
    print("\n3. Test Results")
    print("-" * 50)
    
    if all_started and all_blocked and all_completed and registry_clean:
        print("🎉 SUCCESS: Element duplication prevention is working correctly!")
        print("\nKey Features Validated:")
        print("• Each element can only be processed once")
        print("• Duplicate attempts are properly blocked")
        print("• Element completion is tracked correctly")
        print("• Registry state is maintained properly")
        print("• No element duplication occurs")
        
        return True
    else:
        print("❌ FAILED: Some validation checks did not pass")
        print(f"  - Started correctly: {all_started}")
        print(f"  - Blocked duplicates: {all_blocked}")
        print(f"  - Completed correctly: {all_completed}")
        print(f"  - Registry clean: {registry_clean}")
        
        return False

if __name__ == "__main__":
    success = test_validation()
    exit(0 if success else 1)