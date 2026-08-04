import json
import re
from pathlib import Path

# Test loading the JSON
patterns_path = Path("C:/Users/pc/.laosi/skills/contract-review-skill/legal_patterns/required_clauses.json")
print(f"Loading from: {patterns_path}")
print(f"File exists: {patterns_path.exists()}")

try:
    with open(patterns_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print("JSON loaded successfully")
    print(f"Keys: {list(data.keys())}")
    
    # Test one pattern
    if "confidentiality" in data:
        pattern = data["confidentiality"]["pattern"]
        print(f"Confidentiality pattern: {pattern}")
        # Test if it's a valid regex
        try:
            compiled = re.compile(pattern, re.IGNORECASE)
            print("Pattern compiled successfully")
        except Exception as e:
            print(f"Pattern compilation failed: {e}")
            
except Exception as e:
    print(f"Error loading JSON: {e}")
    import traceback
    traceback.print_exc()