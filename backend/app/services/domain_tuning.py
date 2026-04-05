import re
from typing import Any, Dict, List, Optional, Tuple


TRANSLATION_TABLE = str.maketrans(
    {
        "ç": "c",
        "ğ": "g",
        "ı": "i",
        "ö": "o",
        "ş": "s",
        "ü": "u",
        "Ç": "c",
        "Ğ": "g",
        "İ": "i",
        "Ö": "o",
        "Ş": "s",
        "Ü": "u",
    }
)

NAME_STOPWORDS = {
    "alan",
    "alani",
    "field",
    "value",
    "deger",
    "degeri",
    "bilgi",
    "bilgileri",
    "info",
    "type",
    "tipi",
    "tip",
    "ve",
    "ile",
    "the",
    "and",
}

TAG_HINTS = {
    "document": ["document", "doc", "belge", "irsaliye", "invoice", "evrak"],
    "serial": ["serial", "seri", "doc nr", "document number", "reference no", "order no", "check nr", "belge no"],
    "amount": ["amount", "tutar", "quantity", "miktar", "total", "discount", "iskonto", "price", "fiyat"],
    "currency": ["currency", "para birimi", "doviz", "kur", "rate", "exchange", "card currency"],
    "person": ["user", "kullanici", "customer", "vendor", "debtor", "receiver", "teslim alan"],
    "address": ["address", "adres", "sevk adresi", "city", "country", "district", "mahalle"],
    "status": ["status", "durum", "state", "deleted", "accounting"],
    "date": ["date", "tarih", "due", "shipment date", "receiving date", "attached date"],
    "time": ["time", "saat"],
    "tax": ["tax", "vergi", "vat", "kdv", "deduction", "tevkifat"],
    "card": ["card", "kart", "current", "cari", "finance card", "warehouse section"],
    "warehouse": ["warehouse", "depo", "section", "sube", "branch"],
    "check": ["check", "cek", "senet", "note case"],
    "attachment": ["attachment", "ekli belge", "attached", "doc name"],
}

TYPE_ALIASES = {
    "numeric": "number",
    "number": "number",
    "amount": "number",
    "quantity": "number",
    "rate": "number",
    "ratio": "number",
    "int": "number",
    "integer": "number",
    "float": "number",
    "double": "number",
    "decimal": "number",
    "bool": "bool",
    "boolean": "bool",
    "date": "date",
    "datetime": "date",
    "time": "date",
    "text": "string",
    "string": "string",
    "str": "string",
    "none": "string",
    "nonetype": "string",
    "uuid": "id",
    "id": "id",
    "code": "id",
    "enum": "enum",
    "object": "object",
    "dict": "object",
    "array": "array",
    "list": "array",
}


def normalize_text(text: Optional[str]) -> str:
    if not text:
        return ""
    normalized = text.translate(TRANSLATION_TABLE).lower()
    normalized = normalized.replace("&", " and ")
    return re.sub(r"\s+", " ", normalized).strip()


def normalize_field_type(field_type: Optional[str]) -> str:
    normalized = normalize_text(field_type)
    if not normalized:
        return "string"
    normalized = normalized.replace("<", " ").replace(">", " ").strip()
    return TYPE_ALIASES.get(normalized, normalized)


def resolve_preferred_field_type(
    explicit_type: Optional[str] = None,
    schema_type: Optional[str] = None,
) -> str:
    explicit = normalize_field_type(explicit_type)
    schema = normalize_field_type(schema_type)

    if schema in {"bool", "date", "number"}:
        return schema
    if explicit in {"enum", "id"} and schema in {"string", "object", "array"}:
        return explicit
    if schema in {"id", "enum"}:
        return schema
    if explicit in {"bool", "date", "number", "string", "id", "enum"}:
        return explicit
    if schema in {"string", "object", "array"}:
        return schema
    return "string"


def _contains_any(text: str, hints: List[str]) -> bool:
    for hint in hints:
        normalized_hint = normalize_text(hint)
        if not normalized_hint:
            continue
        if " " in normalized_hint:
            if normalized_hint in text:
                return True
            continue
        if re.search(rf"(?<![a-z0-9]){re.escape(normalized_hint)}(?![a-z0-9])", text):
            return True
    return False


def extract_name_tokens(*texts: Optional[str]) -> List[str]:
    tokens: List[str] = []
    for text in texts:
        normalized = normalize_text(text)
        for token in re.split(r"[^a-z0-9]+", normalized):
            if not token or token in NAME_STOPWORDS or len(token) < 2 or token.isdigit():
                continue
            tokens.append(token)
    return list(dict.fromkeys(tokens))


