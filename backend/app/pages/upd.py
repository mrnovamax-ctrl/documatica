"""
УПД - публичные страницы (хаб и лендинги)
Рефакторинг: динамическая регистрация роутов из _pages.yaml
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


# ============== УНИВЕРСАЛЬНЫЕ ОБРАБОТЧИКИ ==============

async def upd_landing_handler(request: Request):
    """Универсальный обработчик лендингов УПД"""
    path = request.url.path
    slug = path.strip("/").split("/")[-1]
    
    config = get_landing_config(slug)
    if not config:
        raise HTTPException(status_code=404, detail="Страница не найдена")
    
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


async def upd_info_handler(request: Request):
    """Универсальный обработчик информационных страниц"""
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


async def upd_download_handler(request: Request):
    """Универсальный обработчик страниц скачивания"""
    path = request.url.path
    slug = path.strip("/").split("/")[-1]
    
    config = get_download_config(slug)
    if not config:
        raise HTTPException(status_code=404, detail="Страница не найдена")
    
    # Определяем тип бланка для API
    blank_type = f"upd-{slug}"
    download_filename = f"upd-blank-2026.{'xls' if 'excel' in slug else 'doc'}"
    
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
            },
            "config": {
                "blank_type": blank_type,
                "download_filename": download_filename,
            },
            "breadcrumbs": [
                {"title": "Главная", "url": "/"},
                {"title": "УПД", "url": "/upd/"},
                {"title": config["breadcrumb"], "url": None},
            ]
        }
    )


async def upd_redirect_handler(request: Request):
    """Универсальный редирект на URL с trailing slash"""
    path = request.url.path
    return RedirectResponse(url=f"{path}/", status_code=301)


# ============== ДИНАМИЧЕСКАЯ РЕГИСТРАЦИЯ РОУТОВ ==============

def register_upd_routes():
    """Динамически регистрирует все роуты из _pages.yaml"""
    config = load_upd_pages_config()
    
    # Регистрируем лендинги
    for slug in config.get("landings", {}).keys():
        router.add_api_route(
            f"/{slug}/",
            upd_landing_handler,
            methods=["GET"],
            response_class=HTMLResponse,
            name=f"upd_landing_{slug}"
        )
        # Редирект без trailing slash
        router.add_api_route(
            f"/{slug}",
            upd_redirect_handler,
            methods=["GET"],
            response_class=RedirectResponse,
            name=f"upd_landing_{slug}_redirect"
        )
    
    # Регистрируем информационные страницы
    for slug, page_config in config.get("info_pages", {}).items():
        router.add_api_route(
            f"/{slug}/",
            upd_info_handler,
            methods=["GET"],
            response_class=HTMLResponse,
            name=f"upd_info_{slug}"
        )
        # Редирект без trailing slash
        router.add_api_route(
            f"/{slug}",
            upd_redirect_handler,
            methods=["GET"],
            response_class=RedirectResponse,
            name=f"upd_info_{slug}_redirect"
        )
        
        # Регистрируем алиасы
        for alias in page_config.get("aliases", []):
            router.add_api_route(
                f"/{alias}/",
                upd_info_handler,
                methods=["GET"],
                response_class=HTMLResponse,
                name=f"upd_info_{alias}"
            )
            router.add_api_route(
                f"/{alias}",
                upd_redirect_handler,
                methods=["GET"],
                response_class=RedirectResponse,
                name=f"upd_info_{alias}_redirect"
            )
    
    # Регистрируем страницы скачивания
    for slug in config.get("downloads", {}).keys():
        router.add_api_route(
            f"/{slug}/",
            upd_download_handler,
            methods=["GET"],
            response_class=HTMLResponse,
            name=f"upd_download_{slug}"
        )
        # Редирект без trailing slash
        router.add_api_route(
            f"/{slug}",
            upd_redirect_handler,
            methods=["GET"],
            response_class=RedirectResponse,
            name=f"upd_download_{slug}_redirect"
        )


# Регистрируем роуты при импорте модуля
register_upd_routes()
