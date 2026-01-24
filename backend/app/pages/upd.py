"""
УПД - публичные страницы (хаб и лендинги)
Рефакторинг: универсальный роутер на основе конфига
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
CONFIG_PATH = Path(__file__).parent.parent.parent / "content" / "upd" / "_pages.yaml"


@lru_cache(maxsize=1)
def load_upd_pages_config() -> Dict[str, Any]:
    """Загрузка конфигурации УПД страниц"""
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}


def get_landing_config(slug: str) -> Optional[Dict[str, Any]]:
    """Получение конфига лендинга по slug"""
    config = load_upd_pages_config()
    return config.get("landings", {}).get(slug)


def get_info_config(slug: str) -> Optional[Dict[str, Any]]:
    """Получение конфига информационной страницы по slug"""
    config = load_upd_pages_config()
    info_pages = config.get("info_pages", {})
    
    # Прямой поиск
    if slug in info_pages:
        return info_pages[slug]
    
    # Поиск по алиасам
    for page_slug, page_config in info_pages.items():
        if slug in page_config.get("aliases", []):
            return page_config
    
    return None


def get_download_config(slug: str) -> Optional[Dict[str, Any]]:
    """Получение конфига страницы скачивания по slug"""
    config = load_upd_pages_config()
    return config.get("downloads", {}).get(slug)


# ============== ГЛАВНАЯ СТРАНИЦА РАЗДЕЛА ==============

@router.get("/", response_class=HTMLResponse)
async def upd_hub(request: Request):
    """Хаб УПД - главная страница раздела"""
    content = load_content("upd/index")
    
    return templates.TemplateResponse(
        request=request,
        name="public/upd/index.html",
        context={
            "content": content,
            "breadcrumbs": [
                {"title": "Главная", "url": "/"},
                {"title": "УПД", "url": None},
            ]
        }
    )


# ============== УНИВЕРСАЛЬНЫЙ РОУТЕР ЛЕНДИНГОВ ==============

# Определяем все возможные лендинги статически для FastAPI
LANDING_SLUGS = ["ooo", "ip", "samozanyatye", "s-nds", "bez-nds", "usn", "2026", "xml-edo"]


@router.get("/ooo/", response_class=HTMLResponse)
@router.get("/ip/", response_class=HTMLResponse)
@router.get("/samozanyatye/", response_class=HTMLResponse)
@router.get("/s-nds/", response_class=HTMLResponse)
@router.get("/bez-nds/", response_class=HTMLResponse)
@router.get("/usn/", response_class=HTMLResponse)
@router.get("/2026/", response_class=HTMLResponse)
@router.get("/xml-edo/", response_class=HTMLResponse)
async def upd_landing(request: Request):
    """Универсальный обработчик лендингов УПД"""
    # Извлекаем slug из пути
    path = request.url.path
    slug = path.strip("/").split("/")[-1]
    
    # Получаем конфиг
    config = get_landing_config(slug)
    if not config:
        raise HTTPException(status_code=404, detail="Страница не найдена")
    
    # Загружаем контент
    content = load_content(config["content_file"])
    
    return templates.TemplateResponse(
        request=request,
        name="public/upd/landing.html",
        context={
            "content": content,
            "breadcrumbs": [
                {"title": "Главная", "url": "/"},
                {"title": "УПД", "url": "/upd/"},
                {"title": config["breadcrumb"], "url": None},
            ]
        }
    )


# ============== ИНФОРМАЦИОННЫЕ СТРАНИЦЫ ==============

@router.get("/obrazec/", response_class=HTMLResponse)
@router.get("/obrazec-zapolneniya/", response_class=HTMLResponse)
async def upd_info(request: Request):
    """Информационные страницы УПД"""
    path = request.url.path
    slug = path.strip("/").split("/")[-1]
    
    config = get_info_config(slug)
    if not config:
        raise HTTPException(status_code=404, detail="Страница не найдена")
    
    content = load_content(config["content_file"])
    
    return templates.TemplateResponse(
        request=request,
        name="public/upd/info.html",
        context={
            "content": content,
            "breadcrumbs": [
                {"title": "Главная", "url": "/"},
                {"title": "УПД", "url": "/upd/"},
                {"title": config["breadcrumb"], "url": None},
            ]
        }
    )


# ============== СТРАНИЦЫ СКАЧИВАНИЯ ==============

@router.get("/blank-excel/", response_class=HTMLResponse)
@router.get("/blank-word/", response_class=HTMLResponse)
async def upd_download(request: Request):
    """Страницы скачивания бланков"""
    path = request.url.path
    slug = path.strip("/").split("/")[-1]
    
    config = get_download_config(slug)
    if not config:
        raise HTTPException(status_code=404, detail="Страница не найдена")
    
    return templates.TemplateResponse(
        request=request,
        name="public/upd/download.html",
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
                {"title": "УПД", "url": "/upd/"},
                {"title": config["breadcrumb"], "url": None},
            ]
        }
    )


# ============== РЕДИРЕКТЫ (без trailing slash) ==============

REDIRECT_SLUGS = [
    "s-nds", "bez-nds", "ooo", "ip", "samozanyatye", "usn", "2026",
    "obrazec-zapolneniya", "xml-edo", "blank-excel", "blank-word"
]


@router.get("/s-nds", response_class=RedirectResponse)
@router.get("/bez-nds", response_class=RedirectResponse)
@router.get("/ooo", response_class=RedirectResponse)
@router.get("/ip", response_class=RedirectResponse)
@router.get("/samozanyatye", response_class=RedirectResponse)
@router.get("/usn", response_class=RedirectResponse)
@router.get("/2026", response_class=RedirectResponse)
@router.get("/obrazec-zapolneniya", response_class=RedirectResponse)
@router.get("/xml-edo", response_class=RedirectResponse)
@router.get("/blank-excel", response_class=RedirectResponse)
@router.get("/blank-word", response_class=RedirectResponse)
async def upd_redirect(request: Request):
    """Редирект на URL с trailing slash"""
    path = request.url.path
    return RedirectResponse(url=f"{path}/", status_code=301)
