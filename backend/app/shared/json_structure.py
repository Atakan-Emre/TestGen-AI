"""
JSON yapısı analizi ve manipülasyon fonksiyonları
"""
import re
from typing import Any, Dict, List, Set, Optional, Union
from dataclasses import dataclass
from .logging import get_logger
from .types import JsonSchemaInfo, SchemaInferenceError


logger = get_logger(__name__)


def analyze_structure(template: Dict[str, Any]) -> JsonSchemaInfo:
    """
    JSON template'ini analiz et ve şema bilgisi çıkar
    
    Args:
        template: JSON template verisi
        
    Returns:
        JSON şema analiz sonucu
        
    Raises:
        SchemaInferenceError: Şema çıkarım hatası
    """
    try:
        logger.info("JSON yapısı analiz ediliyor...")
        
        paths = []
        types = {}
        mandatory = set()
        
        def _analyze_value(value: Any, path: str = "") -> None:
            """Recursive olarak değerleri analiz et"""
            if isinstance(value, dict):
                for key, val in value.items():
                    new_path = f"{path}.{key}" if path else key
                    
                    # Tip belirleme
                    field_type = _infer_type(val, new_path)
                    types[new_path] = field_type
                    paths.append(new_path)
                    
                    # Zorunlu alan kontrolü
                    if _is_mandatory_field(new_path, val):
                        mandatory.add(new_path)
                    
                    # Recursive analiz
                    _analyze_value(val, new_path)
                    
            elif isinstance(value, list) and value:
                # Array için ilk elemanı analiz et
                array_path = f"{path}[0]"
                field_type = _infer_type(value[0], array_path)
                types[array_path] = f"array<{field_type}>"
                paths.append(array_path)
                _analyze_value(value[0], array_path)
        
        _analyze_value(template)
        
        schema_info = JsonSchemaInfo(
            paths=sorted(paths),
            types=types,
            mandatory=mandatory
        )
        
        logger.info(f"JSON analizi tamamlandı: {len(paths)} alan, {len(mandatory)} zorunlu")
        return schema_info
        
    except Exception as e:
        error_msg = f"JSON şema analiz hatası: {e}"
        logger.error(error_msg)
        raise SchemaInferenceError(error_msg)


def _infer_type(value: Any, path: str) -> str:
    """
    Değer tipini çıkar (heuristic tabanlı)
    
    Args:
        value: Analiz edilecek değer
        path: Alan yolu
        
    Returns:
        Tip string'i
    """
    # Temel tip kontrolü
    if value is None:
        return "null"
    elif isinstance(value, bool):
        return "bool"
    elif isinstance(value, int):
        return _infer_numeric_type(path)
    elif isinstance(value, float):
        return _infer_numeric_type(path)
    elif isinstance(value, str):
        # String alt tiplerini belirle
        return _infer_string_type(value, path)
    elif isinstance(value, dict):
        return "object"
    elif isinstance(value, list):
        return "array"
    else:
        return "unknown"


