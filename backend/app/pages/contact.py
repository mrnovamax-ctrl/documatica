"""
Страница контактов
"""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from app.core.templates import templates

router = APIRouter()


@router.get("/contact", response_class=HTMLResponse)
async def contact_page(request: Request):
    """Страница контактов"""
    return templates.TemplateResponse(
        request=request,
        name="contact.html",
        context={
            "title": "Контакты — Documatica",
            "description": "Свяжитесь с нами для получения помощи по работе с документами"
        }
    )
