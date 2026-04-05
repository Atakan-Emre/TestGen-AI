import json
from pathlib import Path

class JSONValidator:
    def __init__(self, template_path):
        self.template_path = template_path
        self.template = self._load_template()
        
    def _load_template(self):
        with open(self.template_path, 'r', encoding='utf-8') as f:
            return json.load(f)
            
    def validate_structure(self, test_case):
        template_keys = self._get_json_paths(self.template)
        test_keys = self._get_json_paths(test_case)
        
        return {
            "missing_keys": list(template_keys - test_keys),
            "extra_keys": list(test_keys - template_keys),
            "valid": len(template_keys - test_keys) == 0
        }
        
    def _get_json_paths(self, obj, parent_path="", paths=None):
        if paths is None:
            paths = set()
            
        if isinstance(obj, dict):
            for key, value in obj.items():
                current_path = f"{parent_path}.{key}" if parent_path else key
                paths.add(current_path)
                self._get_json_paths(value, current_path, paths)
                
        elif isinstance(obj, list) and obj:
            self._get_json_paths(obj[0], f"{parent_path}[0]", paths)
            
        return paths 