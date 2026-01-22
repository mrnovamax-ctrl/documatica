"""
Admin Auth - авторизация админа
"""

from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse

from app.core.templates import templates
from app.admin.context import (
    verify_admin, 
    create_admin_token, 
    get_admin_from_request
)

router = APIRouter()


@router.get("/login/", response_class=HTMLResponse)
async def admin_login_page(request: Request, error: str = None):
    """Страница входа в админку"""
    # Если уже авторизован - редирект на дашборд
    if get_admin_from_request(request):
        return RedirectResponse(url="/admin/", status_code=302)
    
    return templates.TemplateResponse(
        request=request,
        name="admin/login.html",
        context={
            "request": request,
            "title": "Вход в админ-панель — Documatica",
            "error": error,
        }
    )


@router.post("/login/", response_class=HTMLResponse)
async def admin_login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...)
):
    """Обработка формы входа"""
    if verify_admin(username, password):
        token = create_admin_token()
        response = RedirectResponse(url="/admin/", status_code=302)
        response.set_cookie(
            key="admin_token",
            value=token,
            httponly=True,
            max_age=86400,  # 24 часа
            samesite="lax"
        )
        return response
    
    # Неверные креды
    return templates.TemplateResponse(
        request=request,
        name="admin/login.html",
        context={
            "request": request,
            "title": "Вход в админ-панель — Documatica",
            "error": "Неверный логин или пароль",
        }
    )


@router.get("/logout/")
async def admin_logout():
    """Выход из админки"""
    response = RedirectResponse(url="/admin/login/", status_code=302)
    response.delete_cookie("admin_token")
    return response
