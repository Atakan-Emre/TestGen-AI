"""
Test senaryosu ayrıştırma ve kısıtlama çıkarma
"""
import re
from typing import Optional, Tuple, List
from dataclasses import dataclass
from app.shared.types import Constraints
from app.shared.logging import get_logger


logger = get_logger(__name__)


def parse_line(text: str) -> Optional[Constraints]:
    """
    Test senaryosu satırını parse et ve kısıtlamaları çıkar
    
    Args:
        text: Parse edilecek satır metni
        
    Returns:
        Çıkarılan kısıtlamalar veya None
    """
    try:
        if not text or not text.strip():
            return None
        if text.strip().startswith("#"):
            return None
        
        text = text.strip()
        logger.debug(f"Satır parse ediliyor: {text}")
        
        # TR ve EN kısımlarını ayır
        tr_text, en_text = _extract_tr_en_parts(text)
        
        # İsim ipuçlarını çıkar
        name_hints = _extract_name_hints(tr_text, en_text)
        semantic_tags = _extract_semantic_tags(tr_text, en_text)
        
        # Tip ve limit bilgilerini çıkar
        field_type, max_len, pattern = extract_type_and_limits(text)
        
        # Zorunlu alan kontrolü
        required = is_required(text)
        optional = is_optional(text)
        unique = is_unique(text)
        
        # Enum değerlerini çıkar
        enum_values = _extract_enum_values(text)
        
        # Locale bilgisi
        locale = _extract_locale(text)
        
        constraints = Constraints(
            name_hints=name_hints,
            field_type=field_type,
            required=required,
            max_len=max_len,
            pattern=pattern,
            enum=enum_values,
            locale=locale,
            optional=optional,
            unique=unique,
            raw_text=text,
            source_field_tr=tr_text or None,
            source_field_en=en_text or None,
            semantic_tags=semantic_tags,
            confidence=0.6,
        )
        
        logger.debug(f"Parse sonucu: {constraints}")
        return constraints
        
    except Exception as e:
        logger.warning(f"Satır parse hatası: {e}")
        return None


def _extract_tr_en_parts(text: str) -> Tuple[str, str]:
    """TR ve EN kısımlarını ayır"""
    matches = list(re.finditer(r"\(([^)]+)\)", text))
    if not matches:
        return text, ""

    last_match = matches[-1]
    en_part = last_match.group(1).strip()
    tr_part = f"{text[:last_match.start()]} {text[last_match.end():]}".strip()
    return tr_part, en_part


def _extract_name_hints(tr_text: str, en_text: str) -> List[str]:
    """İsim ipuçlarını çıkar"""
    hints = []
    
    if tr_text:
        hints.append(tr_text.strip())
        hints.extend(_tokenize_name_parts(tr_text))

    # TR metinden ipuçları
    tr_hints = _extract_keywords_from_text(tr_text, "tr")
    hints.extend(tr_hints)
    
    # EN metinden ipuçları
    if en_text:
        hints.append(en_text.strip())
        hints.extend(_tokenize_name_parts(en_text))
        en_hints = _extract_keywords_from_text(en_text, "en")
        hints.extend(en_hints)
    
    return list(set(hints))  # Tekrarları kaldır


def _tokenize_name_parts(text: str) -> List[str]:
    tokens = []
    for token in re.split(r"[^a-zA-Z0-9çğıöşüÇĞİÖŞÜ]+", text):
        normalized = token.strip()
        if normalized and len(normalized) > 1:
            tokens.append(normalized)
    return tokens


def _extract_semantic_tags(tr_text: str, en_text: str) -> List[str]:
    tags = []
    tags.extend(_extract_keywords_from_text(tr_text, "tr"))
    if en_text:
        tags.extend(_extract_keywords_from_text(en_text, "en"))
    return list(set(tags))


def _extract_keywords_from_text(text: str, language: str) -> List[str]:
    """Metinden anahtar kelimeleri çıkar"""
    keywords = []
    text_lower = text.lower()
    
    # Alan adı sözlükleri
    if language == "tr":
        field_keywords = {
            "tarih": ["tarih", "date", "zaman", "time"],
            "vergi": ["vergi", "tax", "kdv", "vat"],
            "tutar": ["tutar", "amount", "price", "fiyat", "miktar", "quantity"],
            "kod": ["kod", "code", "numara", "number", "no"],
            "ad": ["ad", "name", "isim", "title", "başlık"],
            "açıklama": ["açıklama", "description", "detay", "detail"],
            "iban": ["iban"],
            "tckn": ["tckn", "tc kimlik", "tc"],
            "vkn": ["vkn", "vergi kimlik"],
            "kullanıcı": ["kullanıcı", "user", "username"],
            "stok": ["stok", "stock", "ürün", "product"],
            "birim": ["birim", "unit", "para birimi", "currency"],
            "hareket": ["hareket", "movement", "transaction", "işlem"],
            "seri": ["seri", "serial", "sıra", "sequence"],
            "belge": ["belge", "document", "doc", "evrak"],
            "kart": ["kart", "card"],
            "para": ["para", "money", "currency", "döviz"],
            "kur": ["kur", "rate", "exchange"]
        }
    else:
        field_keywords = {
            "date": ["date", "time", "tarih", "zaman"],
            "tax": ["tax", "vat", "vergi", "kdv"],
            "amount": ["amount", "price", "tutar", "fiyat", "quantity", "miktar"],
            "code": ["code", "number", "kod", "numara", "no"],
            "name": ["name", "title", "ad", "isim", "başlık"],
            "description": ["description", "detail", "açıklama", "detay"],
            "iban": ["iban"],
            "tc": ["tc", "tckn", "tc kimlik"],
            "tax_id": ["vkn", "vergi kimlik", "tax id"],
            "user": ["user", "username", "kullanıcı"],
            "stock": ["stock", "product", "stok", "ürün"],
            "unit": ["unit", "currency", "birim", "para birimi"],
            "movement": ["movement", "transaction", "hareket", "işlem"],
            "serial": ["serial", "sequence", "seri", "sıra"],
            "document": ["document", "doc", "belge", "evrak"],
            "card": ["card", "kart"],
            "money": ["money", "currency", "döviz", "para"],
            "rate": ["rate", "exchange", "kur"]
        }
    
    # Anahtar kelimeleri ara
    for category, words in field_keywords.items():
        if any(word in text_lower for word in words):
            keywords.append(category)
    
    return keywords


