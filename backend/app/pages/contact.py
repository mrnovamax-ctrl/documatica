"""
Страница контактов
"""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

router = APIRouter()


@router.get("/contact", response_class=HTMLResponse)
async def contact_page(request: Request):
    """Страница контактов"""
    return templates.TemplateResponse(
        "contact.html",
        {
            "request": request,
            "title": "Контакты — Documatica",
            "description": "Свяжитесь с нами для получения помощи по работе с документами"
        }
    )
