# Copy the working content from temp_report_function.py and replace the broken function
import streamlit as st
from datetime import datetime
import os

# Read the clean function from temp file
with open('temp_report_function.py', 'r') as f:
    clean_function_content = f.read()

# Read the broken app.py file
with open('app.py', 'r') as f:
    app_content = f.read()

# Find the start and end of the broken function
start_marker = "def generate_enhanced_html_report(include_charts, include_recommendations):"
end_marker = "def generate_window_elements_csv():"

# Find positions
start_pos = app_content.find(start_marker)
end_pos = app_content.find(end_marker)

if start_pos != -1 and end_pos != -1:
    # Replace the broken function with the clean one
    before_function = app_content[:start_pos]
    after_function = app_content[end_pos:]
    
    # Create the fixed content
    fixed_content = before_function + clean_function_content + "\n\n" + after_function
    
    # Write the fixed content
    with open('app.py', 'w') as f:
        f.write(fixed_content)
    
    print("Fixed the corrupted HTML report function")
else:
    print("Could not locate function boundaries")