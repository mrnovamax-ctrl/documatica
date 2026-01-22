"""
API endpoints для организаций и контрагентов
"""

import json
import os
from pathlib import Path
from datetime import datetime
import uuid
from typing import List, Optional

import jwt
from fastapi import APIRouter, HTTPException, Header, Cookie

from app.schemas.organizations import (
    Organization, OrganizationCreate, OrganizationUpdate,
    Contractor, ContractorCreate, ContractorUpdate
)

router = APIRouter()

# Настройки JWT (должны совпадать с auth.py)
SECRET_KEY = os.getenv("SECRET_KEY", "documatica-secret-key-change-in-production")
ALGORITHM = "HS256"

# Путь к файлам данных (для MVP используем JSON файлы)
DATA_DIR = Path(__file__).parent.parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

ORGANIZATIONS_FILE = DATA_DIR / "organizations.json"
CONTRACTORS_FILE = DATA_DIR / "contractors.json"


def get_user_id_from_token(authorization: Optional[str] = None, access_token: Optional[str] = None) -> Optional[int]:
    """Извлекает user_id из JWT токена (Header или Cookie). Возвращает None если токен отсутствует или невалиден."""
    token = None
    
    # Сначала пробуем Header
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
    # Потом Cookie
    elif access_token:
        token = access_token
    
    if not token:
        return None
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        # Токен использует "sub" для user_id
        user_id_str = payload.get("sub") or payload.get("user_id")
        return int(user_id_str) if user_id_str else None
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, ValueError, TypeError):
        return None


