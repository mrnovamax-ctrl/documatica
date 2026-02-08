"""
УПД — публичные страницы. Только CMS (БД). YAML не используется.
Главная /upd/ и подстраницы /upd/ooo/, /upd/ip/ и т.д. — из Page по slug.
Страницы скачивания бланков (blank-excel, blank-word) — хардкод в коде при отсутствии страницы в CMS.
"""

from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session, joinedload

from app.core.templates import templates
from app.core.heroicons import get_icon_paths_html
from app.database import get_db
from app.models import Page
from app.pages.cms_dynamic import _build_sections_for_template

router = APIRouter()

# Страницы скачивания бланков (если нет в CMS)
UPD_DOWNLOADS = {
    "blank-excel": {
        "breadcrumb": "Скачать Excel",
        "title": "Скачать бланк УПД Excel бесплатно — Documatica",
        "description": "Скачайте пустой бланк УПД в формате Excel (.xls) бесплатно. Актуальная форма 2026 года.",
        "h1": "Скачать бланк УПД Excel",
        "format": "Excel (.xls)",
        "blank_type": "upd-blank-excel",
        "download_filename": "upd-blank-2026.xls",
    },
    "blank-word": {
        "breadcrumb": "Скачать Word",
        "title": "Скачать бланк УПД Word бесплатно — Documatica",
        "description": "Скачайте пустой бланк УПД в формате Word (.doc) бесплатно. Актуальная форма 2026 года.",
        "h1": "Скачать бланк УПД Word",
        "format": "Word (.doc)",
        "blank_type": "upd-blank-word",
        "download_filename": "upd-blank-2026.doc",
    },
}


def _page_view(page):
    sections_for_template = _build_sections_for_template(page)
    return type("PageView", (), {
        "id": page.id,
        "title": page.title,
        "meta_title": getattr(page, "meta_title", None),
        "meta_description": getattr(page, "meta_description", None),
        "meta_keywords": getattr(page, "meta_keywords", None),
        "canonical_url": getattr(page, "canonical_url", None),
        "sections": sections_for_template,
    })()


@router.get("/", response_class=HTMLResponse)
async def upd_hub(request: Request, db: Session = Depends(get_db)):
    """Хаб УПД: только из CMS (slug=upd). Без страницы — 404."""
    if not request.url.path.endswith("/"):
        return RedirectResponse(url=request.url.path + "/", status_code=301)
    page = (
        db.query(Page)
        .options(joinedload(Page.sections))
        .filter(Page.slug == "upd")
        .first()
    )
    if not page or getattr(page, "status", None) != "published":
        raise HTTPException(status_code=404, detail="Страница не найдена")
    page_view = _page_view(page)
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


@router.get("/{path:path}", response_class=HTMLResponse)
async def upd_subpage(request: Request, path: str, db: Session = Depends(get_db)):
    """Подстраницы УПД: только CMS (slug=upd/...) или хардкод для blank-excel/blank-word."""
    if not request.url.path.endswith("/"):
        return RedirectResponse(url=request.url.path + "/", status_code=301)
    path = (path or "").strip("/")
    if not path:
        raise HTTPException(status_code=404, detail="Страница не найдена")
    slug = f"upd/{path}"

    page = (
        db.query(Page)
        .options(joinedload(Page.sections))
        .filter(Page.slug == slug, Page.status == "published")
        .first()
    )
    if page:
        page_view = _page_view(page)
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
                    {"title": "УПД", "url": "/upd/"},
                    {"title": page.title, "url": None},
                ],
            },
        )

    if path in UPD_DOWNLOADS:
        cfg = UPD_DOWNLOADS[path]
        return templates.TemplateResponse(
            request=request,
            name="public/upd/download.html",
            context={
                "meta": {"title": cfg["title"], "description": cfg["description"]},
                "page": {"h1": cfg["h1"], "format": cfg["format"]},
                "config": {
                    "blank_type": cfg["blank_type"],
                    "download_filename": cfg["download_filename"],
                },
                "breadcrumbs": [
                    {"title": "Главная", "url": "/"},
                    {"title": "УПД", "url": "/upd/"},
                    {"title": cfg["breadcrumb"], "url": None},
                ],
            },
        )

    raise HTTPException(status_code=404, detail="Страница не найдена")
