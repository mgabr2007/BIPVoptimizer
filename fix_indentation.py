#!/usr/bin/env python3

import re

def fix_radiation_grid_indentation():
    """Fix indentation issues in radiation_grid.py caused by try-catch block"""
    
    with open('pages_modules/radiation_grid.py', 'r') as f:
        content = f.read()
    
    # Find the function definition
    function_start = content.find('def render_radiation_grid():')
    if function_start == -1:
        print("Function not found")
        return
    
    # Find the try block
    try_block = content.find('try:', function_start)
    if try_block == -1:
        print("Try block not found")
        return
    
    # Find lines after the try block that need to be indented
    lines = content.split('\n')
    
    # Get the function line number
    func_line = content[:function_start].count('\n')
    try_line = content[:try_block].count('\n')
    
    print(f"Function at line {func_line + 1}, try block at line {try_line + 1}")
    
    # Find the end of the function
    in_function = False
    new_lines = []
    
    for i, line in enumerate(lines):
        if i == func_line:
            in_function = True
            new_lines.append(line)
        elif in_function:
            # Check if we're still in the function
            if line and not line.startswith('    ') and not line.startswith('\t') and line.strip():
                # This might be the end of the function
                if line.startswith('def ') or line.startswith('class ') or not line.strip():
                    in_function = False
                    new_lines.append(line)
                else:
                    # This line needs proper indentation
                    if i > try_line:
                        # Add proper indentation for content inside try block
                        new_lines.append('        ' + line.lstrip())
                    else:
                        new_lines.append('    ' + line.lstrip())
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)
    
    # Write back the fixed content
    with open('pages_modules/radiation_grid.py', 'w') as f:
        f.write('\n'.join(new_lines))
    
    print("Fixed indentation issues")

if __name__ == "__main__":
    fix_radiation_grid_indentation()