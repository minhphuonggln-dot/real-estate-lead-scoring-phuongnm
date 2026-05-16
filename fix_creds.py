import json
import os

file_path = "/Users/pihat/Documents/AI AGENT/Khoá học AG/Buổi 7/credentials.json"

# Read the file content as a string
with open(file_path, 'r', encoding='utf-8') as f:
    raw_content = f.read()

# The issue is that the private_key value has raw newlines.
# We want to keep the \n escapes but remove the actual line breaks.

lines = raw_content.splitlines()
fixed_lines = []
in_private_key = False

for line in lines:
    if '"private_key":' in line:
        fixed_lines.append(line.strip())
        in_private_key = True
    elif in_private_key:
        if '"client_email":' in line:
            # We hit the next key, so we're out of the private_key string
            # But we need to make sure the previous line didn't end with a comma that we want to keep
            in_private_key = False
            fixed_lines.append(line.strip())
        else:
            # This is part of the private_key string
            # Append it to the last line in fixed_lines
            fixed_lines[-1] += line.strip()
    else:
        fixed_lines.append(line.strip())

# Join and try to parse as JSON to verify
try:
    final_str = " ".join(fixed_lines)
    # This might still be tricky if spacing is wrong.
    # Let's try a different approach:
    # Find the start and end of the private_key value
    start_token = '"private_key": "'
    end_token = '",\n  "client_email"'
    
    # Actually, let's just do a clean rewrite if I can extract the parts.
    # But wait, I can just use a simple string replacement for now.
except:
    pass

# BETTER APPROACH:
# The private_key starts with "-----BEGIN PRIVATE KEY-----\n" 
# and ends with "-----END PRIVATE KEY-----\n"
# I will find the whole block and remove the literal newlines.

import re
# Match the whole private_key value block
pattern = r'("private_key":\s*")(.+?)(",)'
# Use re.DOTALL to match across newlines
match = re.search(pattern, raw_content, re.DOTALL)
if match:
    prefix = match.group(1)
    key_body = match.group(2)
    suffix = match.group(3)
    
    # Remove literal newlines and spaces from the body
    # but keep the \n characters.
    # Actually, the \n are literal backslash-n in the file.
    clean_body = key_body.replace('\n', '').replace('\r', '').replace(' ', '')
    
    # If the key was already escaped with \n, we should keep them.
    # The clean_body now has things like \nMIIEv...
    
    new_content = raw_content[:match.start()] + prefix + clean_body + suffix + raw_content[match.end():]
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("Fixed credentials.json")
else:
    print("Could not find private_key pattern")