def load_organizations() -> List[dict]:
    """Загрузка организаций из файла"""
    if ORGANIZATIONS_FILE.exists():
        with open(ORGANIZATIONS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


def save_organizations(organizations: List[dict]):
    """Сохранение организаций в файл"""
    with open(ORGANIZATIONS_FILE, 'w', encoding='utf-8') as f:
        json.dump(organizations, f, ensure_ascii=False, indent=2)


def load_contractors() -> List[dict]:
    """Загрузка контрагентов из файла"""
    if CONTRACTORS_FILE.exists():
        with open(CONTRACTORS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


def save_contractors(contractors: List[dict]):
    """Сохранение контрагентов в файл"""
    with open(CONTRACTORS_FILE, 'w', encoding='utf-8') as f:
        json.dump(contractors, f, ensure_ascii=False, indent=2)


# ============== ОРГАНИЗАЦИИ ==============

@router.get("/organizations/")
@router.get("/organizations", response_model=List[Organization])
async def get_organizations(
    authorization: Optional[str] = Header(None),
    access_token: Optional[str] = Cookie(None)
):
    """Получить список организаций пользователя"""
    user_id = get_user_id_from_token(authorization, access_token)
    organizations = load_organizations()
    
    # Фильтруем по user_id
    if user_id is not None:
        return [org for org in organizations if org.get("user_id") == user_id]
    return []  # Без авторизации возвращаем пустой список


@router.get("/organizations/{org_id}", response_model=Organization)
async def get_organization(org_id: str):
    """Получить организацию по ID"""
    organizations = load_organizations()
    for org in organizations:
        if org["id"] == org_id:
            return org
    raise HTTPException(status_code=404, detail="Организация не найдена")


@router.post("/organizations/")
@router.post("/organizations", response_model=Organization)
async def create_organization(
    org: OrganizationCreate,
    authorization: Optional[str] = Header(None),
    access_token: Optional[str] = Cookie(None)
):
    """Создать новую организацию"""
    user_id = get_user_id_from_token(authorization, access_token)
    print(f"[DEBUG] Creating org for user_id={user_id}, inn={org.inn}")
    organizations = load_organizations()
    
    # Проверяем уникальность ИНН только для данного пользователя
    for existing in organizations:
        # Дубликат только если совпадает ИНН И user_id (оба не None)
        if existing["inn"] == org.inn and existing.get("user_id") == user_id and user_id is not None:
            raise HTTPException(status_code=400, detail="Организация с таким ИНН уже существует")
    
    now = datetime.now().isoformat()
    new_org = {
        "id": str(uuid.uuid4()),
        **org.model_dump(),
        "user_id": user_id,
        "created_at": now,
        "updated_at": now
    }
    
    # Конвертируем date в строку
    if new_org.get("certificate_date"):
        new_org["certificate_date"] = new_org["certificate_date"].isoformat()
    
    organizations.append(new_org)
    save_organizations(organizations)
    return new_org


@router.put("/organizations/{org_id}", response_model=Organization)
async def update_organization(org_id: str, org: OrganizationUpdate):
    """Обновить организацию"""
    organizations = load_organizations()
    
    for i, existing in enumerate(organizations):
        if existing["id"] == org_id:
            update_data = org.model_dump(exclude_unset=True)
            
            # Конвертируем date в строку
            if update_data.get("certificate_date"):
                update_data["certificate_date"] = update_data["certificate_date"].isoformat()
            
            organizations[i].update(update_data)
            organizations[i]["updated_at"] = datetime.now().isoformat()
            save_organizations(organizations)
            return organizations[i]
    
    raise HTTPException(status_code=404, detail="Организация не найдена")


@router.delete("/organizations/{org_id}")
async def delete_organization(org_id: str):
    """Удалить организацию"""
    organizations = load_organizations()
    
    for i, org in enumerate(organizations):
        if org["id"] == org_id:
            organizations.pop(i)
            save_organizations(organizations)
            return {"success": True, "message": "Организация удалена"}
    
    raise HTTPException(status_code=404, detail="Организация не найдена")


# ============== КОНТРАГЕНТЫ ==============

@router.get("/contractors/")
@router.get("/contractors", response_model=List[Contractor])
async def get_contractors(
    authorization: Optional[str] = Header(None),
    access_token: Optional[str] = Cookie(None)
):
    """Получить список контрагентов пользователя"""
    user_id = get_user_id_from_token(authorization, access_token)
    contractors = load_contractors()
    
    # Фильтруем по user_id
    if user_id is not None:
        return [c for c in contractors if c.get("user_id") == user_id]
    return []  # Без авторизации возвращаем пустой список


@router.get("/contractors/{contractor_id}", response_model=Contractor)
async def get_contractor(contractor_id: str):
    """Получить контрагента по ID"""
    contractors = load_contractors()
    for c in contractors:
        if c["id"] == contractor_id:
            return c
    raise HTTPException(status_code=404, detail="Контрагент не найден")


@router.get("/contractors/search/{inn}")
async def search_contractor_by_inn(inn: str):
    """Поиск контрагента по ИНН"""
    contractors = load_contractors()
    for c in contractors:
        if c["inn"] == inn:
            return c
    raise HTTPException(status_code=404, detail="Контрагент не найден")


@router.post("/contractors/")
@router.post("/contractors", response_model=Contractor)
async def create_contractor(
    contractor: ContractorCreate,
    authorization: Optional[str] = Header(None),
    access_token: Optional[str] = Cookie(None)
):
    """Создать нового контрагента"""
    user_id = get_user_id_from_token(authorization, access_token)
    contractors = load_contractors()
    
    # Проверяем уникальность ИНН для данного пользователя
    for existing in contractors:
        if existing["inn"] == contractor.inn and existing.get("user_id") == user_id:
            raise HTTPException(status_code=400, detail="Контрагент с таким ИНН уже существует")
    
    now = datetime.now().isoformat()
    new_contractor = {
        "id": str(uuid.uuid4()),
        **contractor.model_dump(),
        "user_id": user_id,
        "created_at": now,
        "updated_at": now
    }
    
    contractors.append(new_contractor)
    save_contractors(contractors)
    return new_contractor


@router.put("/contractors/{contractor_id}", response_model=Contractor)
async def update_contractor(contractor_id: str, contractor: ContractorUpdate):
    """Обновить контрагента"""
    contractors = load_contractors()
    
    for i, existing in enumerate(contractors):
        if existing["id"] == contractor_id:
            update_data = contractor.model_dump(exclude_unset=True)
            contractors[i].update(update_data)
            contractors[i]["updated_at"] = datetime.now().isoformat()
            save_contractors(contractors)
            return contractors[i]
    
    raise HTTPException(status_code=404, detail="Контрагент не найден")


@router.delete("/contractors/{contractor_id}")
async def delete_contractor(contractor_id: str):
    """Удалить контрагента"""
    contractors = load_contractors()
    
    for i, c in enumerate(contractors):
        if c["id"] == contractor_id:
            contractors.pop(i)
            save_contractors(contractors)
            return {"success": True, "message": "Контрагент удалён"}
    
    raise HTTPException(status_code=404, detail="Контрагент не найден")
