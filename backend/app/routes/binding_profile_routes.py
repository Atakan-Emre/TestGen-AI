from datetime import datetime
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.json_file import JsonFile
from ..services.binding_autopilot_service import BindingAutopilotService
from ..services.binding_profile_service import BindingProfileService
from ..services.binding_validation_agent import BindingValidationAgent


logger = logging.getLogger(__name__)
router = APIRouter(tags=["binding-profiles"])
binding_profile_service = BindingProfileService()


class BindingSuggestionRequest(BaseModel):
    json_file_id: int = Field(..., ge=1)
    variables_profile: str = Field(..., min_length=1)
    generators: Optional[List[str]] = None


class AutoBindingResolveRequest(BaseModel):
    json_file_id: int = Field(..., ge=1)
    variables_profile: str = Field(..., min_length=1)
    generators: Optional[List[str]] = None
    profile_name: Optional[str] = None
    description: Optional[str] = None


class BindingValidationRequest(BaseModel):
    scenario_id: Optional[str] = None
    scenario_path: Optional[str] = None
    json_file_id: int = Field(..., ge=1)
    variables_profile: str = Field(..., min_length=1)
    generators: Optional[List[str]] = None
    binding_profile_name: Optional[str] = None
    auto_resolve: bool = True
    profile_name: Optional[str] = None
    description: Optional[str] = None


class BindingFieldEntry(BaseModel):
    json_path: str
    schema_type: str
    suggested_variable_key: Optional[str] = None
    variable_key: Optional[str] = None
    confidence: float = Field(..., ge=0, le=1)
    status: str
    action: str
    locked: bool
    generators: List[str]


class BindingSuggestionResponse(BaseModel):
    success: bool = True
    message: str
    data: Dict[str, Any]


class BindingProfileSaveRequest(BaseModel):
    json_file_id: int = Field(..., ge=1)
    variables_profile: str = Field(..., min_length=1)
    description: Optional[str] = None
    bindings: List[BindingFieldEntry]


class BindingProfileResponse(BaseModel):
    success: bool = True
    message: str
    data: Dict[str, Any]


def _get_autopilot_service() -> BindingAutopilotService:
    return BindingAutopilotService(binding_profile_service=binding_profile_service)


def _get_validation_agent() -> BindingValidationAgent:
    return BindingValidationAgent(binding_profile_service=binding_profile_service)


@router.post("/suggest", response_model=BindingSuggestionResponse)
async def suggest_binding_profile(
    request: BindingSuggestionRequest,
    db: Session = Depends(get_db),
):
    try:
        json_file = db.query(JsonFile).filter(JsonFile.id == request.json_file_id).first()
        if not json_file:
            raise HTTPException(status_code=404, detail=f"JSON dosyası bulunamadı: {request.json_file_id}")

        suggestion = binding_profile_service.suggest_bindings_for_json_file(
            json_file=json_file,
            variables_profile=request.variables_profile,
            generators=request.generators,
        )
        return BindingSuggestionResponse(
            success=True,
            message="Binding önerileri oluşturuldu",
            data=suggestion,
        )
    except HTTPException:
        raise
    except FileNotFoundError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error("Binding suggestion hatası", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/auto-resolve", response_model=BindingSuggestionResponse)
async def auto_resolve_binding_profile(
    request: AutoBindingResolveRequest,
    db: Session = Depends(get_db),
):
    try:
        json_file = db.query(JsonFile).filter(JsonFile.id == request.json_file_id).first()
        if not json_file:
            raise HTTPException(status_code=404, detail=f"JSON dosyası bulunamadı: {request.json_file_id}")

        result = _get_autopilot_service().resolve_auto_profile(
            json_file=json_file,
            variables_profile=request.variables_profile,
            generators=request.generators,
            profile_name=request.profile_name,
            description=request.description,
        )
        return BindingSuggestionResponse(
            success=True,
            message="Otomatik binding profili oluşturuldu",
            data=result,
        )
    except HTTPException:
        raise
    except FileNotFoundError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error("Auto binding hatası", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/profiles", response_model=BindingProfileResponse)
async def list_binding_profiles():
    try:
        profiles = binding_profile_service.list_profiles()
        return BindingProfileResponse(
            success=True,
            message=f"{len(profiles)} binding profili bulundu",
            data={"profiles": profiles},
        )
    except Exception as exc:
        logger.error("Binding profil listesi hatası", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/profiles/{name}", response_model=BindingProfileResponse)
async def get_binding_profile(name: str):
    try:
        profile = binding_profile_service.load_profile(name)
        return BindingProfileResponse(
            success=True,
            message=f"Binding profili yüklendi: {name}",
            data=profile,
        )
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Binding profili bulunamadı: {name}")
    except Exception as exc:
        logger.error("Binding profil okuma hatası", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@router.put("/profiles/{name}", response_model=BindingProfileResponse)
async def save_binding_profile(name: str, request: BindingProfileSaveRequest):
    try:
        data = binding_profile_service.save_profile(
            name=name,
            payload=request.model_dump(),
        )
        return BindingProfileResponse(
            success=True,
            message=f"Binding profili kaydedildi: {name}",
            data=data,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error("Binding profil kaydetme hatası", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@router.delete("/profiles/{name}", response_model=BindingProfileResponse)
async def delete_binding_profile(name: str):
    try:
        deleted = binding_profile_service.delete_profile(name)
        if not deleted:
            raise HTTPException(status_code=404, detail=f"Binding profili bulunamadı: {name}")
        return BindingProfileResponse(
            success=True,
            message=f"Binding profili silindi: {name}",
            data={"name": name},
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Binding profil silme hatası", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/validate", response_model=BindingSuggestionResponse)
async def validate_binding_profile(
    request: BindingValidationRequest,
    db: Session = Depends(get_db),
):
    try:
        json_file = db.query(JsonFile).filter(JsonFile.id == request.json_file_id).first()
        if not json_file:
            raise HTTPException(status_code=404, detail=f"JSON dosyası bulunamadı: {request.json_file_id}")

        result = _get_validation_agent().run_validation(
            scenario_id=request.scenario_id,
            scenario_path=request.scenario_path,
            json_file=json_file,
            variables_profile=request.variables_profile,
            generators=request.generators,
            binding_profile_name=request.binding_profile_name,
            auto_resolve=request.auto_resolve,
            auto_profile_name=request.profile_name,
            description=request.description,
        )
        return BindingSuggestionResponse(
            success=True,
            message="Binding doğrulama tamamlandı",
            data=result,
        )
    except HTTPException:
        raise
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error("Binding doğrulama hatası", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))
