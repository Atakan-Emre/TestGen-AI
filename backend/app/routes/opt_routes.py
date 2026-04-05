from fastapi import APIRouter, HTTPException
from typing import List, Optional
from pydantic import BaseModel
import os
import logging
from pathlib import Path
from src.generators.opt_generator import OPTGenerator
from ..services.variables_loader import VariablesLoader
from ..shared.binding_runtime import apply_binding_profile
from ..shared.io_loader import load_template
from ..shared.test_case_summary import list_test_case_directory

logger = logging.getLogger(__name__)
router = APIRouter()

# Base dizinler
TEST_CASES_DIR = "/app/data/output/test_cases"
INPUT_DIR = "/app/data/input"

# Variables loader instance
variables_loader = VariablesLoader()

class OPTTestRequest(BaseModel):
    scenario_id: str
    test_name: str
    json_files: List[int]
    variables_profile: Optional[str] = None
    binding_profile: Optional[str] = None

@router.post("/generate")
async def generate_opt_test(request: OPTTestRequest):
    """OPT test senaryosu oluşturur"""
    try:
        logger.debug(f"OPT test oluşturma isteği alındı: {request}")
        
        # Test klasörünü oluştur
        test_dir = os.path.join(TEST_CASES_DIR, request.test_name, "opt")
        os.makedirs(test_dir, exist_ok=True)
        logger.debug(f"OPT test dizini oluşturuldu: {test_dir}")
        
        # Senaryo dosyasının tam yolunu oluştur
        scenario_path = os.path.join("/app/data/output/test_scenarios", request.scenario_id)
        if not os.path.exists(scenario_path):
            raise HTTPException(status_code=404, detail=f"Senaryo dosyası bulunamadı: {request.scenario_id}")
        
        # OPT generator'ı başlat
        generator = OPTGenerator()

        # Değişken profili yükle (varsa)
        profile_name = Path(request.variables_profile).stem if request.variables_profile else None
        template = load_template(request.json_files[0])

        if profile_name:
            try:
                generator.variables = variables_loader.load_profile(profile_name)
            except FileNotFoundError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Variables profili bulunamadı: {profile_name}. Mevcut profilleri '/api/variables/profiles' ile kontrol edin."
                )
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"Variables profili yüklenemedi: {str(e)}")

        if request.binding_profile:
            bound_variables, ignored_fields, mutation_blocked_fields, _binding_payload = apply_binding_profile(
                request.binding_profile,
                generator.variables,
                template,
                "opt",
            )
            generator.variables = bound_variables
            generator.binding_ignored_fields = ignored_fields
            generator.binding_mutation_blocked_fields = mutation_blocked_fields

        result = generator.generate_opt_tests(
            scenario_path=scenario_path,
            test_name=request.test_name,
            json_file_id=request.json_files[0]  # İlk JSON dosyasını kullan
        )
        
        return {
            "message": "OPT test senaryosu oluşturuldu",
            "test_name": request.test_name,
            "result": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OPT test oluşturma hatası: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/list/{test_name}")
async def list_opt_tests(test_name: str):
    """Belirli bir test için OPT senaryolarını listeler"""
    try:
        test_dir = os.path.join(TEST_CASES_DIR, test_name, "opt")
        return list_test_case_directory(test_dir)
        
    except Exception as e:
        logger.error(f"OPT test listeleme hatası: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 
