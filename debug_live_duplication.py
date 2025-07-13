#!/usr/bin/env python3
"""
Debug Live Duplication Issue
Analyze the actual duplication pattern from the log
"""

import re
from collections import defaultdict
from datetime import datetime

def parse_log_file(log_content):
    """Parse the log file to understand the duplication pattern"""
    
    print("=" * 60)
    print("DUPLICATION ANALYSIS FROM LIVE LOG")
    print("=" * 60)
    
    # Parse log entries
    processing_pattern = r'\[(\d{2}:\d{2}:\d{2})\] 🔄 Processing (\d+) \(([^)]+)\)'
    completion_pattern = r'\[(\d{2}:\d{2}:\d{2})\] ✅ (\d+) completed \(([^)]+)\)'
    
    processing_events = []
    completion_events = []
    
    for line in log_content.split('\n'):
        line = line.strip()
        if not line:
            continue
            
        # Check for processing events
        proc_match = re.match(processing_pattern, line)
        if proc_match:
            time_str, element_id, details = proc_match.groups()
            processing_events.append({
                'time': time_str,
                'element_id': element_id,
                'details': details,
                'line': line
            })
        
        # Check for completion events
        comp_match = re.match(completion_pattern, line)
        if comp_match:
            time_str, element_id, details = comp_match.groups()
            completion_events.append({
                'time': time_str,
                'element_id': element_id,
                'details': details,
                'line': line
            })
    
    print(f"Total processing events: {len(processing_events)}")
    print(f"Total completion events: {len(completion_events)}")
    
    # Analyze duplication patterns
    processing_counts = defaultdict(int)
    completion_counts = defaultdict(int)
    
    print("\n1. PROCESSING EVENT ANALYSIS:")
    for event in processing_events:
        processing_counts[event['element_id']] += 1
        
    for element_id, count in processing_counts.items():
        if count > 1:
            print(f"   Element {element_id}: {count} processing events")
    
    print("\n2. COMPLETION EVENT ANALYSIS:")
    for event in completion_events:
        completion_counts[event['element_id']] += 1
        
    for element_id, count in completion_counts.items():
        if count > 1:
            print(f"   Element {element_id}: {count} completion events")
    
    # Time analysis
    print("\n3. TIME PATTERN ANALYSIS:")
    element_times = defaultdict(list)
    
    for event in processing_events:
        element_times[event['element_id']].append(event['time'])
    
    for element_id, times in element_times.items():
        if len(times) > 1:
            print(f"   Element {element_id} processing times: {times}")
            # Check if they're all the same time (simultaneous) or different times (sequential)
            unique_times = set(times)
            if len(unique_times) == 1:
                print(f"     → SIMULTANEOUS: All at {times[0]} (race condition)")
            else:
                print(f"     → SEQUENTIAL: Different times (loop issue)")
    
    # Sequence analysis
    print("\n4. SEQUENCE ANALYSIS:")
    print("   First 10 events:")
    for i, event in enumerate(processing_events[:10]):
        print(f"     {i+1}. {event['time']} - {event['element_id']}")
    
    # Pattern detection
    print("\n5. PATTERN DETECTION:")
    
    # Check for identical simultaneous events
    time_groups = defaultdict(list)
    for event in processing_events:
        time_groups[event['time']].append(event['element_id'])
    
    for time_stamp, elements in time_groups.items():
        if len(elements) > 1:
            print(f"   {time_stamp}: {len(elements)} simultaneous events - {elements}")
    
    # Check for repeating sequences
    element_sequence = [event['element_id'] for event in processing_events]
    
    # Look for patterns like [A, A, B, A, B, C, A, B, C, D]
    pattern_length = 3
    for i in range(len(element_sequence) - pattern_length):
        subseq = element_sequence[i:i+pattern_length]
        if element_sequence[i:i+pattern_length*2] == subseq + subseq:
            print(f"   Repeating pattern found: {subseq}")
            break
    
    return processing_counts, completion_counts

# Test with the provided log
log_content = '''Live Processing Log:

[17:41:31] 🔄 Processing 367277 (West (225-315°), 23.4m²)
[17:41:31] 🔄 Processing 367277 (West (225-315°), 23.4m²)
[17:41:34] ✅ 367277 completed (755 kWh/m²/year, 2.79s)
[17:41:31] 🔄 Processing 367277 (West (225-315°), 23.4m²)
[17:41:34] ✅ 367277 completed (755 kWh/m²/year, 2.79s)
[17:41:34] 🔄 Processing 367278 (West (225-315°), 23.4m²)
[17:41:31] 🔄 Processing 367277 (West (225-315°), 23.4m²)
[17:41:34] ✅ 367277 completed (755 kWh/m²/year, 2.79s)
[17:41:34] 🔄 Processing 367278 (West (225-315°), 23.4m²)
[17:41:37] ✅ 367278 completed (755 kWh/m²/year, 2.83s)
[17:41:31] 🔄 Processing 367277 (West (225-315°), 23.4m²)
[17:41:34] ✅ 367277 completed (755 kWh/m²/year, 2.79s)
[17:41:34] 🔄 Processing 367278 (West (225-315°), 23.4m²)
[17:41:37] ✅ 367278 completed (755 kWh/m²/year, 2.83s)
[17:41:37] 🔄 Processing 367279 (West (225-315°), 23.4m²)
[17:41:34] ✅ 367277 completed (755 kWh/m²/year, 2.79s)
[17:41:34] 🔄 Processing 367278 (West (225-315°), 23.4m²)
[17:41:37] ✅ 367278 completed (755 kWh/m²/year, 2.83s)
[17:41:37] 🔄 Processing 367279 (West (225-315°), 23.4m²)
[17:41:40] ✅ 367279 completed (755 kWh/m²/year, 2.92s)
[17:41:34] 🔄 Processing 367278 (West (225-315°), 23.4m²)
[17:41:37] ✅ 367278 completed (755 kWh/m²/year, 2.83s)
[17:41:37] 🔄 Processing 367279 (West (225-315°), 23.4m²)
[17:41:40] ✅ 367279 completed (755 kWh/m²/year, 2.92s)
[17:41:40] 🔄 Processing 367280 (West (225-315°), 23.4m²)
[17:41:37] ✅ 367278 completed (755 kWh/m²/year, 2.83s)
[17:41:37] 🔄 Processing 367279 (West (225-315°), 23.4m²)
[17:41:40] ✅ 367279 completed (755 kWh/m²/year, 2.92s)
[17:41:40] 🔄 Processing 367280 (West (225-315°), 23.4m²)
[17:41:43] ✅ 367280 completed (755 kWh/m²/year, 2.86s)
[17:41:37] 🔄 Processing 367279 (West (225-315°), 23.4m²)
[17:41:40] ✅ 367279 completed (755 kWh/m²/year, 2.92s)
[17:41:40] 🔄 Processing 367280 (West (225-315°), 23.4m²)
[17:41:43] ✅ 367280 completed (755 kWh/m²/year, 2.86s)
[17:41:43] 🔄 Processing 367274 (West (225-315°), 23.4m²)
[17:41:40] ✅ 367279 completed (755 kWh/m²/year, 2.92s)
[17:41:40] 🔄 Processing 367280 (West (225-315°), 23.4m²)
[17:41:43] ✅ 367280 completed (755 kWh/m²/year, 2.86s)'''

if __name__ == "__main__":
    parse_log_file(log_content)