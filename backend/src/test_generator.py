from generators.bert_ner_generator import BertNerGenerator

def test_generator():
    try:
        # Generator'ı başlat
        print("BERT Generator başlatılıyor...")
        generator = BertNerGenerator()
        
        # Test için CSV dosyası ve senaryo adı
        input_file = "table_1.csv"
        scenario_name = "deneme"
        
        print(f"CSV dosyası: {input_file}")
        print(f"Senaryo adı: {scenario_name}")
        
        # Senaryoları oluştur
        scenarios = generator.generate_scenarios(input_file, scenario_name)
        
        print("\nOluşturulan senaryolar:")
        for i, scenario in enumerate(scenarios, 1):
            print(f"{i}. {scenario}")
            
        print("\nTest başarılı!")
        
    except Exception as e:
        print(f"Test sırasında hata oluştu: {str(e)}")

if __name__ == "__main__":
    test_generator() 