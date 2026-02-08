"""
Публичные страницы контентных хабов: /hub/, /hub/{hub_slug}/, /hub/{hub_slug}/{section_slug}/
"""

from typing import Optional
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session, joinedload

from app.core.templates import templates
from app.database import get_db
from app.models import ContentHub, ContentHubSection, HubSectionArticle

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def hub_index(request: Request, db: Session = Depends(get_db)):
    """Список опубликованных хабов."""
    hubs = (
        db.query(ContentHub)
        .filter(ContentHub.is_published.is_(True))
        .order_by(ContentHub.position, ContentHub.id)
        .all()
    )
    breadcrumbs = [{"title": "Главная", "url": "/"}, {"title": "Контент-хабы", "url": None}]
    base_url = str(request.base_url).rstrip("/")
    return templates.TemplateResponse(
        request=request,
        name="public/hub/index.html",
        context={
            "hubs": hubs,
            "breadcrumbs": breadcrumbs,
            "base_url": base_url,
            "title": "Контент-хабы",
            "description": "Тематические подборки статей и материалов",
        },
    )


@router.get("/{hub_slug}", response_class=RedirectResponse, include_in_schema=False)
async def hub_view_redirect(request: Request, hub_slug: str):
    """Редирект /hub/slug -> /hub/slug/."""
    return RedirectResponse(url=f"/hub/{hub_slug}/", status_code=301)


@router.get("/{hub_slug}/", response_class=HTMLResponse)
async def hub_view(
    request: Request,
    hub_slug: str,
    db: Session = Depends(get_db),
):
    """Страница хаба: контент + список разделов."""
    hub = (
        db.query(ContentHub)
        .options(joinedload(ContentHub.sections))
        .filter(ContentHub.slug == hub_slug, ContentHub.is_published.is_(True))
        .first()
    )
    if not hub:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Хаб не найден")

    sections = sorted(hub.sections, key=lambda s: (s.position, s.id))
    breadcrumbs = [
        {"title": "Главная", "url": "/"},
        {"title": "Контент-хабы", "url": "/hub/"},
        {"title": hub.title, "url": None},
    ]
    base_url = str(request.base_url).rstrip("/")
    return templates.TemplateResponse(
        request=request,
        name="public/hub/view.html",
        context={
            "hub": hub,
            "sections": sections,
            "breadcrumbs": breadcrumbs,
            "base_url": base_url,
            "title": hub.meta_title or hub.title,
            "description": hub.meta_description or "",
        },
    )


@router.get("/{hub_slug}/{section_slug}", response_class=RedirectResponse, include_in_schema=False)
async def hub_section_redirect(request: Request, hub_slug: str, section_slug: str):
    """Редирект /hub/hub_slug/section_slug -> с trailing slash."""
    return RedirectResponse(url=f"/hub/{hub_slug}/{section_slug}/", status_code=301)


@router.get("/{hub_slug}/{section_slug}/", response_class=HTMLResponse)
async def hub_section_view(
    request: Request,
    hub_slug: str,
    section_slug: str,
    db: Session = Depends(get_db),
):
    """Страница раздела хаба: контент раздела + привязанные статьи."""
    hub = (
        db.query(ContentHub)
        .filter(ContentHub.slug == hub_slug, ContentHub.is_published.is_(True))
        .first()
    )
    if not hub:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Хаб не найден")

    section = (
        db.query(ContentHubSection)
        .options(
            joinedload(ContentHubSection.article_links).joinedload(HubSectionArticle.article),
        )
        .filter(
            ContentHubSection.hub_id == hub.id,
            ContentHubSection.slug == section_slug,
        )
        .first()
    )
    if not section:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Раздел не найден")

    linked_articles = []
    for link in sorted(section.article_links, key=lambda x: (x.position, x.id)):
        art = link.article
        if art and art.is_published:
            linked_articles.append(art)

    breadcrumbs = [
        {"title": "Главная", "url": "/"},
        {"title": "Контент-хабы", "url": "/hub/"},
        {"title": hub.title, "url": f"/hub/{hub.slug}/"},
        {"title": section.title, "url": None},
    ]
    base_url = str(request.base_url).rstrip("/")
    return templates.TemplateResponse(
        request=request,
        name="public/hub/section.html",
        context={
            "hub": hub,
            "section": section,
            "linked_articles": linked_articles,
            "breadcrumbs": breadcrumbs,
            "base_url": base_url,
            "title": section.meta_title or section.title,
            "description": section.meta_description or "",
        },
    )
