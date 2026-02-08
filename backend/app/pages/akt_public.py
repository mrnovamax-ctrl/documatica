"""
Акт выполненных работ — публичные страницы. Только CMS (БД). YAML не используется.
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

AKT_DOWNLOADS = {
    "blank-excel": {
        "breadcrumb": "Скачать Excel",
        "title": "Скачать бланк Акта Excel бесплатно — Documatica",
        "description": "Скачайте пустой бланк акта выполненных работ в формате Excel (.xls) бесплатно. Актуальная форма 2026 года.",
        "h1": "Скачать бланк Акта Excel",
        "format": "Excel (.xls)",
        "blank_type": "akt-blank-excel",
        "download_filename": "akt-blank-2026.xls",
    },
    "blank-word": {
        "breadcrumb": "Скачать Word",
        "title": "Скачать бланк Акта Word бесплатно — Documatica",
        "description": "Скачайте пустой бланк акта выполненных работ в формате Word (.doc) бесплатно. Актуальная форма 2026 года.",
        "h1": "Скачать бланк Акта Word",
        "format": "Word (.doc)",
        "blank_type": "akt-blank-word",
        "download_filename": "akt-blank-2026.doc",
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
async def akt_hub(request: Request, db: Session = Depends(get_db)):
    """Хаб Акт: только CMS (slug=akt). Без страницы — 404."""
    if not request.url.path.endswith("/"):
        return RedirectResponse(url=request.url.path + "/", status_code=301)
    page = (
        db.query(Page)
        .options(joinedload(Page.sections))
        .filter(Page.slug == "akt")
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
async def akt_subpage(request: Request, path: str, db: Session = Depends(get_db)):
    """Подстраницы Акт: только CMS (slug=akt/...) или хардкод для blank-excel/blank-word."""
    if not request.url.path.endswith("/"):
        return RedirectResponse(url=request.url.path + "/", status_code=301)
    path = (path or "").strip("/")
    if not path:
        raise HTTPException(status_code=404, detail="Страница не найдена")
    slug = f"akt/{path}"

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
                    {"title": "Акт выполненных работ", "url": "/akt/"},
                    {"title": page.title, "url": None},
                ],
            },
        )

    if path in AKT_DOWNLOADS:
        cfg = AKT_DOWNLOADS[path]
        return templates.TemplateResponse(
            request=request,
            name="public/akt/download.html",
            context={
                "config": {
                    **cfg,
                    "blank_type": cfg["blank_type"],
                    "download_filename": cfg["download_filename"],
                },
                "breadcrumbs": [
                    {"title": "Главная", "url": "/"},
                    {"title": "Акт", "url": "/akt/"},
                    {"title": cfg["breadcrumb"], "url": None},
                ],
            },
        )

    raise HTTPException(status_code=404, detail="Страница не найдена")
