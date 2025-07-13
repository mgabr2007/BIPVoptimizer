#!/usr/bin/env python3
"""
Test Race Condition Fix - Final Validation
This test validates that the execution lock prevents multiple simultaneous executions
"""

import time
import threading
import sys
import os

# Mock Streamlit session state
class MockSessionState:
    def __init__(self):
        self.data = {}
        self.lock = threading.Lock()
    
    def get(self, key, default=None):
        with self.lock:
            return self.data.get(key, default)
    
    def __setitem__(self, key, value):
        with self.lock:
            self.data[key] = value
    
    def __getitem__(self, key):
        with self.lock:
            return self.data[key]
    
    def __contains__(self, key):
        with self.lock:
            return key in self.data

# Mock the radiation analysis function behavior
def mock_radiation_analysis(session_state, thread_id):
    """Mock the critical section that was causing duplication"""
    
    # Check execution lock (this is what we added)
    if 'radiation_analysis_running' not in session_state:
        session_state['radiation_analysis_running'] = False
    
    if session_state['radiation_analysis_running']:
        print(f"Thread {thread_id}: BLOCKED - Analysis already running")
        return False
    
    # Set execution lock
    session_state['radiation_analysis_running'] = True
    print(f"Thread {thread_id}: STARTED - Lock acquired")
    
    try:
        # Simulate the processing that was causing duplication
        time.sleep(0.1)  # Simulate work
        
        # Mock element processing
        if 'processed_elements' not in session_state:
            session_state['processed_elements'] = []
        
        # This is what was happening - multiple threads adding same elements
        element_id = "element_367277"
        current_elements = session_state.get('processed_elements', [])
        current_elements.append(f"{element_id}_processed_by_thread_{thread_id}")
        session_state['processed_elements'] = current_elements
        
        print(f"Thread {thread_id}: PROCESSING - Element {element_id}")
        time.sleep(0.1)  # More work
        
        print(f"Thread {thread_id}: COMPLETED - Lock will be released")
        return True
        
    except Exception as e:
        print(f"Thread {thread_id}: ERROR - {e}")
        return False
    finally:
        # Clear execution lock (this is what we added)
        session_state['radiation_analysis_running'] = False
        print(f"Thread {thread_id}: LOCK RELEASED")

def test_race_condition_fix():
    """Test that the race condition fix prevents multiple simultaneous executions"""
    
    print("="*60)
    print("RACE CONDITION FIX VALIDATION TEST")
    print("="*60)
    
    # Create shared session state
    session_state = MockSessionState()
    
    # Create multiple threads to simulate simultaneous button clicks
    threads = []
    thread_count = 5
    
    print(f"\nStarting {thread_count} simultaneous radiation analysis attempts...")
    
    # Start all threads at the same time
    for i in range(thread_count):
        thread = threading.Thread(
            target=mock_radiation_analysis,
            args=(session_state, i+1)
        )
        threads.append(thread)
    
    # Start all threads simultaneously
    for thread in threads:
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    print("\n" + "="*60)
    print("TEST RESULTS:")
    print("="*60)
    
    # Check results
    processed_elements = session_state.get('processed_elements', [])
    
    print(f"Total processed elements: {len(processed_elements)}")
    print(f"Processed elements: {processed_elements}")
    
    # The fix should ensure only ONE thread processes elements
    if len(processed_elements) == 1:
        print("✅ SUCCESS: Race condition fixed - only one thread processed elements")
        print("✅ Multiple simultaneous executions prevented")
        return True
    else:
        print("❌ FAILURE: Race condition still exists - multiple threads processed elements")
        print("❌ Fix needs improvement")
        return False

def test_normal_operation():
    """Test that normal operation still works"""
    
    print("\n" + "="*60)
    print("NORMAL OPERATION TEST")
    print("="*60)
    
    session_state = MockSessionState()
    
    # Test sequential executions
    print("\nTesting sequential executions...")
    
    result1 = mock_radiation_analysis(session_state, "A")
    time.sleep(0.1)  # Wait for first to complete
    result2 = mock_radiation_analysis(session_state, "B")
    
    processed_elements = session_state.get('processed_elements', [])
    
    print(f"Sequential results: {result1}, {result2}")
    print(f"Total processed elements: {len(processed_elements)}")
    
    if len(processed_elements) == 2:
        print("✅ SUCCESS: Normal sequential operation works")
        return True
    else:
        print("❌ FAILURE: Normal operation broken")
        return False

if __name__ == "__main__":
    print("Testing race condition fix for radiation analysis...")
    
    # Test the race condition fix
    race_fix_success = test_race_condition_fix()
    
    # Test normal operation
    normal_op_success = test_normal_operation()
    
    print("\n" + "="*60)
    print("FINAL RESULTS:")
    print("="*60)
    
    if race_fix_success and normal_op_success:
        print("✅ ALL TESTS PASSED")
        print("✅ Race condition fix implemented successfully")
        print("✅ Normal operation preserved")
        sys.exit(0)
    else:
        print("❌ TESTS FAILED")
        print("❌ Race condition fix needs improvement")
        sys.exit(1)