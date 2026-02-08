"""
Admin - SSR роутеры для административной панели
"""

from fastapi import APIRouter
from fastapi.responses import RedirectResponse

from app.admin import auth, dashboard, users, payments, articles, promocodes, pages, categories, shortcodes, news_sidebar, hubs, seo_tools

router = APIRouter(prefix="/admin")


@router.get("", include_in_schema=False)
async def admin_index_no_slash():
    """Редирект /admin -> /admin/"""
    return RedirectResponse(url="/admin/", status_code=307)


# Подключаем роутеры админки (раздел Контент YAML удалён — страницы в CMS)
router.include_router(auth.router)
router.include_router(dashboard.router)
router.include_router(pages.router, prefix="/pages")  # Block Builder
router.include_router(users.router, prefix="/users")
router.include_router(payments.router, prefix="/payments")
router.include_router(articles.router, prefix="/articles")
router.include_router(categories.router, prefix="/categories")
router.include_router(hubs.router, prefix="/hubs")
router.include_router(promocodes.router, prefix="/promocodes")
router.include_router(shortcodes.router, prefix="/shortcodes")
router.include_router(news_sidebar.router, prefix="/news-sidebar")
router.include_router(seo_tools.router, prefix="/seo-tools")