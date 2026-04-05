import json
import copy
from datetime import datetime
import os
from app.generators.bsc.matcher import DefaultMatcher
from app.services.domain_tuning import build_valid_value, normalize_text, resolve_preferred_field_type, resolve_target_leaf_path
from app.services.scenario_intelligence import load_scenario_profiles
from app.shared.json_structure import analyze_structure
from .bsc_generator import BSCGenerator
from .shared_runtime import get_legacy_test_runtime

class OPTGenerator(BSCGenerator):
    def __init__(self):
        # BSC Generator'dan miras al
        super().__init__()
        self.mandatory_fields = {}
        self.optional_fields = {}
        runtime = get_legacy_test_runtime()
        self.ner = runtime["ner"]
        self.nlp = runtime["nlp"]
        self.sentence_model = runtime["sentence_model"]
        self.field_matcher = runtime["field_matcher"]
        self.value_generator = runtime["value_generator"]
        self.semantic_matcher = DefaultMatcher()
        self.binding_ignored_fields = set()
        self.binding_mutation_blocked_fields = set()
            
    def _analyze_scenario_line(self, line):
        """Test senaryosunu analiz et"""
        try:
            # Sadece opsiyonel alanları işle
            if "opsiyoneldir" not in line.lower():
                return None
                
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
            
            # Tipi belirlemek için basit kontrol
            field_type = None
            lower_line = line.lower()
            if "tarih" in lower_line or "date" in en_text.lower():
                field_type = "date"
            elif "sayısal" in lower_line or "numeric" in en_text.lower():
                field_type = "numeric"
            elif "metin" in lower_line or "text" in en_text.lower():
                field_type = "text"
            
            max_length = None
            if "maksimum" in lower_line and "karakterli" in lower_line:
                try:
                    segment = line.lower().split("maksimum")[1].split("karakterli")[0]
                    max_length = int(''.join(filter(str.isdigit, segment)))
                except:
                    pass
                
            print(f"\nOpsiyonel Senaryo Analizi:")
            print(f"TR Metin: {tr_text}")
            print(f"EN Alan: {en_text}")
            print(f"Tip: {field_type}")
            print(f"Max Uzunluk: {max_length}")
            print(f"Bulunan Varlıklar: {entities}")
            
            return {
                "tr_text": tr_text,
                "en_text": en_text,
                "is_required": False,
                "field_type": field_type,
                "max_length": max_length,
                "optional": True,
                "entities": entities,
                "embeddings": self._get_field_embeddings(en_text)
            }
            
        except Exception as e:
            print(f"Opsiyonel senaryo analiz hatası: {str(e)}")
            return None
            
    def _create_optional_variations(self):
        """Opsiyonel alan kombinasyonlarını oluştur"""
        variations = []
        baseline = self._create_test_case()
        base_payload = baseline["test_data"] if baseline else self._create_null_data(self.template_json)
        
        # 1. Tüm opsiyonel alanlar dolu
        all_optional_payload = copy.deepcopy(base_payload)
        for field, analysis in self.optional_fields.items():
            if field in self.binding_mutation_blocked_fields:
                continue
            json_field = analysis.get('json_field') or self._find_matching_json_field(analysis)
            if json_field:
                value = self.variables.get(json_field) if self.variables and json_field in self.variables else build_valid_value(
                    self._build_field_context(json_field, analysis)
                )
                self._set_nested_value(all_optional_payload, json_field, value)
        variations.append({
            "scenario_type": "OPT",
            "description": "Tüm opsiyonel alanlar dolu senaryo",
            "test_data": all_optional_payload,
            "expected_result": "SUCCESS"
        })
        
        # 2. Tüm opsiyonel alanlar boş
        variations.append({
            "scenario_type": "OPT",
            "description": "Tüm opsiyonel alanlar boş senaryo",
            "test_data": copy.deepcopy(base_payload),
            "expected_result": "SUCCESS"
        })
        
        # 3. Her opsiyonel alan için tek tek dolu senaryo
        for field, analysis in self.optional_fields.items():
            if field in self.binding_mutation_blocked_fields:
                continue
            test_payload = copy.deepcopy(base_payload)
            json_field = analysis.get('json_field') or self._find_matching_json_field(analysis)
            if json_field:
                value = self.variables.get(json_field) if self.variables and json_field in self.variables else build_valid_value(
                    self._build_field_context(json_field, analysis)
                )
                self._set_nested_value(test_payload, json_field, value)
            variations.append({
                "scenario_type": "OPT",
                "description": f"Sadece {analysis.get('tr_text', field)} dolu senaryo",
                "test_data": test_payload,
                "expected_result": "SUCCESS"
            })
        
        return variations

    def _load_semantic_optional_fields(self, scenario_path):
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

            field_payload = {
                "tr_text": profile.field_name_tr,
                "en_text": profile.field_name_en,
                "json_field": resolved_path,
                "field_type": resolve_preferred_field_type(
                    profile.field_type,
                    schema_info.types.get(resolved_path),
                ),
                "type": resolve_preferred_field_type(
                    profile.field_type,
                    schema_info.types.get(resolved_path),
                ),
                "schema_type": schema_info.types.get(resolved_path),
                "max_length": profile.max_len,
                "pattern": profile.pattern,
                "enum_values": profile.enum_values,
                "optional": True,
                "entities": profile.ner_entities,
                "semantic_tags": profile.semantic_tags,
            }

            if profile.required:
                self.mandatory_fields[resolved_path] = {
                    **field_payload,
                    "optional": False,
                    "analysis": field_payload,
                }
            elif profile.optional:
                self.optional_fields[resolved_path] = {
                    **field_payload,
                    "analysis": field_payload,
                }

        return bool(self.optional_fields or self.mandatory_fields)

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
    
    def generate_opt_tests(self, scenario_path, test_name, json_file_id):
        """OPT test senaryolarını oluştur"""
        try:
            print(f"\nTest senaryosu okunuyor: {scenario_path}")
            
            if not os.path.exists(scenario_path):
                raise Exception(f"Senaryo dosyası bulunamadı: {scenario_path}")
            
            # JSON şablonunu yükle
            self.template_json = self._load_template(json_file_id)
            if self.variables is None:
                self.variables = self._load_variables()
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

            if not self._load_semantic_optional_fields(scenario_path):
                with open(scenario_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                print(f"Toplam {len(lines)} satır okundu.")
                
                for line in lines:
                    if "opsiyoneldir" in line.lower():
                        analysis = self._analyze_scenario_line(line)
                        if analysis:
                            json_field = self._find_matching_json_field(analysis)
                            if not json_field:
                                continue
                            target_path = self._resolve_target_path(json_field, analysis)
                            payload = {
                                **analysis,
                                "json_field": target_path,
                                "type": resolve_preferred_field_type(
                                    analysis.get("field_type"),
                                    self._schema_path_types().get(target_path),
                                ),
                                "analysis": analysis,
                            }
                            self.optional_fields[target_path] = payload

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
            variations = self._create_optional_variations()
            
            # Test senaryolarını kaydet
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_dir = os.path.join("/app/data/output/test_cases", test_name, "opt")
            os.makedirs(output_dir, exist_ok=True)
            
            saved_tests = []
            for i, test_case in enumerate(variations):
                filepath = os.path.join(output_dir, f"opt_test_case_{timestamp}_{i+1}.json")
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(test_case, f, indent=2, ensure_ascii=False)
                print(f"Test case kaydedildi: {filepath}")
                test_case["file_path"] = filepath
                saved_tests.append(test_case)
            
            print(f"\nOpsiyonel alan sayısı: {len(self.optional_fields)}")
            return saved_tests
            
        except Exception as e:
            print(f"OPT test üretme hatası: {str(e)}")
            raise
