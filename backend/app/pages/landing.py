"""
Landing Page Router
"""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from app.core.templates import templates

router = APIRouter()


@router.get("/landing", response_class=HTMLResponse)
async def landing_page(request: Request):
    """Лендинг проекта Documatica"""
    return templates.TemplateResponse(
        request=request,
        name="public/landing.html",
        context={
            "title": "Documatica - Генератор первичных документов"
        }
    )
