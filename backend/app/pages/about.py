"""
Страница "О нас"
"""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from app.core.templates import templates

router = APIRouter()


@router.get("/about", response_class=HTMLResponse)
async def about_page(request: Request):
    """Страница О нас / О компании"""
    return templates.TemplateResponse(
        request=request,
        name="public/about.html",
        context={
            "title": "О сервисе Documatica — Генератор документов для бизнеса",
            "description": "Documatica — современный онлайн-сервис для автоматической генерации бухгалтерских документов. УПД, счета, акты, договоры.",
            "current_year": "2026"
        }
    )
