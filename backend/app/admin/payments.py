"""
Admin Payments - управление платежами
"""

from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc

from app.database import get_db
from app.models import Payment
from app.core.templates import templates
from app.admin.context import require_admin, get_admin_context

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def payments_list(request: Request, page: int = 1, per_page: int = 50, db: Session = Depends(get_db)):
    """Список платежей из БД"""
    auth_check = require_admin(request)
    if auth_check:
        return auth_check

    total = db.query(func.count(Payment.id)).scalar() or 0
    total_pages = (total + per_page - 1) // per_page if total > 0 else 1
    offset = (page - 1) * per_page

    payments = (
        db.query(Payment)
        .options(joinedload(Payment.user))
        .order_by(desc(Payment.created_at))
        .offset(offset)
        .limit(per_page)
        .all()
    )

    return templates.TemplateResponse(
        request=request,
        name="admin/payments/list.html",
        context=get_admin_context(
            request=request,
            title="Платежи — Админ-панель",
            active_menu="payments",
            payments=payments,
            total_payments=total,
            page=page,
            per_page=per_page,
            total_pages=total_pages,
        ),
    )
