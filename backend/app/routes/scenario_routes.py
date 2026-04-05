from collections import Counter
from pathlib import Path
import threading
from fastapi import APIRouter, HTTPException, UploadFile, File
from typing import Callable, List, Optional
from pydantic import BaseModel
from src.generators.bert_ner_generator import BertNerGenerator
from ..services.variables_loader import VariablesLoader
from ..services.scenario_intelligence import load_scenario_bundle
from ..services.scenario_job_manager import ScenarioJobManager
from src.config.settings import VARIABLES_DIR
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter()
variables_loader = VariablesLoader(str(VARIABLES_DIR))
scenario_job_manager = ScenarioJobManager()
SCENARIOS_DIR = Path("/app/data/output/test_scenarios")

class ScenarioGenerateRequest(BaseModel):
    name: str
    csv_file_id: int
    csv_file_name: str
    generator_type: str
    variables_profile: Optional[str] = "default"


def _split_scenario_name(stem: str) -> tuple[str, str]:
    parts = stem.rsplit("_", 2)
    if len(parts) == 3 and parts[1].isdigit() and parts[2].isdigit():
        return parts[0], f"{parts[1]}_{parts[2]}"
    return stem, ""


def _serialize_field(field) -> dict:
    return {
        "field_name_tr": field.field_name_tr,
        "field_name_en": field.field_name_en,
        "field_type": field.field_type,
        "raw_type": field.raw_type,
        "required": field.required,
        "optional": field.optional,
        "unique": field.unique,
        "max_len": field.max_len,
        "min_len": field.min_len,
        "pattern": field.pattern,
        "enum_values": field.enum_values,
        "semantic_tags": field.semantic_tags,
        "confidence": field.confidence,
    }


def _build_metadata(bundle, include_fields: bool = False) -> Optional[dict]:
    if not bundle:
        return None

    required_count = sum(1 for field in bundle.fields if field.required)
    optional_count = sum(1 for field in bundle.fields if field.optional)
    unique_count = sum(1 for field in bundle.fields if field.unique)
    confidences = [field.confidence for field in bundle.fields if field.confidence is not None]
    average_confidence = round(sum(confidences) / len(confidences), 3) if confidences else 0.0
    tag_counter = Counter()
    type_counter = Counter()

    for field in bundle.fields:
        tag_counter.update(field.semantic_tags or [])
        type_counter.update([field.field_type or "unknown"])

    metadata = {
        "scenario_name": bundle.scenario_name,
        "source_csv": bundle.source_csv,
        "generator_type": bundle.generator_type,
        "generated_at": bundle.generated_at,
        "field_count": len(bundle.fields),
        "required_count": required_count,
        "optional_count": optional_count,
        "unique_count": unique_count,
        "average_confidence": average_confidence,
        "semantic_tags": [tag for tag, _count in tag_counter.most_common(8)],
        "type_distribution": [
            {"type": field_type, "count": count}
            for field_type, count in type_counter.most_common()
        ],
    }

    if include_fields:
        metadata["fields"] = [_serialize_field(field) for field in bundle.fields]

    return metadata


def _build_generator(progress_callback: Optional[Callable[[str, Optional[float], Optional[str]], None]] = None) -> BertNerGenerator:
    return BertNerGenerator(progress_callback=progress_callback)


