"""
Admin Hubs - контентные хабы (хаб → разделы → привязанные статьи)
"""

import re
import logging
from typing import Optional
from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from sqlalchemy.orm import Session, joinedload

from app.core.templates import templates
from app.database import get_db
from app.models import ContentHub, ContentHubSection, HubSectionArticle, Article
from app.admin.context import require_admin, get_admin_context

logger = logging.getLogger(__name__)
router = APIRouter()


def _slugify(s: str) -> str:
    s = (s or "").strip().lower()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[-\s]+", "-", s)
    return s.strip("-") or "hub"


@router.get("/", response_class=HTMLResponse)
async def hubs_list(request: Request, db: Session = Depends(get_db)):
    """Список хабов"""
    auth_check = require_admin(request)
    if auth_check:
        return auth_check

    hubs = (
        db.query(ContentHub)
        .options(joinedload(ContentHub.sections))
        .order_by(ContentHub.position, ContentHub.id)
        .all()
    )

    return templates.TemplateResponse(
        request=request,
        name="admin/hubs/list.html",
        context=get_admin_context(
            request=request,
            title="Хабы — Админ-панель",
            active_menu="hubs",
            hubs=hubs,
        )
    )


@router.get("/create/", response_class=HTMLResponse)
async def hub_create_form(request: Request, db: Session = Depends(get_db)):
    """Форма создания хаба"""
    auth_check = require_admin(request)
    if auth_check:
        return auth_check

    return templates.TemplateResponse(
        request=request,
        name="admin/hubs/form.html",
        context=get_admin_context(
            request=request,
            title="Новый хаб — Админ-панель",
            active_menu="hubs",
            hub=None,
            is_new=True,
        )
    )


@router.post("/create/", response_class=HTMLResponse)
async def hub_create_post(
    request: Request,
    db: Session = Depends(get_db),
    title: str = Form(...),
    slug: str = Form(""),
    content: str = Form(""),
    meta_title: str = Form(""),
    meta_description: str = Form(""),
    meta_keywords: str = Form(""),
    is_published: bool = Form(False),
):
    """Создание хаба"""
    auth_check = require_admin(request)
    if auth_check:
        return auth_check

    slug = (slug or _slugify(title)).strip() or "hub"
    if db.query(ContentHub).filter(ContentHub.slug == slug).first():
        slug = f"{slug}-{len(db.query(ContentHub).all())}"

    hub = ContentHub(
        slug=slug,
        title=title,
        content=content or None,
        meta_title=meta_title or title,
        meta_description=meta_description or None,
        meta_keywords=meta_keywords or None,
        is_published=is_published,
        position=db.query(ContentHub).count(),
    )
    db.add(hub)
    db.commit()
    db.refresh(hub)
    return RedirectResponse(url=f"/admin/hubs/{hub.id}/", status_code=303)


@router.get("/{hub_id}/", response_class=HTMLResponse)
async def hub_edit_form(
    request: Request,
    hub_id: int,
    db: Session = Depends(get_db),
):
    """Редактирование хаба + список разделов"""
    auth_check = require_admin(request)
    if auth_check:
        return auth_check

    hub = (
        db.query(ContentHub)
        .options(
            joinedload(ContentHub.sections).joinedload(ContentHubSection.article_links).joinedload(HubSectionArticle.article)
        )
        .filter(ContentHub.id == hub_id)
        .first()
    )
    if not hub:
        return RedirectResponse(url="/admin/hubs/", status_code=303)

    return templates.TemplateResponse(
        request=request,
        name="admin/hubs/form.html",
        context=get_admin_context(
            request=request,
            title=f"Хаб: {hub.title} — Админ-панель",
            active_menu="hubs",
            hub=hub,
            is_new=False,
            saved=request.query_params.get("saved") == "1",
        )
    )


