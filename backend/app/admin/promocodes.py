"""
Admin Promocodes - управление промокодами
"""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models import Promocode, PromocodeUsage, User
from app.core.templates import templates
from app.admin.context import require_admin, get_admin_context

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def promocodes_list(request: Request, db: Session = Depends(get_db)):
    """Список промокодов"""
    auth_check = require_admin(request)
    if auth_check:
        return auth_check
    
    # Загружаем все промокоды
    promocodes = db.query(Promocode).order_by(Promocode.created_at.desc()).all()
    
    # Статистика
    total_promocodes = len(promocodes)
    active_promocodes = len([p for p in promocodes if p.is_active])
    total_usages = sum(p.uses_count or 0 for p in promocodes)
    
    return templates.TemplateResponse(
        request=request,
        name="admin/promocodes/list.html",
        context=get_admin_context(
            request=request,
            title="Промокоды — Админ-панель",
            active_menu="promocodes",
            promocodes=promocodes,
            total_promocodes=total_promocodes,
            active_promocodes=active_promocodes,
            total_usages=total_usages,
        )
    )


@router.get("/create", response_class=HTMLResponse)
async def promocode_create_form(request: Request):
    """Форма создания промокода"""
    auth_check = require_admin(request)
    if auth_check:
        return auth_check
    
    return templates.TemplateResponse(
        request=request,
        name="admin/promocodes/form.html",
        context=get_admin_context(
            request=request,
            title="Создать промокод — Админ-панель",
            active_menu="promocodes",
            promocode=None,
            is_edit=False,
        )
    )


