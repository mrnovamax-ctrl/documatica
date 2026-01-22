"""
Dashboard - SSR роутеры для личного кабинета
"""

from fastapi import APIRouter

from app.dashboard import main, upd, invoice, documents, organizations, contractors, products, tariffs
from app.dashboard import templates as doc_templates

router = APIRouter(prefix="/dashboard")

# Подключаем роутеры личного кабинета
router.include_router(main.router)
router.include_router(upd.router, prefix="/upd")
router.include_router(invoice.router, prefix="/invoice")
router.include_router(documents.router, prefix="/documents")
router.include_router(organizations.router, prefix="/organizations")
router.include_router(contractors.router, prefix="/contractors")
router.include_router(products.router, prefix="/products")
router.include_router(doc_templates.router, prefix="/templates")
router.include_router(tariffs.router, prefix="/tariffs")
router.include_router(tariffs.router, prefix="/payment")  # Алиас для callback'ов
