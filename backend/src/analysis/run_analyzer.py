from test_scenario_analyzer import TestScenarioAnalyzer
from pattern_learner import PatternLearner
from field_analyzer import FieldAnalyzer
import logging
from pathlib import Path

# Log klasörü oluştur
log_dir = Path("data/output/analysis")
log_dir.mkdir(parents=True, exist_ok=True)

# Logging ayarları
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / 'analysis.log'),
        logging.StreamHandler()
    ]
)

def main():
    try:
        logging.info("Analiz başlatılıyor...")
        
        # Test Senaryo Analizi
        analyzer = TestScenarioAnalyzer()
        analyzer.load_data()
        logging.info("Veriler yüklendi")
        
        # Pattern Learner oluştur
        pattern_learner = PatternLearner()
        
        # Field Analyzer oluştur
        field_analyzer = FieldAnalyzer()
        field_analyzer.pattern_learner = pattern_learner
        
        # NER modelini eğit ve field analyzer'a ata
        training_examples = analyzer.train_field_analyzer()
        field_analyzer.ner_model = analyzer.nlp  # NER modelini field analyzer'a ata
        logging.info(f"{len(training_examples)} eğitim örneği oluşturuldu")
        
        # Pattern'leri öğren
        field_names = analyzer._get_field_names()
        json_paths = analyzer._get_json_paths(analyzer.json_template)
        pattern_learner.learn_patterns(field_names, json_paths, training_examples)
        logging.info("Pattern'ler öğrenildi")
        
        # Test senaryolarını analiz et
        results = analyzer.analyze_test_cases()
        logging.info(f"{len(results)} test senaryosu analiz edildi")
        
        # Her test senaryosu için alan eşleştirmelerini kontrol et
        for result in results:
            test_case = result["test_case"]
            error_msg = test_case.get("expected_message", "")
            
            if "Alan '" in error_msg:
                field_name = error_msg.split("'")[1]
                json_path = field_analyzer.analyze(
                    field_name, 
                    json_paths,
                    context=error_msg
                )
                if json_path:
                    logging.info(f"Alan eşleştirme: {field_name} -> {json_path}")
                    
                    # Eşleştirme sonucunu rapora ekle
                    result["field_mapping"] = {
                        "field_name": field_name,
                        "json_path": json_path,
                        "confidence": field_analyzer._calculate_similarity(field_name, json_path)
                    }
                else:
                    logging.warning(f"Eşleştirme bulunamadı: {field_name}")
                    result["field_mapping"] = None
        
        # Rapor oluştur
        report = analyzer.generate_report(results)
        logging.info("Rapor oluşturuldu")
        
        # Sonuçları göster
        print("\nAnaliz Sonuçları:")
        print(f"Toplam test senaryosu: {report['total_cases']}")
        print(f"Başarılı JSON yapısı: {report['valid_json']}")
        print(f"Başarılı senaryo: {report['valid_scenario']}")
        print(f"Başarılı hata mesajları: {report['valid_errors']}")
        
        # Öğrenilen pattern'leri göster
        print("\nÖğrenilen Pattern'ler:")
        for field, patterns in pattern_learner.patterns.items():
            print(f"{field}: {patterns}")
            
    except Exception as e:
        logging.error(f"Hata oluştu: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    main() 