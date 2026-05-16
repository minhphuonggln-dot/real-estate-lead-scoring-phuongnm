import json
from google.oauth2.service_account import Credentials

try:
    with open("credentials.json", "r") as f:
        info = json.load(f)
    
    # Try the raw info first
    try:
        creds = Credentials.from_service_account_info(info)
        print("Raw info load: SUCCESS")
    except Exception as e:
        print(f"Raw info load: FAILED - {e}")

    # Try with replacement
    info["private_key"] = info["private_key"].replace("\\n", "\n")
    try:
        creds = Credentials.from_service_account_info(info)
        print("Fixed info load: SUCCESS")
    except Exception as e:
        print(f"Fixed info load: FAILED - {e}")
        
except Exception as e:
    print(f"File read error: {e}")