def detect_domain_type(
    field_name_tr: str,
    field_name_en: str,
    raw_type: Optional[str] = None,
    default_text: Optional[str] = None,
) -> Tuple[Optional[str], float]:
    name_text = normalize_text(f"{field_name_tr} {field_name_en}")
    raw_text = normalize_text(raw_type)
    default_lower = normalize_text(default_text)
    combined = " ".join(part for part in [name_text, raw_text, default_lower] if part)

    is_lookup_selection = _contains_any(
        combined,
        [
            "listesinden secilir",
            "listesinden secim",
            "listesinden secilebilir",
            "secim yapilabilir",
            "kullanici listesinden",
            "adres bilgileri listesinden",
            "otomatik olarak getirilir",
            "readonly",
        ],
    )

    if _contains_any(raw_text, ["boolean", "bool"]) or _contains_any(
        combined, ["evet/hayir", "true/false", "yes/no", "incl./excl", "incl/excl"]
    ):
        return "bool", 0.99

    if _contains_any(raw_text, ["enum", "deger listesinden secilir", "deger listesinden"]) or _contains_any(
        name_text, ["class", "status", "type", "turu", "turu"]
    ) and "enum" in raw_text:
        return "enum", 0.99

    if raw_text == "time" or _contains_any(name_text, [" time", "saat"]):
        return "date", 0.93

    if _contains_any(raw_text, ["date&time", "datetime", "date"]) or _contains_any(
        name_text, ["date", "tarih", "vade tarihi", "shipment date", "receiving date"]
    ):
        return "date", 0.98

    if _contains_any(name_text, ["type", "turu", "tipi", "class", "sinifi", "status", "durumu"]):
        return "enum", 0.9

    if _contains_any(raw_text, ["alfanumerik", "alfenumerik", "alphanumeric", "string", "text", "metin"]):
        if _contains_any(
            name_text,
            [
                "serial",
                "seri",
                "code",
                "kod",
                "doc nr",
                "document number",
                "reference no",
                "order no",
                "check nr",
                "check no",
                "iban",
                "hesap numarasi",
                "account number",
                "plate nr",
                "e-delivery note nr",
                "note nr",
            ],
        ):
            return "id", 0.97

        if _contains_any(name_text, ["note", "notu", "description", "aciklama", "debtor", "title", "name"]):
            return "string", 0.97

        return "string", 0.96

    if _contains_any(raw_text, ["numeric", "numerik", "decimal"]) and not _contains_any(
        raw_text, ["alfanumerik", "alfenumerik", "alphanumeric"]
    ):
        return "number", 0.99

    if _contains_any(
        name_text,
        [
            "amount",
            "tutar",
            "quantity",
            "miktar",
            "rate",
            "ratio",
            "oran",
            "fiyat",
            "discount",
            "iskonto",
            "days",
            "gun",
            "adet",
        ],
    ):
        return "number", 0.92

    if _contains_any(
        name_text,
        [
            "iban",
            "tckn",
            "vkn",
            "tax no",
            "vergi no",
            "code",
            "kod",
            "serial",
            "seri",
            "reference no",
            "order no",
            "document no",
            "doc nr",
            "current code",
            "vendor code",
            "customer code",
            "account number",
            "hesap numarasi",
            "check nr",
        ],
    ):
        return "id", 0.95

    if _contains_any(name_text, ["address", "adres", "shipment address", "sevk adresi"]):
        return ("id", 0.91) if is_lookup_selection else ("string", 0.9)

    if _contains_any(name_text, ["user", "kullanici", "customer", "vendor", "current account", "finance card"]):
        return ("id", 0.9) if is_lookup_selection or _contains_any(combined, ["getirilir", "secilir"]) else ("string", 0.78)

    if is_lookup_selection and _contains_any(
        name_text,
        ["card", "kart", "currency", "para birimi", "warehouse", "depo", "branch", "sube", "country", "city"],
    ):
        return "id", 0.88

    if _contains_any(name_text, ["note", "notu", "description", "aciklama", "address", "adres", "name", "title"]):
        return "string", 0.88

    return None, 0.0


def derive_domain_tags(
    field_name_tr: str,
    field_name_en: str,
    raw_type: Optional[str] = None,
    default_text: Optional[str] = None,
) -> List[str]:
    combined = normalize_text(f"{field_name_tr} {field_name_en} {raw_type or ''} {default_text or ''}")
    tags: List[str] = []

    for tag, hints in TAG_HINTS.items():
        if _contains_any(combined, hints):
            tags.append(tag)

    tags.extend(extract_name_tokens(field_name_tr, field_name_en)[:8])
    return list(dict.fromkeys(tags))