@router.post("/{hub_id}/", response_class=HTMLResponse)
async def hub_update(
    request: Request,
    hub_id: int,
    db: Session = Depends(get_db),
    title: str = Form(...),
    slug: str = Form(""),
    content: str = Form(""),
    meta_title: str = Form(""),
    meta_description: str = Form(""),
    meta_keywords: str = Form(""),
    is_published: bool = Form(False),
):
    """Обновление хаба"""
    auth_check = require_admin(request)
    if auth_check:
        return auth_check

    hub = db.query(ContentHub).filter(ContentHub.id == hub_id).first()
    if not hub:
        return RedirectResponse(url="/admin/hubs/", status_code=303)

    slug = (slug or _slugify(title)).strip()
    if slug and slug != hub.slug:
        existing = db.query(ContentHub).filter(ContentHub.slug == slug).first()
        if existing:
            return RedirectResponse(url=f"/admin/hubs/{hub_id}/?error=slug", status_code=303)
        hub.slug = slug

    hub.title = title
    hub.content = content or None
    hub.meta_title = meta_title or title
    hub.meta_description = meta_description or None
    hub.meta_keywords = meta_keywords or None
    hub.is_published = is_published
    db.commit()
    return RedirectResponse(url=f"/admin/hubs/{hub_id}/?saved=1", status_code=303)


@router.get("/{hub_id}/sections/create/", response_class=HTMLResponse)
async def section_create_form(
    request: Request,
    hub_id: int,
    db: Session = Depends(get_db),
):
    auth_check = require_admin(request)
    if auth_check:
        return auth_check

    hub = db.query(ContentHub).filter(ContentHub.id == hub_id).first()
    if not hub:
        return RedirectResponse(url="/admin/hubs/", status_code=303)

    return templates.TemplateResponse(
        request=request,
        name="admin/hubs/section_form.html",
        context=get_admin_context(
            request=request,
            title="Новый раздел хаба — Админ-панель",
            active_menu="hubs",
            hub=hub,
            section=None,
            is_new_section=True,
        )
    )


@router.post("/{hub_id}/sections/create/", response_class=HTMLResponse)
async def section_create_post(
    request: Request,
    hub_id: int,
    db: Session = Depends(get_db),
    title: str = Form(...),
    slug: str = Form(""),
    content: str = Form(""),
    meta_title: str = Form(""),
    meta_description: str = Form(""),
    meta_keywords: str = Form(""),
    position: int = Form(0),
):
    auth_check = require_admin(request)
    if auth_check:
        return auth_check

    hub = db.query(ContentHub).filter(ContentHub.id == hub_id).first()
    if not hub:
        return RedirectResponse(url="/admin/hubs/", status_code=303)

    slug = (slug or _slugify(title)).strip() or "section"
    existing = db.query(ContentHubSection).filter(
        ContentHubSection.hub_id == hub_id,
        ContentHubSection.slug == slug,
    ).first()
    max_pos = db.query(ContentHubSection).filter(ContentHubSection.hub_id == hub_id).count()
    if existing:
        slug = f"{slug}-{max_pos}"
    section = ContentHubSection(
        hub_id=hub_id,
        slug=slug,
        title=title,
        content=content or None,
        meta_title=meta_title or title,
        meta_description=meta_description or None,
        meta_keywords=meta_keywords or None,
        position=max_pos,
    )
    db.add(section)
    db.commit()
    db.refresh(section)
    return RedirectResponse(url=f"/admin/hubs/{hub_id}/sections/{section.id}/", status_code=303)


@router.get("/{hub_id}/sections/{section_id}/", response_class=HTMLResponse)
async def section_edit_form(
    request: Request,
    hub_id: int,
    section_id: int,
    db: Session = Depends(get_db),
):
    auth_check = require_admin(request)
    if auth_check:
        return auth_check

    section = (
        db.query(ContentHubSection)
        .options(
            joinedload(ContentHubSection.hub),
            joinedload(ContentHubSection.article_links).joinedload(HubSectionArticle.article),
        )
        .filter(ContentHubSection.id == section_id, ContentHubSection.hub_id == hub_id)
        .first()
    )
    if not section:
        return RedirectResponse(url=f"/admin/hubs/{hub_id}/", status_code=303)

    articles_for_select = (
        db.query(Article)
        .order_by(Article.title)
        .limit(500)
        .all()
    )
    linked_ids = {la.article_id for la in section.article_links}

    return templates.TemplateResponse(
        request=request,
        name="admin/hubs/section_form.html",
        context=get_admin_context(
            request=request,
            title=f"Раздел: {section.title} — Админ-панель",
            active_menu="hubs",
            hub=section.hub,
            section=section,
            is_new_section=False,
            articles_for_select=articles_for_select,
            linked_article_ids=linked_ids,
            saved=request.query_params.get("saved") == "1",
        )
    )


