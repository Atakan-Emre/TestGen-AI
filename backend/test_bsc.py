import json
import os
from app.generators.bsc import BSCGenerator

def test_bsc_generator():
    # BSC Generator'ı başlat
    bsc_gen = BSCGenerator()
    
    # Test senaryosunu oku
    with open('data/output/test_scenarios/test1_20241225_190816.txt', 'r', encoding='utf-8') as f:
        scenario_content = f.read()
    
    # JSON örneğini oku
    with open('data/input/Json/example.json', 'r', encoding='utf-8') as f:
        json_data = json.load(f)
        
    # Variables dosyasını oku
    with open('data/input/Variables/variables.txt', 'r', encoding='utf-8') as f:
        variables_content = f.read()
    
    # Test senaryosu dosyasını oluştur
    test_scenario_path = 'data/output/test_scenarios/test_scenario.txt'
    with open(test_scenario_path, 'w', encoding='utf-8') as f:
        f.write(scenario_content)
    
    # BSC testlerini oluştur
    print("\nBSC test senaryoları oluşturuluyor...")
    try:
        test_case = bsc_gen.generate_bsc_test(test_scenario_path)
        
        if test_case:
            print("\nOluşturulan Test Senaryosu:")
            print("-" * 50)
            print(f"Senaryo Tipi: {test_case['scenario_type']}")
            print(f"Açıklama: {test_case['description']}")
            print(f"Beklenen Sonuç: {test_case['expected_result']}")
            print(f"Test Verisi:")
            print(json.dumps(test_case['test_data'], indent=2, ensure_ascii=False))
            print("-" * 50)
        else:
            print("Test senaryosu oluşturulamadı.")
            
    except Exception as e:
        print(f"Hata oluştu: {str(e)}")

if __name__ == "__main__":
    test_bsc_generator() 