@router.post("/create")
async def promocode_create(
    request: Request,
    code: str = Form(...),
    promo_type: str = Form(...),
    description: str = Form(None),
    subscription_days: Optional[int] = Form(None),
    subscription_price: Optional[int] = Form(None),
    documents_count: Optional[int] = Form(None),
    discount_percent: Optional[int] = Form(None),
    is_reusable: bool = Form(True),
    max_uses: Optional[int] = Form(None),
    valid_until: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """Создание промокода"""
    auth_check = require_admin(request)
    if auth_check:
        return auth_check
    
    # Проверяем уникальность кода
    code_upper = code.strip().upper()
    existing = db.query(Promocode).filter(Promocode.code == code_upper).first()
    if existing:
        return templates.TemplateResponse(
            request=request,
            name="admin/promocodes/form.html",
            context=get_admin_context(
                request=request,
                title="Создать промокод — Админ-панель",
                active_menu="promocodes",
                promocode=None,
                is_edit=False,
                error="Промокод с таким кодом уже существует"
            )
        )
    
    # Парсим дату
    valid_until_dt = None
    if valid_until:
        try:
            valid_until_dt = datetime.strptime(valid_until, "%Y-%m-%d")
        except:
            pass
    
    # Создаем промокод
    promocode = Promocode(
        code=code_upper,
        promo_type=promo_type,
        description=description,
        subscription_days=subscription_days if promo_type == "subscription" else None,
        subscription_price=subscription_price if promo_type == "subscription" else None,
        documents_count=documents_count if promo_type == "documents" else None,
        discount_percent=discount_percent if promo_type == "discount" else None,
        is_reusable=is_reusable,
        max_uses=max_uses if max_uses and max_uses > 0 else None,
        valid_until=valid_until_dt,
        is_active=True,
    )
    
    db.add(promocode)
    db.commit()
    
    return RedirectResponse(url="/admin/promocodes/", status_code=303)


@router.get("/{promocode_id}", response_class=HTMLResponse)
async def promocode_detail(request: Request, promocode_id: int, db: Session = Depends(get_db)):
    """Детальная страница промокода с историей использования"""
    auth_check = require_admin(request)
    if auth_check:
        return auth_check
    
    promocode = db.query(Promocode).filter(Promocode.id == promocode_id).first()
    if not promocode:
        return RedirectResponse(url="/admin/promocodes/", status_code=303)
    
    # Получаем историю использования
    usages = db.query(PromocodeUsage, User).join(
        User, PromocodeUsage.user_id == User.id
    ).filter(
        PromocodeUsage.promocode_id == promocode_id
    ).order_by(
        PromocodeUsage.activated_at.desc()
    ).all()
    
    return templates.TemplateResponse(
        request=request,
        name="admin/promocodes/detail.html",
        context=get_admin_context(
            request=request,
            title=f"Промокод {promocode.code} — Админ-панель",
            active_menu="promocodes",
            promocode=promocode,
            usages=usages,
        )
    )


@router.get("/{promocode_id}/edit", response_class=HTMLResponse)
async def promocode_edit_form(request: Request, promocode_id: int, db: Session = Depends(get_db)):
    """Форма редактирования промокода"""
    auth_check = require_admin(request)
    if auth_check:
        return auth_check
    
    promocode = db.query(Promocode).filter(Promocode.id == promocode_id).first()
    if not promocode:
        return RedirectResponse(url="/admin/promocodes/", status_code=303)
    
    return templates.TemplateResponse(
        request=request,
        name="admin/promocodes/form.html",
        context=get_admin_context(
            request=request,
            title=f"Редактировать {promocode.code} — Админ-панель",
            active_menu="promocodes",
            promocode=promocode,
            is_edit=True,
        )
    )


@router.post("/{promocode_id}/edit")
async def promocode_edit(
    request: Request,
    promocode_id: int,
    description: str = Form(None),
    subscription_days: Optional[int] = Form(None),
    subscription_price: Optional[int] = Form(None),
    documents_count: Optional[int] = Form(None),
    discount_percent: Optional[int] = Form(None),
    is_active: bool = Form(False),
    is_reusable: bool = Form(True),
    max_uses: Optional[int] = Form(None),
    valid_until: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """Обновление промокода"""
    auth_check = require_admin(request)
    if auth_check:
        return auth_check
    
    promocode = db.query(Promocode).filter(Promocode.id == promocode_id).first()
    if not promocode:
        return RedirectResponse(url="/admin/promocodes/", status_code=303)
    
    # Парсим дату
    valid_until_dt = None
    if valid_until:
        try:
            valid_until_dt = datetime.strptime(valid_until, "%Y-%m-%d")
        except:
            pass
    
    # Обновляем
    promocode.description = description
    promocode.is_active = is_active
    promocode.is_reusable = is_reusable
    promocode.max_uses = max_uses if max_uses and max_uses > 0 else None
    promocode.valid_until = valid_until_dt
    
    if promocode.promo_type == "subscription":
        promocode.subscription_days = subscription_days
        promocode.subscription_price = subscription_price
    elif promocode.promo_type == "documents":
        promocode.documents_count = documents_count
    elif promocode.promo_type == "discount":
        promocode.discount_percent = discount_percent
    
    db.commit()
    
    return RedirectResponse(url=f"/admin/promocodes/{promocode_id}", status_code=303)


@router.post("/{promocode_id}/toggle")
async def promocode_toggle(request: Request, promocode_id: int, db: Session = Depends(get_db)):
    """Включить/выключить промокод"""
    auth_check = require_admin(request)
    if auth_check:
        return auth_check
    
    promocode = db.query(Promocode).filter(Promocode.id == promocode_id).first()
    if promocode:
        promocode.is_active = not promocode.is_active
        db.commit()
    
    return RedirectResponse(url="/admin/promocodes/", status_code=303)


@router.post("/{promocode_id}/delete")
async def promocode_delete(request: Request, promocode_id: int, db: Session = Depends(get_db)):
    """Удаление промокода"""
    auth_check = require_admin(request)
    if auth_check:
        return auth_check
    
    promocode = db.query(Promocode).filter(Promocode.id == promocode_id).first()
    if promocode:
        # Удаляем историю использования
        db.query(PromocodeUsage).filter(PromocodeUsage.promocode_id == promocode_id).delete()
        db.delete(promocode)
        db.commit()
    
    return RedirectResponse(url="/admin/promocodes/", status_code=303)
