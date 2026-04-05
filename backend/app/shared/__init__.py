"""
Shared modülleri - ortak fonksiyonlar ve tipler
"""

# I/O fonksiyonları
from .io_loader import load_template, load_variables, save_json, save_text

# JSON yapısı analizi
from .json_structure import analyze_structure, set_nested_value, JsonSchemaInfo, split_camel_case, normalize_name

# Değer üretimi
from .value_factory import generate_value, create_null_payload

# Ayarlar
from .settings import *

# Tipler
from .types import *

# Logging
from .logging import get_logger

__all__ = [
    # I/O
    "load_template", "load_variables", "save_json", "save_text",
    
    # JSON yapısı
    "analyze_structure", "set_nested_value", "JsonSchemaInfo", "split_camel_case", "normalize_name",
    
    # Değer üretimi
    "generate_value", "create_null_payload",
    
    # Tipler
    "Constraints", "MatchResult", "JsonSchemaInfo", "ScenarioFieldProfile", "ScenarioBundle",
    
    # Exception'lar
    "BSCException", "TemplateLoadError", "VariablesLoadError", "SchemaInferenceError", 
    "MatchingError", "WriteError", "RLModelError",
    
    # Logging
    "get_logger",
    
    # Ayarlar (settings'den gelenler)
    "OUTPUT_PATH", "DEFAULT_VARIABLES_PATH", "JSON_TEMPLATES_PATH",
    "EMB_MODEL_NAME", "MATCH_WEIGHTS", "USE_RL", "RL_MODELS_PATH",
    "LOG_LEVEL", "LOG_FORMAT", "TEST_SEED",
    "resolve_json_path", "get_output_dir"
]
