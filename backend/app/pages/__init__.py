"""
Pages - SSR роутеры для публичных страниц
"""

from fastapi import APIRouter

from app.pages import home, upd, schet, auth_pages, news, hub, about, legal, akt_public, landing, envato, contact, cms_dynamic

router = APIRouter()

# Подключаем роутеры публичных страниц (более специфичные первыми)
router.include_router(home.router)
router.include_router(landing.router)
router.include_router(envato.router)
router.include_router(upd.router, prefix="/upd")
router.include_router(schet.router, prefix="/schet")
router.include_router(akt_public.router, prefix="/akt")
router.include_router(auth_pages.router)
router.include_router(news.router, prefix="/news")
router.include_router(hub.router, prefix="/hub")
router.include_router(about.router)
router.include_router(legal.router)
router.include_router(contact.router)
# Страницы из CMS по slug (catch-all): /test/, /my-page/ и т.д. — в конце
router.include_router(cms_dynamic.router)

