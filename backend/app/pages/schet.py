"""
Счет на оплату — публичные страницы. Только CMS (БД). YAML не используется.
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

SCHET_DOWNLOADS = {
    "blank-excel": {
        "breadcrumb": "Скачать Excel",
        "title": "Скачать бланк счета на оплату Excel бесплатно — Documatica",
        "description": "Скачайте пустой бланк счета на оплату в формате Excel (.xls) бесплатно. Актуальный образец 2026 года.",
        "h1": "Скачать бланк счета на оплату Excel",
        "format": "Excel (.xls)",
        "file_url": "/api/v1/documents/blanks/schet-blank-excel",
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
async def schet_hub(request: Request, db: Session = Depends(get_db)):
    """Хаб Счет: только CMS (slug=schet). Без страницы — 404."""
    if not request.url.path.endswith("/"):
        return RedirectResponse(url=request.url.path + "/", status_code=301)
    page = (
        db.query(Page)
        .options(joinedload(Page.sections))
        .filter(Page.slug == "schet")
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
async def schet_subpage(request: Request, path: str, db: Session = Depends(get_db)):
    """Подстраницы Счет: только CMS (slug=schet/...) или хардкод для blank-excel."""
    if not request.url.path.endswith("/"):
        return RedirectResponse(url=request.url.path + "/", status_code=301)
    path = (path or "").strip("/")
    if not path:
        raise HTTPException(status_code=404, detail="Страница не найдена")
    slug = f"schet/{path}"

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
                    {"title": "Счет на оплату", "url": "/schet/"},
                    {"title": page.title, "url": None},
                ],
            },
        )

    if path in SCHET_DOWNLOADS:
        cfg = SCHET_DOWNLOADS[path]
        return templates.TemplateResponse(
            request=request,
            name="public/schet/download.html",
            context={
                "meta": {"title": cfg["title"], "description": cfg["description"]},
                "page": {"h1": cfg["h1"], "format": cfg["format"], "file_url": cfg["file_url"]},
                "breadcrumbs": [
                    {"title": "Главная", "url": "/"},
                    {"title": "Счет на оплату", "url": "/schet/"},
                    {"title": cfg["breadcrumb"], "url": None},
                ],
            },
        )

    raise HTTPException(status_code=404, detail="Страница не найдена")