def _infer_string_type(value: str, path: str) -> str:
    """
    String değerinin alt tipini belirle
    
    Args:
        value: String değer
        path: Alan yolu
        
    Returns:
        String alt tipi
    """
    path_lower = path.lower()
    value_lower = value.lower()
    
    # Tarih kontrolü
    if any(keyword in path_lower for keyword in ["date", "tarih", "time", "zaman"]):
        return "date"
    
    # ID kontrolü
    if path_lower.endswith(".id") or path_lower.endswith("id"):
        return "id"
    
    # Kod kontrolü
    if any(keyword in path_lower for keyword in ["code", "kod"]):
        return "code"
    
    # Tutar/fiyat kontrolü
    if any(keyword in path_lower for keyword in ["amount", "price", "total", "tutar"]):
        return "amount"

    # Sayısal string alanlar
    if any(keyword in path_lower for keyword in ["quantity", "miktar", "qty", "rate", "ratio", "denominator", "numerator", "unit"]):
        return "number"
    
    # Email kontrolü
    if "@" in value and "." in value:
        return "email"
    
    # URL kontrolü
    if value.startswith(("http://", "https://")):
        return "url"
    
    # UUID kontrolü
    if re.match(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', value, re.IGNORECASE):
        return "uuid"
    
    return "string"


def _infer_numeric_type(path: str) -> str:
    """Sayısal alanın semantik tipini belirle."""
    path_lower = path.lower()

    if path_lower.endswith(".id") or path_lower.endswith("id"):
        return "id"

    if any(keyword in path_lower for keyword in ["amount", "price", "total", "tutar"]):
        return "amount"

    return "number"


def _is_mandatory_field(path: str, value: Any) -> bool:
    """
    Alanın zorunlu olup olmadığını belirle
    
    Args:
        path: Alan yolu
        value: Alan değeri
        
    Returns:
        Zorunlu alan mı?
    """
    path_lower = path.lower()
    
    # Boş değerler muhtemelen zorunlu
    if value is None or value == "":
        return True
    
    # Belirli alanlar her zaman zorunlu
    mandatory_keywords = ["id", "code", "name", "title", "type"]
    if any(keyword in path_lower for keyword in mandatory_keywords):
        return True
    
    return False


def set_nested_value(doc: Dict[str, Any], path: str, value: Any) -> None:
    """
    Nested JSON path'e değer ata
    
    Args:
        doc: JSON dokümanı
        path: Dot notation path (örn: "lines[0].unitPrice")
        value: Atanacak değer
        
    Raises:
        SchemaInferenceError: Değer atama hatası
    """
    try:
        logger.debug(f"Nested değer atanıyor: {path} = {value}")
        
        # Array index desteği ile path'i parse et
        parts = _parse_path(path)
        current = doc
        
        # Son eleman hariç tüm path'i oluştur
        for part in parts[:-1]:
            if isinstance(part, int):
                # Array index
                if not isinstance(current, list):
                    raise ValueError(f"Array beklenirken {type(current)} bulundu")
                while len(current) <= part:
                    current.append({})
                current = current[part]
            else:
                # Object key
                if not isinstance(current, dict):
                    current = {}
                if part not in current:
                    current[part] = {}
                current = current[part]
        
        # Son değeri ata
        last_part = parts[-1]
        if isinstance(last_part, int):
            if not isinstance(current, list):
                raise ValueError(f"Array beklenirken {type(current)} bulundu")
            while len(current) <= last_part:
                current.append({})
            current[last_part] = value
        else:
            if not isinstance(current, dict):
                current = {}
            current[last_part] = value
        
        logger.debug(f"Nested değer başarıyla atandı: {path}")
        
    except Exception as e:
        error_msg = f"Nested değer atama hatası ({path}): {e}"
        logger.error(error_msg)
        raise SchemaInferenceError(error_msg)


def _parse_path(path: str) -> List[Union[str, int]]:
    """
    Path string'ini parse et
    
    Args:
        path: Path string (örn: "lines[0].unitPrice")
        
    Returns:
        Parse edilmiş path parçaları
    """
    parts = []
    current = ""
    i = 0
    
    while i < len(path):
        char = path[i]
        
        if char == '.':
            if current:
                parts.append(current)
                current = ""
        elif char == '[':
            if current:
                parts.append(current)
                current = ""
            # Index'i bul
            i += 1
            index_str = ""
            while i < len(path) and path[i] != ']':
                index_str += path[i]
                i += 1
            if index_str.isdigit():
                parts.append(int(index_str))
            else:
                parts.append(index_str)  # String index
        else:
            current += char
        
        i += 1
    
    if current:
        parts.append(current)
    
    return parts


def get_nested_type(info: JsonSchemaInfo, path: str) -> str:
    """
    Path için tip bilgisini al
    
    Args:
        info: JSON şema bilgisi
        path: Alan path'i
        
    Returns:
        Alan tipi
    """
    return info.types.get(path, "unknown")


def split_camel_case(name: str) -> List[str]:
    """
    CamelCase metni kelimelere ayır
    
    Args:
        name: CamelCase string
        
    Returns:
        Kelime listesi
    """
    if not name:
        return []
    
    words = []
    current_word = name[0].lower()
    
    for char in name[1:]:
        if char.isupper():
            words.append(current_word)
            current_word = char.lower()
        else:
            current_word += char
    
    words.append(current_word)
    return [word for word in words if word]  # Boş kelimeleri filtrele


def normalize_name(name: str) -> str:
    """
    İsmi normalize et (lowercase + underscore + Türkçe karakter normalize)
    
    Args:
        name: Normalize edilecek isim
        
    Returns:
        Normalize edilmiş isim
    """
    if not name:
        return ""
    
    # Türkçe karakterleri normalize et
    turkish_chars = {
        'ç': 'c', 'ğ': 'g', 'ı': 'i', 'ö': 'o', 'ş': 's', 'ü': 'u',
        'Ç': 'C', 'Ğ': 'G', 'İ': 'I', 'Ö': 'O', 'Ş': 'S', 'Ü': 'U'
    }
    
    normalized = name
    for tr_char, en_char in turkish_chars.items():
        normalized = normalized.replace(tr_char, en_char)
    
    # CamelCase'i kelimelere ayır
    words = split_camel_case(normalized)
    
    # Underscore ile birleştir ve lowercase yap
    return "_".join(words).lower()
