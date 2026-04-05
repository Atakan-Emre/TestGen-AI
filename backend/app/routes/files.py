from fastapi import APIRouter, HTTPException
from pathlib import Path
from datetime import datetime
import os

router = APIRouter(prefix="/api/files")

@router.get("/scenarios")
async def list_scenarios():
    try:
        # Docker içindeki test_scenarios dizini
        scenario_dir = Path("/app/data/test_scenarios")
        
        if not scenario_dir.exists():
            return []
        
        files = []
        # Tüm .txt dosyalarını listele
        for file_path in scenario_dir.glob("*.txt"):
            stat = file_path.stat()
            files.append({
                "name": file_path.name,
                "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "size": stat.st_size,
                "path": str(file_path)
            })
        
        return files

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Dosya listesi alınamadı: {str(e)}"
        )

@router.get("/scenarios/{filename}")
async def read_scenario(filename: str):
    try:
        file_path = Path("/app/data/test_scenarios") / filename
        
        if not file_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Dosya bulunamadı: {filename}"
            )
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        return {"content": content}

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Dosya okunamadı: {str(e)}"
        )

@router.delete("/scenarios/{filename}")
async def delete_scenario(filename: str):
    try:
        file_path = Path("/app/data/test_scenarios") / filename
        
        if not file_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"Dosya bulunamadı: {filename}"
            )
        
        os.remove(file_path)
        return {"message": f"{filename} başarıyla silindi"}

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Dosya silinemedi: {str(e)}"
        ) 