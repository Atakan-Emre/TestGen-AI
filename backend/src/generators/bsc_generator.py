import json
from datetime import datetime
import os
import numpy as np
from sentence_transformers import util
from app.services.domain_tuning import (
    build_valid_value,
    derive_domain_tags,
    detect_domain_pattern,
    resolve_preferred_field_type,
    resolve_target_leaf_path,
)
from ..utils.file_handler import save_test_scenarios
from ..config.settings import OUTPUT_PATH
from ..utils.chat_logger import ChatLogger
from .shared_runtime import get_base_runtime

class BSCGenerator:
    def __init__(self):
        runtime = get_base_runtime()
        self.nlp = runtime["nlp"]
        self.sentence_model = runtime["sentence_model"]
        self.field_matcher = runtime["field_matcher"]
        self.value_generator = runtime["value_generator"]
            
        self.template_json = None  # Template'i generate_bsc_test'te yükleyeceğiz
        self.variables = None      # Değişkenleri generate_bsc_test'te yükleyeceğiz
        self.json_structure = None # Yapıyı generate_bsc_test'te analiz edeceğiz
        self.mandatory_fields = {}
        self.chat_logger = ChatLogger()
        
    def _load_template(self, json_file_id):
        """JSON şablonunu yükle"""
        try:
            json_dir = "/app/data/input/Json"
            json_files = [f for f in os.listdir(json_dir) if f.endswith('.json')]
            
            if not json_files:
                raise Exception("JSON dizininde şablon dosyası bulunamadı")
            
            # JSON dosyasını ID'ye göre seç
            selected_file = json_files[json_file_id - 1] if 0 < json_file_id <= len(json_files) else json_files[0]
            template_path = os.path.join(json_dir, selected_file)
            
            if not os.path.exists(template_path):
                raise Exception(f"Seçilen JSON şablonu bulunamadı: {template_path}")
            
            with open(template_path, 'r', encoding='utf-8') as f:
                return json.load(f)
            
        except Exception as e:
            print(f"Template yükleme hatası: {str(e)}")
            raise
    
    def _load_variables(self):
        """Değişken dosyasını yükle ve parse et"""
        try:
            variables = {}
            variable_path = os.path.join("/app/data/input/Variables", "variables.txt")
            
            with open(variable_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
                for line in lines:
                    line = line.strip()
                    if not line or '=' not in line:
                        continue
                    
                    path, value = line.split('=', 1)
                    path = path.strip()
                    value = value.strip()
                    
                    if '{{' in value and '}}' in value:
                        variables[path] = value
            
            print(f"Yüklenen değişkenler: {variables}")
            return variables
            
        except Exception as e:
            print(f"Değişken dosyası yükleme hatası: {str(e)}")
            return {}
    
    def _analyze_json_structure(self):
        """JSON yapısını analiz et ve alan tiplerini çıkar"""
        structure = {}
        
        def analyze_value(value, path=""):
            if isinstance(value, dict):
                for key, val in value.items():
                    new_path = f"{path}.{key}" if path else key
                    if new_path in self.variables:
                        structure[new_path] = {
                            'type': 'variable',
                            'json_field': new_path,
                            'value': self.variables[new_path],
                            'embeddings': self._get_field_embeddings(key)
                        }
                    else:
                        structure[new_path] = {
                            'type': type(val).__name__,
                            'json_field': new_path,
                            'sample': val,
                            'embeddings': self._get_field_embeddings(key)
                        }
                    analyze_value(val, new_path)
            elif isinstance(value, list) and value:
                analyze_value(value[0], f"{path}[0]")
                
        analyze_value(self.template_json)
        return structure

    def _schema_path_types(self):
        return {
            path: info.get("type")
            for path, info in (self.json_structure or {}).items()
        }
    
    def _get_field_embeddings(self, text):
        """Metin için embedding vektörü oluştur"""
        try:
            if not text:
                return None
            return self.sentence_model.encode(text, convert_to_numpy=True)
        except Exception as e:
            print(f"Embedding oluşturma hatası: {str(e)}")
            return None
    
    def _split_camel_case(self, text):
        """CamelCase metni kelimelere ayır"""
        words = []
        current_word = text[0]
        
        for char in text[1:]:
            if char.isupper():
                words.append(current_word.lower())
                current_word = char
            else:
                current_word += char
        words.append(current_word.lower())
        return " ".join(words)
    
    def _analyze_scenario_line(self, line):
        """Test senaryosunu analiz et"""
        try:
            tr_text = line.split("(")[0].strip()
            en_text = line[line.index("(")+1:line.index(")")].strip() if "(" in line else ""
            
            is_required = (
                "zorunludur" in line.lower() or 
                "doldurulması zorunludur" in line.lower()
            )
            
            # Tipi belirlemek için basit kontrol (geliştirilebilir)
            field_type = None
            lower_line = line.lower()
            if "tarih" in lower_line or "date" in en_text.lower():
                field_type = "date"
            elif "sayısal" in lower_line or "numeric" in en_text.lower():
                field_type = "numeric"
            elif "metin" in lower_line or "text" in en_text.lower():
                field_type = "text"
            
            max_length = None
            # "maksimum X karakterli" ifadesinden max_length çekme
            # Satırda "maksimum" ve "karakterli" geçiyorsa aradaki rakamları al.
            if "maksimum" in lower_line and "karakterli" in lower_line:
                try:
                    segment = line.lower().split("maksimum")[1].split("karakterli")[0]
                    max_length = int(''.join(filter(str.isdigit, segment)))
                except:
                    pass
                
            print(f"\nSenaryo Analizi:")
            print(f"TR Metin: {tr_text}")
            print(f"EN Alan: {en_text}")
            print(f"Zorunlu: {is_required}")
            print(f"Tip: {field_type}")
            print(f"Max Uzunluk: {max_length}")
            
            return {
                "tr_text": tr_text,
                "en_text": en_text,
                "is_required": is_required,
                "field_type": field_type,
                "max_length": max_length
            }
            
        except Exception as e:
            print(f"Senaryo analiz hatası: {str(e)}")
            return None
    
    def _find_matching_json_field(self, analysis):
        """JSON alanını NER veya embedding benzerliğiyle eşleştir"""
        try:
            if not analysis or not analysis.get('en_text'):
                return None
            
            en_text = analysis['en_text'].strip()
            if not en_text:
                return None
            
            # En_text için embedding al
            en_emb = self.sentence_model.encode(en_text)
            if not isinstance(en_emb, np.ndarray):
                en_emb = np.array(en_emb)
            
            best_match = None
            best_score = -1
            
            # json_structure içindeki her alanın embeddings'i ile benzerlik ölç
            for field_path, info in self.json_structure.items():
                if info['embeddings'] is not None:
                    field_emb = info['embeddings']
                    if not isinstance(field_emb, np.ndarray):
                        field_emb = np.array(field_emb)
                    
                    # Vektörleri normalize et
                    en_emb_norm = en_emb / np.linalg.norm(en_emb)
                    field_emb_norm = field_emb / np.linalg.norm(field_emb)
                    
                    # Kosinüs benzerliğini hesapla
                    sim = np.dot(en_emb_norm, field_emb_norm)
                    
                    if sim > best_score:
                        best_score = sim
                        best_match = field_path
            
            if best_match:
                print(f"Eşleşen alan bulundu: {en_text} -> {best_match} (Benzerlik: {best_score})")
                return best_match
            else:
                print(f"Eşleşen alan bulunamadı: {en_text}")
                return None
            
        except Exception as e:
            print(f"Alan eşleştirme hatası: {str(e)}")
            return None

    def _resolve_target_path(self, requested_path, analysis=None):
        if not requested_path:
            return requested_path
        field_context = {
            "json_field": requested_path,
            "field_name_tr": (analysis or {}).get("tr_text"),
            "field_name_en": (analysis or {}).get("en_text"),
            "field_type": (analysis or {}).get("field_type"),
            "semantic_tags": (analysis or {}).get("semantic_tags") or derive_domain_tags(
                (analysis or {}).get("tr_text", ""),
                (analysis or {}).get("en_text", ""),
                (analysis or {}).get("field_type", ""),
                "",
            ),
        }
        return resolve_target_leaf_path(
            requested_path,
            list((self.json_structure or {}).keys()),
            self._schema_path_types(),
            field_context,
        )

    def _build_field_context(self, field_path, field_info):
        analysis = field_info.get("analysis", {})
        field_type = resolve_preferred_field_type(
            field_info.get("type") or analysis.get("field_type"),
            self._schema_path_types().get(field_path),
        )
        field_name_tr = analysis.get("tr_text", field_path.split(".")[-1])
        field_name_en = analysis.get("en_text", field_path.split(".")[-1])
        semantic_tags = analysis.get("semantic_tags") or field_info.get("semantic_tags") or derive_domain_tags(
            field_name_tr,
            field_name_en,
            field_type,
            "",
        )
        pattern = field_info.get("pattern") or detect_domain_pattern(
            field_name_tr,
            field_name_en,
            field_type,
            "",
        )
        return {
            "json_field": field_path,
            "field_name_tr": field_name_tr,
            "field_name_en": field_name_en,
            "field_type": field_type,
            "schema_type": self._schema_path_types().get(field_path),
            "semantic_tags": semantic_tags,
            "pattern": pattern,
            "enum_values": field_info.get("enum_values", []),
            "max_length": field_info.get("max_length"),
        }
    
    def generate_bsc_test(self, scenario_path, test_name, json_file_id):
        """BSC test senaryosu oluştur"""
        try:
            print(f"\nTest senaryosu okunuyor: {scenario_path}")
            
            if not os.path.exists(scenario_path):
                raise Exception(f"Senaryo dosyası bulunamadı: {scenario_path}")
            
            # JSON şablonunu yükle
            self.template_json = self._load_template(json_file_id)
            self.variables = self._load_variables()
            self.json_structure = self._analyze_json_structure()
            self.mandatory_fields = {}
            
            with open(scenario_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            print(f"Toplam {len(lines)} satır okundu.")
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                analysis = self._analyze_scenario_line(line)
                if not analysis:
                    continue
                
                if analysis['is_required']:
                    json_field = self._find_matching_json_field(analysis)
                    
                    if json_field:
                        target_path = self._resolve_target_path(json_field, analysis)
                        self.mandatory_fields[target_path] = {
                            'json_field': target_path,
                            'analysis': {
                                **analysis,
                                'semantic_tags': derive_domain_tags(
                                    analysis.get('tr_text', ''),
                                    analysis.get('en_text', ''),
                                    analysis.get('field_type', ''),
                                    '',
                                ),
                            },
                            'type': resolve_preferred_field_type(
                                analysis['field_type'] or 'text',
                                self._schema_path_types().get(target_path),
                            ),
                            'max_length': analysis['max_length'],
                            'pattern': detect_domain_pattern(
                                analysis.get('tr_text', ''),
                                analysis.get('en_text', ''),
                                analysis.get('field_type', ''),
                                '',
                            ),
                        }
                        print(f"Zorunlu alan belirlendi: {target_path}")
            
            test_case = self._create_test_case()
            if test_case:
                output_path = self._save_test_case(test_case, test_name)
                test_case["file_path"] = output_path
            
            print(f"\nZorunlu alan sayısı: {len(self.mandatory_fields)}")
            return test_case
            
        except Exception as e:
            print(f"BSC test oluşturma hatası: {str(e)}")
            raise
    
    def _create_test_case(self):
        """Test case oluştur"""
        try:
            test_data = self._create_null_data(self.template_json)
            
            for var_path, var_value in self.variables.items():
                parts = var_path.split('.')
                current = test_data
                for part in parts[:-1]:
                    if part not in current:
                        current[part] = {}
                    current = current[part]
                current[parts[-1]] = var_value
            
            for field, field_info in self.mandatory_fields.items():
                if field not in self.variables:
                    value = self._generate_value_by_type(field_info, field)
                    if value is not None:
                        self._set_nested_value(test_data, field, value)
            
            # lineList içi örnek atama
            if "lineList" in test_data:
                if not test_data["lineList"]:
                    test_data["lineList"] = [{}]
                
                test_data["lineList"][0].update({
                    "cardType": "STOCK_CARD",
                    "quantity": 1,
                    "unitPrice": 100,
                    "currencyExchangeRateItem": 1,
                    "vatRate": {
                        "id": "18",
                        "ratio": {
                            "denominator": 100,
                            "numerator": 18
                        }
                    }
                })
            
            return {
                "scenario_type": "BSC",
                "description": "Zorunlu alanların doldurulduğu başarılı senaryo",
                "test_data": test_data,
                "expected_result": "SUCCESS"
            }
            
        except Exception as e:
            print(f"Test case oluşturma hatası: {str(e)}")
            return None

    def _create_null_data(self, template):
        if isinstance(template, dict):
            return {k: self._create_null_data(v) if isinstance(v, (dict, list)) else None 
                   for k, v in template.items()}
        elif isinstance(template, list):
            if template:
                return [self._create_null_data(template[0])]
            return []
        return None

    def _generate_value_by_type(self, field_info, field_path=None):
        field_path = str(field_path or field_info.get('json_field', ''))
        
        try:
            if field_info.get('type') == 'variable':
                return field_info.get('sample')
            
            if field_path in self.variables:
                return self.variables[field_path]
            return build_valid_value(self._build_field_context(field_path, field_info))
            
        except Exception as e:
            print(f"Değer üretme hatası ({field_path}): {str(e)}")
            return "test_value"
    
    def _set_nested_value(self, data, field_path, value):
        try:
            if field_path in self.variables:
                parts = field_path.split('.')
                current = data
                for part in parts[:-1]:
                    if part not in current:
                        current[part] = {}
                    current = current[part]
                last_part = parts[-1]
                current[last_part] = self.variables[field_path]
                return

            if "lineList[" in field_path:
                parts = field_path.split(".")
                current = data
                for part in parts:
                    if "[" in part:
                        list_name = part.split("[")[0]
                        index = int(part.split("[")[1].split("]")[0])
                        if list_name not in current:
                            current[list_name] = []
                        while len(current[list_name]) <= index:
                            current[list_name].append({})
                        current = current[list_name][index]
                    else:
                        if part not in current:
                            current[part] = {}
                        current = current[part]
            else:
                parts = field_path.split('.')
                current = data
                for part in parts[:-1]:
                    if part not in current:
                        current[part] = {}
                    current = current[part]
                current[parts[-1]] = value
                
        except Exception as e:
            print(f"Değer atama hatası ({field_path}): {str(e)}")
    
    def _save_test_case(self, test_case, test_name):
        """Test case'i kaydet"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_dir = os.path.join("/app/data/output/test_cases", test_name, "bsc")
            os.makedirs(output_dir, exist_ok=True)
            
            output_file = f"bsc_test_{timestamp}.json"
            output_path = os.path.join(output_dir, output_file)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(test_case, f, indent=2, ensure_ascii=False)
            
            print(f"Test case kaydedildi: {output_path}")
            return output_path
            
        except Exception as e:
            print(f"Test case kaydetme hatası: {str(e)}")
            raise

    def generate_bsc_test_with_variables(self, scenario_path, test_name, json_file_id, selected_variables=None):
        """Seçilen variables ile BSC test senaryosu oluştur"""
        try:
            print(f"\nTest senaryosu okunuyor: {scenario_path}")
            print(f"Seçilen variables: {selected_variables}")
            
            if not os.path.exists(scenario_path):
                raise Exception(f"Senaryo dosyası bulunamadı: {scenario_path}")
            
            # JSON şablonunu yükle
            self.template_json = self._load_template(json_file_id)
            
            # Seçilen variables'ı kullan, yoksa tüm variables'ı yükle
            if selected_variables:
                self.variables = {}
                all_variables = self._load_variables()
                for var_path in selected_variables:
                    if var_path in all_variables:
                        self.variables[var_path] = all_variables[var_path]
                print(f"Seçilen {len(self.variables)} değişken kullanılıyor")
            else:
                self.variables = self._load_variables()
                print(f"Tüm {len(self.variables)} değişken kullanılıyor")
            
            self.json_structure = self._analyze_json_structure()
            self.mandatory_fields = {}
            
            with open(scenario_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            print(f"Toplam {len(lines)} satır okundu.")
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                analysis = self._analyze_scenario_line(line)
                if not analysis:
                    continue
                
                if analysis['is_required']:
                    json_field = self._find_matching_json_field(analysis)
                    
                    if json_field:
                        target_path = self._resolve_target_path(json_field, analysis)
                        self.mandatory_fields[target_path] = {
                            'json_field': target_path,
                            'analysis': {
                                **analysis,
                                'semantic_tags': derive_domain_tags(
                                    analysis.get('tr_text', ''),
                                    analysis.get('en_text', ''),
                                    analysis.get('field_type', ''),
                                    '',
                                ),
                            },
                            'type': resolve_preferred_field_type(
                                analysis['field_type'] or 'text',
                                self._schema_path_types().get(target_path),
                            ),
                            'max_length': analysis['max_length'],
                            'pattern': detect_domain_pattern(
                                analysis.get('tr_text', ''),
                                analysis.get('en_text', ''),
                                analysis.get('field_type', ''),
                                '',
                            ),
                        }
                        print(f"Zorunlu alan belirlendi: {target_path}")
            
            test_case = self._create_test_case()
            if test_case:
                output_path = self._save_test_case(test_case, test_name)
                test_case["file_path"] = output_path
            
            print(f"\nZorunlu alan sayısı: {len(self.mandatory_fields)}")
            return test_case
            
        except Exception as e:
            print(f"BSC test oluşturma hatası: {str(e)}")
            raise
