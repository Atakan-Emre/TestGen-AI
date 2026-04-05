import json
import hashlib
import logging
from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request
from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from ..database import get_db
from ..models.file_model import File as DBFile, FileType
from ..schemas.file_schema import FileCreate, FileResponse
from ..shared.settings import INPUT_DIR

router = APIRouter(tags=["files"])
logger = logging.getLogger(__name__)
VARIABLES_DIR = INPUT_DIR / "Variables"


def _ensure_variables_dir() -> Path:
    VARIABLES_DIR.mkdir(parents=True, exist_ok=True)
    return VARIABLES_DIR


def _resolve_variables_path(filename: str) -> Path:
    base_dir = _ensure_variables_dir().resolve()
    file_path = (base_dir / filename).resolve()
    try:
        file_path.relative_to(base_dir)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Geçersiz dosya yolu") from exc
    return file_path

@router.post("/upload")
async def upload_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        content = await file.read()
        content_str = content.decode()
        
        # Hash hesapla
        hash_obj = hashlib.sha256(content)
        file_hash = hash_obj.hexdigest()
        
        # Dosya tipini belirle
        file_extension = file.filename.split('.')[-1].lower()
        if file_extension not in [e.value for e in FileType]:
            raise HTTPException(status_code=400, detail="Unsupported file type")
            
        file_type = FileType(file_extension)
        
        # JSON içeriğini parse et
        json_content = None
        if file_type == FileType.json:
            try:
                json_content = json.loads(content_str)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid JSON content")
        
        # Veritabanına kaydet
        db_file = DBFile(
            name=file.filename,
            type=file_type,
            content=content_str,
            json_content=json_content,
            size=len(content),
            hash=file_hash
        )
        
        db.add(db_file)
        db.commit()
        db.refresh(db_file)
        
        return {"message": "File uploaded successfully", "file_id": db_file.id}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Variables dosya yönetimi
@router.get("/variables")
async def get_variables_files():
    """Variables klasöründeki dosyaları listele"""
    try:
        variables_dir = _ensure_variables_dir()
        files = []
        for file_path in variables_dir.iterdir():
            if file_path.is_file():
                stat = file_path.stat()
                files.append({
                    "id": len(files) + 1,
                    "name": file_path.name,
                    "size": stat.st_size,
                    "created_at": stat.st_ctime,
                    "updated_at": stat.st_mtime,
                    "type": file_path.suffix[1:] if file_path.suffix else "txt"
                })
        
        # Tarihe göre sırala (en yeni önce)
        files.sort(key=lambda x: x["updated_at"], reverse=True)
        return {"files": files}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Variables dosyalari listelenemedi", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Variables dosyaları listelenirken hata: {str(e)}")

@router.get("/variables/{filename}")
async def get_variables_file_content(filename: str):
    """Variables dosyasının içeriğini getir"""
    try:
        file_path = _resolve_variables_path(filename)
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Dosya bulunamadı")
        
        with file_path.open('r', encoding='utf-8') as f:
            content = f.read()
        
        return {"content": content}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Dosya içeriği okunurken hata: {str(e)}")

@router.put("/variables/{filename}")
async def update_variables_file(filename: str, request: Request):
    """Variables dosyasını güncelle veya oluştur"""
    try:
        file_path = _resolve_variables_path(filename)
        
        # Request body'den içeriği al
        content = await request.body()
        content_str = content.decode('utf-8')
        
        # Dosyayı güncelle veya oluştur
        with file_path.open('w', encoding='utf-8') as f:
            f.write(content_str)
        
        return {"message": "Dosya başarıyla güncellendi"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Dosya güncellenirken hata: {str(e)}")

@router.delete("/variables/{filename}")
async def delete_variables_file(filename: str):
    """Variables dosyasını sil"""
    try:
        file_path = _resolve_variables_path(filename)
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Dosya bulunamadı")
        
        file_path.unlink()
        return {"message": "Dosya başarıyla silindi"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Dosya silinirken hata: {str(e)}")

# Genel dosya yönetimi
@router.get("/", response_model=List[FileResponse])
def get_files(db: Session = Depends(get_db)):
    files = db.query(DBFile).filter(DBFile.deleted_at.is_(None)).all()
    return files

@router.get("/{file_id}", response_model=FileResponse)
def get_file(file_id: int, db: Session = Depends(get_db)):
    file = db.query(DBFile).filter(DBFile.id == file_id, DBFile.deleted_at.is_(None)).first()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    return file

@router.delete("/{file_id}")
def delete_file(file_id: int, db: Session = Depends(get_db)):
    file = db.query(DBFile).filter(DBFile.id == file_id, DBFile.deleted_at.is_(None)).first()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")
    
    file.deleted_at = func.now()
    db.commit()
    return {"message": "File deleted successfully"} 
