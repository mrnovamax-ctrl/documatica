"""
API v1 - REST API для Block Builder и других функций
"""

from fastapi import APIRouter
from app.api.v1 import pages, categories

router = APIRouter(prefix="/api/v1")

# Подключаем роутеры API
router.include_router(pages.router)
router.include_router(categories.router)
