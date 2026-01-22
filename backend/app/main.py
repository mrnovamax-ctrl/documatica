"""
Documatica Backend - FastAPI Application
Сервис генерации бухгалтерских документов (УПД)
"""

from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api import documents, organizations, products, auth, dadata, templates, billing, payment, ai, upload
from app.pages import router as pages_router
from app.dashboard import router as dashboard_router
from app.admin import router as admin_router
from app.database import init_db

# Пути к статике (app/static внутри модуля app)
STATIC_DIR = Path(__file__).parent / "static"

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

# Статические файлы
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

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
