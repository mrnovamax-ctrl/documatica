"""
Главная страница
"""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app.core.templates import templates
from app.core.content import load_content

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Главная страница сайта"""
    content = load_content("home")
    
    return templates.TemplateResponse(
        request=request,
        name="public/home.html",
        context={
            "content": content,
            "title": content.get("meta", {}).get("title", "Documatica — генератор документов для бизнеса"),
            "description": content.get("meta", {}).get("description", "Создавайте УПД, счета, акты и договоры онлайн бесплатно."),
        }
    )


# ============== РЕДИРЕКТЫ СО СТАРЫХ URL ==============

@router.get("/upd-s-nds", response_class=RedirectResponse)
async def redirect_upd_s_nds():
    return RedirectResponse(url="/upd/s-nds/", status_code=301)


@router.get("/upd-bez-nds", response_class=RedirectResponse)
async def redirect_upd_bez_nds():
    return RedirectResponse(url="/upd/bez-nds/", status_code=301)


@router.get("/upd-dlya-ooo", response_class=RedirectResponse)
async def redirect_upd_ooo():
    return RedirectResponse(url="/upd/ooo/", status_code=301)


@router.get("/upd-dlya-ip", response_class=RedirectResponse)
async def redirect_upd_ip():
    return RedirectResponse(url="/upd/ip/", status_code=301)


@router.get("/upd-samozanyatye", response_class=RedirectResponse)
async def redirect_upd_samozanyatye():
    return RedirectResponse(url="/upd/samozanyatye/", status_code=301)


@router.get("/upd-usn", response_class=RedirectResponse)
async def redirect_upd_usn():
    return RedirectResponse(url="/upd/usn/", status_code=301)


@router.get("/upd-demo", response_class=RedirectResponse)
async def redirect_upd_demo():
    return RedirectResponse(url="/upd/", status_code=301)


@router.get("/obrazets-zapolneniya", response_class=RedirectResponse)
async def redirect_obrazets():
    return RedirectResponse(url="/upd/obrazec-zapolneniya/", status_code=301)


@router.get("/upd-xml-edo", response_class=RedirectResponse)
async def redirect_upd_xml_edo():
    return RedirectResponse(url="/upd/xml-edo/", status_code=301)


@router.get("/skachat-excel", response_class=RedirectResponse)
async def redirect_skachat_excel():
    return RedirectResponse(url="/upd/blank-excel/", status_code=301)


@router.get("/upd-create", response_class=RedirectResponse)
async def redirect_upd_create(request: Request):
    """Редирект на создание УПД - всегда на dashboard (доступно и гостям)"""
    return RedirectResponse(url="/dashboard/upd/create/", status_code=302)


@router.get("/demo/", response_class=HTMLResponse)
async def demo_page(request: Request):
    """Демо-страница - призыв к регистрации для полного доступа"""
    return templates.TemplateResponse(
        request=request,
        name="public/demo.html",
        context={
            "title": "Демо УПД — Попробуйте бесплатно | Documatica",
            "description": "Зарегистрируйтесь, чтобы получить полный доступ к функционалу.",
        }
    )
