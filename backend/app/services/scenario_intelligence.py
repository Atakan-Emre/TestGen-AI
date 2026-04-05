import json
import re
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional, Tuple

import numpy as np
import pandas as pd

from app.shared.logging import get_logger
from app.shared.settings import INPUT_DIR, OUTPUT_DIR
from app.shared.types import Constraints, ScenarioBundle, ScenarioFieldProfile
from .domain_tuning import (
    detect_domain_pattern,
    detect_domain_type,
    derive_domain_tags,
)
from .nlp_runtime import get_ner_pipeline, get_sentence_model


logger = get_logger(__name__)

SCENARIO_OUTPUT_DIR = OUTPUT_DIR / "test_scenarios"

TYPE_PROTOTYPES = {
    "date": [
        "date tarih due date issue date shipment date receiving date attached date timestamp time saat",
    ],
    "number": [
        "numeric number amount quantity tutar miktar oran rate ratio fiyat quantity total tax discount gun adet",
    ],
    "bool": [
        "boolean bool evet hayir true false deleted dahil haric accounting status turnover onay",
    ],
    "enum": [
        "enum secim listesi deger listesinden secilir option type class status delivery note class card type",
    ],
    "id": [
        "id code kod serial seri belge no document number reference no order no iban account number current code vendor code customer code",
    ],
    "string": [
        "string text metin aciklama description note ad name title debtor address text city branch bank",
    ],
    "object": [
        "card kart address adres branch sube account hesap warehouse depo user current account",
    ],
}

TAG_PROTOTYPES = {
    "document": ["document belge evrak doc movement delivery note invoice"],
    "serial": ["serial seri numara no number reference order check nr document no"],
    "amount": ["amount tutar quantity miktar total toplam discount iskonto"],
    "currency": ["currency doviz para birimi kur rate exchange card currency"],
    "person": ["user kullanici debtor person driver customer vendor receiver teslim alan"],
    "address": ["address adres city country district mahalle shipment address"],
    "status": ["status durum state active accounting deleted"],
    "date": ["date tarih due shipment attached receiving"],
    "time": ["time saat"],
    "tax": ["tax vergi vat kdv deduction tevkifat"],
    "card": ["card kart current finance bank warehouse current account"],
    "check": ["check cek senet note case"],
    "warehouse": ["warehouse depo section branch sube"],
}

STOPWORDS = {
    "alan",
    "alani",
    "field",
    "the",
    "and",
    "ve",
    "ile",
    "of",
    "a",
    "an",
}


def _cosine_similarity(left: np.ndarray, right: np.ndarray) -> float:
    left_norm = np.linalg.norm(left)
    right_norm = np.linalg.norm(right)
    if left_norm == 0 or right_norm == 0:
        return 0.0
    return float(np.dot(left, right) / (left_norm * right_norm))


