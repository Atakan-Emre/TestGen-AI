import json
from pathlib import Path
from datetime import datetime

def save_test_scenarios(scenarios: list, output_dir: str = "data/output/test_scenarios") -> str:
    try:
        # Çıktı dizinini oluştur
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Dosya adı oluştur
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"scenarios_{timestamp}.json"
        file_path = output_path / filename

        # Senaryoları JSON olarak kaydet
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(scenarios, f, indent=2, ensure_ascii=False)

        return str(file_path)

    except Exception as e:
        raise Exception(f"Senaryo kaydetme hatası: {str(e)}") 