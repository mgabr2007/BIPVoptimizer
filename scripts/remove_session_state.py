#!/usr/bin/env python3
"""
Script to systematically remove all session state usage from BIPV Optimizer
and replace with database-driven architecture
"""

import os
import re
import glob

def find_session_state_files():
    """Find all Python files containing session_state usage"""
    files_with_session_state = []
    
    # Search in all Python directories
    search_dirs = ['pages_modules', 'utils', 'components', 'services', '.']
    
    for directory in search_dirs:
        if os.path.exists(directory):
            for root, dirs, files in os.walk(directory):
                for file in files:
                    if file.endswith('.py') and file != 'remove_session_state.py':
                        filepath = os.path.join(root, file)
                        try:
                            with open(filepath, 'r', encoding='utf-8') as f:
                                content = f.read()
                                if 'st.session_state' in content:
                                    # Count occurrences
                                    count = content.count('st.session_state')
                                    files_with_session_state.append((filepath, count))
                        except Exception as e:
                            print(f"Error reading {filepath}: {e}")
    
    return sorted(files_with_session_state, key=lambda x: x[1], reverse=True)

def get_replacement_patterns():
    """Define replacement patterns for common session state usage"""
    return [
        # Current step management
        (r'st\.session_state\.current_step', 'db_state_manager.get_current_step()'),
        (r'st\.session_state\.current_step\s*=\s*[\'"]([^\'"]+)[\'"]', 
         r'db_state_manager.set_current_step("\1")'),
        
        # Project data access
        (r'st\.session_state\.get\([\'"]project_data[\'"], \{\}\)', 
         'db_state_manager.get_step_data("project_setup") or {}'),
        (r'st\.session_state\.project_data\.get\([\'"]([^\'"]+)[\'"]', 
         r'(db_state_manager.get_step_data("project_setup") or {}).get("\1"'),
        
        # Step completion flags
        (r'st\.session_state\.get\([\'"]([^_]+)_completed[\'"], False\)', 
         r'db_state_manager.is_step_completed("\1")'),
        (r'st\.session_state\.([^_]+)_completed\s*=\s*True', 
         r'db_state_manager.save_step_completion("\1")'),
        
        # Scroll to top
        (r'st\.session_state\.scroll_to_top\s*=\s*True', '# Database-driven navigation'),
        (r'st\.session_state\.get\([\'"]scroll_to_top[\'"], False\)', 'False'),
        
        # Data storage patterns
        (r'st\.session_state\[([\'"][^\'"]+[\'"])\]\s*=', 
         r'# Database storage: db_state_manager.save_step_data(\1, '),
    ]

def apply_replacements(filepath, content):
    """Apply replacement patterns to file content"""
    patterns = get_replacement_patterns()
    modified_content = content
    changes_made = 0
    
    for pattern, replacement in patterns:
        new_content = re.sub(pattern, replacement, modified_content)
        if new_content != modified_content:
            changes_made += modified_content.count(pattern.replace(r'\.', '.'))
            modified_content = new_content
    
    return modified_content, changes_made

def add_database_imports(content):
    """Add necessary database imports if not present"""
    imports_to_add = [
        'from services.database_state_manager import db_state_manager',
        'from services.io import get_current_project_id'
    ]
    
    modified_content = content
    
    # Check if imports already exist
    for import_line in imports_to_add:
        if import_line not in content:
            # Find a good place to add the import
            if 'import streamlit as st' in content:
                modified_content = modified_content.replace(
                    'import streamlit as st',
                    f'import streamlit as st\n{import_line}'
                )
            elif 'from ' in content[:500]:  # Add after other imports
                lines = modified_content.split('\n')
                insert_index = 0
                for i, line in enumerate(lines):
                    if line.strip().startswith(('import ', 'from ')):
                        insert_index = i + 1
                lines.insert(insert_index, import_line)
                modified_content = '\n'.join(lines)
    
    return modified_content

def process_file(filepath):
    """Process a single file to remove session state usage"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            original_content = f.read()
        
        # Apply replacements
        modified_content, changes_made = apply_replacements(filepath, original_content)
        
        # Add database imports if changes were made
        if changes_made > 0:
            modified_content = add_database_imports(modified_content)
        
        # Write back if changes were made
        if modified_content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(modified_content)
            print(f"✅ {filepath}: {changes_made} session state references updated")
            return changes_made
        else:
            print(f"⏭️  {filepath}: No changes needed")
            return 0
            
    except Exception as e:
        print(f"❌ Error processing {filepath}: {e}")
        return 0

def main():
    """Main execution function"""
    print("🔄 Starting session state removal process...")
    
    # Find all files with session state usage
    files_with_session_state = find_session_state_files()
    
    if not files_with_session_state:
        print("✅ No session state usage found!")
        return
    
    print(f"\n📋 Found session state usage in {len(files_with_session_state)} files:")
    for filepath, count in files_with_session_state:
        print(f"  - {filepath}: {count} occurrences")
    
    print("\n🔧 Processing files...")
    total_changes = 0
    
    for filepath, count in files_with_session_state:
        changes = process_file(filepath)
        total_changes += changes
    
    print(f"\n✅ Session state removal complete!")
    print(f"📊 Total changes made: {total_changes}")
    print(f"📁 Files processed: {len(files_with_session_state)}")
    
    # Generate summary report
    remaining_files = find_session_state_files()
    if remaining_files:
        print(f"\n⚠️  {len(remaining_files)} files still contain session state usage:")
        for filepath, count in remaining_files[:5]:  # Show top 5
            print(f"  - {filepath}: {count} occurrences")
        if len(remaining_files) > 5:
            print(f"  ... and {len(remaining_files) - 5} more files")
    else:
        print("\n🎉 All session state usage successfully removed!")

if __name__ == "__main__":
    main()