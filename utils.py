import json
import re

def extract_json_from_llm_response(text):
    """Extract valid JSON from LLM output (handles markdown fences)."""
    # Try to find JSON between ```json ... ``` or just { ... }
    match = re.search(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL)
    if match:
        return match.group(1)
    match = re.search(r'(\{.*\})', text, re.DOTALL)
    if match:
        return match.group(1)
    return text

def validate_and_fix_data(data):
    """Ensure required keys exist with defaults."""
    defaults = {
        "title": "Operating System Notes",
        "gantt": {"processes": ["P1", "P2"], "arrival": [0, 1], "burst": [5, 3], "colors": ["#FF6B6B", "#4ECDC4"]},
        "paging": {"page_table": [[1, 0], [0, 1]]},
        "inode": {"direct": [10, 20], "single_indirect": 30, "double_indirect": 40},
        "bullet_points": ["Key concept extracted from notes."]
    }
    
    for key, default_val in defaults.items():
        if key not in data or not data[key]:
            data[key] = default_val
    return data