def detect_domain_pattern(
    field_name_tr: str,
    field_name_en: str,
    raw_type: Optional[str] = None,
    default_text: Optional[str] = None,
) -> Optional[str]:
    combined = normalize_text(f"{field_name_tr} {field_name_en} {raw_type or ''} {default_text or ''}")
    if "iban" in combined:
        return r"^TR\d{24}$"
    if "tckn" in combined or "tc kimlik" in combined:
        return r"^\d{11}$"
    if "vkn" in combined or "vergi" in combined:
        return r"^\d{10}$"
    if "email" in combined or "e-posta" in combined:
        return r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
    return None


def _clip_text(value: str, max_length: Optional[int]) -> str:
    if max_length and max_length > 0:
        return value[:max_length]
    return value


def resolve_target_leaf_path(
    requested_path: str,
    available_paths: List[str],
    path_types: Dict[str, str],
    field_context: Optional[Dict[str, Any]] = None,
) -> str:
    if not requested_path:
        return requested_path

    normalized_type = normalize_field_type(path_types.get(requested_path))
    if normalized_type not in {"object", "array"}:
        return requested_path

    subtree_paths = [
        path
        for path in available_paths
        if path.startswith(f"{requested_path}.") or path.startswith(f"{requested_path}[")
    ]
    leaf_paths = [
        path
        for path in subtree_paths
        if normalize_field_type(path_types.get(path)) not in {"object", "array"}
    ]

    if not leaf_paths:
        return requested_path

    field_context = field_context or {}
    name_text = normalize_text(
        f"{field_context.get('field_name_tr', '')} {field_context.get('field_name_en', '')}"
    )
    tags = set(field_context.get("semantic_tags") or [])
    preferred_type = resolve_preferred_field_type(
        field_context.get("field_type"),
        path_types.get(requested_path),
    )

    def score(candidate: str) -> Tuple[int, int]:
        candidate_text = normalize_text(candidate)
        candidate_type = resolve_preferred_field_type(None, path_types.get(candidate))
        rank = 0

        if candidate_type == preferred_type:
            rank += 7

        if any(tag in tags for tag in ["person"]) and (
            candidate_text.endswith(".id") or candidate_text.endswith(".username")
        ):
            rank += 9
        if any(tag in tags for tag in ["address"]) and (
            candidate_text.endswith(".id") or "textaddress" in candidate_text
        ):
            rank += 8
        if any(tag in tags for tag in ["currency"]) and (
            candidate_text.endswith(".id") or "numericcode" in candidate_text or candidate_text.endswith(".unit")
        ):
            rank += 8
        if any(tag in tags for tag in ["document", "serial"]) and (
            "number" in candidate_text or "serial" in candidate_text or candidate_text.endswith(".id")
        ):
            rank += 8

        if _contains_any(name_text, ["description", "aciklama", "note", "notu"]) and candidate_text.endswith("description"):
            rank += 8
        if _contains_any(name_text, ["user", "kullanici"]) and (
            candidate_text.endswith(".username") or candidate_text.endswith(".id")
        ):
            rank += 8
        if _contains_any(name_text, ["date", "tarih", "time", "saat"]) and (
            "date" in candidate_text or "time" in candidate_text
        ):
            rank += 8
        if _contains_any(name_text, ["amount", "tutar", "quantity", "miktar", "rate", "ratio", "oran"]) and (
            any(token in candidate_text for token in ["amount", "quantity", "rate", "ratio"])
        ):
            rank += 8

        if candidate_text.endswith(".id"):
            rank += 4
        if candidate_text.endswith(".code"):
            rank += 3
        if candidate_text.endswith(".documentnumber"):
            rank += 3
        if candidate_text.endswith(".username"):
            rank += 3
        if candidate_text.endswith(".description"):
            rank += 2
        if candidate_text.endswith(".name"):
            rank += 2

        depth_penalty = candidate.count(".") + candidate.count("[")
        return rank, -depth_penalty

    return max(leaf_paths, key=score)