class ScenarioIntelligenceService:
    def __init__(self, progress_callback: Optional[Callable[[str, Optional[float], Optional[str]], None]] = None):
        self._progress_callback = progress_callback
        self._emit_progress("Embedding modeli hazırlanıyor.", 0.22, "embedding_model")
        self.model = get_sentence_model()
        self._emit_progress("NER pipeline hazırlanıyor.", 0.26, "ner_pipeline")
        self.ner = get_ner_pipeline()
        self._emit_progress("Semantic prototipler hazırlanıyor.", 0.3, "semantic_bootstrap")
        self._type_embeddings = self._embed_label_map(TYPE_PROTOTYPES)
        self._tag_embeddings = self._embed_label_map(TAG_PROTOTYPES)

    def generate_bundle(
        self,
        input_file: str,
        scenario_name: Optional[str] = None,
        generator_type: str = "nlp_hybrid",
        progress_callback: Optional[Callable[[str, Optional[float], Optional[str]], None]] = None,
    ) -> Tuple[ScenarioBundle, Path]:
        if progress_callback is not None:
            self._progress_callback = progress_callback

        self._emit_progress("CSV dosyası okunuyor.", 0.35, "csv_loading")
        df = self._detect_and_read_csv(INPUT_DIR / "Csv" / input_file)
        profiles: List[ScenarioFieldProfile] = []
        scenario_lines: List[str] = []
        total_fields = len(df.index)

        self._emit_progress(
            f"CSV okundu, {total_fields} alan tespit edildi.",
            0.42,
            "csv_loaded",
        )

        checkpoint = max(1, total_fields // 8) if total_fields else 1

        for index, (field_name_tr, row) in enumerate(df.iterrows(), start=1):
            profile = self._build_profile(str(field_name_tr), row, generator_type)
            profiles.append(profile)
            scenario_lines.extend(profile.scenario_lines)
            if index == 1 or index == total_fields or index % checkpoint == 0:
                progress = 0.42 + (index / max(total_fields, 1)) * 0.43
                self._emit_progress(
                    f"Alan profilleri işleniyor: {index}/{total_fields} ({field_name_tr}).",
                    round(min(progress, 0.85), 3),
                    "profiling",
                )

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_stem = f"{scenario_name}_{timestamp}" if scenario_name else f"test_senaryolari_{timestamp}"
        scenario_path = SCENARIO_OUTPUT_DIR / f"{file_stem}.txt"
        scenario_path.parent.mkdir(parents=True, exist_ok=True)
        self._emit_progress("Senaryo çıktısı dosyaya yazılıyor.", 0.9, "writing_output")
        scenario_path.write_text("\n".join(scenario_lines), encoding="utf-8")

        bundle = ScenarioBundle(
            scenario_name=scenario_name or file_stem,
            source_csv=input_file,
            generator_type=generator_type,
            generated_at=datetime.now().isoformat(),
            scenario_file=scenario_path.name,
            fields=profiles,
        )
        self._save_bundle(bundle, scenario_path)
        self._emit_progress(
            f"Scenario bundle kaydedildi: {scenario_path.name}.",
            0.97,
            "bundle_saved",
        )

        logger.info("Scenario bundle olusturuldu: %s (%s alan)", scenario_path.name, len(profiles))
        return bundle, scenario_path

    def _emit_progress(
        self,
        message: str,
        progress: Optional[float] = None,
        stage: Optional[str] = None,
    ) -> None:
        if self._progress_callback:
            self._progress_callback(message, progress, stage)

    def _detect_and_read_csv(self, file_path: Path) -> pd.DataFrame:
        candidate_headers = [0, 1, 2, 3]
        expected_cols = {"Alan adı (İng)", "Tip", "Boyut", "Zorunlu mu?", "Tekil mi?"}

        best_df = None
        best_score = -1

        for header_idx in candidate_headers:
            try:
                df_try = pd.read_csv(file_path, encoding="utf-8", sep=",", header=header_idx)
            except Exception:
                continue

            df_try.columns = [str(column).strip() for column in df_try.columns]
            score = len(expected_cols.intersection(set(df_try.columns)))
            if score > best_score:
                best_score = score
                best_df = df_try
            if score >= 4:
                break

        if best_df is None:
            raise ValueError(f"CSV basligi tespit edilemedi: {file_path}")

        return best_df.set_index(best_df.columns[0])

    def _build_profile(
        self,
        field_name_tr: str,
        row: pd.Series,
        generator_type: str,
    ) -> ScenarioFieldProfile:
        field_name_en = self._get_row_value(row, ["Alan adı (İng)", "Field Name", "Name"]) or field_name_tr
        raw_type = self._get_row_value(row, ["Tip", "Type"])
        size_text = self._get_row_value(row, ["Boyut", "Size"])
        default_text = self._get_row_value(row, ["Öndeğer", "Default"])
        required_text = self._get_row_value(row, ["Zorunlu mu?", "Required"])
        unique_text = self._get_row_value(row, ["Tekil mi?", "Unique"])

        required = self._is_required(required_text)
        unique = self._is_unique(unique_text)
        minimum_length, maximum_length = self._extract_lengths(size_text)
        semantic_tags = self._infer_semantic_tags(field_name_tr, field_name_en, raw_type, default_text)
        field_type, confidence = self._infer_field_type(
            field_name_tr, field_name_en, raw_type, default_text, semantic_tags, generator_type
        )
        enum_values = self._extract_enum_values(raw_type, default_text)
        pattern = self._infer_pattern(field_name_tr, field_name_en, semantic_tags)
        ner_entities = self._extract_entities(
            " ".join(part for part in [field_name_tr, field_name_en, raw_type, default_text] if part)
        )

        profile = ScenarioFieldProfile(
            field_name_tr=field_name_tr,
            field_name_en=field_name_en,
            field_type=field_type,
            raw_type=raw_type,
            required=required,
            optional=not required,
            unique=unique,
            max_len=maximum_length,
            min_len=minimum_length,
            pattern=pattern,
            enum_values=enum_values,
            semantic_tags=semantic_tags,
            ner_entities=ner_entities,
            scenario_lines=[],
            confidence=confidence,
            source_text=" | ".join(part for part in [raw_type, size_text, default_text, required_text, unique_text] if part),
            locale="tr-TR",
        )
        profile.scenario_lines = self._generate_scenario_lines(profile)
        return profile

    def _generate_scenario_lines(self, profile: ScenarioFieldProfile) -> List[str]:
        label = f"{profile.field_name_tr} ({profile.field_name_en})"
        lines: List[str] = []

        if profile.min_len:
            lines.append(f"{label} alanı en az {profile.min_len} karakterli olmalıdır.")
        if profile.max_len:
            lines.append(f"{label} alanı maksimum {profile.max_len} karakterli olmalıdır.")

        if profile.enum_values:
            preview = ", ".join(profile.enum_values[:5])
            lines.append(f"{label} alanı şu değerlerden biri olmalıdır: {preview}.")

        type_messages = {
            "date": f"{label} alanı geçerli bir tarih formatında olmalıdır.",
            "number": f"{label} alanına sadece sayısal değer girilebilir.",
            "bool": f"{label} alanı evet/hayır veya true/false tipinde olmalıdır.",
            "string": f"{label} alanına sadece metin girişi yapılabilir.",
            "id": f"{label} alanı benzersiz bir kimlik veya kod formatında olmalıdır.",
        }
        if profile.field_type in type_messages:
            lines.append(type_messages[profile.field_type])

        if profile.pattern:
            lines.append(f"{label} alanı tanımlı format kuralına uymalıdır.")

        if profile.required:
            lines.append(f"{label} alanı doldurulması zorunludur.")
        else:
            lines.append(f"{label} alanı opsiyoneldir.")

        if profile.unique:
            lines.append(f"{label} alanı tekildir.")

        return lines

    def _infer_field_type(
        self,
        field_name_tr: str,
        field_name_en: str,
        raw_type: Optional[str],
        default_text: Optional[str],
        semantic_tags: List[str],
        generator_type: str,
    ) -> Tuple[str, float]:
        raw_type_lower = (raw_type or "").lower()
        field_name_lower = " ".join([field_name_tr.lower(), field_name_en.lower()])

        domain_type, domain_confidence = detect_domain_type(
            field_name_tr=field_name_tr,
            field_name_en=field_name_en,
            raw_type=raw_type,
            default_text=default_text,
        )
        if domain_type:
            return domain_type, domain_confidence

        if "date&time" in raw_type_lower or raw_type_lower.strip() == "date":
            return "date", 0.98
        if raw_type_lower.strip() == "time":
            return "date", 0.92
        if any(token in raw_type_lower for token in ["string", "text", "alfanumerik", "alfenumerik", "alphanumeric"]):
            return "string", 0.96
        if any(token in raw_type_lower for token in ["numeric", "numerik", "decimal"]):
            return "number", 0.98
        if "boolean" in raw_type_lower or "bool" in raw_type_lower:
            return "bool", 0.98
        if "enum" in raw_type_lower:
            return "enum", 0.98

        if any(token in field_name_lower for token in ["rate", "amount", "quantity", "miktar", "tutar", "oran", "kur değeri"]):
            return "number", 0.9
        if any(token in field_name_lower for token in ["currency", "para birimi", "döviz", "doviz"]):
            return "id", 0.86

        combined_text = " ".join(
            part for part in [field_name_tr, field_name_en, raw_type or "", default_text or "", " ".join(semantic_tags)] if part
        )
        lowered = combined_text.lower()

        direct_rules = [
            ("date", ["date", "tarih", "timestamp", "due date", "shipment"]),
            ("number", ["numeric", "sayisal", "sayısal", "amount", "quantity", "rate", "oran", "tutar", "miktar"]),
            ("bool", ["boolean", "bool", "evet/hayir", "evet/hayır", "true/false"]),
            ("enum", ["enum", "deger listesinden secilir", "değer listesinden seçilir"]),
            ("id", ["iban", "tckn", "vkn", "kimlik", "serial", "seri", "code", "kod", "doc nr", "document number"]),
        ]
        for label, hints in direct_rules:
            if any(hint in lowered for hint in hints):
                return label, 0.95

        if generator_type == "rule_based":
            return "string", 0.55

        text_embedding = self.model.encode([combined_text], convert_to_numpy=True)[0]
        best_label = "string"
        best_score = 0.0
        for label, prototype_embedding in self._type_embeddings.items():
            score = _cosine_similarity(text_embedding, prototype_embedding)
            if score > best_score:
                best_score = score
                best_label = label

        return best_label, round(best_score, 4)

    def _infer_semantic_tags(
        self,
        field_name_tr: str,
        field_name_en: str,
        raw_type: Optional[str],
        default_text: Optional[str],
    ) -> List[str]:
        combined_text = " ".join(part for part in [field_name_tr, field_name_en, raw_type or "", default_text or ""] if part)

        text_embedding = self.model.encode([combined_text], convert_to_numpy=True)[0]
        semantic_tags = derive_domain_tags(field_name_tr, field_name_en, raw_type, default_text)
        for tag, prototype_embedding in self._tag_embeddings.items():
            score = _cosine_similarity(text_embedding, prototype_embedding)
            if score >= 0.42:
                semantic_tags.append(tag)

        return list(dict.fromkeys(semantic_tags))

    def _extract_entities(self, text: str) -> List[Dict[str, str]]:
        if not text.strip():
            return []
        try:
            results = self.ner(text)
        except Exception as exc:
            logger.warning("NER extraction failed: %s", exc)
            return []

        entities = []
        for entity in results:
            entities.append(
                {
                    "text": entity.get("word") or entity.get("entity_group", ""),
                    "label": entity.get("entity_group", ""),
                    "score": round(float(entity.get("score", 0.0)), 4),
                }
            )
        return entities

    def _extract_enum_values(self, raw_type: Optional[str], default_text: Optional[str]) -> List[str]:
        enum_candidates: List[str] = []
        source_text = " ".join(filter(None, [raw_type, default_text]))
        if "enum" not in source_text.lower() and "değer listesinden" not in source_text.lower() and "deger listesinden" not in source_text.lower():
            return enum_candidates

        matches = re.findall(r"\(([A-Za-z0-9_ /\-]+)\)", source_text)
        for match in matches:
            candidate = match.strip()
            if 1 < len(candidate) <= 40 and candidate.upper() not in {"KURALI", "RULE"}:
                enum_candidates.append(candidate)

        uppercase_matches = re.findall(r"\b[A-Z][A-Z0-9_]{2,}\b", source_text)
        enum_candidates.extend(
            token for token in uppercase_matches if token.upper() not in {"KURALI", "RULE"}
        )
        return list(dict.fromkeys(enum_candidates))[:10]

    def _extract_lengths(self, size_text: Optional[str]) -> Tuple[Optional[int], Optional[int]]:
        if not size_text:
            return None, None

        lowered = size_text.lower()
        numbers = [int(number) for number in re.findall(r"\d+", lowered)]
        if not numbers:
            return None, None

        minimum = None
        maximum = None
        if "min" in lowered:
            minimum = numbers[0]
        if "max" in lowered:
            maximum = numbers[-1]
        elif len(numbers) == 1:
            maximum = numbers[0]
        elif len(numbers) >= 2:
            minimum, maximum = numbers[0], numbers[-1]

        return minimum, maximum

    def _infer_pattern(self, field_name_tr: str, field_name_en: str, semantic_tags: List[str]) -> Optional[str]:
        domain_pattern = detect_domain_pattern(field_name_tr, field_name_en, " ".join(semantic_tags), None)
        if domain_pattern:
            return domain_pattern
        combined = " ".join([field_name_tr.lower(), field_name_en.lower(), " ".join(semantic_tags)])
        if "iban" in combined:
            return r"^TR\d{2}\d{4}\d{16}$"
        if "tckn" in combined or "tc" in combined:
            return r"^\d{11}$"
        if "vkn" in combined or "vergi" in combined:
            return r"^\d{10}$"
        if "email" in combined or "e-posta" in combined:
            return r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
        return None

    def _is_required(self, value: Optional[str]) -> bool:
        if not value:
            return False
        lowered = value.lower()
        return any(token in lowered for token in ["zorunlu", "mandatory", "required"])

    def _is_unique(self, value: Optional[str]) -> bool:
        if not value:
            return False
        lowered = value.lower()
        return any(token in lowered for token in ["tekil", "unique", "benzersiz", "tekrarlanamaz"])

    def _get_row_value(self, row: pd.Series, candidates: Iterable[str]) -> Optional[str]:
        lowered_index = {str(column).strip().lower(): column for column in row.index}
        for candidate in candidates:
            direct = lowered_index.get(candidate.strip().lower())
            if direct is not None:
                value = row.get(direct)
                if pd.notna(value):
                    return str(value).strip()
        return None

    def _embed_label_map(self, labels: Dict[str, List[str]]) -> Dict[str, np.ndarray]:
        embeddings = {}
        for label, texts in labels.items():
            vector = self.model.encode(texts, convert_to_numpy=True)
            embeddings[label] = np.mean(vector, axis=0)
        return embeddings

    def _save_bundle(self, bundle: ScenarioBundle, scenario_path: Path) -> None:
        sidecar_path = get_bundle_path(scenario_path)
        sidecar_path.write_text(
            json.dumps(asdict(bundle), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )


def get_bundle_path(scenario_path: Path) -> Path:
    return scenario_path.with_suffix(".meta.json")


def load_scenario_bundle(scenario_path: str) -> Optional[ScenarioBundle]:
    path = Path(scenario_path)
    sidecar_path = get_bundle_path(path)
    if not sidecar_path.exists():
        return None

    raw_bundle = json.loads(sidecar_path.read_text(encoding="utf-8"))
    fields = [
        ScenarioFieldProfile(
            field_name_tr=field["field_name_tr"],
            field_name_en=field["field_name_en"],
            field_type=field.get("field_type"),
            raw_type=field.get("raw_type"),
            required=field.get("required", False),
            optional=field.get("optional", False),
            unique=field.get("unique", False),
            max_len=field.get("max_len"),
            min_len=field.get("min_len"),
            pattern=field.get("pattern"),
            enum_values=field.get("enum_values") or [],
            semantic_tags=field.get("semantic_tags") or [],
            ner_entities=field.get("ner_entities") or [],
            scenario_lines=field.get("scenario_lines") or [],
            confidence=field.get("confidence", 0.0),
            source_text=field.get("source_text"),
            locale=field.get("locale"),
        )
        for field in raw_bundle.get("fields", [])
    ]
    return ScenarioBundle(
        scenario_name=raw_bundle["scenario_name"],
        source_csv=raw_bundle["source_csv"],
        generator_type=raw_bundle["generator_type"],
        generated_at=raw_bundle["generated_at"],
        scenario_file=raw_bundle["scenario_file"],
        fields=fields,
    )


def load_scenario_profiles(scenario_path: str) -> List[ScenarioFieldProfile]:
    bundle = load_scenario_bundle(scenario_path)
    if bundle:
        return bundle.fields
    return []


def load_scenario_constraints(scenario_path: str) -> List[Constraints]:
    profiles = load_scenario_profiles(scenario_path)
    if profiles:
        return [profile.to_constraints() for profile in profiles]

    from app.generators.bsc.scenario_parser import parse_line

    constraints: List[Constraints] = []
    with open(scenario_path, "r", encoding="utf-8") as scenario_file:
        for line in scenario_file.readlines():
            parsed = parse_line(line.strip())
            if parsed:
                constraints.append(parsed)
    return constraints
