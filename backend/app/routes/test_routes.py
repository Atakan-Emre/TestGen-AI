from fastapi import APIRouter, HTTPException
from typing import List, Optional
from pydantic import BaseModel
import os
import logging
from datetime import datetime
from app.generators.bsc import BSCGenerator
from src.generators.ngv_generator import NGVGenerator
from src.generators.ngi_generator import NGIGenerator
from src.generators.opt_generator import OPTGenerator
import shutil
from app.shared.test_case_summary import list_test_case_directory

logger = logging.getLogger(__name__)
router = APIRouter()

# Base dizinler
TEST_CASES_DIR = "/app/data/output/test_cases"
INPUT_DIR = "/app/data/input"

class TestCreateRequest(BaseModel):
    name: str
    scenario_id: str
    generators: List[str]
    json_files: List[int]
    output_dir: Optional[str] = None

class DeleteTestRequest(BaseModel):
    test_name: str
    file_name: str
    file_path: str

@router.post("/create")
async def create_test(request: TestCreateRequest):
    """Test senaryosu oluşturur"""
    try:
        logger.debug(f"Test oluşturma isteği alındı: {request}")
        
        # Test klasörünü oluştur
        test_dir = os.path.join(TEST_CASES_DIR, request.name)
        if os.path.exists(test_dir):
            raise HTTPException(status_code=400, detail=f"'{request.name}' adında bir test zaten mevcut")
        
        os.makedirs(test_dir)
        logger.debug(f"Test dizini oluşturuldu: {test_dir}")
        
        if not request.json_files:
            raise HTTPException(status_code=400, detail="En az bir JSON dosyasi secilmelidir")

        results = []
        scenario_path = _resolve_scenario_path(request.scenario_id)
        
        # Her generator için test oluştur
        for generator_type in request.generators:
            try:
                generator_dir = os.path.join(test_dir, generator_type)
                os.makedirs(generator_dir)
                
                # Generator'ı seç ve çalıştır
                if generator_type == "bsc":
                    generator = BSCGenerator()
                    result = generator.generate_bsc_test(
                        scenario_path=scenario_path,
                        test_name=request.name,
                        json_file_id=request.json_files[0]
                    )
                    results.append({
                        "type": "bsc",
                        "status": "success",
                        "result": result
                    })
                    
                elif generator_type == "ngv":
                    generator = NGVGenerator()
                    result = generator.generate_ngv_tests(
                        scenario_path=scenario_path,
                        test_name=request.name,
                        json_file_id=request.json_files[0]
                    )
                    results.append({
                        "type": "ngv",
                        "status": "success",
                        "result": result
                    })
                    
                elif generator_type == "ngi":
                    generator = NGIGenerator()
                    result = generator.generate_ngi_tests(
                        scenario_path=scenario_path,
                        test_name=request.name,
                        json_file_id=request.json_files[0]
                    )
                    results.append({
                        "type": "ngi",
                        "status": "success",
                        "result": result
                    })
                    
                elif generator_type == "opt":
                    generator = OPTGenerator()
                    result = generator.generate_opt_tests(
                        scenario_path=scenario_path,
                        test_name=request.name,
                        json_file_id=request.json_files[0]
                    )
                    results.append({
                        "type": "opt",
                        "status": "success",
                        "result": result
                    })
                else:
                    raise HTTPException(status_code=400, detail=f"Desteklenmeyen generator: {generator_type}")
                    
            except HTTPException as e:
                logger.error(f"{generator_type} generator hatası: {str(e.detail)}")
                results.append({
                    "type": generator_type,
                    "status": "error",
                    "error": e.detail
                })
            except Exception as e:
                logger.error(f"{generator_type} generator hatası: {str(e)}")
                results.append({
                    "type": generator_type,
                    "status": "error",
                    "error": str(e)
                })
        
        return {
            "message": "Test oluşturma tamamlandı",
            "test_name": request.name,
            "results": results
        }
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Test oluşturma hatası: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


def _resolve_scenario_path(scenario_ref: str) -> str:
    base_dir = "/app/data/output/test_scenarios"
    raw_ref = str(scenario_ref)

    candidates = []
    if os.path.isabs(raw_ref):
        candidates.append(raw_ref)
    else:
        candidates.append(os.path.join(base_dir, raw_ref))
        if not raw_ref.endswith(".txt"):
            candidates.append(os.path.join(base_dir, f"{raw_ref}.txt"))
            candidates.append(os.path.join(base_dir, f"scenario_{raw_ref}.txt"))

    for candidate in candidates:
        if os.path.exists(candidate):
            return candidate

    raise HTTPException(status_code=404, detail=f"Senaryo dosyasi bulunamadi: {scenario_ref}")

