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

from fastapi import HTTPException

from app.core.templates import templates
from app.core.heroicons import get_icon_paths_html
from app.database import get_db
from app.models import Page, Article
from app.pages.cms_dynamic import _build_sections_for_template

router = APIRouter()

# Путь к данным
DATA_DIR = Path(__file__).parent.parent.parent / "data"
STATIC_DIR = Path(__file__).parent.parent / "static"


# Верификация домена Mail.ru
@router.get("/mailru-domainsZDnkw0eMC2tYYqi.html", response_class=PlainTextResponse)
async def mailru_verification():
    """Файл верификации домена для Mail.ru"""
    return "mailru-domain: sZDnkw0eMC2tYYqi"


def _default_home_content() -> Dict:
    """Контент для главной, когда в CMS нет опубликованной страницы."""
    return {
        "meta": {"title": "Documatica — Онлайн генератор УПД", "description": "Создавайте УПД, счета-фактуры и акты онлайн."},
        "hero": {"title": "Документы с интеллектом.", "title_accent": "интеллектом", "subtitle": "Полный цикл автоматизации документов.", "cta_text": "Создать УПД бесплатно", "cta_url": "/dashboard/upd/create/", "note": "Попробуйте прямо сейчас", "note_accent": "С проверкой от AI"},
        "features": {"title": "Почему Documatica", "subtitle": "Всё в одном месте", "cards": [{"title": "Сверка реквизитов", "description": "Проверка по ИНН.", "icon": "check-circle"}, {"title": "Экспорт PDF", "description": "Скачивание документов.", "icon": "download"}, {"title": "Бесплатный старт", "description": "5 документов в месяц.", "icon": "gift"}]},
        "upd_types": {"title": "УПД", "label": "Виды", "cards": [{"tag": "С НДС", "title": "УПД с НДС", "description": "Для плательщиков НДС.", "url": "/upd/s-nds/", "icon": "dollar-sign"}, {"tag": "Без НДС", "title": "УПД без НДС", "description": "Без налога.", "url": "/upd/bez-nds/", "icon": "slash"}, {"tag": "УСН", "title": "УПД для УСН", "description": "Упрощенка.", "url": "/upd/usn/", "icon": "layers"}]},
        "pricing": {"label": "Тарифы", "title": "Инвестируйте в", "title_accent": "простоту", "plans": [{"name": "Бесплатный", "price": "0 руб", "period": "Для знакомства", "badge": "", "features": [{"text": "5 документов", "enabled": True}], "button_text": "Начать", "button_url": "/register", "style": "outline"}, {"name": "Подписка", "price": "300 руб", "period": "В месяц", "badge": "Популярный", "featured": True, "features": [{"text": "50 документов", "enabled": True}], "button_text": "Оформить", "button_url": "/dashboard/tariffs/", "style": "primary"}]},
        "about": {"label": "О нас", "title": "Кто стоит за", "title_accent": "Documatica", "description": "Команда экспертов по документообороту."},
        "cta": {"label": "Начните", "title": "Готовы", "title_accent": "автоматизировать?", "subtitle": "Первый УПД за 2 минуты.", "button_text": "Создать документ", "button_url": "/dashboard/upd/create/"},
    }


def get_latest_articles(db: Session, limit: int = 5) -> List[Article]:
    """Последние опубликованные статьи для главной страницы (из БД)."""
    return (
        db.query(Article)
        .options(joinedload(Article.category))
        .filter(Article.is_published.is_(True))
        .order_by(Article.created_at.desc(), Article.id.desc())
        .limit(limit)
        .all()
    )


@router.get("/", response_class=HTMLResponse)
async def home(request: Request, db: Session = Depends(get_db)):
    """Главная: из CMS или fallback на статичную страницу."""
    latest_articles = get_latest_articles(db, 5)
    page = (
        db.query(Page)
        .options(joinedload(Page.sections))
        .filter(Page.slug.in_(["", "home"]))
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
                "latest_articles": latest_articles,
                "title": page.meta_title or page.title,
                "description": page.meta_description or "",
                "is_home_page": True,
                "heroicon_paths": get_icon_paths_html(),
            },
        )
    content = _default_home_content()
    return templates.TemplateResponse(
        request=request,
        name="public/home.html",
        context={
            "content": content,
            "latest_articles": latest_articles,
            "heroicon_paths": get_icon_paths_html(),
        },
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
