"""
Счет на оплату - публичные страницы (хаб и лендинги)
Аналогичная структура с УПД
"""

import yaml
from pathlib import Path
from functools import lru_cache
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from typing import Dict, Any, Optional

from app.core.templates import templates
from app.core.content import load_content

router = APIRouter()

# Путь к конфигу страниц
CONFIG_PATH = Path(__file__).parent.parent.parent / "content" / "schet" / "_pages.yaml"


@lru_cache(maxsize=1)
def load_schet_pages_config() -> Dict[str, Any]:
    """Загрузка конфигурации страниц счетов"""
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}


def get_landing_config(slug: str) -> Optional[Dict[str, Any]]:
    """Получение конфига лендинга по slug"""
    config = load_schet_pages_config()
    return config.get("landings", {}).get(slug)


def get_info_config(slug: str) -> Optional[Dict[str, Any]]:
    """Получение конфига информационной страницы по slug"""
    config = load_schet_pages_config()
    return config.get("info_pages", {}).get(slug)


def get_download_config(slug: str) -> Optional[Dict[str, Any]]:
    """Получение конфига страницы скачивания по slug"""
    config = load_schet_pages_config()
    return config.get("downloads", {}).get(slug)


# ============== ГЛАВНАЯ СТРАНИЦА РАЗДЕЛА ==============

@router.get("/", response_class=HTMLResponse)
async def schet_hub(request: Request):
    """Хаб Счетов - главная страница раздела"""
    content = load_content("schet/index")
    
    return templates.TemplateResponse(
        request=request,
        name="public/schet/index.html",
        context={
            "content": content,
            "breadcrumbs": [
                {"title": "Главная", "url": "/"},
                {"title": "Счет на оплату", "url": None},
            ]
        }
    )


# ============== УНИВЕРСАЛЬНЫЙ РОУТЕР ЛЕНДИНГОВ ==============

@router.get("/ip/", response_class=HTMLResponse)
@router.get("/ooo/", response_class=HTMLResponse)
@router.get("/samozanyatye/", response_class=HTMLResponse)
@router.get("/s-nds/", response_class=HTMLResponse)
@router.get("/bez-nds/", response_class=HTMLResponse)
@router.get("/qr-kod/", response_class=HTMLResponse)
async def schet_landing(request: Request):
    """Универсальный обработчик лендингов счетов"""
    path = request.url.path
    slug = path.strip("/").split("/")[-1]
    
    config = get_landing_config(slug)
    if not config:
        raise HTTPException(status_code=404, detail="Страница не найдена")
    
    content = load_content(config["content_file"])
    
    return templates.TemplateResponse(
        request=request,
        name="public/schet/landing.html",
        context={
            "content": content,
            "breadcrumbs": [
                {"title": "Главная", "url": "/"},
                {"title": "Счет на оплату", "url": "/schet/"},
                {"title": config["breadcrumb"], "url": None},
            ]
        }
    )


# ============== ИНФОРМАЦИОННЫЕ СТРАНИЦЫ ==============

@router.get("/obrazec/", response_class=HTMLResponse)
async def schet_info(request: Request):
    """Информационные страницы счетов"""
    path = request.url.path
    slug = path.strip("/").split("/")[-1]
    
    config = get_info_config(slug)
    if not config:
        raise HTTPException(status_code=404, detail="Страница не найдена")
    
    content = load_content(config["content_file"])
    
    return templates.TemplateResponse(
        request=request,
        name="public/schet/info.html",
        context={
            "content": content,
            "breadcrumbs": [
                {"title": "Главная", "url": "/"},
                {"title": "Счет на оплату", "url": "/schet/"},
                {"title": config["breadcrumb"], "url": None},
            ]
        }
    )


# ============== СТРАНИЦЫ СКАЧИВАНИЯ ==============

@router.get("/blank-excel/", response_class=HTMLResponse)
async def schet_download(request: Request):
    """Страницы скачивания бланков"""
    path = request.url.path
    slug = path.strip("/").split("/")[-1]
    
    config = get_download_config(slug)
    if not config:
        raise HTTPException(status_code=404, detail="Страница не найдена")
    
    return templates.TemplateResponse(
        request=request,
        name="public/schet/download.html",
        context={
            "meta": {
                "title": config["title"],
                "description": config["description"],
            },
            "page": {
                "h1": config["h1"],
                "format": config["format"],
                "file_url": config["file_url"],
            },
            "breadcrumbs": [
                {"title": "Главная", "url": "/"},
                {"title": "Счет на оплату", "url": "/schet/"},
                {"title": config["breadcrumb"], "url": None},
            ]
        }
    )


# ============== РЕДИРЕКТЫ (без trailing slash) ==============

@router.get("/ip", response_class=RedirectResponse)
@router.get("/ooo", response_class=RedirectResponse)
@router.get("/samozanyatye", response_class=RedirectResponse)
@router.get("/s-nds", response_class=RedirectResponse)
@router.get("/bez-nds", response_class=RedirectResponse)
@router.get("/qr-kod", response_class=RedirectResponse)
@router.get("/obrazec", response_class=RedirectResponse)
@router.get("/blank-excel", response_class=RedirectResponse)
async def schet_redirect(request: Request):
    """Редирект на URL с trailing slash"""
    path = request.url.path
    return RedirectResponse(url=f"{path}/", status_code=301)
