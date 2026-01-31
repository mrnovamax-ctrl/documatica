"""
Documatica Backend - FastAPI Application
Сервис генерации бухгалтерских документов (УПД)
"""

from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api import documents, organizations, products, auth, dadata, templates, billing, payment, ai, upload, promocodes, oauth, drafts, contact
from app.pages import router as pages_router
from app.dashboard import router as dashboard_router
from app.admin import router as admin_router
from app.database import init_db
from app.core.redirects import RedirectMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

# Пути к статике и шаблонам
STATIC_DIR = Path(__file__).parent / "static"
TEMPLATES_DIR = Path(__file__).parent / "templates"
error_templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

app = FastAPI(
    title="Documatica API",
    description="API для генерации бухгалтерских документов (УПД, счёт-фактура, акт)",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS - разрешаем запросы с фронтенда
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Разрешаем все origins для разработки
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 301 редиректы со старых URL
app.add_middleware(RedirectMiddleware)


# Middleware для управления кэшированием
class CacheControlMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        path = request.url.path
        
        # Статические файлы с версией - кэшируем надолго
        if path.startswith("/static/") and ("?v=" in str(request.url) or "?ver=" in str(request.url)):
            response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
        # Статические файлы без версии - короткий кэш
        elif path.startswith("/static/"):
            response.headers["Cache-Control"] = "public, max-age=3600"
        # HTML страницы - не кэшировать
        elif not path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
        
        return response

app.add_middleware(CacheControlMiddleware)

# Статические файлы
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# ===== Обработчик ошибок 404 =====
@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Кастомный обработчик HTTP ошибок с красивой страницей 404"""
    if exc.status_code == 404:
        return error_templates.TemplateResponse(
            "errors/404.html",
            {"request": request},
            status_code=404
        )
    # Для остальных ошибок возвращаем стандартный ответ
    return HTMLResponse(
        content=f"<h1>Error {exc.status_code}</h1><p>{exc.detail}</p>",
        status_code=exc.status_code
    )


# ===== API роутеры =====
app.include_router(
    documents.router,
    prefix="/api/v1/documents",
    tags=["documents"]
)

app.include_router(
    organizations.router,
    prefix="/api/v1",
    tags=["organizations", "contractors"]
)

app.include_router(
    products.router,
    prefix="/api/v1",
    tags=["products"]
)

app.include_router(
    auth.router,
    prefix="/api/v1/auth",
    tags=["auth"]
)

app.include_router(
    dadata.router,
    prefix="/api/v1/dadata",
    tags=["dadata"]
)

app.include_router(
    templates.router,
    prefix="/api/v1",
    tags=["templates"]
)

app.include_router(
    billing.router,
    prefix="/api/v1",
    tags=["billing"]
)

app.include_router(
    promocodes.router,
    prefix="/api/v1",
    tags=["promocodes"]
)

app.include_router(
    payment.router,
    prefix="/api/v1",
    tags=["payment"]
)

app.include_router(
    ai.router,
    prefix="/api/v1",
    tags=["ai"]
)

app.include_router(
    upload.router,
    prefix="/api/v1",
    tags=["upload"]
)

# Contact - форма обратной связи
app.include_router(
    contact.router,
    prefix="/api/v1",
    tags=["contact"]
)

# Черновики документов гостей (без авторизации)
app.include_router(
    drafts.router,
    tags=["drafts"]
)

# OAuth роутеры (на уровне /auth/ для callback)
app.include_router(
    oauth.router,
    prefix="/auth",
    tags=["oauth"]
)

# ===== SSR роутеры =====
# Admin (панель администратора)
app.include_router(admin_router, tags=["admin"])

# Dashboard (личный кабинет) - перед pages чтобы /dashboard/ работал
app.include_router(dashboard_router, tags=["dashboard"])

# Публичные страницы - в конце чтобы не перехватывали API
app.include_router(pages_router, tags=["pages"])


# Инициализация БД при старте
@app.on_event("startup")
async def startup_event():
    init_db()


# Health check endpoint
@app.get("/api/health", tags=["health"])
async def health_check():
    """Детальная проверка состояния сервиса"""
    return {
        "status": "healthy",
        "service": "Documatica API",
        "version": "1.0.0",
        "database": "json_files",
        "pdf_engine": "html_print"
    }