def build_valid_value(field_context: Dict[str, Any]) -> Any:
    field_type = resolve_preferred_field_type(
        field_context.get("field_type") or field_context.get("type"),
        field_context.get("schema_type"),
    )
    tags = set(field_context.get("semantic_tags") or [])
    enum_values = field_context.get("enum_values") or []
    pattern = field_context.get("pattern")
    max_length = field_context.get("max_length") or field_context.get("max_len")
    json_field = normalize_text(field_context.get("json_field"))
    name_text = normalize_text(f"{field_context.get('field_name_tr', '')} {field_context.get('field_name_en', '')}")

    if enum_values:
        return enum_values[0]

    if "financecardtype" in json_field:
        return "CUSTOMER"
    if "currentcardtype" in json_field:
        return "VENDOR_CARD"
    if "cardtype" in json_field:
        return "STOCK_CARD"
    if "subdocumentclass" in json_field:
        return "NONE"
    if "documentclass" in json_field:
        return "PURCHASE_RETURN_DELIVERY_NOTE"
    if "entitystatus" in json_field:
        return "SAVED_TO_PHOENIX"
    if "currencydescription" in json_field and "numericcode" in json_field:
        return _clip_text("TRY", max_length)
    if "currencydescription" in json_field and json_field.endswith(".unit"):
        return 1
    if json_field.endswith(".username"):
        return _clip_text("test.user", max_length)
    if any(token in json_field for token in ["documentnumber", "serial", "referenceno", "orderno"]):
        return _clip_text("DOC-2026-0001", max_length)
    if "externalid" in json_field:
        return _clip_text("EXT-2026-0001", max_length)
    if "documentdate" in json_field or (
        field_type == "date" and not _contains_any(name_text, ["time", "saat"])
    ):
        return "2026-01-15T10:30:00.000Z"
    if json_field.endswith("time") or _contains_any(name_text, ["time", "saat"]):
        return "10:30:00"

    if json_field == "id" or json_field.endswith(".id"):
        if "currency" in tags:
            return "11111111-1111-4111-8111-111111111111"
        if _contains_any(name_text, ["serial", "seri"]):
            return _clip_text("SR001", max_length)
        if _contains_any(name_text, ["reference", "referans"]):
            return _clip_text("REF001", max_length)
        if _contains_any(name_text, ["order", "siparis"]):
            return _clip_text("ORD001", max_length)
        if _contains_any(name_text, ["code", "kod"]):
            return _clip_text("CODE001", max_length)
        return "11111111-1111-4111-8111-111111111111"

    if pattern == r"^TR\d{24}$":
        return "TR330006100519786457841326"
    if pattern == r"^\d{11}$":
        return "10000000146"
    if pattern == r"^\d{10}$":
        return "1234567890"
    if pattern == r"^[^@\s]+@[^@\s]+\.[^@\s]+$":
        return "test@example.com"

    if field_type == "date":
        if json_field.endswith("time") or _contains_any(name_text, ["time", "saat"]):
            return "10:30:00"
        return "2026-01-15T10:30:00.000Z"

    if field_type == "number":
        if _contains_any(name_text, ["rate", "ratio", "oran", "kur"]):
            return 1.25
        if _contains_any(name_text, ["days", "gun", "adet", "quantity", "miktar"]):
            return 1
        if "tax" in tags:
            return 18
        return 100

    if field_type == "id":
        if _contains_any(name_text, ["iban"]):
            return "TR330006100519786457841326"
        if _contains_any(name_text, ["tckn", "tc kimlik"]):
            return "10000000146"
        if _contains_any(name_text, ["vkn", "vergi"]):
            return "1234567890"
        if ".id" in json_field or any(tag in tags for tag in ["person", "card", "document", "address", "warehouse", "check"]):
            return "11111111-1111-4111-8111-111111111111"
        if "currency" in tags:
            return "11111111-1111-4111-8111-111111111111"
        if _contains_any(name_text, ["serial", "seri"]):
            return _clip_text("SR001", max_length)
        if _contains_any(name_text, ["reference", "referans"]):
            return _clip_text("REF001", max_length)
        if _contains_any(name_text, ["order", "siparis"]):
            return _clip_text("ORD001", max_length)
        if _contains_any(name_text, ["code", "kod"]):
            return _clip_text("CODE001", max_length)
        return _clip_text("ID001", max_length)

    if field_type == "string":
        if _contains_any(name_text, ["username", "user name"]):
            return _clip_text("test.user", max_length)
        if _contains_any(name_text, ["email", "e-posta"]):
            return _clip_text("test@example.com", max_length)
        if _contains_any(name_text, ["plate", "plaka"]):
            return _clip_text("34ABC123", max_length)
        if _contains_any(name_text, ["phone", "telefon", "gsm"]):
            return _clip_text("5551234567", max_length)
        if "currency" in tags and _contains_any(name_text, ["code", "kod", "numeric code", "numericcode"]):
            return _clip_text("TRY", max_length)
        if "address" in tags:
            return _clip_text("Istanbul Merkez", max_length)
        if _contains_any(name_text, ["description", "aciklama", "note", "notu"]):
            return _clip_text("Test aciklama", max_length)
        if _contains_any(name_text, ["name", "ad", "title"]):
            return _clip_text("Test Adi", max_length)
        if _contains_any(name_text, ["serial", "seri", "number", "numara", "reference", "referans"]):
            return _clip_text("DOC-2026-0001", max_length)
        return _clip_text("test_value", max_length)

    if field_type == "bool":
        return True

    if field_type == "enum":
        if "financecardtype" in json_field:
            return "CUSTOMER"
        if "cardtype" in json_field:
            return "STOCK_CARD"
        if "currentcardtype" in json_field:
            return "VENDOR_CARD"
        if "subdocumentclass" in json_field:
            return "NONE"
        if "entitystatus" in json_field:
            return "SAVED_TO_PHOENIX"
        return "DEFAULT"

    return _clip_text("test_value", max_length)


