"""
Dashboard - генератор Счёта на оплату
"""

import json
from datetime import date
from pathlib import Path
from fastapi import APIRouter, Request, Path as PathParam
from fastapi.responses import HTMLResponse
from typing import Optional

from app.core.templates import templates
from app.dashboard.context import get_dashboard_context, require_auth

router = APIRouter()

# Путь к сохранённым документам
DOCUMENTS_DIR = Path(__file__).parent.parent.parent / "documents"


@router.get("/create/", response_class=HTMLResponse)
async def invoice_create(request: Request, preset: Optional[str] = None):
    """
    Страница создания Счёта на оплату
    
    Args:
        preset: Пресет для автозаполнения (ooo, ip)
    """
    # Проверка авторизации
    auth_check = require_auth(request)
    if auth_check:
        return auth_check
    
    preset_config = {
        "ooo": {"org_type": "ooo", "has_nds": True},
        "ip": {"org_type": "ip", "has_nds": False},
    }
    
    config = preset_config.get(preset, {})
    
    return templates.TemplateResponse(
        request=request,
        name="dashboard/invoice/create_v12.html",
        context=get_dashboard_context(
            request=request,
            title="Создать счёт на оплату — Documatica",
            active_menu="invoice",
            preset=preset,
            config=config,
            today=date.today().isoformat(),
        )
    )


@router.get("/edit/{document_id}/", response_class=HTMLResponse)
async def invoice_edit(request: Request, document_id: str = PathParam(...)):
    """Страница редактирования счёта"""
    # Проверка авторизации
    auth_check = require_auth(request)
    if auth_check:
        return auth_check
    
    # Загружаем данные документа
    document = None
    form_data = None
    doc_folder = DOCUMENTS_DIR / document_id
    
    # Пробуем metadata.json (новый формат), затем meta.json (старый)
    meta_path = doc_folder / "metadata.json"
    if not meta_path.exists():
        meta_path = doc_folder / "meta.json"
    
    form_data_path = doc_folder / "form_data.json"
    
    if meta_path.exists():
        with open(meta_path, "r", encoding="utf-8") as f:
            document = json.load(f)
    
    if form_data_path.exists():
        with open(form_data_path, "r", encoding="utf-8") as f:
            form_data = json.load(f)
    elif document:
        form_data = document.get("form_data", {})
    
    return templates.TemplateResponse(
        request=request,
        name="dashboard/invoice/create_v12.html",
        context=get_dashboard_context(
            request=request,
            title="Редактировать счёт — Documatica",
            active_menu="invoice",
            edit_document_id=document_id,
            document=document,
            form_data=form_data,
            today=date.today().isoformat(),
        )
    )


@router.get("/{document_id}/", response_class=HTMLResponse)
async def invoice_view(request: Request, document_id: str = PathParam(...)):
    """Страница просмотра счёта"""
    # Проверка авторизации
    auth_check = require_auth(request)
    if auth_check:
        return auth_check
    
    # Загружаем данные документа
    document = None
    doc_folder = DOCUMENTS_DIR / document_id
    
    # Пробуем metadata.json (новый формат), затем meta.json (старый)
    meta_path = doc_folder / "metadata.json"
    if not meta_path.exists():
        meta_path = doc_folder / "meta.json"
    
    if meta_path.exists():
        with open(meta_path, "r", encoding="utf-8") as f:
            document = json.load(f)
            # Преобразуем в объект-like для шаблона
            class DocDict(dict):
                def __getattr__(self, item):
                    return self.get(item)
            document = DocDict(document)
    
    return templates.TemplateResponse(
        request=request,
        name="dashboard/invoice/view.html",
        context=get_dashboard_context(
            request=request,
            title="Просмотр счёта — Documatica",
            active_menu="documents",
            document_id=document_id,
            document=document,
        )
    )

