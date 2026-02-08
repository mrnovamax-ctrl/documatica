"""
Admin Payments - управление платежами
"""

from datetime import datetime
from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc
from pydantic import BaseModel
from typing import List

from app.database import get_db
from app.models import Payment, User
from app.core.templates import templates
from app.admin.context import require_admin, get_admin_context
from app.services.billing import BillingService
from app.api.payment import get_state_from_tbank

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def payments_list(
    request: Request,
    page: int = 1,
    per_page: int = 50,
    reconcile: str = "",
    sync: str = "",
    show_reconcile: int = 0,
    updated: int = 0,
    not_found: int = 0,
    db: Session = Depends(get_db),
):
    """Список платежей из БД"""
    auth_check = require_admin(request)
    if auth_check:
        return auth_check

    total = db.query(func.count(Payment.id)).scalar() or 0
    total_pages = (total + per_page - 1) // per_page if total > 0 else 1
    offset = (page - 1) * per_page

    confirmed_count = db.query(func.count(Payment.id)).filter(Payment.status == "confirmed").scalar() or 0
    confirmed_revenue = float(
        db.query(func.coalesce(func.sum(Payment.amount), 0)).filter(Payment.status == "confirmed").scalar() or 0
    )

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
            confirmed_count=confirmed_count,
            confirmed_revenue=confirmed_revenue,
            page=page,
            per_page=per_page,
            total_pages=total_pages,
            reconcile=reconcile,
            sync=sync,
            show_reconcile=bool(show_reconcile),
            reconcile_updated=updated,
            reconcile_not_found=not_found,
        ),
    )


class ReconcileRequest(BaseModel):
    """Список order_id из выписки банка для сверки"""
    order_ids: List[str]


@router.post("/reconcile/", response_class=RedirectResponse)
async def payments_reconcile(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Сверка с выпиской банка: помечает платежи как confirmed по списку order_id из банка.
    Принимает form: order_ids_text (текст, по одному UUID на строку).
    """
    auth_check = require_admin(request)
    if auth_check:
        return auth_check

    form = await request.form()
    text = form.get("order_ids_text", "") or ""
    order_ids = [s.strip() for s in text.splitlines() if s.strip()]

    if not order_ids:
        return RedirectResponse(url="/admin/payments/?reconcile=empty", status_code=303)

    updated = 0
    not_found = []
    billing = BillingService(db)

    for order_id in order_ids:
        payment = db.query(Payment).filter(Payment.tbank_order_id == order_id).first()
        if not payment:
            not_found.append(order_id)
            continue
        if payment.status == "confirmed":
            continue
        old_status = payment.status
        payment.status = "confirmed"
        payment.confirmed_at = payment.confirmed_at or datetime.utcnow()
        if old_status != "confirmed":
            user = db.query(User).filter(User.id == payment.user_id).first()
            if user:
                if payment.payment_type == "subscription":
                    billing.activate_subscription(user, months=1)
                elif payment.payment_type == "pay_per_doc":
                    billing.add_purchased_documents(user, payment.documents_count)
        updated += 1

    db.commit()

    params = f"?reconcile=ok&updated={updated}"
    if not_found:
        params += f"&not_found={len(not_found)}"
    return RedirectResponse(url=f"/admin/payments/{params}", status_code=303)


@router.post("/sync-tbank/", response_class=RedirectResponse)
async def payments_sync_tbank(request: Request, db: Session = Depends(get_db)):
    """
    Синхронизация статусов с Т-Банком: для платежей с tbank_payment_id
    запрашивает GetState и обновляет status при CONFIRMED.
    """
    auth_check = require_admin(request)
    if auth_check:
        return auth_check

    payments = (
        db.query(Payment)
        .filter(
            Payment.tbank_payment_id.isnot(None),
            Payment.status.in_(["pending", "created", "authorized"]),
        )
        .all()
    )
    updated = 0
    billing = BillingService(db)
    for payment in payments:
        status = await get_state_from_tbank(payment.tbank_payment_id)
        if status == "CONFIRMED":
            if payment.status != "confirmed":
                payment.status = "confirmed"
                payment.confirmed_at = payment.confirmed_at or datetime.utcnow()
                user = db.query(User).filter(User.id == payment.user_id).first()
                if user:
                    if payment.payment_type == "subscription":
                        billing.activate_subscription(user, months=1)
                    elif payment.payment_type == "pay_per_doc":
                        billing.add_purchased_documents(user, payment.documents_count)
                updated += 1
        elif status in ("REJECTED", "REFUNDED", "CANCELED"):
            payment.status = status.lower()

    db.commit()
    return RedirectResponse(url=f"/admin/payments/?sync=ok&updated={updated}", status_code=303)
