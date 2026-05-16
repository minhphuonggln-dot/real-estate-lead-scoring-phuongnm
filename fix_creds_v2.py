import json
import os

file_path = "/Users/pihat/Documents/AI AGENT/Khoá học AG/Buổi 7/credentials.json"

# Read the current content
with open(file_path, 'r', encoding='utf-8') as f:
    raw_content = f.read()

# Fix headers that I accidentally broke (removed spaces)
fixed_content = raw_content.replace("-----BEGINPRIVATEKEY-----", "-----BEGIN PRIVATE KEY-----")
fixed_content = fixed_content.replace("-----ENDPRIVATEKEY-----", "-----END PRIVATE KEY-----")

# Now ensure the \n are preserved and there are NO raw newlines in the string
# The cat output showed it was already mostly fixed but let's be 100% sure with JSON library

try:
    # Try to parse it. If it's valid JSON now, we're good.
    # But it might fail if there are hidden characters.
    # Let's clean it properly.
    
    import re
    # Find the private_key value
    pattern = r'("private_key":\s*")(.+?)(",)'
    match = re.search(pattern, fixed_content, re.DOTALL)
    if match:
        prefix = match.group(1)
        body = match.group(2)
        suffix = match.group(3)
        
        # Remove literal newlines but keep the string escape sequences like \n
        # Actually, \n in a JSON file is a backslash and an n.
        # Literal newlines are actual line breaks.
        clean_body = body.replace('\n', '').replace('\r', '')
        
        final_content = fixed_content[:match.start()] + prefix + clean_body + suffix + fixed_content[match.end():]
        
        # Now parse it with json.loads to ensure it's valid
        data = json.loads(final_content)
        # Write it back formatted correctly
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        print("Successfully fixed and validated credentials.json")
    else:
        print("Could not find pattern")
except Exception as e:
    print(f"Error: {e}")
