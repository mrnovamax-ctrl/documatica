"""
Legal pages router - Политика конфиденциальности и Согласие на обработку ПД
"""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from app.core.templates import templates
from app.core.content import load_content

router = APIRouter()


@router.get("/privacy", response_class=HTMLResponse)
async def privacy_page(request: Request):
    """Политика конфиденциальности"""
    content = load_content("privacy")
    
    return templates.TemplateResponse(
        request=request,
        name="public/legal.html",
        context={
            "request": request,
            "content": content,
            "page_type": "privacy",
        }
    )


@router.get("/agreement", response_class=HTMLResponse)
async def agreement_page(request: Request):
    """Согласие на обработку персональных данных"""
    content = load_content("agreement")
    
    return templates.TemplateResponse(
        request=request,
        name="public/legal.html",
        context={
            "request": request,
            "content": content,
            "page_type": "agreement",
        }
    )
