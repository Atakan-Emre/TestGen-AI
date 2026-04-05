import pandas as pd
from datetime import datetime
from ..utils.file_handler import save_test_scenarios
from ..config.settings import INPUT_PATH, OUTPUT_PATH

class BertNerGenerator:
    def __init__(self):
        self.model_name = "dslim/bert-large-NER"
        
    def generate_test_scenarios(self, input_file="table_1.csv"):
        """Test senaryolarını oluşturur"""
        try:
            # CSV dosyasını oku
            df = pd.read_csv(f"{INPUT_PATH}/{input_file}", encoding='utf-8', sep=',', header=1)
            df = df.set_index(df.columns[0])
            
            test_scenarios = []
            
            print("Test senaryoları oluşturuluyor...")
            
            # Her alan için test senaryoları oluştur
            for alan_adi, row in df.iterrows():
                try:
                    ing_adi = row.get('Alan adı (İng)', '')
                    tip = str(row.get('Tip', ''))
                    boyut = str(row.get('Boyut', ''))
                    zorunluluk = str(row.get('Zorunlu mu?', '')).lower()
                    
                    # Test senaryoları oluşturma
                    scenarios = self._create_scenarios(alan_adi, ing_adi, tip, boyut, zorunluluk)
                    test_scenarios.extend(scenarios)
                    
                except Exception as e:
                    print(f"Alan işleme hatası ({alan_adi}): {str(e)}")
            
            # Senaryoları kaydet
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            save_test_scenarios(test_scenarios, timestamp)
            
            return test_scenarios
            
        except Exception as e:
            print(f"CSV okuma hatası: {str(e)}")
            return []
            
    def _create_scenarios(self, alan_adi, ing_adi, tip, boyut, zorunluluk):
        """Belirli bir alan için test senaryolarını oluşturur"""
        scenarios = []
        
        # Boyut kontrolü
        if boyut.strip() and 'nan' not in boyut.lower():
            if 'max' in boyut.lower():
                boyut = boyut.lower().replace('max', '').strip()
            scenarios.append(f"{alan_adi} ({ing_adi}) alanı maksimum {boyut} karakterli olmalıdır.")
        
        # Tip kontrolleri
        if 'date' in tip.lower():
            scenarios.append(f"{alan_adi} ({ing_adi}) alanı geçerli bir tarih formatında olmalıdır.")
        elif 'numeric' in tip.lower():
            scenarios.append(f"{alan_adi} ({ing_adi}) alanına sadece sayısal değer girilebilir.")
        elif 'string' in tip.lower() or 'alfenumerik' in tip.lower():
            scenarios.append(f"{alan_adi} ({ing_adi}) alanına sadece metin girişi yapılabilir.")
        
        # Zorunluluk kontrolü
        if 'zorunlu' in zorunluluk:
            scenarios.append(f"{alan_adi} ({ing_adi}) alanı doldurulması zorunludur.")
        else:
            scenarios.append(f"{alan_adi} ({ing_adi}) alanı opsiyoneldir.")
            
        return scenarios 