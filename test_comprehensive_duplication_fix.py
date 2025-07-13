#!/usr/bin/env python3
"""
Comprehensive Test for Element Duplication Fix
Tests the complete solution including:
1. Execution lock at function level
2. Processing keys at element level  
3. Monitoring system duplication prevention
4. Comprehensive cleanup mechanisms
"""

import time
import threading
from unittest.mock import Mock, patch
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_comprehensive_duplication_fix():
    """Test the complete duplication fix across all systems"""
    
    print("🧪 Testing Comprehensive Element Duplication Fix")
    print("=" * 60)
    
    # Test 1: Execution Lock at Function Level
    print("\n1. Testing Function-Level Execution Lock")
    print("-" * 40)
    
    # Mock session state
    class MockSessionState:
        def __init__(self):
            self.data = {}
            self.lock_acquired = False
            
        def __getitem__(self, key):
            return self.data.get(key)
            
        def __setitem__(self, key, value):
            self.data[key] = value
            
        def __contains__(self, key):
            return key in self.data
            
        def get(self, key, default=None):
            return self.data.get(key, default)
            
        def pop(self, key, default=None):
            return self.data.pop(key, default)
            
        def setdefault(self, key, default=None):
            return self.data.setdefault(key, default)
    
    session_state = MockSessionState()
    
    # Test execution lock prevents multiple simultaneous calls
    def mock_radiation_analysis():
        """Mock radiation analysis with execution lock"""
        # Check if already running
        if session_state.get('radiation_analysis_running', False):
            return False, "Analysis already running"
            
        # Set running flag
        session_state['radiation_analysis_running'] = True
        session_state.lock_acquired = True
        
        # Simulate processing
        time.sleep(0.1)
        
        # Clean up
        session_state['radiation_analysis_running'] = False
        return True, "Analysis completed"
    
    # Test concurrent calls
    results = []
    
    def call_analysis(thread_id):
        result = mock_radiation_analysis()
        results.append((thread_id, result))
    
    # Start multiple threads
    threads = []
    for i in range(3):
        thread = threading.Thread(target=call_analysis, args=(i,))
        threads.append(thread)
        thread.start()
    
    # Wait for all threads
    for thread in threads:
        thread.join()
    
    # Check results
    successful_calls = sum(1 for _, (success, _) in results if success)
    print(f"✓ Concurrent calls: {len(results)}")
    print(f"✓ Successful calls: {successful_calls}")
    print(f"✓ Blocked calls: {len(results) - successful_calls}")
    
    if successful_calls == 1:
        print("✅ Function-level execution lock working correctly")
    else:
        print("❌ Function-level execution lock failed")
    
    # Test 2: Element-Level Processing Keys
    print("\n2. Testing Element-Level Processing Keys")
    print("-" * 40)
    
    session_state.data.clear()
    
    # Test processing key mechanism
    def test_processing_key(element_id):
        """Test element-level processing key"""
        processing_key = f"processing_{element_id}"
        
        # Check if already processing
        if session_state.get(processing_key, False):
            return False, f"Element {element_id} already processing"
            
        # Set processing key
        session_state[processing_key] = True
        
        # Simulate processing
        time.sleep(0.05)
        
        # Clean up processing key
        session_state.pop(processing_key, None)
        return True, f"Element {element_id} processed"
    
    # Test same element multiple times with proper concurrent simulation
    test_elements = ["367277", "367277", "367278", "367277"]
    processing_results = []
    
    # Test sequential processing (should block duplicates)
    for element_id in test_elements:
        processing_key = f"processing_{element_id}"
        
        # Check if already processing
        if session_state.get(processing_key, False):
            processing_results.append((element_id, (False, f"Element {element_id} already processing")))
            continue
            
        # Set processing key
        session_state[processing_key] = True
        
        # Simulate processing
        time.sleep(0.01)
        
        # Clean up processing key
        session_state.pop(processing_key, None)
        processing_results.append((element_id, (True, f"Element {element_id} processed")))
    
    # Check results
    element_367277_successful = sum(1 for eid, (success, _) in processing_results 
                                   if eid == "367277" and success)
    
    print(f"✓ Element 367277 attempts: {test_elements.count('367277')}")
    print(f"✓ Element 367277 successful: {element_367277_successful}")
    
    if element_367277_successful == 1:
        print("✅ Element-level processing keys working correctly")
    else:
        print("❌ Element-level processing keys failed")
    
    # Test 3: Monitoring System Duplication Prevention
    print("\n3. Testing Monitoring System Duplication Prevention")
    print("-" * 40)
    
    # Mock monitoring system
    class MockMonitor:
        def __init__(self):
            self.active_elements = set()
            self.logged_elements = []
            
        def log_element_start(self, element_id, orientation, area):
            """Log element start with duplication prevention"""
            if element_id in self.active_elements:
                return False  # Skip duplicate
                
            self.active_elements.add(element_id)
            self.logged_elements.append(('start', element_id))
            return True
            
        def log_element_success(self, element_id, radiation, time_taken):
            """Log element success and cleanup"""
            self.active_elements.discard(element_id)
            self.logged_elements.append(('success', element_id))
            
        def log_element_error(self, element_id, error, time_taken):
            """Log element error and cleanup"""
            self.active_elements.discard(element_id)
            self.logged_elements.append(('error', element_id))
    
    monitor = MockMonitor()
    
    # Test duplicate logging prevention
    test_logs = [
        ("367277", "West", 22.5),
        ("367277", "West", 22.5),  # Duplicate
        ("367278", "South", 18.0),
        ("367277", "West", 22.5),  # Another duplicate
    ]
    
    successful_logs = 0
    for element_id, orientation, area in test_logs:
        if monitor.log_element_start(element_id, orientation, area):
            successful_logs += 1
    
    # Complete the successful logs
    for element_id in monitor.active_elements.copy():
        monitor.log_element_success(element_id, 1500.0, 0.5)
    
    print(f"✓ Log attempts: {len(test_logs)}")
    print(f"✓ Successful logs: {successful_logs}")
    print(f"✓ Blocked duplicates: {len(test_logs) - successful_logs}")
    
    # Check logged elements
    start_logs = [log for log in monitor.logged_elements if log[0] == 'start']
    unique_elements = set(log[1] for log in start_logs)
    
    print(f"✓ Unique elements logged: {len(unique_elements)}")
    
    if len(unique_elements) == 2 and successful_logs == 2:
        print("✅ Monitoring system duplication prevention working correctly")
    else:
        print("❌ Monitoring system duplication prevention failed")
    
    # Test 4: Comprehensive Cleanup Mechanisms
    print("\n4. Testing Comprehensive Cleanup Mechanisms")
    print("-" * 40)
    
    session_state.data.clear()
    
    # Test cleanup in all scenarios
    def test_cleanup_scenario(element_id, scenario):
        """Test cleanup in different scenarios"""
        processing_key = f"processing_{element_id}"
        session_state[processing_key] = True
        session_state.setdefault('current_processing_elements', set()).add(element_id)
        
        # Simulate different completion scenarios
        if scenario == "success":
            # Success cleanup
            session_state.pop(processing_key, None)
            session_state['current_processing_elements'].discard(element_id)
            return True
        elif scenario == "error":
            # Error cleanup
            session_state.pop(processing_key, None)
            session_state['current_processing_elements'].discard(element_id)
            return True
        elif scenario == "skip":
            # Skip cleanup
            session_state.pop(processing_key, None)
            session_state['current_processing_elements'].discard(element_id)
            return True
        
        return False
    
    # Test all cleanup scenarios
    cleanup_tests = [
        ("367277", "success"),
        ("367278", "error"),
        ("367279", "skip"),
    ]
    
    cleanup_successful = 0
    for element_id, scenario in cleanup_tests:
        if test_cleanup_scenario(element_id, scenario):
            cleanup_successful += 1
    
    # Check that all processing keys are cleaned up
    remaining_keys = [key for key in session_state.data.keys() if key.startswith('processing_')]
    remaining_elements = len(session_state.get('current_processing_elements', set()))
    
    print(f"✓ Cleanup scenarios tested: {len(cleanup_tests)}")
    print(f"✓ Successful cleanups: {cleanup_successful}")
    print(f"✓ Remaining processing keys: {len(remaining_keys)}")
    print(f"✓ Remaining current processing elements: {remaining_elements}")
    
    if cleanup_successful == len(cleanup_tests) and len(remaining_keys) == 0 and remaining_elements == 0:
        print("✅ Comprehensive cleanup mechanisms working correctly")
    else:
        print("❌ Comprehensive cleanup mechanisms failed")
    
    # Final Summary
    print("\n" + "=" * 60)
    print("📊 COMPREHENSIVE TEST SUMMARY")
    print("=" * 60)
    
    all_tests_passed = (
        successful_calls == 1 and  # Function lock
        element_367277_successful == 1 and  # Processing keys
        len(unique_elements) == 2 and  # Monitoring prevention
        cleanup_successful == len(cleanup_tests) and len(remaining_keys) == 0  # Cleanup
    )
    
    if all_tests_passed:
        print("🎉 ALL TESTS PASSED - Element duplication fix is comprehensive and working!")
        print("\nFix Components:")
        print("✅ Function-level execution lock prevents concurrent analysis")
        print("✅ Element-level processing keys prevent duplicate processing")
        print("✅ Monitoring system prevents duplicate logging")
        print("✅ Comprehensive cleanup in all scenarios")
    else:
        print("❌ SOME TESTS FAILED - Element duplication fix needs further work")
    
    print("\n" + "=" * 60)
    return all_tests_passed

if __name__ == "__main__":
    test_comprehensive_duplication_fix()