def _generate_scenarios_internal(
    request: ScenarioGenerateRequest,
    progress_callback: Optional[Callable[[str, Optional[float], Optional[str], str], None]] = None,
):
    def emit(
        message: str,
        progress: Optional[float] = None,
        stage: Optional[str] = None,
        level: str = "info",
    ) -> None:
        if progress_callback:
            progress_callback(message, progress, stage, level)

    emit("Senaryo üretim isteği doğrulanıyor.", 0.05, "validating")
    if request.generator_type not in {"bert_ner", "nlp_hybrid", "rule_based"}:
        raise HTTPException(
            status_code=400,
            detail=f"Desteklenmeyen generator_type: {request.generator_type}"
        )

    csv_file_path = os.path.join("/app/data/input/Csv", request.csv_file_name)
    logger.debug(f"CSV dosya yolu: {csv_file_path}")
    if not os.path.exists(csv_file_path):
        logger.error(f"CSV dosyası bulunamadı: {request.csv_file_name}")
        raise HTTPException(status_code=404, detail=f"CSV dosyası bulunamadı: {request.csv_file_name}")
    emit(f"CSV dosyası doğrulandı: {request.csv_file_name}", 0.12, "csv_validated")

    variables = {}
    if request.variables_profile and request.variables_profile != "default":
        emit(f"Variables profili yükleniyor: {request.variables_profile}", 0.15, "variables_loading")
        try:
            variables = variables_loader.load_profile(request.variables_profile)
            logger.debug(f"Variables profil yüklendi: {request.variables_profile} ({len(variables)} değişken)")
            emit(
                f"Variables profili yüklendi: {request.variables_profile} ({len(variables)} değişken).",
                0.18,
                "variables_loaded",
            )
        except FileNotFoundError:
            logger.warning(f"Variables profil bulunamadı: {request.variables_profile}")
            raise HTTPException(
                status_code=400,
                detail=f"Variables profil bulunamadı: {request.variables_profile}. Mevcut profilleri kontrol etmek için GET /api/variables/profiles kullanın."
            )
        except Exception as e:
            logger.error(f"Variables profil yüklenirken hata: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Variables profil yüklenemedi: {str(e)}")
    else:
        emit("Varsayılan variables profili kontrol ediliyor.", 0.15, "variables_loading")
        try:
            variables = variables_loader.load_profile("default")
            logger.debug(f"Default variables profil yüklendi ({len(variables)} değişken)")
            emit(
                f"Varsayılan variables profili yüklendi ({len(variables)} değişken).",
                0.18,
                "variables_loaded",
            )
        except FileNotFoundError:
            logger.info("Default variables profil bulunamadı, boş değişkenlerle devam ediliyor")
            emit(
                "Varsayılan variables profili bulunamadı, boş değişkenlerle devam ediliyor.",
                0.18,
                "variables_skipped",
                "warning",
            )
        except Exception as e:
            logger.warning(f"Default variables profil yüklenirken hata: {str(e)}")
            emit(
                f"Varsayılan variables profili yüklenirken hata alındı: {str(e)}",
                0.18,
                "variables_warning",
                "warning",
            )

    emit("NLP senaryo üretimi başlatılıyor.", 0.2, "model_preparing")
    generator = _build_generator(
        progress_callback=lambda message, progress=None, stage=None: emit(message, progress, stage)
    )
    result = generator.generate_scenarios(
        input_file=request.csv_file_name,
        scenario_name=request.name,
        generator_type=request.generator_type,
        progress_callback=lambda message, progress=None, stage=None: emit(message, progress, stage),
    )

    if not result:
        logger.error("Senaryo oluşturulamadı")
        raise HTTPException(status_code=500, detail="Senaryo oluşturulamadı")

    if variables:
        emit("Variables placeholder değerleri uygulanıyor.", 0.94, "variables_applying")
        result = _apply_variables(result, variables)
        logger.debug(f"Variables uygulandı: {len(variables)} değişken")
        emit(f"Variables uygulandı: {len(variables)} değişken.", 0.96, "variables_applied")

    logger.debug(f"Senaryolar başarıyla oluşturuldu: {len(result)} adet")
    bundle = getattr(generator, "last_bundle", None)
    scenario_path = getattr(generator, "last_scenario_path", None)
    emit(
        f"Senaryo üretimi tamamlandı: {scenario_path.name if scenario_path else request.name}",
        1.0,
        "completed",
    )
    return {
        "message": "Senaryolar başarıyla oluşturuldu",
        "scenarios": result,
        "scenario_file": scenario_path.name if scenario_path else None,
        "summary": _build_metadata(bundle, include_fields=False),
    }


def _run_scenario_generation_job(job_id: str, request_data: dict) -> None:
    try:
        request = ScenarioGenerateRequest(**request_data)
        scenario_job_manager.start_job(
            job_id,
            message=f"Senaryo üretimi başlatıldı: {request.name}",
            progress=0.02,
            stage="starting",
        )

        def report(
            message: str,
            progress: Optional[float] = None,
            stage: Optional[str] = None,
            level: str = "info",
        ) -> None:
            scenario_job_manager.append_log(
                job_id,
                message,
                level=level,
                progress=progress,
                stage=stage,
            )

        result = _generate_scenarios_internal(request, progress_callback=report)
        scenario_job_manager.complete(job_id, result)
    except HTTPException as exc:
        scenario_job_manager.fail(job_id, str(exc.detail), stage="failed")
    except Exception as exc:
        logger.error("Senaryo job hatası: %s", exc, exc_info=True)
        scenario_job_manager.fail(job_id, str(exc), stage="failed")

@router.post("/generate")
async def generate_scenarios(request: ScenarioGenerateRequest):
    """Test senaryolarını oluşturur"""
    try:
        logger.debug(f"Senaryo oluşturma isteği alındı: {request}")
        return _generate_scenarios_internal(request)
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Senaryo oluşturma hatası: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/jobs")
async def create_scenario_generation_job(request: ScenarioGenerateRequest):
    """Senaryo üretimini arka planda başlatır ve takip için job id döner."""
    job = scenario_job_manager.create_job(request.model_dump())
    worker = threading.Thread(
        target=_run_scenario_generation_job,
        args=(job["job_id"], request.model_dump()),
        daemon=True,
    )
    worker.start()
    return job


