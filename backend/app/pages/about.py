"""
Страница "О нас".
Если в CMS есть опубликованная страница со slug=about, отдаём из БД; иначе — статичный about.html.
"""

from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session, joinedload

from app.core.templates import templates
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


@router.get("/about", response_class=HTMLResponse)
@router.get("/about/", response_class=HTMLResponse)
async def about_page(request: Request, db: Session = Depends(get_db)):
    """О нас: из CMS (slug=about) или fallback на about.html."""
    page = db.query(Page).options(joinedload(Page.sections)).filter(Page.slug == "about").first()
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
    return templates.TemplateResponse(
        request=request,
        name="public/about.html",
        context={
            "title": "О сервисе Documatica — Генератор документов для бизнеса",
            "description": "Documatica — современный онлайн-сервис для автоматической генерации бухгалтерских документов. УПД, счета, акты, договоры.",
            "current_year": "2026",
        },
    )
