import re
from pathlib import Path
from typing import Any, Dict, List, Optional

class SecurityValidator:
    def __init__(self):
        self.threat_patterns = [
            r"(union\s+select|insert\s+into|delete\s+from|drop\s+table)",
            r"<script>.*?</script>",
            r"(\/\*.*?\*\/|--\s)",
            r"(\.\.\/|~\/|\\\.\\\.)"
        ]
        self.compiled_patterns = [re.compile(p, re.IGNORECASE) for p in self.threat_patterns]

    def validate_input(self, input_data: Any, field_name: str = None) -> List[str]:
        """Validate input data for potential security threats"""
        errors = []
        if input_data is None:
            return errors
        if isinstance(input_data, dict):
            for key, value in input_data.items():
                errors.extend(self.validate_input(value, key))
        elif isinstance(input_data, list):
            for item in input_data:
                errors.extend(self.validate_input(item, field_name))
        elif isinstance(input_data, str):
            for pattern in self.compiled_patterns:
                if pattern.search(input_data):
                    errors.append(f"Potential threat detected in {field_name or 'input'}: {pattern.pattern}")
        return errors

    def validate_file_path(self, path: str, allowed_dirs: List[str]) -> bool:
        """Validate file path to prevent directory traversal attacks"""
        try:
            resolved_path = Path(path).resolve()
            return any(resolved_path.is_relative_to(Path(allowed_dir)) for allowed_dir in allowed_dirs)
        except Exception:
            return False

    def sanitize_input(self, input_data: Any) -> Any:
        """Sanitize input data by removing potentially dangerous content"""
        if isinstance(input_data, str):
            for pattern in self.compiled_patterns:
                input_data = pattern.sub("[REDACTED]", input_data)
        return input_data


# Instancia global del validador de seguridad
_security_validator = None

def get_security_validator() -> SecurityValidator:
    """Obtiene la instancia global del validador de seguridad"""
    global _security_validator
    if _security_validator is None:
        _security_validator = SecurityValidator()
    return _security_validator

