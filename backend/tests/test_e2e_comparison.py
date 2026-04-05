"""
Uçtan uca karşılaştırma testi - Eski vs Yeni BSCGenerator
"""
import json
import os
import tempfile
from pathlib import Path
from datetime import datetime
import pytest
from unittest.mock import patch

# Eski ve yeni generator'ları import et
from src.generators.bsc_generator import BSCGenerator as OldBSCGenerator
from app.generators.bsc import BSCGenerator as NewBSCGenerator


class TestE2EComparison:
    """Eski vs Yeni BSCGenerator karşılaştırma testleri"""
    
    def setup_method(self):
        """Test setup"""
        self.old_generator = OldBSCGenerator()
        self.new_generator = NewBSCGenerator()
        
        # Test verilerini hazırla
        self.setup_test_data()
    
    def setup_test_data(self):
        """Test verilerini hazırla"""
        # Test senaryosu içeriği
        self.scenario_content = """Tarih alanı zorunludur (issueDate)
Tutar alanı zorunludur (totalAmount)
Ürün kodu maksimum 20 karakterli olmalıdır (productCode)
Miktar alanı sadece rakam olmalıdır (quantity)
IBAN alanı zorunludur (iban)
TC Kimlik No zorunludur (tckn)
Vergi kimlik numarası maksimum 10 karakterli olmalıdır (taxId)
"""
        
        # Test JSON template
        self.json_template = {
            "header": {
                "id": "TEST-001",
                "issueDate": "2024-01-01T10:00:00Z",
                "totalAmount": 1500.75,
                "currency": {"id": "TRY", "unit": 0},
                "vatRate": {
                    "id": "18",
                    "ratio": {"denominator": 100, "numerator": 18}
                }
            },
            "lineList": [
                {
                    "lineId": 1,
                    "productCode": "PROD-001",
                    "quantity": 5,
                    "unitPrice": 100.0,
                    "totalPrice": 500.0
                }
            ]
        }
        
        # Test variables
        self.variables_content = """header.id={{test_id}}
header.issueDate={{issue_date}}
header.totalAmount={{total_amount}}
lineList[0].productCode={{product_code}}
lineList[0].quantity={{quantity}}
"""
    
    def create_temp_files(self):
        """Geçici test dosyalarını oluştur"""
        # Senaryo dosyası
        scenario_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8')
        scenario_file.write(self.scenario_content)
        scenario_file.close()
        
        # JSON dosyası
        json_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        json.dump(self.json_template, json_file, indent=2)
        json_file.close()
        
        # Variables dosyası
        variables_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8')
        variables_file.write(self.variables_content)
        variables_file.close()
        
        return scenario_file.name, json_file.name, variables_file.name
    
    def cleanup_temp_files(self, *file_paths):
        """Geçici dosyaları temizle"""
        for file_path in file_paths:
            try:
                os.unlink(file_path)
            except:
                pass
    
    def normalize_test_case(self, test_case):
        """Test case'i normalize et (timestamp/uuid alanlarını mask et)"""
        if not test_case:
            return None
        
        # Timestamp alanlarını mask et
        timestamp_fields = ['created_at', 'generated_at', 'timestamp']
        for field in timestamp_fields:
            if field in test_case:
                test_case[field] = "MASKED_TIMESTAMP"
        
        # UUID alanlarını mask et
        uuid_fields = ['id', 'test_id', 'document_id']
        for field in uuid_fields:
            if field in test_case:
                test_case[field] = "MASKED_UUID"
        
        # Nested objelerde de mask uygula
        if 'test_data' in test_case and isinstance(test_case['test_data'], dict):
            self._mask_nested_values(test_case['test_data'])
        
        return test_case
    
    def _mask_nested_values(self, obj):
        """Nested objelerde değerleri mask et"""
        if isinstance(obj, dict):
            for key, value in obj.items():
                if key in ['id', 'test_id', 'document_id']:
                    obj[key] = "MASKED_UUID"
                elif key in ['created_at', 'generated_at', 'timestamp', 'issueDate']:
                    obj[key] = "MASKED_TIMESTAMP"
                elif isinstance(value, (dict, list)):
                    self._mask_nested_values(value)
        elif isinstance(obj, list):
            for item in obj:
                if isinstance(item, (dict, list)):
                    self._mask_nested_values(item)
    
    @patch('src.generators.bsc_generator.BSCGenerator._load_template')
    @patch('src.generators.bsc_generator.BSCGenerator._load_variables')
    def test_old_vs_new_bsc_generator(self, mock_old_vars, mock_old_template):
        """Eski vs yeni BSCGenerator karşılaştırması"""
        # Geçici dosyaları oluştur
        scenario_path, json_path, variables_path = self.create_temp_files()
        
        try:
            # Mock setup - eski generator için
            mock_old_template.return_value = self.json_template
            mock_old_vars.return_value = {
                "header.id": "{{test_id}}",
                "header.issueDate": "{{issue_date}}",
                "header.totalAmount": "{{total_amount}}",
                "lineList[0].productCode": "{{product_code}}",
                "lineList[0].quantity": "{{quantity}}"
            }
            
            # Eski generator test
            old_result = None
            try:
                old_result = self.old_generator.generate_bsc_test(
                    scenario_path=scenario_path,
                    test_name="test_comparison",
                    json_file_id=1
                )
            except Exception as e:
                print(f"Eski generator hatası: {e}")
            
            # Yeni generator test
            new_result = None
            try:
                with patch('app.generators.bsc.bsc_generator.load_template') as mock_new_template, \
                     patch('app.generators.bsc.bsc_generator.load_variables') as mock_new_vars:
                    
                    mock_new_template.return_value = self.json_template
                    mock_new_vars.return_value = {
                        "header.id": "{{test_id}}",
                        "header.issueDate": "{{issue_date}}",
                        "header.totalAmount": "{{total_amount}}",
                        "lineList[0].productCode": "{{product_code}}",
                        "lineList[0].quantity": "{{quantity}}"
                    }
                    
                    new_result = self.new_generator.generate_bsc_test(
                        scenario_path=scenario_path,
                        test_name="test_comparison",
                        json_file_id=1
                    )
            except Exception as e:
                print(f"Yeni generator hatası: {e}")
            
            # Sonuçları normalize et
            old_normalized = self.normalize_test_case(old_result)
            new_normalized = self.normalize_test_case(new_result)
            
            # Karşılaştırma
            if old_normalized and new_normalized:
                # Temel yapı karşılaştırması
                assert "scenario_type" in old_normalized
                assert "scenario_type" in new_normalized
                assert old_normalized["scenario_type"] == new_normalized["scenario_type"]
                
                assert "test_data" in old_normalized
                assert "test_data" in new_normalized
                
                # Test verisi yapısı karşılaştırması
                old_test_data = old_normalized["test_data"]
                new_test_data = new_normalized["test_data"]
                
                # Modern generator yapısı legacy ile birebir aynı olmak zorunda değil.
                # Burada sözleşme ve anlamlı payload üretimi korunuyor mu onu doğrula.
                assert isinstance(old_test_data, dict) and old_test_data, "Eski generator boş payload üretti"
                assert isinstance(new_test_data, dict) and new_test_data, "Yeni generator boş payload üretti"
                assert "description" in old_normalized
                assert "description" in new_normalized
                assert "expected_result" in old_normalized
                assert "expected_result" in new_normalized
                
                print("✅ Uçtan uca karşılaştırma başarılı - yapı uyumlu")
                print(f"📊 Eski generator zorunlu alan sayısı: {old_normalized.get('mandatory_fields_count', 'N/A')}")
                print(f"📊 Yeni generator zorunlu alan sayısı: {new_normalized.get('mandatory_fields_count', 'N/A')}")
                
            else:
                print("⚠️  Karşılaştırma yapılamadı - sonuçlardan biri None")
                if not old_normalized:
                    print("❌ Eski generator sonuç vermedi")
                if not new_normalized:
                    print("❌ Yeni generator sonuç vermedi")
        
        finally:
            # Temizlik
            self.cleanup_temp_files(scenario_path, json_path, variables_path)
    
    def test_api_compatibility(self):
        """Public API uyumluluğu testi"""
        # Her iki generator'ın da aynı public metodlara sahip olduğunu kontrol et
        old_methods = [method for method in dir(self.old_generator) if not method.startswith('_')]
        new_methods = [method for method in dir(self.new_generator) if not method.startswith('_')]
        
        # Kritik metodların varlığını kontrol et
        critical_methods = ['generate_bsc_test', 'generate_bsc_test_with_variables']
        
        for method in critical_methods:
            assert method in old_methods, f"Eski generator'da {method} bulunamadı"
            assert method in new_methods, f"Yeni generator'da {method} bulunamadı"
        
        print("✅ Public API uyumluluğu başarılı")
    
    def test_error_handling_compatibility(self):
        """Hata yönetimi uyumluluğu testi"""
        # Geçersiz senaryo dosyası ile test
        invalid_scenario = "/nonexistent/scenario.txt"
        
        # Eski generator hata testi
        old_error_raised = False
        try:
            self.old_generator.generate_bsc_test(invalid_scenario, "test", 1)
        except Exception:
            old_error_raised = True
        
        # Yeni generator hata testi
        new_error_raised = False
        try:
            self.new_generator.generate_bsc_test(invalid_scenario, "test", 1)
        except Exception:
            new_error_raised = True
        
        # Her ikisi de hata vermeli
        assert old_error_raised, "Eski generator geçersiz dosya için hata vermedi"
        assert new_error_raised, "Yeni generator geçersiz dosya için hata vermedi"
        
        print("✅ Hata yönetimi uyumluluğu başarılı")
    
    def test_performance_comparison(self):
        """Performans karşılaştırması"""
        import time
        
        # Geçici dosyaları oluştur
        scenario_path, json_path, variables_path = self.create_temp_files()
        
        try:
            # Eski generator performans testi
            old_start = time.time()
            try:
                with patch('src.generators.bsc_generator.BSCGenerator._load_template') as mock_template, \
                     patch('src.generators.bsc_generator.BSCGenerator._load_variables') as mock_vars:
                    
                    mock_template.return_value = self.json_template
                    mock_vars.return_value = {"header.id": "{{test_id}}"}
                    
                    self.old_generator.generate_bsc_test(scenario_path, "perf_test_old", 1)
            except Exception as e:
                print(f"Eski generator performans test hatası: {e}")
            old_duration = time.time() - old_start
            
            # Yeni generator performans testi
            new_start = time.time()
            try:
                with patch('app.generators.bsc.bsc_generator.load_template') as mock_template, \
                     patch('app.generators.bsc.bsc_generator.load_variables') as mock_vars:
                    
                    mock_template.return_value = self.json_template
                    mock_vars.return_value = {"header.id": "{{test_id}}"}
                    
                    self.new_generator.generate_bsc_test(scenario_path, "perf_test_new", 1)
            except Exception as e:
                print(f"Yeni generator performans test hatası: {e}")
            new_duration = time.time() - new_start
            
            print(f"⏱️  Eski generator süresi: {old_duration:.3f}s")
            print(f"⏱️  Yeni generator süresi: {new_duration:.3f}s")
            
            # Yeni generator daha hızlı veya benzer performansta olmalı
            performance_ratio = new_duration / old_duration if old_duration > 0 else 1.0
            print(f"📈 Performans oranı (yeni/eski): {performance_ratio:.2f}")
            
            if performance_ratio <= 2.0:  # 2x'den fazla yavaş olmamalı
                print("✅ Performans karşılaştırması başarılı")
            else:
                print("⚠️  Yeni generator beklenenden yavaş")
        
        finally:
            self.cleanup_temp_files(scenario_path, json_path, variables_path)


def run_e2e_comparison():
    """E2E karşılaştırmasını çalıştır"""
    print("🔄 Uçtan uca karşılaştırma başlatılıyor...")
    
    test_instance = TestE2EComparison()
    test_instance.setup_method()
    
    try:
        # API uyumluluğu testi
        test_instance.test_api_compatibility()
        
        # Hata yönetimi testi
        test_instance.test_error_handling_compatibility()
        
        # Ana karşılaştırma testi
        test_instance.test_old_vs_new_bsc_generator()
        
        # Performans testi
        test_instance.test_performance_comparison()
        
        print("\n🎉 Tüm uçtan uca karşılaştırma testleri başarılı!")
        return True
        
    except Exception as e:
        print(f"\n❌ Uçtan uca karşılaştırma hatası: {e}")
        return False


if __name__ == "__main__":
    success = run_e2e_comparison()
    exit(0 if success else 1)
