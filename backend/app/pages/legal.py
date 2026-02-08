"""
Политика конфиденциальности и Согласие на обработку ПД. Только CMS (БД). YAML не используется.
"""

from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session, joinedload

from app.core.templates import templates
from app.core.heroicons import get_icon_paths_html
from app.database import get_db
from app.models import Page
from app.pages.cms_dynamic import _build_sections_for_template

router = APIRouter()


@router.get("/privacy", response_class=HTMLResponse)
@router.get("/privacy/", response_class=HTMLResponse)
async def privacy_page(request: Request, db: Session = Depends(get_db)):
    """Политика конфиденциальности: только из CMS. Без страницы — 404."""
    page = db.query(Page).options(joinedload(Page.sections)).filter(Page.slug == "privacy").first()
    if not page or getattr(page, "status", None) != "published":
        raise HTTPException(status_code=404, detail="Страница не найдена")
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


@router.get("/agreement", response_class=HTMLResponse)
@router.get("/agreement/", response_class=HTMLResponse)
async def agreement_page(request: Request, db: Session = Depends(get_db)):
    """Согласие на обработку ПД: только из CMS. Без страницы — 404."""
    page = db.query(Page).options(joinedload(Page.sections)).filter(Page.slug == "agreement").first()
    if not page or getattr(page, "status", None) != "published":
        raise HTTPException(status_code=404, detail="Страница не найдена")
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
