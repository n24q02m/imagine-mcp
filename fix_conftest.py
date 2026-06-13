import sys

with open('tests/conftest.py', 'r') as f:
    content = f.read()

start_marker = "<<<<<<< SEARCH"
end_marker = ">>>>>>> REPLACE"

if start_marker in content and end_marker in content:
    start_idx = content.find(start_marker)
    end_idx = content.find(end_marker) + len(end_marker)
    middle_marker = "======="
    middle_idx = content.find(middle_marker, start_idx, end_idx)

    if middle_idx != -1:
        replacement = content[middle_idx + len(middle_marker):content.find(end_marker, middle_idx)].strip()
        new_content = content[:start_idx] + replacement + content[end_idx:]
        with open('tests/conftest.py', 'w') as f:
            f.write(new_content)
        print("Successfully fixed tests/conftest.py")
