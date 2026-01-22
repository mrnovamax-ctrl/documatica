"""
API endpoints для шаблонов документов
"""

import json
import os
from pathlib import Path
from datetime import datetime
import uuid
from typing import List, Optional

import jwt
from fastapi import APIRouter, HTTPException, Header, Cookie
from pydantic import BaseModel, Field

router = APIRouter()

# Настройки JWT
SECRET_KEY = os.getenv("SECRET_KEY", "documatica-secret-key-change-in-production")
ALGORITHM = "HS256"

# Путь к файлам данных
DATA_DIR = Path(__file__).parent.parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

TEMPLATES_FILE = DATA_DIR / "document_templates.json"


def get_user_id_from_token(authorization: Optional[str] = None, access_token: Optional[str] = None) -> Optional[int]:
    """Извлекает user_id из JWT токена."""
    token = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
    elif access_token:
        token = access_token
    
    if not token:
        return None
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id_str = payload.get("sub") or payload.get("user_id")
        return int(user_id_str) if user_id_str else None
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, ValueError, TypeError):
        return None


class TemplateCreate(BaseModel):
    name: str = Field(..., description="Название шаблона")
    doc_type: str = Field("upd", description="Тип документа: upd, schet, akt")
    data: dict = Field(..., description="Данные шаблона")


class TemplateUpdate(BaseModel):
    name: Optional[str] = None
    data: Optional[dict] = None


class Template(BaseModel):
    id: str
    name: str
    doc_type: str
    data: dict
    user_id: int
    created_at: str
    updated_at: str


def load_templates() -> List[dict]:
    """Загрузка шаблонов из файла"""
    if TEMPLATES_FILE.exists():
        with open(TEMPLATES_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


def save_templates(templates: List[dict]):
    """Сохранение шаблонов в файл"""
    with open(TEMPLATES_FILE, 'w', encoding='utf-8') as f:
        json.dump(templates, f, ensure_ascii=False, indent=2)


@router.get("/templates/")
@router.get("/templates", response_model=List[Template])
async def get_templates(
    authorization: Optional[str] = Header(None),
    access_token: Optional[str] = Cookie(None)
):
    """Получить список шаблонов пользователя"""
    user_id = get_user_id_from_token(authorization, access_token)
    templates = load_templates()
    
    if user_id is not None:
        return [t for t in templates if t.get("user_id") == user_id]
    return []


@router.get("/templates/{template_id}", response_model=Template)
async def get_template(
    template_id: str,
    authorization: Optional[str] = Header(None),
    access_token: Optional[str] = Cookie(None)
):
    """Получить шаблон по ID"""
    user_id = get_user_id_from_token(authorization, access_token)
    templates = load_templates()
    
    for t in templates:
        if t["id"] == template_id:
            # Проверяем принадлежность пользователю
            if user_id is None or t.get("user_id") != user_id:
                raise HTTPException(status_code=403, detail="Нет доступа к этому шаблону")
            return t
    
    raise HTTPException(status_code=404, detail="Шаблон не найден")


@router.post("/templates/")
@router.post("/templates", response_model=Template)
async def create_template(
    template: TemplateCreate,
    authorization: Optional[str] = Header(None),
    access_token: Optional[str] = Cookie(None)
):
    """Создать новый шаблон"""
    user_id = get_user_id_from_token(authorization, access_token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Необходима авторизация")
    
    templates = load_templates()
    
    now = datetime.now().isoformat()
    new_template = {
        "id": str(uuid.uuid4()),
        "name": template.name,
        "doc_type": template.doc_type,
        "data": template.data,
        "user_id": user_id,
        "created_at": now,
        "updated_at": now
    }
    
    templates.append(new_template)
    save_templates(templates)
    
    return new_template


@router.put("/templates/{template_id}", response_model=Template)
async def update_template(
    template_id: str, 
    template: TemplateUpdate,
    authorization: Optional[str] = Header(None),
    access_token: Optional[str] = Cookie(None)
):
    """Обновить шаблон"""
    user_id = get_user_id_from_token(authorization, access_token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Необходима авторизация")
    
    templates = load_templates()
    
    for i, existing in enumerate(templates):
        if existing["id"] == template_id:
            if existing.get("user_id") != user_id:
                raise HTTPException(status_code=403, detail="Нет доступа к этому шаблону")
            
            if template.name:
                existing["name"] = template.name
            if template.data:
                existing["data"] = template.data
            existing["updated_at"] = datetime.now().isoformat()
            
            save_templates(templates)
            return existing
    
    raise HTTPException(status_code=404, detail="Шаблон не найден")


@router.delete("/templates/{template_id}")
async def delete_template(
    template_id: str,
    authorization: Optional[str] = Header(None),
    access_token: Optional[str] = Cookie(None)
):
    """Удалить шаблон"""
    user_id = get_user_id_from_token(authorization, access_token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Необходима авторизация")
    
    templates = load_templates()
    
    for i, t in enumerate(templates):
        if t["id"] == template_id:
            if t.get("user_id") != user_id:
                raise HTTPException(status_code=403, detail="Нет доступа к этому шаблону")
            
            templates.pop(i)
            save_templates(templates)
            return {"success": True, "message": "Шаблон удален"}
    
    raise HTTPException(status_code=404, detail="Шаблон не найден")
