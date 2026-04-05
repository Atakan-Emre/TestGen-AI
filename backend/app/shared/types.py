"""
Ortak tip tanımları ve exception sınıfları
"""
from dataclasses import dataclass
from typing import Any, Optional, List, Dict, Set


@dataclass
class Constraints:
    """Test senaryosundan çıkarılan kısıtlamalar"""
    name_hints: List[str]        # alan adı ipuçları (örn: "tarih", "vergi no")
    field_type: Optional[str]    # beklenen tür ("date","number","string","bool"...)
    required: bool               # "zorunlu"/"mandatory" tespiti
    max_len: Optional[int]       # maksimum uzunluk
    pattern: Optional[str]       # regex pattern
    enum: Optional[List[str]]    # sabit değerler
    locale: Optional[str]        # "tr-TR" gibi
    optional: bool = False
    unique: bool = False
    raw_text: Optional[str] = None
    source_field_tr: Optional[str] = None
    source_field_en: Optional[str] = None
    semantic_tags: Optional[List[str]] = None
    confidence: float = 0.0


@dataclass
class MatchResult:
    """Alan eşleştirme sonucu"""
    path: str                    # JSON path
    score: float                 # benzerlik skoru (0-1)
    rationale: str               # eşleştirme gerekçesi


@dataclass
class JsonSchemaInfo:
    """JSON şema analiz sonucu"""
    paths: List[str]             # dot-path listesi
    types: Dict[str, str]        # path -> "string|number|bool|date|array|object|null"
    mandatory: Set[str]          # zorunlu alan path'leri


@dataclass
class ScenarioFieldProfile:
    """CSV veya scenario metninden uretilen yapilandirilmis alan profili"""
    field_name_tr: str
    field_name_en: str
    field_type: Optional[str]
    raw_type: Optional[str]
    required: bool
    optional: bool
    unique: bool
    max_len: Optional[int]
    min_len: Optional[int]
    pattern: Optional[str]
    enum_values: List[str]
    semantic_tags: List[str]
    ner_entities: List[Dict[str, Any]]
    scenario_lines: List[str]
    confidence: float = 0.0
    source_text: Optional[str] = None
    locale: Optional[str] = None

    def to_constraints(self) -> Constraints:
        hints = [
            self.field_name_tr,
            self.field_name_en,
            *self.semantic_tags,
        ]
        normalized_hints = [hint for hint in hints if hint]
        return Constraints(
            name_hints=list(dict.fromkeys(normalized_hints)),
            field_type=self.field_type,
            required=self.required,
            max_len=self.max_len,
            pattern=self.pattern,
            enum=self.enum_values or None,
            locale=self.locale,
            optional=self.optional,
            unique=self.unique,
            raw_text=self.source_text,
            source_field_tr=self.field_name_tr,
            source_field_en=self.field_name_en,
            semantic_tags=self.semantic_tags,
            confidence=self.confidence,
        )


@dataclass
class ScenarioBundle:
    """Bir senaryo dosyasi icin yapilandirilmis metadata"""
    scenario_name: str
    source_csv: str
    generator_type: str
    generated_at: str
    scenario_file: str
    fields: List[ScenarioFieldProfile]


# Exception sınıfları
class BSCException(Exception):
    """BSC generator için temel exception"""
    pass


class TemplateLoadError(BSCException):
    """Template yükleme hatası"""
    pass


class VariablesLoadError(BSCException):
    """Variables yükleme hatası"""
    pass


class SchemaInferenceError(BSCException):
    """Şema çıkarım hatası"""
    pass


class MatchingError(BSCException):
    """Alan eşleştirme hatası"""
    pass


class WriteError(BSCException):
    """Dosya yazma hatası"""
    pass


class RLModelError(BSCException):
    """RL model hatası"""
    pass