@router.post("/{hub_id}/sections/{section_id}/", response_class=HTMLResponse)
async def section_update(
    request: Request,
    hub_id: int,
    section_id: int,
    db: Session = Depends(get_db),
    title: str = Form(...),
    slug: str = Form(""),
    content: str = Form(""),
    meta_title: str = Form(""),
    meta_description: str = Form(""),
    meta_keywords: str = Form(""),
    position: int = Form(0),
):
    auth_check = require_admin(request)
    if auth_check:
        return auth_check

    section = (
        db.query(ContentHubSection)
        .filter(ContentHubSection.id == section_id, ContentHubSection.hub_id == hub_id)
        .first()
    )
    if not section:
        return RedirectResponse(url=f"/admin/hubs/{hub_id}/", status_code=303)

    slug = (slug or _slugify(title)).strip() or "section"
    existing = db.query(ContentHubSection).filter(
        ContentHubSection.hub_id == hub_id,
        ContentHubSection.slug == slug,
        ContentHubSection.id != section_id,
    ).first()
    if existing:
        return RedirectResponse(url=f"/admin/hubs/{hub_id}/sections/{section_id}/?error=slug", status_code=303)

    section.slug = slug
    section.title = title
    section.content = content or None
    section.meta_title = meta_title or title
    section.meta_description = meta_description or None
    section.meta_keywords = meta_keywords or None
    section.position = position
    db.commit()
    return RedirectResponse(url=f"/admin/hubs/{hub_id}/sections/{section_id}/?saved=1", status_code=303)


@router.post("/{hub_id}/sections/{section_id}/add-article/", response_class=RedirectResponse)
async def section_add_article(
    request: Request,
    hub_id: int,
    section_id: int,
    db: Session = Depends(get_db),
    article_id: int = Form(...),
):
    auth_check = require_admin(request)
    if auth_check:
        return auth_check

    section = (
        db.query(ContentHubSection)
        .filter(ContentHubSection.id == section_id, ContentHubSection.hub_id == hub_id)
        .first()
    )
    if not section:
        return RedirectResponse(url=f"/admin/hubs/{hub_id}/", status_code=303)

    existing = db.query(HubSectionArticle).filter(
        HubSectionArticle.section_id == section_id,
        HubSectionArticle.article_id == article_id,
    ).first()
    if not existing:
        max_pos = (
            db.query(HubSectionArticle)
            .filter(HubSectionArticle.section_id == section_id)
            .count()
        )
        link = HubSectionArticle(section_id=section_id, article_id=article_id, position=max_pos)
        db.add(link)
        db.commit()
    return RedirectResponse(url=f"/admin/hubs/{hub_id}/sections/{section_id}/", status_code=303)


@router.post("/{hub_id}/sections/{section_id}/remove-article/", response_class=RedirectResponse)
async def section_remove_article(
    request: Request,
    hub_id: int,
    section_id: int,
    db: Session = Depends(get_db),
    link_id: int = Form(...),
):
    auth_check = require_admin(request)
    if auth_check:
        return auth_check

    link = (
        db.query(HubSectionArticle)
        .filter(
            HubSectionArticle.id == link_id,
            HubSectionArticle.section_id == section_id,
        )
        .first()
    )
    if link:
        db.delete(link)
        db.commit()
    return RedirectResponse(url=f"/admin/hubs/{hub_id}/sections/{section_id}/", status_code=303)


@router.post("/{hub_id}/sections/{section_id}/delete/", response_class=RedirectResponse)
async def section_delete(
    request: Request,
    hub_id: int,
    section_id: int,
    db: Session = Depends(get_db),
):
    auth_check = require_admin(request)
    if auth_check:
        return auth_check

    section = (
        db.query(ContentHubSection)
        .filter(ContentHubSection.id == section_id, ContentHubSection.hub_id == hub_id)
        .first()
    )
    if section:
        db.delete(section)
        db.commit()
    return RedirectResponse(url=f"/admin/hubs/{hub_id}/", status_code=303)
