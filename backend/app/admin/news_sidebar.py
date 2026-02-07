"""
Админка: настраиваемый сайдбар раздела «Новости».
Один общий сайдбар для всех статей: порядок блоков и вставка шорткодов.
"""

from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session, joinedload

from app.core.templates import templates
from app.database import get_db
from app.models import NewsSidebarItem, Shortcode
from app.admin.context import require_admin, get_admin_context

router = APIRouter()

BLOCK_TYPE_LABELS = {
    "cta_card": "Блок CTA (призыв)",
    "related_articles": "Похожие статьи",
    "shortcode": "Шорткод",
}


@router.get("/", response_class=HTMLResponse)
async def news_sidebar_list(request: Request, db: Session = Depends(get_db)):
    auth_check = require_admin(request)
    if auth_check:
        return auth_check
    items = (
        db.query(NewsSidebarItem)
        .options(joinedload(NewsSidebarItem.shortcode))
        .order_by(NewsSidebarItem.position, NewsSidebarItem.id)
        .all()
    )
    shortcodes = db.query(Shortcode).filter(Shortcode.is_active.is_(True)).order_by(Shortcode.name).all()
    return templates.TemplateResponse(
        request=request,
        name="admin/news_sidebar/list.html",
        context=get_admin_context(
            request=request,
            title="Сайдбар новостей",
            active_menu="news_sidebar",
            items=items,
            shortcodes=shortcodes,
            block_type_labels=BLOCK_TYPE_LABELS,
        ),
    )


@router.post("/add/", response_class=RedirectResponse)
async def news_sidebar_add(
    request: Request,
    db: Session = Depends(get_db),
    block_type: str = Form(...),
    shortcode_id: str = Form(""),
):
    auth_check = require_admin(request)
    if auth_check:
        return auth_check
    if block_type not in BLOCK_TYPE_LABELS:
        return RedirectResponse(url="/admin/news-sidebar/?error=type", status_code=303)
    sc_id = None
    if block_type == "shortcode" and shortcode_id:
        try:
            sc_id = int(shortcode_id)
        except ValueError:
            pass
    max_pos = db.query(NewsSidebarItem).count()
    item = NewsSidebarItem(position=max_pos, block_type=block_type, shortcode_id=sc_id if sc_id else None)
    db.add(item)
    db.commit()
    return RedirectResponse(url="/admin/news-sidebar/?saved=1", status_code=303)


@router.post("/{item_id}/delete/", response_class=RedirectResponse)
async def news_sidebar_delete(request: Request, item_id: int, db: Session = Depends(get_db)):
    auth_check = require_admin(request)
    if auth_check:
        return auth_check
    item = db.query(NewsSidebarItem).filter(NewsSidebarItem.id == item_id).first()
    if item:
        db.delete(item)
        db.commit()
    return RedirectResponse(url="/admin/news-sidebar/", status_code=303)


@router.post("/{item_id}/move-up/", response_class=RedirectResponse)
async def news_sidebar_move_up(request: Request, item_id: int, db: Session = Depends(get_db)):
    auth_check = require_admin(request)
    if auth_check:
        return auth_check
    item = db.query(NewsSidebarItem).filter(NewsSidebarItem.id == item_id).first()
    if not item:
        return RedirectResponse(url="/admin/news-sidebar/", status_code=303)
    prev = db.query(NewsSidebarItem).filter(NewsSidebarItem.position < item.position).order_by(NewsSidebarItem.position.desc()).first()
    if prev:
        item.position, prev.position = prev.position, item.position
        db.commit()
    return RedirectResponse(url="/admin/news-sidebar/", status_code=303)


@router.post("/{item_id}/move-down/", response_class=RedirectResponse)
async def news_sidebar_move_down(request: Request, item_id: int, db: Session = Depends(get_db)):
    auth_check = require_admin(request)
    if auth_check:
        return auth_check
    item = db.query(NewsSidebarItem).filter(NewsSidebarItem.id == item_id).first()
    if not item:
        return RedirectResponse(url="/admin/news-sidebar/", status_code=303)
    next_ = db.query(NewsSidebarItem).filter(NewsSidebarItem.position > item.position).order_by(NewsSidebarItem.position.asc()).first()
    if next_:
        item.position, next_.position = next_.position, item.position
        db.commit()
    return RedirectResponse(url="/admin/news-sidebar/", status_code=303)