@router.get("/list")
async def list_tests():
    """Tüm testleri listeler"""
    try:
        if not os.path.exists(TEST_CASES_DIR):
            return []
            
        tests = []
        for test_name in os.listdir(TEST_CASES_DIR):
            test_dir = os.path.join(TEST_CASES_DIR, test_name)
            if os.path.isdir(test_dir):
                # Her test için generator sonuçlarını topla
                generators = []
                for generator_type in ["bsc", "ngv", "ngi", "opt"]:
                    generator_dir = os.path.join(test_dir, generator_type)
                    if os.path.exists(generator_dir):
                        generators.append({
                            "type": generator_type,
                            "count": len([f for f in os.listdir(generator_dir) if f.endswith('.json')])
                        })
                
                tests.append({
                    "name": test_name,
                    "created_at": datetime.fromtimestamp(os.path.getctime(test_dir)).isoformat(),
                    "generators": generators
                })
                
        return tests
        
    except Exception as e:
        logger.error(f"Test listeleme hatası: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{test_type}/list/{test_name}")
async def list_test_files(test_type: str, test_name: str):
    """Belirli bir test klasöründeki dosyaları listeler"""
    try:
        test_dir = os.path.join(TEST_CASES_DIR, test_name, test_type)
        return list_test_case_directory(test_dir)
        
    except Exception as e:
        logger.error(f"Test dosyaları listelenirken hata: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{test_type}/file/{test_name}/{file_name}")
async def get_test_file(test_type: str, test_name: str, file_name: str):
    """Tek bir test dosyasının tam içeriğini getir"""
    try:
        file_path = os.path.join(TEST_CASES_DIR, test_name, test_type, file_name)
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"Dosya bulunamadı: {file_name}")

        item = list_test_case_directory(
            os.path.join(TEST_CASES_DIR, test_name, test_type),
            include_content=True,
        )
        matched = next((entry for entry in item if entry["name"] == file_name), None)
        if not matched:
            raise HTTPException(status_code=404, detail=f"Dosya bulunamadı: {file_name}")
        return matched
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Test dosyası getirilirken hata: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{test_type}/delete")
async def delete_test_file(test_type: str, request: DeleteTestRequest):
    """Test dosyasını siler"""
    try:
        # Dosya yolunu oluştur
        file_path = os.path.join(TEST_CASES_DIR, request.file_path)
        
        # Dosyanın var olup olmadığını kontrol et
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"Dosya bulunamadı: {file_path}")
        
        # Dosyayı sil
        os.remove(file_path)
        
        # Eğer klasör boşsa klasörü de sil
        dir_path = os.path.dirname(file_path)
        if os.path.exists(dir_path) and not os.listdir(dir_path):
            shutil.rmtree(dir_path)
            
        return {"message": f"{request.file_name} başarıyla silindi"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/list-directories")
async def list_test_directories():
    """Tüm test klasörlerini listeler"""
    try:
        if not os.path.exists(TEST_CASES_DIR):
            return []
            
        directories = []
        for test_name in os.listdir(TEST_CASES_DIR):
            test_dir = os.path.join(TEST_CASES_DIR, test_name)
            if os.path.isdir(test_dir):
                directories.append({
                    "name": test_name,
                    "created_at": datetime.fromtimestamp(os.path.getctime(test_dir)).isoformat()
                })
                
        return directories
        
    except Exception as e:
        logger.error(f"Klasör listeleme hatası: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/directory/{test_name}")
async def delete_test_directory(test_name: str):
    """Test klasörünü tüm içeriğiyle birlikte siler"""
    try:
        test_dir = os.path.join(TEST_CASES_DIR, test_name)
        
        # Klasörün var olup olmadığını kontrol et
        if not os.path.exists(test_dir):
            raise HTTPException(status_code=404, detail=f"Klasör bulunamadı: {test_name}")
            
        # Klasörü ve tüm içeriğini sil
        shutil.rmtree(test_dir)
        
        return {"message": f"{test_name} klasörü başarıyla silindi"}
        
    except Exception as e:
        logger.error(f"Klasör silme hatası: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/list-names")
async def list_test_names():
    """Tüm test klasörlerinin adlarını listeler"""
    try:
        if not os.path.exists(TEST_CASES_DIR):
            return []
            
        test_names = []
        for test_name in os.listdir(TEST_CASES_DIR):
            test_dir = os.path.join(TEST_CASES_DIR, test_name)
            if os.path.isdir(test_dir):
                test_names.append({
                    "name": test_name,
                    "created_at": datetime.fromtimestamp(os.path.getctime(test_dir)).isoformat()
                })
                
        return test_names
        
    except Exception as e:
        logger.error(f"Test adları listelenirken hata: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 
