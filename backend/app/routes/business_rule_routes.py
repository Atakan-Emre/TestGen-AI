
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List
from pathlib import Path
from ..database import SessionLocal
from ..models.business_rule_model import BusinessRule
from ..schemas.business_rule_schema import BusinessRuleCreate, BusinessRuleUpdate, BusinessRuleResponse

router = APIRouter(prefix="/api/business-rules", tags=["business-rules"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/", response_model=List[BusinessRuleResponse])
async def get_business_rules(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Tüm iş kurallarını listele"""
    try:
        rules = db.query(BusinessRule).filter(BusinessRule.is_active == True).offset(skip).limit(limit).all()
        return rules
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"İş kuralları listelenirken hata: {str(e)}")

@router.get("/files")
async def get_business_rule_files():
    """data/input/BusinessRules/ klasöründeki iş kuralı dosyalarını listele"""
    try:
        business_rules_dir = Path("data/input/BusinessRules")
        if not business_rules_dir.exists():
            return {"files": []}
        
        files = []
        for file_path in business_rules_dir.glob("*.txt"):
            if file_path.is_file():
                stat = file_path.stat()
                files.append({
                    "name": file_path.name,
                    "size": stat.st_size,
                    "created_at": stat.st_ctime,
                    "updated_at": stat.st_mtime,
                    "type": "txt"
                })
        
        # Tarihe göre sırala (en yeni önce)
        files.sort(key=lambda x: x["updated_at"], reverse=True)
        return {"files": files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Dosyalar listelenirken hata: {str(e)}")

@router.get("/{rule_id}", response_model=BusinessRuleResponse)
async def get_business_rule(rule_id: int, db: Session = Depends(get_db)):
    """Belirli bir iş kuralını getir"""
    try:
        rule = db.query(BusinessRule).filter(BusinessRule.id == rule_id).first()
        if not rule:
            raise HTTPException(status_code=404, detail="İş kuralı bulunamadı")
        return rule
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"İş kuralı getirilirken hata: {str(e)}")

@router.post("/", response_model=BusinessRuleResponse)
async def create_business_rule(rule: BusinessRuleCreate, db: Session = Depends(get_db)):
    """Yeni iş kuralı oluştur"""
    try:
        db_rule = BusinessRule(
            name=rule.name,
            content=rule.content,
            source=rule.source,
            is_active=rule.is_active
        )
        db.add(db_rule)
        db.commit()
        db.refresh(db_rule)
        return db_rule
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"İş kuralı oluşturulurken hata: {str(e)}")

@router.put("/{rule_id}", response_model=BusinessRuleResponse)
async def update_business_rule(rule_id: int, rule: BusinessRuleUpdate, db: Session = Depends(get_db)):
    """İş kuralını güncelle"""
    try:
        db_rule = db.query(BusinessRule).filter(BusinessRule.id == rule_id).first()
        if not db_rule:
            raise HTTPException(status_code=404, detail="İş kuralı bulunamadı")
        
        if rule.name is not None:
            db_rule.name = rule.name
        if rule.content is not None:
            db_rule.content = rule.content
        if rule.is_active is not None:
            db_rule.is_active = rule.is_active
        
        db.commit()
        db.refresh(db_rule)
        return db_rule
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"İş kuralı güncellenirken hata: {str(e)}")

@router.delete("/{rule_id}")
async def delete_business_rule(rule_id: int, db: Session = Depends(get_db)):
    """İş kuralını sil (soft delete)"""
    try:
        db_rule = db.query(BusinessRule).filter(BusinessRule.id == rule_id).first()
        if not db_rule:
            raise HTTPException(status_code=404, detail="İş kuralı bulunamadı")
        
        db_rule.is_active = False
        db.commit()
        return {"message": "İş kuralı başarıyla silindi"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"İş kuralı silinirken hata: {str(e)}")

@router.delete("/")
async def delete_all_business_rules(db: Session = Depends(get_db)):
    """Tüm iş kurallarını sil (soft delete)"""
    try:
        db.query(BusinessRule).update({"is_active": False})
        db.commit()
        return {"message": "Tüm iş kuralları başarıyla silindi"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"İş kuralları silinirken hata: {str(e)}")

@router.get("/files/{filename}")
async def get_business_rule_file_content(filename: str):
    """Belirli bir iş kuralı dosyasının içeriğini getir"""
    try:
        business_rules_dir = Path("data/input/BusinessRules")
        file_path = business_rules_dir / filename
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Dosya bulunamadı")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return {
            "filename": filename,
            "type": "txt",
            "content": content
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Dosya okunamadı: {str(e)}")

@router.delete("/files/{filename}")
async def delete_business_rule_file(filename: str):
    """İş kuralı dosyasını sil"""
    try:
        business_rules_dir = Path("data/input/BusinessRules")
        file_path = business_rules_dir / filename
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Dosya bulunamadı")
        
        file_path.unlink()
        return {"message": f"{filename} dosyası başarıyla silindi"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Dosya silinemedi: {str(e)}")

@router.put("/files/{filename}")
async def rename_business_rule_file(filename: str, new_name: str):
    """İş kuralı dosyasını yeniden adlandır"""
    try:
        business_rules_dir = Path("data/input/BusinessRules")
        old_path = business_rules_dir / filename
        new_path = business_rules_dir / new_name
        
        if not old_path.exists():
            raise HTTPException(status_code=404, detail="Dosya bulunamadı")
        
        if new_path.exists():
            raise HTTPException(status_code=400, detail="Bu isimde bir dosya zaten mevcut")
        
        old_path.rename(new_path)
        return {"message": f"Dosya başarıyla '{new_name}' olarak yeniden adlandırıldı"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Dosya yeniden adlandırılamadı: {str(e)}")

@router.delete("/files")
async def delete_all_business_rule_files():
    """Tüm iş kuralı dosyalarını sil"""
    try:
        business_rules_dir = Path("data/input/BusinessRules")
        if not business_rules_dir.exists():
            return {"message": "İş kuralı dosyaları bulunamadı"}
        
        deleted_count = 0
        for file_path in business_rules_dir.glob("*.txt"):
            if file_path.is_file():
                file_path.unlink()
                deleted_count += 1
        
        return {"message": f"{deleted_count} iş kuralı dosyası başarıyla silindi"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Dosyalar silinemedi: {str(e)}")
