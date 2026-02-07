"""
Акт выполненных работ - публичные страницы (хаб и лендинги)
Хаб /akt/ отдаётся из CMS, если есть опубликованная страница с slug=akt.
"""

import yaml
from pathlib import Path
from functools import lru_cache
from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session, joinedload

from app.core.templates import templates
from app.core.content import load_content
from app.core.heroicons import get_icon_paths_html
from app.database import get_db
from app.models import Page
from app.pages.cms_dynamic import _build_sections_for_template

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
async def akt_hub(request: Request, db: Session = Depends(get_db)):
    """Хаб Акт: из CMS (slug=akt), при наличии опубликованной страницы — dynamic_page, иначе YAML."""
    page = (
        db.query(Page)
        .options(joinedload(Page.sections))
        .filter(Page.slug == "akt")
        .first()
    )
    if page and getattr(page, "status", None) == "published":
        sections_for_template = _build_sections_for_template(page)
        page_view = type("PageView", (), {
            "id": page.id,
            "title": page.title,
            "meta_title": getattr(page, "meta_title", None),
            "meta_description": getattr(page, "meta_description", None),
            "meta_keywords": getattr(page, "meta_keywords", None),
            "canonical_url": getattr(page, "canonical_url", None),
            "sections": sections_for_template,
        })()
        return templates.TemplateResponse(
            request=request,
            name="public/dynamic_page.html",
            context={
                "page": page_view,
                "latest_articles": [],
                "title": page.meta_title or page.title,
                "description": page.meta_description or "",
                "is_home_page": False,
                "heroicon_paths": get_icon_paths_html(),
            },
        )
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


# ============== УНИВЕРСАЛЬНЫЕ ОБРАБОТЧИКИ ==============

def _akt_cms_page_response(request: Request, page, breadcrumb_title: str):
    """Общий ответ из CMS для akt (лендинг/инфо)."""
    sections_for_template = _build_sections_for_template(page)
    page_view = type("PageView", (), {
        "id": page.id,
        "title": page.title,
        "meta_title": getattr(page, "meta_title", None),
        "meta_description": getattr(page, "meta_description", None),
        "meta_keywords": getattr(page, "meta_keywords", None),
        "canonical_url": getattr(page, "canonical_url", None),
        "sections": sections_for_template,
    })()
    return templates.TemplateResponse(
        request=request,
        name="public/dynamic_page.html",
        context={
            "page": page_view,
            "latest_articles": [],
            "title": page.meta_title or page.title,
            "description": page.meta_description or "",
            "is_home_page": False,
            "heroicon_paths": get_icon_paths_html(),
            "breadcrumbs": [
                {"title": "Главная", "url": "/"},
                {"title": "Акт выполненных работ", "url": "/akt/"},
                {"title": breadcrumb_title, "url": None},
            ],
        },
    )


async def akt_landing_handler(request: Request, db: Session = Depends(get_db)):
    """Лендинги Акт: сначала CMS (slug=akt/ooo и т.д.), иначе YAML."""
    path = request.url.path.strip("/")
    slug = path.split("/")[-1]
    page = (
        db.query(Page)
        .options(joinedload(Page.sections))
        .filter(Page.slug == path, Page.status == "published")
        .first()
    )
    if page:
        config = get_landing_config(slug)
        bc_title = config.get("breadcrumb", slug) if config else page.title
        return _akt_cms_page_response(request, page, bc_title)
    config = get_landing_config(slug)
    if not config:
        raise HTTPException(status_code=404, detail="Страница не найдена")
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


async def akt_info_handler(request: Request, db: Session = Depends(get_db)):
    """Информационные страницы Акт: сначала CMS, иначе YAML. Алиас obrazec -> akt/obrazec-zapolneniya."""
    path = request.url.path.strip("/")
    slug = path.split("/")[-1]
    cms_slug = "akt/obrazec-zapolneniya" if slug == "obrazec" else path
    page = (
        db.query(Page)
        .options(joinedload(Page.sections))
        .filter(Page.slug == cms_slug, Page.status == "published")
        .first()
    )
    if page:
        config = get_info_config(slug)
        bc_title = config.get("breadcrumb", page.title) if config else page.title
        return _akt_cms_page_response(request, page, bc_title)
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


async def akt_download_handler(request: Request):
    """Универсальный обработчик страниц скачивания"""
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


async def akt_redirect_handler(request: Request):
    """Универсальный редирект на URL с trailing slash"""
    path = request.url.path
    return RedirectResponse(url=f"{path}/", status_code=301)


# ============== ДИНАМИЧЕСКАЯ РЕГИСТРАЦИЯ РОУТОВ ==============

def register_akt_routes():
    """Динамически регистрирует все роуты из _pages.yaml"""
    config = load_akt_pages_config()
    
    # Регистрируем лендинги
    for slug in config.get("landings", {}).keys():
        router.add_api_route(
            f"/{slug}/",
            akt_landing_handler,
            methods=["GET"],
            response_class=HTMLResponse,
            name=f"akt_landing_{slug}"
        )
        # Редирект без trailing slash
        router.add_api_route(
            f"/{slug}",
            akt_redirect_handler,
            methods=["GET"],
            response_class=RedirectResponse,
            name=f"akt_landing_{slug}_redirect"
        )
    
    # Регистрируем информационные страницы
    for slug, page_config in config.get("info_pages", {}).items():
        router.add_api_route(
            f"/{slug}/",
            akt_info_handler,
            methods=["GET"],
            response_class=HTMLResponse,
            name=f"akt_info_{slug}"
        )
        # Редирект без trailing slash
        router.add_api_route(
            f"/{slug}",
            akt_redirect_handler,
            methods=["GET"],
            response_class=RedirectResponse,
            name=f"akt_info_{slug}_redirect"
        )
        
        # Регистрируем алиасы
        for alias in page_config.get("aliases", []):
            router.add_api_route(
                f"/{alias}/",
                akt_info_handler,
                methods=["GET"],
                response_class=HTMLResponse,
                name=f"akt_info_{alias}"
            )
            router.add_api_route(
                f"/{alias}",
                akt_redirect_handler,
                methods=["GET"],
                response_class=RedirectResponse,
                name=f"akt_info_{alias}_redirect"
            )
    
    # Регистрируем страницы скачивания
    for slug in config.get("downloads", {}).keys():
        router.add_api_route(
            f"/{slug}/",
            akt_download_handler,
            methods=["GET"],
            response_class=HTMLResponse,
            name=f"akt_download_{slug}"
        )
        # Редирект без trailing slash
        router.add_api_route(
            f"/{slug}",
            akt_redirect_handler,
            methods=["GET"],
            response_class=RedirectResponse,
            name=f"akt_download_{slug}_redirect"
        )


# Регистрируем роуты при импорте модуля
register_akt_routes()
