"""
Admin - SSR роутеры для административной панели
"""

from fastapi import APIRouter

from app.admin import auth, dashboard, content, users, articles, promocodes

router = APIRouter(prefix="/admin")

# Подключаем роутеры админки
router.include_router(auth.router)
router.include_router(dashboard.router)
router.include_router(content.router, prefix="/content")
router.include_router(users.router, prefix="/users")
router.include_router(articles.router, prefix="/articles")
router.include_router(promocodes.router, prefix="/promocodes")
