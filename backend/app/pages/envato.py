"""
Envato ThemeForest Presentation Landing Page
"""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from app.core.templates import templates

router = APIRouter()


@router.get("/envato", response_class=HTMLResponse)
async def envato_landing(request: Request):
    """Envato ThemeForest presentation page"""
    return templates.TemplateResponse(
        request=request,
        name="public/envato.html",
        context={
            "title": "Documatica v12.0 - Premium Document Management UI Kit",
            "version": "12.0",
            "price": "$49",
            "components_count": "53+",
            "pages_count": "25+",
        }
    )
