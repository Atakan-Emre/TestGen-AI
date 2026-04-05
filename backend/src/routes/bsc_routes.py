from fastapi import APIRouter, HTTPException
from typing import List
from pydantic import BaseModel
from src.generators.bsc_generator import BSCGenerator
import os
import logging

router = APIRouter()
generator = BSCGenerator()
logger = logging.getLogger(__name__)

# Temel dizin yolları
BASE_DIR = "/app/data"
INPUT_DIR = os.path.join(BASE_DIR, "input")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

class BSCTestRequest(BaseModel):
    scenario_id: str
    test_name: str
    json_file_id: int

@router.post("/generate")
async def generate_bsc_test(request: BSCTestRequest):
    """BSC test senaryosu oluşturur"""
    try:
        logger.debug(f"BSC test oluşturma isteği alındı: {request}")
        
        # Dizin yollarını oluştur
        json_dir = os.path.join(INPUT_DIR, "Json")
        variables_dir = os.path.join(INPUT_DIR, "Variables")
        scenarios_dir = os.path.join(OUTPUT_DIR, "test_scenarios")
        test_cases_dir = os.path.join(OUTPUT_DIR, "test_cases", request.test_name, "bsc")
        
        # Dizinlerin varlığını kontrol et
        for dir_path in [json_dir, variables_dir, scenarios_dir]:
            if not os.path.exists(dir_path):
                raise HTTPException(status_code=404, detail=f"Dizin bulunamadı: {dir_path}")
        
        # Test dizinini oluştur
        os.makedirs(test_cases_dir, exist_ok=True)
        logger.debug(f"BSC test dizini oluşturuldu: {test_cases_dir}")
        
        # Senaryo dosyasının varlığını kontrol et
        scenario_path = os.path.join(scenarios_dir, request.scenario_id)
        if not os.path.exists(scenario_path):
            raise HTTPException(status_code=404, detail=f"Senaryo dosyası bulunamadı: {request.scenario_id}")
        
        # BSC test senaryosunu oluştur
        test_case = generator.generate_bsc_test(
            scenario_path=scenario_path,
            test_name=request.test_name,
            json_file_id=request.json_file_id
        )
        
        if not test_case:
            raise HTTPException(status_code=500, detail="BSC test senaryosu oluşturulamadı")
        
        return {
            "message": "BSC test senaryosu başarıyla oluşturuldu",
            "test_case": test_case
        }
        
    except HTTPException as he:
        raise he
    except Exception as e:
        error_msg = str(e) if str(e) else "Bilinmeyen bir hata oluştu"
        logger.error(f"BSC test oluşturma hatası: {error_msg}")
        raise HTTPException(status_code=500, detail=error_msg) 