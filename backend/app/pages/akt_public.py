"""
Акт выполненных работ - публичные страницы (хаб и лендинги)
Универсальный роутер на основе конфига
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
CONFIG_PATH = Path(__file__).parent.parent.parent / "content" / "akt" / "_pages.yaml"


@lru_cache(maxsize=1)
def load_akt_pages_config() -> Dict[str, Any]:
    """Загрузка конфигурации страниц Акта"""
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}


def get_landing_config(slug: str) -> Optional[Dict[str, Any]]:
    """Получение конфига лендинга по slug"""
    config = load_akt_pages_config()
    return config.get("landings", {}).get(slug)


def get_info_config(slug: str) -> Optional[Dict[str, Any]]:
    """Получение конфига информационной страницы по slug"""
    config = load_akt_pages_config()
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
    config = load_akt_pages_config()
    return config.get("downloads", {}).get(slug)


# ============== ГЛАВНАЯ СТРАНИЦА РАЗДЕЛА ==============

@router.get("/", response_class=HTMLResponse)
async def akt_hub(request: Request):
    """Хаб Акт - главная страница раздела"""
    content = load_content("akt/index")
    
    return templates.TemplateResponse(
        request=request,
        name="public/akt/index.html",
        context={
            "content": content,
            "breadcrumbs": [
                {"title": "Главная", "url": "/"},
                {"title": "Акт выполненных работ", "url": None},
            ]
        }
    )


# ============== УНИВЕРСАЛЬНЫЙ РОУТЕР ЛЕНДИНГОВ ==============

@router.get("/ooo/", response_class=HTMLResponse)
@router.get("/ip/", response_class=HTMLResponse)
@router.get("/samozanyatye/", response_class=HTMLResponse)
@router.get("/uslug/", response_class=HTMLResponse)
@router.get("/rabot/", response_class=HTMLResponse)
@router.get("/s-nds/", response_class=HTMLResponse)
@router.get("/bez-nds/", response_class=HTMLResponse)
@router.get("/2026/", response_class=HTMLResponse)
async def akt_landing(request: Request):
    """Универсальный обработчик лендингов Акт"""
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
        name="public/akt/landing.html",
        context={
            "content": content,
            "breadcrumbs": [
                {"title": "Главная", "url": "/"},
                {"title": "Акт", "url": "/akt/"},
                {"title": config["breadcrumb"], "url": None},
            ]
        }
    )


# ============== ИНФОРМАЦИОННЫЕ СТРАНИЦЫ ==============

@router.get("/obrazec-zapolneniya/", response_class=HTMLResponse)
@router.get("/obrazec/", response_class=HTMLResponse)
async def akt_info(request: Request):
    """Информационные страницы Акт"""
    path = request.url.path
    slug = path.strip("/").split("/")[-1]
    
    config = get_info_config(slug)
    if not config:
        raise HTTPException(status_code=404, detail="Страница не найдена")
    
    content = load_content(config["content_file"])
    
    return templates.TemplateResponse(
        request=request,
        name="public/akt/info.html",
        context={
            "content": content,
            "breadcrumbs": [
                {"title": "Главная", "url": "/"},
                {"title": "Акт", "url": "/akt/"},
                {"title": config["breadcrumb"], "url": None},
            ]
        }
    )


# ============== СТРАНИЦЫ СКАЧИВАНИЯ ==============

@router.get("/blank-excel/", response_class=HTMLResponse)
@router.get("/blank-word/", response_class=HTMLResponse)
async def akt_download(request: Request):
    """Страницы скачивания бланков"""
    path = request.url.path
    slug = path.strip("/").split("/")[-1]
    
    config = get_download_config(slug)
    if not config:
        raise HTTPException(status_code=404, detail="Страница не найдена")

    # Обогащаем конфиг данными для gated download (не меняя исходный dict из кэша)
    config = dict(config)
    if slug == "blank-excel":
        config["blank_type"] = "akt-blank-excel"
        config["download_filename"] = "akt-blank-2026.xls"
    elif slug == "blank-word":
        config["blank_type"] = "akt-blank-word"
        config["download_filename"] = "akt-blank-2026.doc"
    
    return templates.TemplateResponse(
        request=request,
        name="public/akt/download.html",
        context={
            "config": config,
            "breadcrumbs": [
                {"title": "Главная", "url": "/"},
                {"title": "Акт", "url": "/akt/"},
                {"title": config["breadcrumb"], "url": None},
            ]
        }
    )
