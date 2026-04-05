from fastapi import APIRouter, HTTPException
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import os
import logging
from app.generators.bsc import BSCGenerator
from app.shared.logging import get_logger
from app.shared.test_case_summary import list_test_case_directory

logger = get_logger(__name__)
router = APIRouter()

# Base dizinler
TEST_CASES_DIR = "/app/data/output/test_cases"
INPUT_DIR = "/app/data/input"

class BSCTestRequest(BaseModel):
    test_type: str = "bsc"
    scenario_path: str
    test_name: str
    json_file_id: int
    selected_variables: Optional[List[str]] = []
    binding_profile: Optional[str] = None

class BSCTestResponse(BaseModel):
    success: bool
    message: str
    test_result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

@router.post("/generate", response_model=BSCTestResponse)
async def generate_bsc_test(request: BSCTestRequest):
    """Yeni mimari ile BSC test senaryosu oluşturur"""
    try:
        logger.info(f"BSC test oluşturma isteği alındı: {request.test_name}")
        
        # Senaryo dosyasının varlığını kontrol et
        if not os.path.exists(request.scenario_path):
            return BSCTestResponse(
                success=False,
                message=f"Senaryo dosyası bulunamadı: {request.scenario_path}",
                error="SCENARIO_NOT_FOUND"
            )
        
        # Yeni mimari ile BSC generator'ı başlat
        generator = BSCGenerator()
        binding_profile = request.binding_profile or None
        
        # Variables seçimi varsa, o yöntemi kullan
        if request.selected_variables:
            result = generator.generate_bsc_test_with_variables(
                scenario_path=request.scenario_path,
                test_name=request.test_name,
                json_file_id=request.json_file_id,
                selected_variables=request.selected_variables,
                binding_profile=binding_profile,
            )
        else:
            # Normal test oluşturma
            result = generator.generate_bsc_test(
                scenario_path=request.scenario_path,
                test_name=request.test_name,
                json_file_id=request.json_file_id,
                binding_profile=binding_profile,
            )
        
        return BSCTestResponse(
            success=True,
            message=f"BSC test senaryosu başarıyla oluşturuldu: {request.test_name}",
            test_result=result
        )
        
    except Exception as e:
        logger.error(f"BSC test oluşturma hatası: {str(e)}")
        return BSCTestResponse(
            success=False,
            message="Test oluşturulurken hata oluştu",
            error=str(e)
        )

@router.get("/list/{test_name}")
async def list_bsc_tests(test_name: str):
    """Belirli bir test için BSC senaryolarını listeler"""
    try:
        test_dir = os.path.join(TEST_CASES_DIR, test_name, "bsc")
        return list_test_case_directory(test_dir)
        
    except Exception as e:
        logger.error(f"BSC test listeleme hatası: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 