def build_invalid_cases(field_context: Dict[str, Any], limit: int = 3) -> List[Dict[str, Any]]:
    field_type = (field_context.get("field_type") or field_context.get("type") or "string").lower()
    tags = set(field_context.get("semantic_tags") or [])
    enum_values = field_context.get("enum_values") or []
    pattern = field_context.get("pattern")
    max_length = field_context.get("max_length") or field_context.get("max_len")
    name_text = normalize_text(f"{field_context.get('field_name_tr', '')} {field_context.get('field_name_en', '')}")
    json_field = normalize_text(field_context.get("json_field"))

    cases: List[Dict[str, Any]] = []

    if enum_values or field_type == "enum":
        cases.extend(
            [
                {"value": "__INVALID_ENUM__", "description": "desteklenmeyen enum değeri"},
                {"value": "", "description": "boş enum değeri"},
                {"value": 999, "description": "yanlış tipte enum değeri"},
            ]
        )

    if pattern == r"^TR\d{24}$":
        cases.extend(
            [
                {"value": "TR12ABC", "description": "geçersiz IBAN formatı"},
                {"value": "TR0000000000000000000000000", "description": "uzun IBAN değeri"},
            ]
        )
    elif pattern == r"^\d{11}$":
        cases.extend(
            [
                {"value": "1234567890", "description": "eksik haneli kimlik değeri"},
                {"value": "1234567890A", "description": "harf içeren kimlik değeri"},
            ]
        )
    elif pattern == r"^\d{10}$":
        cases.extend(
            [
                {"value": "123456789", "description": "eksik haneli vergi değeri"},
                {"value": "12345ABCDE", "description": "harf içeren vergi değeri"},
            ]
        )
    elif pattern == r"^[^@\s]+@[^@\s]+\.[^@\s]+$":
        cases.extend(
            [
                {"value": "invalid-email", "description": "geçersiz e-posta formatı"},
                {"value": "@example.com", "description": "kullanıcı adı eksik e-posta"},
            ]
        )

    if field_type == "date":
        if "time" in tags or _contains_any(name_text, ["time", "saat"]):
            cases.extend(
                [
                    {"value": "25:99:99", "description": "geçersiz saat formatı"},
                    {"value": "not-a-time", "description": "saat olmayan değer"},
                    {"value": 12345, "description": "yanlış tipte saat değeri"},
                ]
            )
        else:
            cases.extend(
                [
                    {"value": "invalid-date", "description": "geçersiz tarih formatı"},
                    {"value": "2026-13-45T00:00:00.000Z", "description": "takvimsel olarak geçersiz tarih"},
                    {"value": "1900-01-01T00:00:00.000Z", "description": "iş kurallarına aykırı çok eski tarih"},
                ]
            )
    elif field_type == "number":
        if "tax" in tags or _contains_any(name_text, ["rate", "ratio", "oran", "kur"]):
            cases.extend(
                [
                    {"value": -0.01, "description": "negatif oran değeri"},
                    {"value": 999999, "description": "aşırı büyük oran değeri"},
                    {"value": "oran-degil", "description": "sayısal olmayan oran değeri"},
                ]
            )
        elif "amount" in tags or _contains_any(name_text, ["amount", "tutar", "quantity", "miktar"]):
            cases.extend(
                [
                    {"value": -1, "description": "negatif tutar değeri"},
                    {"value": "abc", "description": "sayısal olmayan tutar değeri"},
                    {"value": 999999999999, "description": "aşırı büyük tutar değeri"},
                ]
            )
        else:
            cases.extend(
                [
                    {"value": -1, "description": "negatif değer"},
                    {"value": "abc", "description": "sayısal olmayan değer"},
                    {"value": 999999999, "description": "çok büyük değer"},
                ]
            )
    elif field_type == "bool":
        cases.extend(
            [
                {"value": "maybe", "description": "boolean olmayan metin değeri"},
                {"value": 2, "description": "boolean olmayan sayısal değer"},
                {"value": "", "description": "boş boolean değeri"},
            ]
        )
    elif field_type == "id":
        if "currency" in tags:
            cases.extend(
                [
                    {"value": "invalid-currency-id", "description": "geçersiz para birimi referansı"},
                    {"value": "", "description": "boş para birimi referansı"},
                    {"value": 12345, "description": "yanlış tipte para birimi referansı"},
                ]
            )
        elif "person" in tags or "card" in tags or "document" in tags or "address" in tags:
            cases.extend(
                [
                    {"value": "not-a-uuid", "description": "geçersiz referans kimliği"},
                    {"value": "", "description": "boş referans değeri"},
                    {"value": 12345, "description": "yanlış tipte referans değeri"},
                ]
            )
        else:
            cases.extend(
                [
                    {"value": "", "description": "boş kimlik değeri"},
                    {"value": "###INVALID###", "description": "format dışı kimlik değeri"},
                    {"value": 12345, "description": "yanlış tipte kimlik değeri"},
                ]
            )
    else:
        if max_length:
            cases.append(
                {
                    "value": "X" * (int(max_length) + 5),
                    "description": "maksimum uzunluğu aşan değer",
                }
            )
        if "address" in tags:
            cases.extend(
                [
                    {"value": "", "description": "boş adres değeri"},
                    {"value": "###", "description": "anlamsız adres değeri"},
                ]
            )
        elif "person" in tags:
            cases.extend(
                [
                    {"value": "", "description": "boş kişi değeri"},
                    {"value": "123456", "description": "isim alanı için sayısal değer"},
                ]
            )
        else:
            cases.extend(
                [
                    {"value": "", "description": "boş metin"},
                    {"value": "!@#$%^&*()", "description": "özel karakterlerden oluşan metin"},
                ]
            )

    unique_cases: List[Dict[str, Any]] = []
    seen = set()
    for case in cases:
        key = repr(case["value"])
        if key in seen:
            continue
        seen.add(key)
        unique_cases.append(case)
        if len(unique_cases) >= limit:
            break
    return unique_cases


