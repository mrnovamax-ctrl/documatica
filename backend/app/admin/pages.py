"""
Admin Pages - управление страницами через Block Builder
"""

import json
import logging
from typing import Optional
from fastapi import APIRouter, Request, Form, Depends, Body
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import OperationalError

from app.core.templates import templates
from app.core.content import load_content
from app.database import get_db
from app.models import Page, PageSection, ContentBlock
from app.admin.context import require_admin, get_admin_context

logger = logging.getLogger(__name__)
router = APIRouter()


def _group_pages_by_type(pages: list) -> list:
    """Группирует страницы по первому сегменту slug: upd, akt, home, остальные."""
    from collections import defaultdict
    groups_map = defaultdict(list)
    for p in pages:
        key = (p.slug or "").strip().split("/")[0] or "general"
        groups_map[key].append(p)
    order = ["upd", "schet", "akt", "news", "home"]
    group_titles = {"upd": "УПД (/upd/)", "schet": "Счет (/schet/)", "akt": "Акт (/akt/)", "news": "Новости (/news/)", "home": "Главная"}
    result = []
    for key in order:
        if key in groups_map and groups_map[key]:
            result.append({
                "key": key,
                "title": group_titles.get(key, key),
                "pages": groups_map.pop(key),
            })
    for key in sorted(groups_map.keys()):
        if groups_map[key]:
            result.append({
                "key": key,
                "title": f"/{key}/",
                "pages": groups_map[key],
            })
    return result


@router.get("/", response_class=HTMLResponse)
async def pages_list(request: Request, db: Session = Depends(get_db)):
    """Список всех страниц по группам (УПД, Акт, остальные)."""
    auth_check = require_admin(request)
    if auth_check:
        return auth_check

    pages = (
        db.query(Page)
        .options(joinedload(Page.sections))
        .order_by(Page.slug)
        .all()
    )
    page_groups = _group_pages_by_type(pages)

    return templates.TemplateResponse(
        request=request,
        name="admin/pages/list.html",
        context=get_admin_context(
            request=request,
            title="Страницы — Админ-панель",
            active_menu="pages",
            pages=pages,
            page_groups=page_groups,
        )
    )


# Копирование блока — объявлен до /{page_id}/, чтобы "block" не матчился как page_id
@router.post("/block/{block_id}/duplicate/", response_class=JSONResponse)
async def block_duplicate(request: Request, block_id: int, db: Session = Depends(get_db)):
    """Копирование блока в той же секции."""
    auth_check = require_admin(request)
    if auth_check:
        return auth_check
    block = db.query(ContentBlock).filter(ContentBlock.id == block_id).first()
    if not block:
        logger.warning("block_duplicate: block_id=%s not found", block_id)
        return JSONResponse({"success": False, "detail": "Block not found"}, status_code=404)
    raw = block.content
    try:
        content_copy = json.loads(json.dumps(raw)) if raw is not None else {}
    except (TypeError, ValueError):
        content_copy = {}
    if not isinstance(content_copy, dict):
        content_copy = {}
    max_pos = db.query(ContentBlock).filter(ContentBlock.section_id == block.section_id).count()
    new_block = ContentBlock(
        section_id=block.section_id,
        block_type=block.block_type,
        content=content_copy,
        css_classes=block.css_classes,
        position=max_pos,
        is_visible=block.is_visible,
    )
    db.add(new_block)
    db.commit()
    db.refresh(new_block)
    return JSONResponse({
        "success": True,
        "block": {
            "id": new_block.id,
            "block_type": new_block.block_type,
            "position": new_block.position,
            "content": new_block.content,
            "css_classes": new_block.css_classes,
            "is_visible": new_block.is_visible,
        },
    })


def _normalize_slug_segment(segment: str) -> str:
    """Один сегмент URL: латиница, цифры, дефис."""
    return (segment or "").strip().lower().replace(" ", "-").strip("/")


@router.get("/create/", response_class=HTMLResponse)
async def page_create_form(request: Request, db: Session = Depends(get_db)):
    """Форма создания новой страницы (с выбором родителя для вложенности)."""
    auth_check = require_admin(request)
    if auth_check:
        return auth_check
    parent_pages = db.query(Page).order_by(Page.slug).all()
    return templates.TemplateResponse(
        request=request,
        name="admin/pages/create.html",
        context=get_admin_context(
            request=request,
            title="Создать страницу — Админ-панель",
            active_menu="pages",
            parent_pages=parent_pages,
        )
    )


