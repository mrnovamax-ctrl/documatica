"""
Политика конфиденциальности и Согласие на обработку ПД.
Если в CMS есть опубликованная страница (slug=privacy/agreement), отдаём из БД; иначе — YAML + legal.html.
"""

from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session, joinedload

from app.core.templates import templates
from app.core.content import load_content
from app.core.heroicons import get_icon_paths_html
from app.database import get_db
from app.models import Page

router = APIRouter()


def _build_sections_for_template(page):
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
    return sections_for_template


@router.get("/privacy", response_class=HTMLResponse)
@router.get("/privacy/", response_class=HTMLResponse)
async def privacy_page(request: Request, db: Session = Depends(get_db)):
    """Политика конфиденциальности: из CMS или YAML."""
    page = db.query(Page).options(joinedload(Page.sections)).filter(Page.slug == "privacy").first()
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
    content = load_content("privacy")
    return templates.TemplateResponse(
        request=request,
        name="public/legal.html",
        context={"request": request, "content": content, "page_type": "privacy"},
    )


@router.get("/agreement", response_class=HTMLResponse)
@router.get("/agreement/", response_class=HTMLResponse)
async def agreement_page(request: Request, db: Session = Depends(get_db)):
    """Согласие на обработку ПД: из CMS или YAML."""
    page = db.query(Page).options(joinedload(Page.sections)).filter(Page.slug == "agreement").first()
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
    content = load_content("agreement")
    return templates.TemplateResponse(
        request=request,
        name="public/legal.html",
        context={"request": request, "content": content, "page_type": "agreement"},
    )
