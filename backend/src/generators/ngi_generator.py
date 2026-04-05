import json
from datetime import datetime
import os
from app.generators.bsc.matcher import DefaultMatcher
from app.services.domain_tuning import (
    build_invalid_cases,
    build_valid_value,
    normalize_text,
    resolve_preferred_field_type,
    resolve_target_leaf_path,
)
from app.services.scenario_intelligence import load_scenario_profiles
from app.shared.json_structure import analyze_structure
from .bsc_generator import BSCGenerator
from .shared_runtime import get_legacy_test_runtime

class NGIGenerator(BSCGenerator):
    def __init__(self):
        super().__init__()
        self.mandatory_fields = {}  # Zorunlu alanlar için
        self.optional_fields = {}   # Opsiyonel alanlar için
        runtime = get_legacy_test_runtime()
        self.ner = runtime["ner"]
        self.nlp = runtime["nlp"]
        self.sentence_model = runtime["sentence_model"]
        self.field_matcher = runtime["field_matcher"]
        self.value_generator = runtime["value_generator"]
        self.semantic_matcher = DefaultMatcher()
        self.binding_ignored_fields = set()
        self.binding_mutation_blocked_fields = set()

    def _determine_field_type(self, analysis, json_field=None):
        """Alan tipini belirle"""
        try:
            # Önce json_field'dan tip belirlemeye çalış
            if json_field:
                field_info = self.json_structure.get(json_field, {})
                if 'type' in field_info:
                    if field_info['type'] in ['int', 'float', 'decimal']:
                        return 'numeric'
                    elif field_info['type'] in ['datetime', 'date']:
                        return 'date'
                    elif field_info['type'] == 'boolean':
                        return 'boolean'
                    return field_info['type']

            # Metin analizinden tip belirlemeye çalış
            text = analysis.get('tr_text', '').lower()
            
            # Tarih kontrolü
            if any(word in text for word in ['tarih', 'date', 'zaman', 'time']):
                return 'date'
            
            # Sayısal değer kontrolü
            if any(word in text for word in ['miktar', 'tutar', 'oran', 'sayı', 'adet', 'amount', 'quantity', 'rate']):
                return 'numeric'
            
            # Boolean kontrolü
            if any(word in text for word in ['var/yok', 'evet/hayır', 'true/false', 'yes/no']):
                return 'boolean'
            
            # Varsayılan tip
            return 'text'
            
        except Exception as e:
            print(f"Tip belirleme hatası: {str(e)}")
            return 'text'

    def _analyze_scenario_line(self, line):
        """Senaryo satırını analiz et"""
        try:
            tr_text = line.split("(")[0].strip()
            en_text = line[line.index("(")+1:line.index(")")].strip() if "(" in line else ""
            
            # NER analizi
            entities = []
            if self.ner:
                try:
                    ner_results = self.ner(line)
                    entities = [
                        {
                            "text": result["word"],
                            "type": result["entity"],
                            "score": result["score"]
                        }
                        for result in ner_results
                    ]
                except Exception as e:
                    print(f"NER analiz hatası: {str(e)}")
            
            # Alan tipini belirle
            json_field = self._find_matching_json_field({"tr_text": tr_text, "en_text": en_text})
            field_type = self._determine_field_type({"tr_text": tr_text}, json_field)
            
            print(f"\nNGI Senaryo Analizi:")
            print(f"TR Metin: {tr_text}")
            print(f"EN Alan: {en_text}")
            print(f"Alan: {json_field}")
            print(f"Tip: {field_type}")
            print(f"Bulunan Varlıklar: {entities}")
            
            return {
                "tr_text": tr_text,
                "en_text": en_text,
                "entities": entities,
                "json_field": json_field,
                "type": field_type,
                "embeddings": self._get_field_embeddings(en_text)
            }
            
        except Exception as e:
            print(f"Senaryo analiz hatası: {str(e)}")
            return None

    def _create_ngi_variations(self):
        """NGI test varyasyonlarını oluştur"""
        variations = []
        
        # Zorunlu ve opsiyonel alanları birleştir
        all_fields = {
            field: info
            for field, info in {**self.mandatory_fields, **self.optional_fields}.items()
            if field not in self.binding_mutation_blocked_fields
        }
        
        for field, field_info in all_fields.items():
            invalid_values = build_invalid_cases(self._build_field_context(field, field_info), limit=3)
            
            for invalid_case in invalid_values:
                test_case = self._create_test_case()
                if not test_case or "test_data" not in test_case:
                    raise RuntimeError(f"NGI temel test case oluşturulamadı: {field}")
                
                # Önce tüm zorunlu alanları doldur
                for mandatory_field, mandatory_info in self.mandatory_fields.items():
                    if mandatory_field != field and mandatory_field not in self.binding_mutation_blocked_fields:
                        value = self._generate_value_by_type(mandatory_info)
                        self._set_nested_value(test_case['test_data'], mandatory_field, value)
                
                # Test edilen alan için geçersiz değeri ata
                self._set_nested_value(test_case['test_data'], field, invalid_case['value'])

                variations.append({
                    "scenario_type": "NGI",
                    "description": f"Alan '{field}' için {invalid_case['description']} testi",
                    "test_data": test_case['test_data'],
                    "expected_result": "VALIDATION_ERROR",
                    "expected_message": f"Alan '{field}' için geçersiz değer: {invalid_case['value']}"
                })

        return variations

    def _normalize_type(self, profile_type, schema_type):
        profile_lower = (profile_type or "").lower()
        schema_lower = (schema_type or "").lower()

        if profile_lower in {"date"} or schema_lower in {"date", "datetime"}:
            return "date"
        if profile_lower in {"id", "code"} or schema_lower in {"id", "uuid", "code"}:
            return "id"
        if profile_lower in {"enum"} or schema_lower in {"enum"}:
            return "enum"
        if profile_lower in {"number", "numeric", "amount"} or schema_lower in {"number", "amount", "quantity", "rate"}:
            return "numeric"
        if profile_lower in {"bool", "boolean"} or schema_lower in {"bool", "boolean"}:
            return "boolean"
        return "text"

    def _build_field_context(self, field_path, field_info):
        analysis = field_info.get("analysis", {})
        return {
            "json_field": field_path,
            "field_name_tr": analysis.get("tr_text", field_path),
            "field_name_en": analysis.get("en_text", field_path),
            "field_type": field_info.get("type"),
            "semantic_tags": analysis.get("semantic_tags", []),
            "pattern": field_info.get("pattern"),
            "enum_values": field_info.get("enum_values", []),
            "max_length": field_info.get("max_length"),
        }

    def _load_semantic_fields(self, scenario_path):
        profiles = load_scenario_profiles(scenario_path)
        if not profiles:
            return False

        schema_info = analyze_structure(self.template_json)
        for profile in profiles:
            constraints = profile.to_constraints()
            try:
                match_result = self.semantic_matcher.find_best_match(constraints, schema_info)
            except Exception:
                continue

            if match_result.score <= 0.1:
                continue

            resolved_path = resolve_target_leaf_path(
                match_result.path,
                schema_info.paths,
                schema_info.types,
                {
                    "json_field": match_result.path,
                    "field_name_tr": profile.field_name_tr,
                    "field_name_en": profile.field_name_en,
                    "field_type": profile.field_type,
                    "semantic_tags": profile.semantic_tags,
                },
            )
            if self._should_skip_id_like_match(resolved_path, profile.field_name_tr, profile.field_name_en):
                continue
            if match_result.score < self._minimum_match_score(profile.field_type, schema_info.types.get(resolved_path)):
                continue

            field_info = {
                "json_field": resolved_path,
                "analysis": {
                    "tr_text": profile.field_name_tr,
                    "en_text": profile.field_name_en,
                    "json_field": resolved_path,
                    "entities": profile.ner_entities,
                    "semantic_tags": profile.semantic_tags,
                },
                "type": resolve_preferred_field_type(
                    self._normalize_type(profile.field_type, schema_info.types.get(resolved_path)),
                    schema_info.types.get(resolved_path),
                ),
                "schema_type": schema_info.types.get(resolved_path),
                "pattern": profile.pattern,
                "enum_values": profile.enum_values,
                "max_length": profile.max_len,
            }

            if profile.required:
                self.mandatory_fields[resolved_path] = field_info
            elif profile.optional:
                self.optional_fields[resolved_path] = field_info

        return bool(self.mandatory_fields or self.optional_fields)

    def _minimum_match_score(self, explicit_type, schema_type):
        normalized_type = resolve_preferred_field_type(explicit_type, schema_type)
        if normalized_type in {"bool", "date"}:
            return 0.4
        return 0.45

    def _should_skip_id_like_match(self, target_path, field_name_tr, field_name_en):
        normalized_source = normalize_text(f"{field_name_tr or ''} {field_name_en or ''}")
        if not normalized_source or not target_path.endswith(".id"):
            return False

        if any(token in normalized_source for token in ["type", "turu", "tipi", "status", "durum"]):
            return True

        if any(token in normalized_source for token in ["adi", "name", "description", "aciklama", "city", "il"]):
            protected_tokens = [
                "seri",
                "serial",
                "belge no",
                "doc nr",
                "document number",
                "kod",
                "code",
                "currency",
                "para birimi",
                "user",
                "kullanici",
                "card",
                "kart",
                "branch",
                "sube",
                "depo",
                "warehouse",
                "check no",
                "cek no",
            ]
            return not any(token in normalized_source for token in protected_tokens)

        return False

    def generate_ngi_tests(self, scenario_path, test_name, json_file_id):
        """NGI test senaryolarını oluştur"""
        try:
            print(f"\nTest senaryosu okunuyor: {scenario_path}")
            
            if not os.path.exists(scenario_path):
                raise Exception(f"Senaryo dosyası bulunamadı: {scenario_path}")
            
            # JSON şablonunu yükle
            self.template_json = self._load_template(json_file_id)
            self.variables = self.variables or self._load_variables()
            self.json_structure = self._analyze_json_structure()
            self.mandatory_fields = {}
            self.optional_fields = {}
            
            if self.binding_ignored_fields:
                self.mandatory_fields = {
                    field: info for field, info in self.mandatory_fields.items()
                    if field not in self.binding_ignored_fields
                }
                self.optional_fields = {
                    field: info for field, info in self.optional_fields.items()
                    if field not in self.binding_ignored_fields
                }

            if not self._load_semantic_fields(scenario_path):
                with open(scenario_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                print(f"Toplam {len(lines)} satır okundu")
                
                for line in lines:
                    analysis = self._analyze_scenario_line(line)
                    if not analysis:
                        continue

                    if "zorunludur" in line.lower():
                        self.mandatory_fields[analysis['json_field']] = {
                            'json_field': analysis['json_field'],
                            'analysis': analysis,
                            'type': analysis['type']
                        }
                    elif "opsiyoneldir" in line.lower():
                        self.optional_fields[analysis['json_field']] = {
                            'json_field': analysis['json_field'],
                            'analysis': analysis,
                            'type': analysis['type']
                        }

            if self.binding_ignored_fields:
                self.mandatory_fields = {
                    field: info for field, info in self.mandatory_fields.items()
                    if field not in self.binding_ignored_fields
                }
                self.optional_fields = {
                    field: info for field, info in self.optional_fields.items()
                    if field not in self.binding_ignored_fields
                }

            # Test varyasyonlarını oluştur
            variations = self._create_ngi_variations()
            
            if not variations:
                print("Test senaryosu oluşturulamadı.")
                return None
            
            print(f"\nToplam {len(variations)} test varyasyonu oluşturuldu")
            
            # Test senaryolarını kaydet
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_dir = os.path.join("/app/data/output/test_cases", test_name, "ngi")
            os.makedirs(output_dir, exist_ok=True)
            
            saved_tests = []
            for i, test_case in enumerate(variations):
                filepath = os.path.join(output_dir, f"ngi_test_case_{timestamp}_{i+1}.json")
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(test_case, f, indent=2, ensure_ascii=False)
                print(f"Test case kaydedildi: {filepath}")
                test_case["file_path"] = filepath
                saved_tests.append(test_case)
            
            print(f"\nZorunlu alan sayısı: {len(self.mandatory_fields)}")
            print(f"Opsiyonel alan sayısı: {len(self.optional_fields)}")
            return saved_tests
            
        except Exception as e:
            print(f"NGI test üretme hatası: {str(e)}")
            raise

    def _generate_value_by_type(self, field_info, field_path=None):
        """Alan tipine göre geçerli değer üret"""
        target_path = str(field_path or field_info.get("json_field", ""))
        return build_valid_value(self._build_field_context(target_path, field_info))
