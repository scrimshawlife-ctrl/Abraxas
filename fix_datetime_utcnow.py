#!/usr/bin/env python3
"""
Script to replace datetime.now(timezone.utc) with datetime.now(timezone.utc)
and ensure the necessary import is present.
"""

import os
import re
import sys

def process_file(filepath):
    """Process a single Python file."""
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Check if the file contains datetime.utcnow
    if 'datetime.now(timezone.utc)' not in content:
        return False
    
    # Replace datetime.now(timezone.utc) with datetime.now(timezone.utc)
    new_content = re.sub(r'datetime\.utcnow\(\)', 'datetime.now(timezone.utc)', content)
    
    # Check if we need to add the import
    if 'from datetime import timezone' not in new_content and 'import datetime' not in new_content:
        # We'll add the import at the top after other imports
        # Simple approach: add after the first import block or at the top
        lines = new_content.split('\n')
        # Find where to insert: after the last import that is not a comment or empty line
        insert_idx = 0
        for i, line in enumerate(lines):
            if line.strip().startswith('import ') or line.strip().startswith('from '):
                insert_idx = i + 1
            elif line.strip() and not line.strip().startswith('#'):
                # If we hit a non-import, non-comment line, stop looking
                break
        # Insert the import
        lines.insert(insert_idx, 'from datetime import timezone')
        new_content = '\n'.join(lines)
    elif 'from datetime import timezone' not in new_content:
        # If we have import datetime but not the specific import, we can change it or add
        # We'll just add the specific import; having both is fine
        lines = new_content.split('\n')
        insert_idx = 0
        for i, line in enumerate(lines):
            if line.strip().startswith('import ') or line.strip().startswith('from '):
                insert_idx = i + 1
            elif line.strip() and not line.strip().startswith('#'):
                break
        lines.insert(insert_idx, 'from datetime import timezone')
        new_content = '\n'.join(lines)
    
    # Write back if changed
    if new_content != content:
        with open(filepath, 'w') as f:
            f.write(new_content)
        return True
    return False

def main():
    """Main function to walk the directory and process .py files."""
    root_dir = '/Users/appliedalchemylabs/Abraxas'
    modified_files = []
    
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # Skip certain directories if needed (e.g., __pycache__, .git)
        dirnames[:] = [d for d in dirnames if not d.startswith('.') and d not in ['__pycache__', 'node_modules']]
        for filename in filenames:
            if filename.endswith('.py'):
                filepath = os.path.join(dirpath, filename)
                if process_file(filepath):
                    modified_files.append(filepath)
    
    print(f"Modified {len(modified_files)} files:")
    for f in modified_files:
        print(f"  {f}")
    
    return 0 if modified_files else 1

if __name__ == '__main__':
    sys.exit(main())