@router.post("/create/", response_class=HTMLResponse)
async def page_create(
    request: Request,
    db: Session = Depends(get_db),
    slug: str = Form(...),
    title: str = Form(...),
    page_type: str = Form("custom"),
    parent_id: Optional[str] = Form(""),
):
    """Создание новой страницы. Если указан parent_id, slug — сегмент под родителем (итог: parent.slug/segment)."""
    auth_check = require_admin(request)
    if auth_check:
        return auth_check

    parent_id_int = int(parent_id) if (parent_id and str(parent_id).strip()) else None
    segment = _normalize_slug_segment(slug)
    if not segment:
        parent_pages = db.query(Page).order_by(Page.slug).all()
        return templates.TemplateResponse(
            request=request,
            name="admin/pages/create.html",
            context=get_admin_context(
                request=request,
                title="Создать страницу — Админ-панель",
                active_menu="pages",
                parent_pages=parent_pages,
                error="Укажите URL (сегмент или полный путь).",
                form_slug=slug,
                form_title=title,
                form_page_type=page_type,
                form_parent_id=parent_id_int,
            )
        )

    if "/" in segment and parent_id_int:
        parent_pages = db.query(Page).order_by(Page.slug).all()
        return templates.TemplateResponse(
            request=request,
            name="admin/pages/create.html",
            context=get_admin_context(
                request=request,
                title="Создать страницу — Админ-панель",
                active_menu="pages",
                parent_pages=parent_pages,
                error="При выбранной родительской странице укажите один сегмент без слэша (например: ooo).",
                form_slug=slug,
                form_title=title,
                form_page_type=page_type,
                form_parent_id=parent_id_int,
            )
        )

    if parent_id_int:
        parent = db.query(Page).filter(Page.id == parent_id_int).first()
        if not parent:
            parent_id_int = None
            final_slug = segment
        else:
            final_slug = f"{parent.slug.rstrip('/')}/{segment}"
    else:
        final_slug = segment if "/" not in segment else segment

    existing = db.query(Page).filter(Page.slug == final_slug).first()
    if existing:
        parent_pages = db.query(Page).order_by(Page.slug).all()
        return templates.TemplateResponse(
            request=request,
            name="admin/pages/create.html",
            context=get_admin_context(
                request=request,
                title="Создать страницу — Админ-панель",
                active_menu="pages",
                parent_pages=parent_pages,
                error=f"Страница с URL /{final_slug}/ уже существует",
                form_slug=slug,
                form_title=title,
                form_page_type=page_type,
                form_parent_id=parent_id_int,
            )
        )

    page = Page(
        slug=final_slug,
        title=title,
        page_type=page_type,
        status="draft",
    )
    db.add(page)
    db.commit()
    db.refresh(page)
    return RedirectResponse(url=f"/admin/pages/{page.id}/edit/", status_code=303)


@router.get("/{page_id}/edit/", response_class=HTMLResponse)
async def page_edit(request: Request, page_id: int, db: Session = Depends(get_db)):
    """Block Builder - редактор страницы"""
    auth_check = require_admin(request)
    if auth_check:
        return auth_check

    try:
        page = db.query(Page).options(joinedload(Page.sections)).filter(Page.id == page_id).first()
        if not page:
            return RedirectResponse(url="/admin/pages/", status_code=303)

        sections_for_template = []
        for s in sorted(page.sections, key=lambda x: x.position):
            grid_columns = getattr(s, "grid_columns", None)
            grid_gap = getattr(s, "grid_gap", None)
            grid_style = getattr(s, "grid_style", None)
            settings = getattr(s, "settings", None)
            if not isinstance(settings, dict):
                settings = {}
            sections_for_template.append({
                "id": s.id,
                "section_type": s.section_type,
                "position": s.position,
                "blocks": s.blocks,
                "background_style": getattr(s, "background_style", None),
                "container_width": getattr(s, "container_width", None),
                "css_classes": getattr(s, "css_classes", None),
                "is_visible": getattr(s, "is_visible", True),
                "grid_columns": grid_columns if grid_columns is not None else 2,
                "grid_gap": grid_gap or "medium",
                "grid_style": grid_style or "grid",
                "settings": settings,
            })
    except OperationalError as e:
        logger.exception("page_edit: DB error loading page %s", page_id)
        msg = str(e).lower()
        if "grid_columns" in msg or "grid_gap" in msg or "grid_style" in msg or "no such column" in msg or "column" in msg:
            return HTMLResponse(
                status_code=503,
                content="""<!DOCTYPE html><html><head><meta charset="utf-8"><title>Ошибка</title></head><body style="font-family:sans-serif;padding:2rem;">
                <h1>Ошибка загрузки страницы</h1>
                <p>В базе данных не применены миграции для полей сетки секций.</p>
                <p>На сервере выполните: <code>cd backend && alembic upgrade head</code></p>
                <p><a href="/admin/pages/">Вернуться к списку страниц</a></p>
                </body></html>"""
            )
        raise

    # Structure for JS: save only on "Save" button (deferred save)
    page_structure = {
        "page_meta": {
            "title": page.title,
            "meta_title": getattr(page, "meta_title", None),
            "meta_description": getattr(page, "meta_description", None),
            "meta_keywords": getattr(page, "meta_keywords", None),
            "page_type": getattr(page, "page_type", None),
        },
        "sections": [
            {
                "id": s.id,
                "section_type": s.section_type,
                "position": s.position,
                "background_style": getattr(s, "background_style", None) or "light",
                "container_width": getattr(s, "container_width", None) or "default",
                "padding_y": getattr(s, "padding_y", None) or "default",
                "grid_columns": getattr(s, "grid_columns", 2),
                "grid_gap": getattr(s, "grid_gap", None) or "medium",
                "grid_style": getattr(s, "grid_style", None) or "grid",
                "settings": (s.settings if isinstance(s.settings, dict) else None) or {},
                "blocks": [
                    {
                        "id": b.id,
                        "block_type": b.block_type,
                        "position": b.position,
                        "content": b.content if isinstance(b.content, dict) else {},
                        "css_classes": getattr(b, "css_classes", None),
                    }
                    for b in sorted(s.blocks, key=lambda x: x.position)
                ],
            }
            for s in sorted(page.sections, key=lambda x: x.position)
        ],
    }
    page_structure_json = json.dumps(page_structure, ensure_ascii=False)

    response = templates.TemplateResponse(
        request=request,
        name="admin/pages/builder.html",
        context=get_admin_context(
            request=request,
            title=f"Редактирование: {page.title} — Админ-панель",
            active_menu="pages",
            page=page,
            sections=sections_for_template,
            page_structure_json=page_structure_json,
        )
    )
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


