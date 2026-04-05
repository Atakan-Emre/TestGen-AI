from fastapi import APIRouter, HTTPException, UploadFile, File
from typing import List, Optional
from pydantic import BaseModel
from src.generators.bert_ner_generator import BertNerGenerator
from src.models.scenario import Scenario
from src.database import get_db
import os

router = APIRouter()
generator = BertNerGenerator()

class ScenarioGenerateRequest(BaseModel):
    name: str
    csv_file_id: int
    csv_file_name: str
    generator_type: str

@router.post("/generate")
async def generate_scenarios(request: ScenarioGenerateRequest):
    """Test senaryolarını oluşturur"""
    try:
        print(f"Senaryo oluşturma isteği alındı: {request}")
        
        # CSV dosyasının varlığını kontrol et
        csv_file_path = os.path.join("/app/data/input/Csv", request.csv_file_name)
        if not os.path.exists(csv_file_path):
            raise HTTPException(status_code=404, detail=f"CSV dosyası bulunamadı: {request.csv_file_name}")
            
        # Senaryoları oluştur
        result = generator.generate_scenarios(
            input_file=request.csv_file_name,
            scenario_name=request.name
        )
        
        if not result:
            raise HTTPException(status_code=500, detail="Senaryo oluşturulamadı")
            
        return {"message": "Senaryolar başarıyla oluşturuldu", "scenarios": result}
        
    except HTTPException as he:
        raise he
    except Exception as e:
        print(f"Senaryo oluşturma hatası: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/")
async def get_scenarios():
    """Tüm test senaryolarını getirir"""
    try:
        scenarios_dir = "/app/data/output/test_scenarios"
        if not os.path.exists(scenarios_dir):
            return []
            
        scenarios = []
        for file in os.listdir(scenarios_dir):
            if file.endswith('.txt'):
                try:
                    file_path = os.path.join(scenarios_dir, file)
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        name = file.split('_')[0]  # İlk kısım senaryo adı
                        date = '_'.join(file.split('_')[1:])  # Geri kalanı tarih
                        scenarios.append({
                            "id": file.replace('.txt', ''),
                            "name": name,
                            "date": date,
                            "content": content,
                            "filename": file
                        })
                except Exception as e:
                    print(f"Dosya okuma hatası - {file}: {str(e)}")
                    continue
                    
        return scenarios

    except Exception as e:
        print(f"Senaryo listeleme hatası: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sync")
async def sync_scenarios():
    """Test senaryolarını senkronize eder"""
    try:
        scenarios_dir = "/app/data/output/test_scenarios"
        if not os.path.exists(scenarios_dir):
            os.makedirs(scenarios_dir, exist_ok=True)
            return {"message": "Dizin oluşturuldu"}
            
        # Dosyaları listele
        files = [f for f in os.listdir(scenarios_dir) if f.endswith('.txt')]
        
        return {
            "message": f"{len(files)} senaryo senkronize edildi",
            "files": files
        }
        
    except Exception as e:
        print(f"Senaryo senkronizasyon hatası: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 