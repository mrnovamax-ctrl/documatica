"""
Pages - SSR роутеры для публичных страниц
"""

from fastapi import APIRouter

from app.pages import home, upd, schet, auth_pages, news, about, legal

router = APIRouter()

# Подключаем роутеры публичных страниц
router.include_router(home.router)
router.include_router(upd.router, prefix="/upd")
router.include_router(schet.router, prefix="/schet")
router.include_router(auth_pages.router)
router.include_router(news.router, prefix="/news")
router.include_router(about.router)
router.include_router(legal.router)