@router.post("/{page_id}/block-duplicate/", response_class=JSONResponse)
async def page_block_duplicate(
    request: Request,
    page_id: int,
    db: Session = Depends(get_db),
    body: dict = Body(..., embed=False),
):
    """Копирование блока (URL как у publish/unpublish: /admin/pages/{page_id}/block-duplicate/)."""
    auth_check = require_admin(request)
    if auth_check:
        return auth_check
    block_id = body.get("block_id")
    if block_id is None:
        return JSONResponse({"success": False, "detail": "block_id required"}, status_code=400)
    try:
        block_id = int(block_id)
    except (TypeError, ValueError):
        return JSONResponse({"success": False, "detail": "block_id must be integer"}, status_code=400)
    block = db.query(ContentBlock).filter(ContentBlock.id == block_id).first()
    if not block:
        logger.warning("page_block_duplicate: block_id=%s not found", block_id)
        return JSONResponse({"success": False, "detail": "Block not found"}, status_code=404)
    # блок должен относиться к секции этой страницы
    section = db.query(PageSection).filter(PageSection.id == block.section_id).first()
    if not section or section.page_id != page_id:
        return JSONResponse({"success": False, "detail": "Block not on this page"}, status_code=404)
    raw = block.content
    try:
        content_copy = json.loads(json.dumps(raw)) if raw is not None else {}
    except (TypeError, ValueError):
        content_copy = {}
    if not isinstance(content_copy, dict):
        content_copy = {}
    max_pos = db.query(ContentBlock).filter(ContentBlock.section_id == block.section_id).count()
    new_block = ContentBlock(
        section_id=block.section_id,
        block_type=block.block_type,
        content=content_copy,
        css_classes=block.css_classes,
        position=max_pos,
        is_visible=block.is_visible,
    )
    db.add(new_block)
    db.commit()
    db.refresh(new_block)
    return JSONResponse({
        "success": True,
        "block": {
            "id": new_block.id,
            "block_type": new_block.block_type,
            "position": new_block.position,
            "content": new_block.content,
            "css_classes": new_block.css_classes,
            "is_visible": new_block.is_visible,
        },
    })


@router.post("/{page_id}/publish/", response_class=JSONResponse)
async def page_publish(request: Request, page_id: int, db: Session = Depends(get_db)):
    """Публикация страницы"""
    auth_check = require_admin(request)
    if auth_check:
        return auth_check
    
    page = db.query(Page).filter(Page.id == page_id).first()
    
    if not page:
        return JSONResponse({"success": False, "error": "Page not found"}, status_code=404)
    
    page.status = "published"
    db.commit()
    
    return JSONResponse({"success": True, "status": "published"})


@router.post("/{page_id}/unpublish/", response_class=JSONResponse)
async def page_unpublish(request: Request, page_id: int, db: Session = Depends(get_db)):
    """Снятие с публикации"""
    auth_check = require_admin(request)
    if auth_check:
        return auth_check
    
    page = db.query(Page).filter(Page.id == page_id).first()
    
    if not page:
        return JSONResponse({"success": False, "error": "Page not found"}, status_code=404)
    
    page.status = "draft"
    db.commit()
    
    return JSONResponse({"success": True, "status": "draft"})


@router.delete("/{page_id}/", response_class=JSONResponse)
async def page_delete(request: Request, page_id: int, db: Session = Depends(get_db)):
    """Удаление страницы"""
    auth_check = require_admin(request)
    if auth_check:
        return auth_check
    
    page = db.query(Page).filter(Page.id == page_id).first()
    
    if not page:
        return JSONResponse({"success": False, "error": "Page not found"}, status_code=404)
    
    db.delete(page)
    db.commit()
    
    return JSONResponse({"success": True})