def extract_type_and_limits(text: str) -> Tuple[Optional[str], Optional[int], Optional[str]]:
    """
    Metinden tip ve limit bilgilerini çıkar
    
    Args:
        text: Analiz edilecek metin
        
    Returns:
        (field_type, max_len, pattern) tuple'ı
    """
    text_lower = text.lower()
    field_type = None
    max_len = None
    pattern = None
    
    # Tip belirleme
    if any(keyword in text_lower for keyword in ["tarih", "date", "yyyy-aa-gg"]):
        field_type = "date"
    elif any(keyword in text_lower for keyword in ["sayısal", "numeric", "rakam", "sadece rakam"]):
        field_type = "number"
    elif any(keyword in text_lower for keyword in ["metin", "text", "string"]):
        field_type = "string"
    elif any(keyword in text_lower for keyword in ["boolean", "bool", "evet/hayır"]):
        field_type = "bool"
    
    # Maksimum uzunluk çıkarma
    max_len_match = re.search(r'maksimum\s+(\d+)\s+karakter', text_lower)
    if max_len_match:
        max_len = int(max_len_match.group(1))
        if field_type is None:
            field_type = "string"
    
    # Pattern çıkarma
    if "iban" in text_lower:
        pattern = r"^TR\d{2}\d{4}\d{16}$"
    elif "tckn" in text_lower or "tc kimlik" in text_lower:
        pattern = r"^\d{11}$"
    elif "vkn" in text_lower or "vergi kimlik" in text_lower:
        pattern = r"^\d{10}$"
    elif "email" in text_lower or "e-posta" in text_lower:
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    
    return field_type, max_len, pattern


def is_required(text: str) -> bool:
    """
    Metinde zorunlu alan belirteci var mı kontrol et
    
    Args:
        text: Kontrol edilecek metin
        
    Returns:
        Zorunlu alan mı?
    """
    text_lower = text.lower()
    
    required_indicators = [
        "zorunludur", "zorunlu", "doldurulması zorunludur", 
        "doldurulması zorunlu", "mandatory", "required"
    ]
    
    return any(indicator in text_lower for indicator in required_indicators)


def is_optional(text: str) -> bool:
    text_lower = text.lower()
    optional_indicators = [
        "opsiyoneldir",
        "opsiyonel",
        "isteğe bağlıdır",
        "optional",
    ]
    return any(indicator in text_lower for indicator in optional_indicators)


def is_unique(text: str) -> bool:
    text_lower = text.lower()
    unique_indicators = [
        "tekildir",
        "tekil",
        "benzersiz",
        "unique",
        "tekrarlanamaz",
    ]
    return any(indicator in text_lower for indicator in unique_indicators)


def _extract_enum_values(text: str) -> Optional[List[str]]:
    """Metinden enum değerlerini çıkar"""
    matches = re.findall(r'\b[A-Z][A-Z0-9_]{2,}\b', text)

    if len(matches) >= 2:
        return [value.strip() for value in matches]
    
    return None


def _extract_locale(text: str) -> Optional[str]:
    """Metinden locale bilgisini çıkar"""
    if any(keyword in text.lower() for keyword in ["türkçe", "turkish", "tr-tr"]):
        return "tr-TR"
    elif any(keyword in text.lower() for keyword in ["ingilizce", "english", "en-us"]):
        return "en-US"
    
    return None


def pattern_from_phrase(phrase: str) -> Optional[str]:
    """
    Basit ifadelerden regex pattern üret
    
    Args:
        phrase: Pattern üretilecek ifade
        
    Returns:
        Regex pattern veya None
    """
    phrase_lower = phrase.lower()
    
    # Yaygın pattern'ler
    patterns = {
        "sadece rakam": r"^\d+$",
        "sadece harf": r"^[a-zA-Z]+$",
        "harf ve rakam": r"^[a-zA-Z0-9]+$",
        "email formatı": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
        "telefon": r"^\+?[\d\s\-\(\)]+$",
        "tarih": r"^\d{4}-\d{2}-\d{2}$"
    }
    
    for key, pattern in patterns.items():
        if key in phrase_lower:
            return pattern
    
    return None