@router.get("/jobs/{job_id}")
async def get_scenario_generation_job(job_id: str):
    """Senaryo üretim job durumunu ve loglarını döner."""
    job = scenario_job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Scenario job bulunamadı: {job_id}")
    return job

def _apply_variables(scenarios: List[str], variables: dict) -> List[str]:
    """Senaryolarda variables placeholder'larını değiştirir"""
    import re
    
    result = []
    for scenario in scenarios:
        # {{variable_name}} formatındaki placeholder'ları değiştir
        for key, value in variables.items():
            placeholder = f"{{{{{key}}}}}"
            scenario = scenario.replace(placeholder, str(value))
        result.append(scenario)
    
    return result

@router.get("/")
async def get_scenarios():
    """Tüm test senaryolarını getirir"""
    try:
        if not SCENARIOS_DIR.exists():
            logger.warning("Senaryo dizini bulunamadı")
            return []
            
        scenarios = []
        for file_path in SCENARIOS_DIR.glob("*.txt"):
            file = file_path.name
            if file.endswith('.txt'):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        name, date = _split_scenario_name(file_path.stem)
                        bundle = load_scenario_bundle(str(file_path))
                        stat = file_path.stat()
                        scenarios.append({
                            "id": file_path.stem,
                            "name": name,
                            "date": date,
                            "content": content,
                            "filename": file,
                            "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                            "updated_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                            "size": stat.st_size,
                            "metadata": _build_metadata(bundle, include_fields=False),
                        })
                except Exception as e:
                    logger.error(f"Dosya okuma hatası - {file}: {str(e)}")
                    continue
                    
        logger.debug(f"{len(scenarios)} adet senaryo bulundu")
        return scenarios

    except Exception as e:
        logger.error(f"Senaryo listeleme hatası: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{filename}")
async def get_scenario_content(filename: str):
    """Belirli bir senaryonun içeriğini getirir"""
    try:
        file_path = SCENARIOS_DIR / filename
        if not file_path.exists():
            logger.error(f"Senaryo dosyası bulunamadı: {filename}")
            raise HTTPException(status_code=404, detail=f"Senaryo bulunamadı: {filename}")
            
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        bundle = load_scenario_bundle(str(file_path))
            
        return {"content": content, "metadata": _build_metadata(bundle, include_fields=True)}
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Senaryo içeriği okuma hatası: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/upload")
async def upload_scenario(file: UploadFile = File(...)):
    """Hazir senaryo .txt dosyasini kaydeder"""
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="Dosya adı bulunamadı")

        safe_name = os.path.basename(file.filename)
        if not safe_name.lower().endswith(".txt"):
            raise HTTPException(status_code=400, detail="Yalnızca .txt senaryo dosyaları desteklenir")

        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail="Boş senaryo dosyası yüklenemez")

        SCENARIOS_DIR.mkdir(parents=True, exist_ok=True)
        target_path = SCENARIOS_DIR / safe_name
        if target_path.exists():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            target_path = SCENARIOS_DIR / f"{target_path.stem}_{timestamp}{target_path.suffix}"

        target_path.write_bytes(content)
        return {
            "message": "Senaryo başarıyla yüklendi",
            "filename": target_path.name,
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Senaryo yükleme hatası: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sync")
async def sync_scenarios():
    """Test senaryolarını senkronize eder"""
    try:
        if not SCENARIOS_DIR.exists():
            SCENARIOS_DIR.mkdir(parents=True, exist_ok=True)
            logger.info("Senaryo dizini oluşturuldu")
            return {"message": "Dizin oluşturuldu"}
            
        # Dosyaları listele
        files = [f.name for f in SCENARIOS_DIR.glob("*.txt")]
        logger.debug(f"{len(files)} adet senaryo dosyası bulundu")
        
        return {
            "message": f"{len(files)} senaryo senkronize edildi",
            "files": files
        }
        
    except Exception as e:
        logger.error(f"Senaryo senkronizasyon hatası: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{filename}")
async def delete_scenario(filename: str):
    """Belirli bir senaryoyu siler"""
    try:
        file_path = SCENARIOS_DIR / filename
        if not file_path.exists():
            logger.error(f"Silinecek senaryo bulunamadı: {filename}")
            raise HTTPException(status_code=404, detail=f"Senaryo bulunamadı: {filename}")
            
        os.remove(file_path)
        sidecar_path = file_path.with_suffix(".meta.json")
        if sidecar_path.exists():
            sidecar_path.unlink()
        logger.info(f"Senaryo silindi: {filename}")
        return {"message": f"Senaryo başarıyla silindi: {filename}"}
        
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Senaryo silme hatası: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 
