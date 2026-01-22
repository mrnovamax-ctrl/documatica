"""
API endpoints для работы с Dadata - автозаполнение по ИНН
"""

import os
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from dadata import Dadata

router = APIRouter()

# Dadata API ключи
DADATA_TOKEN = os.getenv("DADATA_TOKEN", "41d63b47b1400f33d49570eac86ca3125ab40e67")
DADATA_SECRET = os.getenv("DADATA_SECRET", "112e864e62a73531a1661a5096f980c150bfc01f")


class CompanySearchRequest(BaseModel):
    """Запрос на поиск компании по ИНН"""
    inn: str
    kpp: Optional[str] = None
    branch_type: Optional[str] = "MAIN"  # MAIN или BRANCH


class CompanyInfo(BaseModel):
    """Информация о компании"""
    name: str
    full_name: Optional[str] = None
    inn: str
    kpp: Optional[str] = None
    ogrn: Optional[str] = None
    address: Optional[str] = None
    address_full: Optional[str] = None
    org_type: str  # "ooo" или "ip"
    director_name: Optional[str] = None
    director_position: Optional[str] = None
    okpo: Optional[str] = None
    oktmo: Optional[str] = None
    okato: Optional[str] = None
    okved: Optional[str] = None
    status: Optional[str] = None


@router.post("/company/by-inn", response_model=CompanyInfo)
async def find_company_by_inn(request: CompanySearchRequest):
    """
    Поиск компании по ИНН через Dadata (POST)
    """
    return await _find_company_by_inn(request.inn, request.kpp, request.branch_type)


@router.get("/company", response_model=CompanyInfo)
async def find_company_by_inn_get(inn: str, kpp: Optional[str] = None, branch_type: str = "MAIN"):
    """
    Поиск компании по ИНН через Dadata (GET)
    """
    return await _find_company_by_inn(inn, kpp, branch_type)


async def _find_company_by_inn(inn: str, kpp: Optional[str] = None, branch_type: str = "MAIN"):
    """
    Общая логика поиска компании по ИНН
    """
    if not inn or len(inn) < 10:
        raise HTTPException(status_code=400, detail="ИНН должен содержать минимум 10 символов")
    
    try:
        dadata = Dadata(DADATA_TOKEN, DADATA_SECRET)
        
        # Параметры запроса
        params = {
            "query": inn,
            "branch_type": branch_type or "MAIN"
        }
        
        # Если указан КПП, добавляем его
        if kpp:
            params["kpp"] = kpp
        
        result = dadata.find_by_id("party", **params)
        
        if not result:
            raise HTTPException(status_code=404, detail="Компания не найдена")
        
        company = result[0]
        data = company.get("data", {})
        
        # Определяем тип организации
        org_type = "ip" if data.get("type") == "INDIVIDUAL" else "ooo"
        
        # Получаем наименование
        name_data = data.get("name", {})
        name = name_data.get("short_with_opf") or name_data.get("full_with_opf") or company.get("value", "")
        full_name = name_data.get("full_with_opf") or name
        
        # Для ИП берём ФИО
        if org_type == "ip":
            fio = data.get("fio", {})
            if fio:
                fio_parts = [fio.get("surname", ""), fio.get("name", ""), fio.get("patronymic", "")]
                fio_str = " ".join(p for p in fio_parts if p)
                if fio_str:
                    name = f"ИП {fio_str}"
                    full_name = f"Индивидуальный предприниматель {fio_str}"
        
        # Адрес
        address_data = data.get("address", {})
        address = address_data.get("value", "")
        address_full = address_data.get("unrestricted_value", address)
        
        # Руководитель
        management = data.get("management", {})
        director_name = management.get("name", "")
        director_position = management.get("post", "")
        
        # Для ИП руководитель = сам ИП
        if org_type == "ip" and not director_name:
            fio = data.get("fio", {})
            if fio:
                fio_parts = [fio.get("surname", ""), fio.get("name", ""), fio.get("patronymic", "")]
                director_name = " ".join(p for p in fio_parts if p)
                director_position = "Индивидуальный предприниматель"
        
        # Статус
        state = data.get("state", {})
        status = state.get("status", "")
        
        return CompanyInfo(
            name=name,
            full_name=full_name,
            inn=data.get("inn", inn),
            kpp=data.get("kpp"),
            ogrn=data.get("ogrn"),
            address=address,
            address_full=address_full,
            org_type=org_type,
            director_name=director_name,
            director_position=director_position,
            okpo=data.get("okpo"),
            oktmo=data.get("oktmo"),
            okato=data.get("okato"),
            okved=data.get("okved"),
            status=status
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при обращении к Dadata: {str(e)}")


@router.get("/company/suggest/{query}")
async def suggest_company(query: str, count: int = 5):
    """
    Подсказки компаний по названию или ИНН
    """
    if not query or len(query) < 3:
        return {"suggestions": []}
    
    try:
        dadata = Dadata(DADATA_TOKEN, DADATA_SECRET)
        
        result = dadata.suggest("party", query, count=count)
        
        suggestions = []
        for company in result:
            data = company.get("data", {})
            name_data = data.get("name", {})
            
            org_type = "ip" if data.get("type") == "INDIVIDUAL" else "ooo"
            name = name_data.get("short_with_opf") or company.get("value", "")
            
            address_data = data.get("address", {})
            
            suggestions.append({
                "name": name,
                "inn": data.get("inn", ""),
                "kpp": data.get("kpp"),
                "address": address_data.get("value", ""),
                "org_type": org_type
            })
        
        return {"suggestions": suggestions}
        
    except Exception as e:
        return {"suggestions": [], "error": str(e)}


class BankInfo(BaseModel):
    """Информация о банке"""
    name: str
    bik: str
    correspondent_account: Optional[str] = None
    address: Optional[str] = None


@router.get("/bank", response_model=BankInfo)
async def find_bank_by_bik(bik: str):
    """
    Поиск банка по БИК через Dadata
    """
    if not bik or len(bik) != 9:
        raise HTTPException(status_code=400, detail="БИК должен содержать 9 цифр")
    
    try:
        dadata = Dadata(DADATA_TOKEN, DADATA_SECRET)
        result = dadata.find_by_id("bank", bik)
        
        if not result:
            raise HTTPException(status_code=404, detail="Банк не найден")
        
        bank = result[0]
        data = bank.get("data", {})
        name_data = data.get("name", {})
        address_data = data.get("address", {})
        
        return BankInfo(
            name=name_data.get("payment") or name_data.get("short") or bank.get("value", ""),
            bik=data.get("bic", bik),
            correspondent_account=data.get("correspondent_account"),
            address=address_data.get("value") if address_data else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при обращении к Dadata: {str(e)}")