def build_duplicate_seed(field_context: Dict[str, Any]) -> Any:
    field_type = (field_context.get("field_type") or field_context.get("type") or "string").lower()
    tags = set(field_context.get("semantic_tags") or [])
    enum_values = field_context.get("enum_values") or []
    pattern = field_context.get("pattern")
    max_length = field_context.get("max_length") or field_context.get("max_len")
    json_field = normalize_text(field_context.get("json_field"))
    name_text = normalize_text(f"{field_context.get('field_name_tr', '')} {field_context.get('field_name_en', '')}")

    if enum_values:
        return enum_values[0]
    if pattern:
        return build_valid_value(field_context)
    if field_type == "number":
        if _contains_any(name_text, ["rate", "ratio", "oran", "kur"]):
            return 1.25
        return 100
    if field_type == "date":
        return "2026-01-15T10:30:00.000Z"
    if json_field == "id" or json_field.endswith(".id"):
        if "currency" in tags:
            return "11111111-1111-4111-8111-111111111111"
        if "document" in tags or "serial" in tags:
            return _clip_text("DOC-0001", max_length)
        return "11111111-1111-4111-8111-111111111111"
    if field_type == "bool":
        return True
    if field_type == "id":
        if "document" in tags or "serial" in tags:
            return _clip_text("DOC-0001", max_length)
        if "currency" in tags:
            return "11111111-1111-4111-8111-111111111111"
        return _clip_text("REF-0001", max_length)
    if "address" in tags:
        return _clip_text("Istanbul Merkez", max_length)
    if _contains_any(name_text, ["description", "aciklama", "note", "notu"]):
        return _clip_text("Ayni aciklama", max_length)
    return _clip_text("DUPLICATE_VALUE", max_length)
