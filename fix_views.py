#!/usr/bin/env python3
import re

# Read the file
with open('e:/ProjectFlow/projectflow/dashboard/views.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace pattern
old_pattern = r'user_member = ProjectMember\.objects\.filter\(user=request\.user, project=project\)\.first\(\)'
new_pattern = r'user_member = get_user_project_access(request.user, project)'

# Replace all occurrences
content = re.sub(old_pattern, new_pattern, content)

# Write back to file
with open('e:/ProjectFlow/projectflow/dashboard/views.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Replaced all occurrences of ProjectMember.objects.filter with get_user_project_access")
