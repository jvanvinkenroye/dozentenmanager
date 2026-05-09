
import os
import re

TEST_FILES = [
    "tests/integration/test_backup_routes.py",
    "tests/integration/test_course_routes.py",
    "tests/integration/test_document_routes.py",
    "tests/integration/test_enrollment_routes.py",
    "tests/integration/test_exam_routes.py",
    "tests/integration/test_grade_routes.py",
    "tests/integration/test_student_routes.py",
]

def update_test_file(filepath):
    with open(file_path, 'r') as f:
        content = f.read()

    # Replace client with auth_client in test methods
    content = re.sub(r'def test_(\w+)\(([^)]*)\bclient\b', r'def test_\1(\2auth_client', content)
    
    # Replace client. calls with auth_client.
    content = content.replace('client.get', 'auth_client.get')
    content = content.replace('client.post', 'auth_client.post')
    
    # Remove 'with app.app_context():' and unindent
    lines = content.split('\n')
    new_lines = []
    skip = False
    indent_level = 0
    
    for i, line in enumerate(lines):
        if 'with app.app_context():' in line:
            indent_level = len(line) - len(line.lstrip())
            continue
            
        if line.strip() == "":
            new_lines.append(line)
            continue
            
        current_indent = len(line) - len(line.lstrip())
        
        # Determine if this line was inside the removed context block
        # It was inside if indentation > indent_level of the 'with' statement
        # But we only unindent if we actually removed a 'with' block recently
        # This is a simple heuristic: simply unindent by 4 spaces if line starts with enough spaces
        # and we assume the file was formatted with 4 spaces.
        
        # Better approach: Just replace the 'with app.app_context():' line with nothing
        # and let a formatter fix indentation? No, that's messy.
        
        # Let's try to remove the line and unindent the following block
        pass

    # Since simple regex/replace is tricky with indentation, I'll use a simpler approach:
    # 1. Replace client -> auth_client
    # 2. Remove `with app.app_context():` lines
    # 3. Use `ruff format` to fix indentation (Ruff can't fix logic indentation, but let's see).
    
    # Actually, I will just rewrite the files without `with app.app_context():` 
    # by processing line by line and reducing indentation if inside such block.
    
    final_lines = []
    inside_context = False
    context_indent = 0
    
    for line in lines:
        stripped = line.lstrip()
        current_indent = len(line) - len(stripped)
        
        if 'with app.app_context():' in line:
            inside_context = True
            context_indent = current_indent
            continue
            
        if inside_context:
            if not stripped: # Empty line
                final_lines.append(line)
                continue
                
            if current_indent <= context_indent:
                # End of block
                inside_context = False
                final_lines.append(line)
            else:
                # Inside block, unindent by 4 spaces
                # Check if it matches expected indentation (context_indent + 4)
                if current_indent >= context_indent + 4:
                    final_lines.append(line[4:])
                else:
                    # Should not happen in well-formatted code
                    final_lines.append(line)
        else:
            final_lines.append(line)
            
    with open(file_path, 'w') as f:
        f.write('\n'.join(final_lines))

for file_path in TEST_FILES:
    if os.path.exists(file_path):
        print(f"Processing {file_path}...")
        update_test_file(file_path)
    else:
        print(f"File not found: {file_path}")
