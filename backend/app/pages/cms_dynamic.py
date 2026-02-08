"""
Отдача страниц из CMS (Block Builder) по URL.
Обрабатывает пути, не занятые другими роутерами (upd, news, contact и т.д.).
Страница должна быть опубликована (status=published).
"""

from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session, joinedload

from app.core.templates import templates
from app.core.heroicons import get_icon_paths_html
from app.database import get_db
from app.models import Page

router = APIRouter()


def _build_sections_for_template(page):
    """Собирает секции страницы с settings для шаблона (как в home.py)."""
    sections_for_template = []
    for s in sorted(page.sections, key=lambda x: x.position):
        if not getattr(s, "is_visible", True):
            continue
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


@router.get("/{path:path}", response_class=HTMLResponse)
async def cms_page_by_path(
    request: Request,
    path: str,
    db: Session = Depends(get_db),
):
    """
    Страница из CMS по slug (path).
    path приходит без ведущего слэша; с trailing — зависит от маршрута.
    Примеры: /test/ → path=test, /upd/ooo/ → path=upd/ooo (если роутер не перехватил).
    """
    slug = (path or "").strip("/")
    if not slug:
        raise HTTPException(status_code=404, detail="Not Found")
    # Не отдавать админку/дашборд/API как CMS-страницу
    if slug.split("/")[0].lower() in ("admin", "dashboard", "api", "auth", "login", "logout", "static"):
        raise HTTPException(status_code=404, detail="Not Found")

    page = (
        db.query(Page)
        .options(joinedload(Page.sections))
        .filter(Page.slug == slug, Page.status == "published")
        .first()
    )
    if not page:
        raise HTTPException(status_code=404, detail="Страница не найдена")

    base_url = str(request.base_url).rstrip("/")
    canonical_stored = getattr(page, "canonical_url", None)
    canonical_url = canonical_stored if canonical_stored and (canonical_stored.startswith("http") or canonical_stored.startswith("//")) else f"{base_url}/{slug}/"
    page_view = type("PageView", (), {
        "id": page.id,
        "title": page.title,
        "meta_title": getattr(page, "meta_title", None),
        "meta_description": getattr(page, "meta_description", None),
        "meta_keywords": getattr(page, "meta_keywords", None),
        "canonical_url": canonical_url,
        "sections": _build_sections_for_template(page),
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
            "canonical_url": canonical_url,
            "og_title": page.meta_title or page.title,
            "og_description": page.meta_description or "",
            "base_url": base_url,
        },
    )
