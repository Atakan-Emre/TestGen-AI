"""
Test değerleri üretimi için factory fonksiyonları
"""
import random
import re
from datetime import datetime, timedelta
from typing import Any, Dict, Optional, List
from .logging import get_logger
from .types import Constraints, JsonSchemaInfo
from app.services.domain_tuning import build_valid_value, resolve_preferred_field_type


logger = get_logger(__name__)


def generate_value(field_type: str, constraints: Constraints, variables: Dict[str, str], 
                  seed: Optional[int] = None, field_path: Optional[str] = None,
                  schema_type: Optional[str] = None) -> Any:
    """
    Kısıtlamalara göre test değeri üret
    
    Args:
        field_type: Alan tipi
        constraints: Kısıtlamalar
        variables: Değişken mapping'i
        seed: Rastgele sayı tohumu (deterministiklik için)
        
    Returns:
        Üretilen test değeri
    """
    if seed is not None:
        random.seed(seed)
    
    try:
        logger.debug(f"Değer üretiliyor: tip={field_type}, kısıtlamalar={constraints}")
        
        # Domain-aware valid value üretimi
        field_context = {
            "json_field": field_path,
            "field_name_tr": constraints.source_field_tr,
            "field_name_en": constraints.source_field_en,
            "field_type": resolve_preferred_field_type(field_type or constraints.field_type, schema_type),
            "schema_type": schema_type,
            "semantic_tags": constraints.semantic_tags or constraints.name_hints,
            "pattern": constraints.pattern,
            "enum_values": constraints.enum,
            "max_length": constraints.max_len,
            "locale": constraints.locale,
        }
        generated = build_valid_value(field_context)
        if generated is not None:
            return generated

        # Tip bazlı üretim
        if field_type == "string" or field_type == "text":
            return _generate_string(constraints, variables)
        elif field_type == "number":
            return _generate_number(constraints)
        elif field_type == "date":
            return _generate_date(constraints)
        elif field_type == "bool":
            return _generate_boolean()
        elif field_type == "id":
            return _generate_id(constraints)
        elif field_type == "code":
            return _generate_code(constraints)
        elif field_type == "amount":
            return _generate_amount(constraints)
        elif field_type == "email":
            return _generate_email()
        elif field_type == "url":
            return _generate_url()
        elif field_type == "uuid":
            return _generate_uuid()
        else:
            # Bilinmeyen tip için varsayılan string
            return _generate_string(constraints, variables)
            
    except Exception as e:
        logger.warning(f"Değer üretim hatası: {e}, varsayılan değer kullanılıyor")
        return "test_value"


def _generate_string(constraints: Constraints, variables: Dict[str, str]) -> str:
    """String değer üret"""
    # İsim ipuçlarına göre özel değerler
    name_hints = [hint.lower() for hint in constraints.name_hints]
    
    if any("tarih" in hint or "date" in hint for hint in name_hints):
        return datetime.now().strftime("%Y-%m-%d")
    elif any("ad" in hint or "name" in hint for hint in name_hints):
        return "Test Adı"
    elif any("açıklama" in hint or "description" in hint for hint in name_hints):
        return "Test Açıklaması"
    elif any("kod" in hint or "code" in hint for hint in name_hints):
        return "TEST001"
    elif any("kullanıcı" in hint or "user" in hint for hint in name_hints):
        return "testuser"
    elif any("iban" in hint for hint in name_hints):
        return "TR330006100519786457841326"
    elif any("tckn" in hint or "tc" in hint for hint in name_hints):
        return "12345678901"
    elif any("vkn" in hint for hint in name_hints):
        return "1234567890"
    
    # Genel string üretimi
    if constraints.max_len:
        length = min(constraints.max_len, 50)  # Maksimum 50 karakter
    else:
        length = random.randint(5, 20)
    
    return "Test" + "X" * (length - 4)


def _generate_number(constraints: Constraints) -> float:
    """Sayısal değer üret"""
    # İsim ipuçlarına göre özel değerler
    name_hints = [hint.lower() for hint in constraints.name_hints]
    
    if any("oran" in hint or "rate" in hint or "ratio" in hint for hint in name_hints):
        return 18.0  # KDV oranı
    elif any("miktar" in hint or "quantity" in hint for hint in name_hints):
        return 1.0
    elif any("tutar" in hint or "amount" in hint or "price" in hint for hint in name_hints):
        return 100.0
    
    # Genel sayı üretimi
    return random.uniform(0, 1000)


def _generate_date(constraints: Constraints) -> str:
    """Tarih değeri üret"""
    # Bugünden önce veya sonra rastgele tarih
    days_offset = random.randint(-30, 30)
    date = datetime.now() + timedelta(days=days_offset)
    
    # ISO format
    return date.strftime("%Y-%m-%dT%H:%M:%S.000Z")


def _generate_boolean() -> bool:
    """Boolean değer üret"""
    return random.choice([True, False])


def _generate_id(constraints: Constraints) -> str:
    """ID değeri üret"""
    return f"TEST-{random.randint(1000, 9999)}"


def _generate_code(constraints: Constraints) -> str:
    """Kod değeri üret"""
    return f"CODE{random.randint(100, 999)}"


def _generate_amount(constraints: Constraints) -> float:
    """Tutar değeri üret (2 ondalık)"""
    amount = random.uniform(10, 10000)
    return round(amount, 2)


def _generate_email() -> str:
    """Email değeri üret"""
    domains = ["test.com", "example.org", "demo.net"]
    username = f"user{random.randint(100, 999)}"
    domain = random.choice(domains)
    return f"{username}@{domain}"


def _generate_url() -> str:
    """URL değeri üret"""
    domains = ["example.com", "test.org", "demo.net"]
    domain = random.choice(domains)
    return f"https://{domain}/api/v1"


def _generate_uuid() -> str:
    """UUID değeri üret"""
    import uuid
    return str(uuid.uuid4())


def _generate_from_pattern(pattern: str, max_len: Optional[int] = None) -> str:
    """
    Regex pattern'ine uygun değer üret (basit implementasyon)
    
    Args:
        pattern: Regex pattern
        max_len: Maksimum uzunluk
        
    Returns:
        Pattern'e uygun string
    """
    # Basit pattern'ler için önceden tanımlanmış değerler
    if r"\d" in pattern:
        # Rakam pattern'i
        length = max_len or 10
        return "".join([str(random.randint(0, 9)) for _ in range(length)])
    elif r"[a-zA-Z]" in pattern:
        # Harf pattern'i
        length = max_len or 10
        return "".join([random.choice("abcdefghijklmnopqrstuvwxyz") for _ in range(length)])
    else:
        # Genel pattern için basit string
        return "TestValue123"


def create_null_payload(info: JsonSchemaInfo) -> Dict[str, Any]:
    """
    Tüm alanları null olan JSON payload oluştur
    
    Args:
        info: JSON şema bilgisi
        
    Returns:
        Null payload
    """
    try:
        logger.debug("Null payload oluşturuluyor...")
        
        # Path'leri hiyerarşik yapıya çevir
        payload = {}
        
        for path in info.paths:
            _set_path_value(payload, path, None)
        
        logger.debug(f"Null payload oluşturuldu: {len(info.paths)} alan")
        return payload
        
    except Exception as e:
        logger.error(f"Null payload oluşturma hatası: {e}")
        return {}


def _set_path_value(doc: Dict[str, Any], path: str, value: Any) -> None:
    """Path'e değer ata (nested structure oluştur)"""
    from .json_structure import set_nested_value
    set_nested_value(doc, path, value)
