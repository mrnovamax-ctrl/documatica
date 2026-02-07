"""
Главная страница
"""

import os
import json
from pathlib import Path
from typing import List, Dict
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse, PlainTextResponse
from sqlalchemy.orm import Session, joinedload
from dotenv import load_dotenv

# Загружаем .env
load_dotenv()

from app.core.templates import templates
from app.core.content import load_content
from app.core.heroicons import get_icon_paths_html
from app.database import get_db
from app.models import Page

router = APIRouter()

# Feature flag для CMS из БД
USE_DB_CMS = os.getenv("USE_DB_CMS", "false").lower() == "true"
print(f"[HOME] USE_DB_CMS = {USE_DB_CMS}")

# Путь к данным
DATA_DIR = Path(__file__).parent.parent.parent / "data"
STATIC_DIR = Path(__file__).parent.parent / "static"


# Верификация домена Mail.ru
@router.get("/mailru-domainsZDnkw0eMC2tYYqi.html", response_class=PlainTextResponse)
async def mailru_verification():
    """Файл верификации домена для Mail.ru"""
    return "mailru-domain: sZDnkw0eMC2tYYqi"


def get_latest_articles(limit: int = 5) -> List[Dict]:
    """Получение последних опубликованных статей для главной страницы"""
    filepath = DATA_DIR / "articles.json"
    if not filepath.exists():
        return []
    
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Поддержка старого формата (массив статей)
    if isinstance(data, list):
        articles = data
    else:
        articles = data.get("articles", [])
    
    # Только опубликованные
    published = [a for a in articles if a.get("is_published", False) or a.get("status") == "published"]
    
    # Сортировка по дате (новые сначала)
    published.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    
    return published[:limit]


@router.get("/", response_class=HTMLResponse)
async def home(request: Request, db: Session = Depends(get_db)):
    """
    Главная страница сайта
    ВАЖНО: URL не изменился! Только источник данных: YAML → БД
    """
    # Получаем последние статьи для блока новостей
    latest_articles = get_latest_articles(5)
    
    # Пробуем загрузить из БД (если включен USE_DB_CMS)
    if USE_DB_CMS:
        try:
            page = db.query(Page).options(joinedload(Page.sections)).filter(Page.slug == "").first()  # slug="" для главной, подгружаем секции чтобы section.settings был доступен в шаблоне
            print(f"[HOME] Page from DB: {page}")
            print(f"[HOME] Page status: {page.status if page else 'N/A'}")
        except Exception as e:
            print(f"[HOME] DB error, using YAML fallback: {e}")
            page = None
        
        if page and getattr(page, "status", None) == "published":
            # Новая версия из БД: передаём секции с гарантированным settings (dict), чтобы в шаблоне работали grid_columns и др.
            sections_for_template = []
            for s in sorted(page.sections, key=lambda x: x.position):
                settings = dict(s.settings or {})
                settings.setdefault("grid_columns", getattr(s, "grid_columns", 2))
                settings.setdefault("grid_gap", getattr(s, "grid_gap", "medium"))
                settings.setdefault("grid_style", getattr(s, "grid_style", "grid"))
                bg_style = getattr(s, "background_style", None) or ""
                section_view = type("SectionView", (), {
                    "id": s.id,
                    "section_type": s.section_type,
                    "blocks": s.blocks,
                    "background_style": bg_style,
                    "css_classes": getattr(s, "css_classes", None),
                    "container_width": getattr(s, "container_width", None),
                    "is_visible": getattr(s, "is_visible", True),
                    "settings": settings,
                    "is_dark_bg": bg_style in ("dark", "primary", "gold", "pattern_dots_dark"),
                })()
                sections_for_template.append(section_view)
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
                    "latest_articles": latest_articles,
                    "title": page.meta_title or page.title,
                    "description": page.meta_description,
                    "is_home_page": True,
                    "heroicon_paths": get_icon_paths_html(),
                }
            )
        else:
            print(f"[HOME] Page not published or not found, using YAML fallback")
    
    # Fallback на YAML (старая версия)
    content = load_content("home")
    
    return templates.TemplateResponse(
        request=request,
        name="public/home.html",
        context={
            "content": content,
            "latest_articles": latest_articles,
            "title": content.get("meta", {}).get("title", "Documatica — генератор документов для бизнеса"),
            "description": content.get("meta", {}).get("description", "Создавайте УПД, счета, акты и договоры онлайн бесплатно."),
            "is_home_page": True,  # Флаг для отображения прелоадера
        }
    )


# ============== РЕДИРЕКТЫ СО СТАРЫХ URL ==============

@router.get("/upd-s-nds", response_class=RedirectResponse)
async def redirect_upd_s_nds():
    return RedirectResponse(url="/upd/s-nds/", status_code=301)


@router.get("/upd-bez-nds", response_class=RedirectResponse)
async def redirect_upd_bez_nds():
    return RedirectResponse(url="/upd/bez-nds/", status_code=301)


@router.get("/upd-dlya-ooo", response_class=RedirectResponse)
async def redirect_upd_ooo():
    return RedirectResponse(url="/upd/ooo/", status_code=301)


@router.get("/upd-dlya-ip", response_class=RedirectResponse)
async def redirect_upd_ip():
    return RedirectResponse(url="/upd/ip/", status_code=301)


@router.get("/upd-samozanyatye", response_class=RedirectResponse)
async def redirect_upd_samozanyatye():
    return RedirectResponse(url="/upd/samozanyatye/", status_code=301)


@router.get("/upd-usn", response_class=RedirectResponse)
async def redirect_upd_usn():
    return RedirectResponse(url="/upd/usn/", status_code=301)


@router.get("/upd-demo", response_class=RedirectResponse)
async def redirect_upd_demo():
    return RedirectResponse(url="/upd/", status_code=301)


@router.get("/obrazets-zapolneniya", response_class=RedirectResponse)
async def redirect_obrazets():
    return RedirectResponse(url="/upd/obrazec-zapolneniya/", status_code=301)


@router.get("/upd-xml-edo", response_class=RedirectResponse)
async def redirect_upd_xml_edo():
    return RedirectResponse(url="/upd/xml-edo/", status_code=301)


@router.get("/skachat-excel", response_class=RedirectResponse)
async def redirect_skachat_excel():
    return RedirectResponse(url="/upd/blank-excel/", status_code=301)


@router.get("/upd-create", response_class=RedirectResponse)
async def redirect_upd_create(request: Request):
    """Редирект на создание УПД - всегда на dashboard (доступно и гостям)"""
    return RedirectResponse(url="/dashboard/upd/create/", status_code=302)


@router.get("/demo/", response_class=HTMLResponse)
async def demo_page(request: Request):
    """Демо-страница - призыв к регистрации для полного доступа"""
    return templates.TemplateResponse(
        request=request,
        name="public/demo.html",
        context={
            "title": "Демо УПД — Попробуйте бесплатно | Documatica",
            "description": "Зарегистрируйтесь, чтобы получить полный доступ к функционалу.",
        }
    )
