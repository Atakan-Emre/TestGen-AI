import json
import pandas as pd
from pathlib import Path
import spacy
from spacy.tokens import DocBin
from spacy.training import Example
import random
from tqdm import tqdm

class TestScenarioAnalyzer:
    def __init__(self):
        # Gerekli modelleri yükle
        self.nlp = spacy.blank("tr")  # Türkçe boş model
        
        # Özel etiketleri tanımla
        self.labels = {
            "FIELD_NAME": "Alan adı",
            "FIELD_TYPE": "Alan tipi", 
            "VALIDATION": "Doğrulama kuralı",
            "ERROR_MESSAGE": "Hata mesajı",
            "JSON_PATH": "JSON yolu",
            "EXPECTED_VALUE": "Beklenen değer"
        }
        
    def load_data(self):
        """Veri kaynaklarını yükle"""
        # Pandas ayarları
        pd.set_option('display.max_columns', None)
        pd.set_option('display.max_rows', None)
        pd.set_option('display.width', None)
        
        # CSV'den alan tanımlarını oku
        self.fields_df = pd.read_csv("data/input/table_1.csv", encoding='utf-8')
        
        # Kolon isimlerini göster
        print("CSV kolonları:", self.fields_df.columns.tolist())
        
        # İlk satırı göster
        print("\nİlk satır:")
        print(self.fields_df.iloc[0].to_dict())
        
        # Zorunlu alanları göster
        zorunlu_kolon = 'Alım İade İrsaliyesi -\xa0Purchase Return Delivery Note.5'
        alan_adi_kolon = 'Alım İade İrsaliyesi -\xa0Purchase Return Delivery Note'
        zorunlu_alanlar = self.fields_df[
            self.fields_df[zorunlu_kolon] == "Zorunlu"
        ][alan_adi_kolon].tolist()
        print("\nZorunlu alanlar:", zorunlu_alanlar)
        
        # Test senaryolarını oku
        with open("data/output/test_scenarios/test_senaryolari_20241207_183129.txt", "r", encoding="utf-8") as f:
            self.scenarios = f.readlines()
            
        # Örnek JSON şablonunu oku
        with open("data/output/templates/example.json", "r", encoding="utf-8") as f:
            self.json_template = json.load(f)
            
        # Üretilen test senaryolarını oku
        self.test_cases = []
        ngi_path = Path("data/output/test_cases/ngi")
        for json_file in ngi_path.glob("*.json"):
            with open(json_file, "r", encoding="utf-8") as f:
                self.test_cases.append(json.load(f))
                
    def create_training_data(self):
        """Eğitim verisi oluştur"""
        training_data = []
        
        # Alan tanımlarından
        for _, row in self.fields_df.iterrows():
            # Doğru kolon ismini kullan
            field_name = row['Alım İade İrsaliyesi -\xa0Purchase Return Delivery Note']
            doc = self.nlp(str(field_name))
            ents = [(0, len(str(field_name)), "FIELD_NAME")]
            training_data.append((doc.text, {"entities": ents}))
            
        # Test senaryolarından
        for scenario in self.scenarios:
            doc = self.nlp(scenario)
            # Hata mesajlarını bul
            error_start = scenario.find("için geçersiz değer")
            if error_start != -1:
                ents = [(error_start, error_start + len("için geçersiz değer"), "ERROR_MESSAGE")]
                training_data.append((doc.text, {"entities": ents}))
                
        return training_data
        
    def train_ner(self, training_data, iterations=30):
        """NER modelini eğit"""
        # Yeni pipeline oluştur
        ner = self.nlp.add_pipe("ner")
        
        # Etiketleri ekle
        for label in self.labels.keys():
            ner.add_label(label)
            
        # Eğitim verilerini hazırla
        train_data = []
        for text, annotations in training_data:
            doc = self.nlp.make_doc(text)
            example = Example.from_dict(doc, annotations)
            train_data.append(example)
            
        # Modeli eğit
        optimizer = self.nlp.begin_training()
        for itn in range(iterations):
            random.shuffle(train_data)
            losses = {}
            
            for batch in spacy.util.minibatch(train_data, size=2):
                self.nlp.update(batch, drop=0.5, losses=losses)
                
            print(f"Iteration {itn}, Losses: {losses}")
            
    def analyze_test_cases(self):
        """Test senaryolarını analiz et"""
        results = []
        
        for test_case in self.test_cases:
            # JSON yapısını kontrol et
            json_validation = self._validate_json_structure(test_case)
            
            # Test senaryosu kurallarını kontrol et
            scenario_validation = self._validate_test_scenario(test_case)
            
            # Hata mesajlarını kontrol et
            error_validation = self._validate_error_messages(test_case)
            
            results.append({
                "test_case": test_case,  # Tüm test case'i gönder, sadece description değil
                "json_validation": json_validation,
                "scenario_validation": scenario_validation, 
                "error_validation": error_validation
            })
            
        return results
        
    def _get_json_paths(self, obj, parent_path="", paths=None):
        """JSON nesnesindeki tüm yolları al"""
        if paths is None:
            paths = set()
            
        if isinstance(obj, dict):
            for key, value in obj.items():
                current_path = f"{parent_path}.{key}" if parent_path else key
                paths.add(current_path)
                self._get_json_paths(value, current_path, paths)
                
        elif isinstance(obj, list) and obj:
            # Listenin ilk elemanını kontrol et
            self._get_json_paths(obj[0], f"{parent_path}[0]", paths)
            
        return paths
        
    def _validate_json_structure(self, test_case):
        """JSON yapısını kontrol et"""
        try:
            test_data = test_case.get("test_data", {})
            
            # JSON şablonundaki zorunlu alanları kontrol et
            required_fields = {
                "branchDocumentSeries": ["id"],
                "currencyDescription": ["id", "unit"],
                "lineList": [{
                    "cardType": None,
                    "quantity": None,
                    "unitOfMeasurement": {"id": None},
                    "vatRate": {"id": None, "ratio": {"numerator": None, "denominator": None}}
                }]
            }
            
            # Zorunlu alanları kontrol et
            missing = []
            for field, subfields in required_fields.items():
                if field not in test_data:
                    missing.append(field)
                elif isinstance(subfields, list) and isinstance(subfields[0], dict):
                    # Liste içindeki nesneleri kontrol et
                    if not test_data.get(field):
                        missing.append(f"{field}[0]")
                    else:
                        for item in test_data[field]:
                            for subfield, value in subfields[0].items():
                                if subfield not in item:
                                    missing.append(f"{field}[].{subfield}")
                                
            return {
                "valid": len(missing) == 0,
                "missing_keys": missing
            }
        except Exception as e:
            print(f"JSON doğrulama hatası: {str(e)}")
            return {"valid": False, "error": str(e)}
        
    def _get_required_fields(self):
        """Zorunlu alanların JSON yollarını al"""
        required_fields = set()
        
        # CSV'den zorunlu alanları al
        zorunlu_kolon = 'Alım İade İrsaliyesi -\xa0Purchase Return Delivery Note.5'
        alan_adi_kolon = 'Alım İade İrsaliyesi -\xa0Purchase Return Delivery Note'
        
        zorunlu_alanlar = self.fields_df[
            self.fields_df[zorunlu_kolon] == "Zorunlu"
        ][alan_adi_kolon].tolist()
        
        # JSON şablonunda bu alanların yollarını bul
        template_paths = self._get_json_paths(self.json_template)
        for field in zorunlu_alanlar:
            field_lower = field.lower()
            for path in template_paths:
                if field_lower in path.lower():
                    required_fields.add(path)
                    break
        
        return required_fields
        
    def _check_field_exists(self, test_case, field_name):
        """Test senaryosunda alanın var olup olmadığını kontrol et"""
        try:
            paths = self._get_json_paths(test_case)
            return any(field_name.lower() in path.lower() for path in paths)
        except Exception as e:
            print(f"Alan kontrol hatası: {str(e)}")
            return False
        
    def _validate_test_scenario(self, test_case):
        """Test senaryosu kurallarını kontrol et"""
        try:
            # Senaryo formatını kontrol et
            required_scenario_fields = {
                "scenario_type": ["NGI", "BSC", "OPT"],
                "description": str,
                "test_data": dict,
                "expected_result": ["SUCCESS", "VALIDATION_ERROR"],
                "expected_message": str
            }
            
            missing = []
            invalid = []
            
            for field, expected_type in required_scenario_fields.items():
                if field not in test_case:
                    missing.append(field)
                elif isinstance(expected_type, list):
                    if test_case[field] not in expected_type:
                        invalid.append(field)
                elif not isinstance(test_case[field], expected_type):
                    invalid.append(field)
                    
            return {
                "valid": len(missing) == 0 and len(invalid) == 0,
                "missing_fields": missing,
                "invalid_fields": invalid
            }
        except Exception as e:
            print(f"Senaryo doğrulama hatası: {str(e)}")
            return {"valid": False, "error": str(e)}
        
    def _validate_error_messages(self, test_case):
        """Hata mesajlarını kontrol et"""
        try:
            error_msg = test_case.get("expected_message", "")
            
            # Hata mesajı formatını kontrol et
            if not error_msg:
                return {"valid": False, "message": "Hata mesajı boş"}
            
            # Alan adı kontrolü
            if not error_msg.startswith("Alan '"):
                return {"valid": False, "message": "Hata mesajı 'Alan' ile başlamalı"}
            
            # Alan adı geçerli mi?
            field_name = error_msg.split("'")[1]
            if field_name not in self._get_field_names():
                return {"valid": False, "message": f"Geçersiz alan adı: {field_name}"}
            
            # Geçersiz değer formatı
            if "' için geçersiz değer" not in error_msg:
                return {"valid": False, "message": "Hata mesajı formatı yanlış"}
            
            # Değer kontrolü
            if ":" in error_msg:
                value = error_msg.split(":")[1].strip()
                if not self._validate_error_value(value):
                    return {"valid": False, "message": f"Geçersiz değer: {value}"}
                
            return {
                "valid": True,
                "message": error_msg
            }
        except Exception as e:
            print(f"Hata mesajı doğrulama hatası: {str(e)}")
            return {"valid": False, "error": str(e)}
        
    def generate_report(self, results):
        """Analiz sonuçlarını raporla"""
        report = {
            "total_cases": len(results),
            "valid_json": sum(1 for r in results if r["json_validation"]["valid"]),
            "valid_scenario": sum(1 for r in results if r["scenario_validation"]["valid"]),
            "valid_errors": sum(1 for r in results if r["error_validation"]["valid"]),
            "common_issues": self._get_common_issues(results)
        }
        
        return report
        
    def _get_common_issues(self, results):
        """Sık karşılaşılan hataları belirle"""
        issues = {
            "json_structure": {},
            "missing_fields": {},
            "error_messages": {}
        }
        
        for result in results:
            # JSON yapı hataları
            for key in result["json_validation"].get("missing_keys", []):
                issues["json_structure"][key] = issues["json_structure"].get(key, 0) + 1
                
            # Eksik zorunlu alanlar  
            for field in result["scenario_validation"].get("missing_required", []):
                issues["missing_fields"][field] = issues["missing_fields"].get(field, 0) + 1
                
            # Hatalı hata mesajları
            if not result["error_validation"]["valid"]:
                msg = result["error_validation"]["message"]
                issues["error_messages"][msg] = issues["error_messages"].get(msg, 0) + 1
                
        return issues
        
    def _generate_summary(self, results):
        """Özet rapor oluştur"""
        total = len(results)
        
        # Başarı kriterleri
        valid_json = sum(1 for r in results if r["json_validation"].get("valid", False))
        valid_scenario = sum(1 for r in results if r["scenario_validation"].get("valid", False))
        valid_errors = sum(1 for r in results if r["error_validation"].get("valid", False))
        
        # Hata dağılımı
        error_types = {}
        for r in results:
            if not r["error_validation"].get("valid", False):
                msg = r["error_validation"].get("message", "")
                error_types[msg] = error_types.get(msg, 0) + 1
                
        return {
            "total_cases": total,
            "success_rates": {
                "json": valid_json / total,
                "scenario": valid_scenario / total,
                "errors": valid_errors / total
            },
            "error_distribution": error_types
        }

    def _get_field_names(self):
        """CSV'den alan adlarını al"""
        alan_adi_kolon = 'Alım İade İrsaliyesi -\xa0Purchase Return Delivery Note'
        return self.fields_df[alan_adi_kolon].tolist()

    def _validate_error_value(self, value):
        """Hata mesajındaki değeri doğrula"""
        # Boş değer kontrolü
        if value == "":
            return True
        
        # Çok uzun metin kontrolü (255 karakter)
        if len(value) > 255:
            return False
        
        # Özel karakter kontrolü
        special_chars = set("!@#$%^&*()")
        if any(c in special_chars for c in value):
            return False
        
        # Sayısal değer kontrolü
        if value.replace("-", "").replace(".", "").isdigit():
            try:
                num = float(value)
                # Negatif değer kontrolü
                if num < 0:
                    return False
                # Çok büyük değer kontrolü
                if num > 999999999:
                    return False
            except ValueError:
                return False
            
        return True

    def train_field_analyzer(self):
        """Alan adları ve JSON yolları arasındaki ilişkiyi öğren"""
        # Eğitim verisi hazırla
        training_examples = []
        
        # CSV'den alan adlarını al
        field_names = self.fields_df['Alım İade İrsaliyesi -\xa0Purchase Return Delivery Note'].tolist()
        
        # JSON şablonundan yolları al
        json_paths = self._get_json_paths(self.json_template)
        
        # Test senaryolarından örnekler topla
        for test_case in self.test_cases:
            error_msg = test_case.get("expected_message", "")
            if "Alan '" in error_msg and "' için geçersiz değer" in error_msg:
                field = error_msg.split("'")[1]
                if field in field_names:
                    # JSON'daki karşılığını bul
                    for path in json_paths:
                        if self._is_matching_path(field, path):
                            training_examples.append({
                                "field_name": field,
                                "json_path": path,
                                "context": error_msg
                            })
        
        # NER modelini eğit
        self._train_ner_model(training_examples)
        
        return training_examples

    def _is_matching_path(self, field_name, json_path):
        """Alan adı ile JSON yolu eşleşiyor mu kontrol et"""
        # Kelime benzerliği
        field_tokens = set(field_name.lower().split())
        path_tokens = set(json_path.lower().split('.'))
        
        # Ortak kelime sayısı
        common_tokens = field_tokens.intersection(path_tokens)
        
        # Levenshtein mesafesi
        distance = self._levenshtein_distance(field_name.lower(), json_path.lower())
        
        # Eşleşme skoru
        score = (len(common_tokens) / max(len(field_tokens), len(path_tokens))) - (distance / max(len(field_name), len(json_path)))
        
        return score > 0.5  # Eşik değeri

    def _train_ner_model(self, examples):
        """NER modelini eğit"""
        # Eğitim verisi hazırla
        train_data = []
        for ex in examples:
            doc = self.nlp(ex["context"])
            ents = [(doc.text.find(ex["field_name"]), 
                    doc.text.find(ex["field_name"]) + len(ex["field_name"]), 
                    "FIELD")]
            train_data.append((doc.text, {"entities": ents}))
        
        # Modeli eğit
        ner = self.nlp.add_pipe("ner")
        for _, annotations in train_data:
            for ent in annotations.get("entities"):
                ner.add_label(ent[2])
                
        # Optimize et
        optimizer = self.nlp.begin_training()
        for _ in range(30):
            losses = {}
            random.shuffle(train_data)
            for text, annotations in train_data:
                self.nlp.update([text], [annotations], sgd=optimizer, losses=losses)

def main():
    analyzer = TestScenarioAnalyzer()
    
    # Verileri yükle
    analyzer.load_data()
    
    # Eğitim verisi oluştur
    training_data = analyzer.create_training_data()
    
    # NER modelini eğit
    analyzer.train_ner(training_data)
    
    # Test senaryolarını analiz et
    results = analyzer.analyze_test_cases()
    
    # Rapor oluştur
    report = analyzer.generate_report(results)
    
    # Raporu kaydet
    with open("data/output/analysis_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
        
if __name__ == "__main__":
    main() 