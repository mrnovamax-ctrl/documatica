"""
УПД - публичные страницы (хаб и лендинги)
"""

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from typing import Optional

from app.core.templates import templates
from app.core.content import load_content

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def upd_hub(request: Request):
    """Хаб УПД - главная страница раздела"""
    content = load_content("upd/index")
    
    return templates.TemplateResponse(
        request=request,
        name="public/upd/index.html",
        context={
            "content": content,
            "breadcrumbs": [
                {"title": "Главная", "url": "/"},
                {"title": "УПД", "url": None},
            ]
        }
    )


@router.get("/ooo/", response_class=HTMLResponse)
async def upd_ooo(request: Request):
    """УПД для ООО"""
    content = load_content("upd/ooo")
    
    return templates.TemplateResponse(
        request=request,
        name="public/upd/landing.html",
        context={
            "content": content,
            "breadcrumbs": [
                {"title": "Главная", "url": "/"},
                {"title": "УПД", "url": "/upd/"},
                {"title": "Для ООО", "url": None},
            ]
        }
    )


@router.get("/ip/", response_class=HTMLResponse)
async def upd_ip(request: Request):
    """УПД для ИП"""
    content = load_content("upd/ip")
    
    return templates.TemplateResponse(
        request=request,
        name="public/upd/landing.html",
        context={
            "content": content,
            "breadcrumbs": [
                {"title": "Главная", "url": "/"},
                {"title": "УПД", "url": "/upd/"},
                {"title": "Для ИП", "url": None},
            ]
        }
    )


@router.get("/samozanyatye/", response_class=HTMLResponse)
async def upd_samozanyatye(request: Request):
    """УПД для самозанятых"""
    content = load_content("upd/samozanyatye")
    
    return templates.TemplateResponse(
        request=request,
        name="public/upd/landing.html",
        context={
            "content": content,
            "breadcrumbs": [
                {"title": "Главная", "url": "/"},
                {"title": "УПД", "url": "/upd/"},
                {"title": "Для самозанятых", "url": None},
            ]
        }
    )


@router.get("/s-nds/", response_class=HTMLResponse)
async def upd_s_nds(request: Request):
    """УПД с НДС"""
    content = load_content("upd/s-nds")
    
    return templates.TemplateResponse(
        request=request,
        name="public/upd/landing.html",
        context={
            "content": content,
            "breadcrumbs": [
                {"title": "Главная", "url": "/"},
                {"title": "УПД", "url": "/upd/"},
                {"title": "С НДС", "url": None},
            ]
        }
    )


@router.get("/bez-nds/", response_class=HTMLResponse)
async def upd_bez_nds(request: Request):
    """УПД без НДС"""
    content = load_content("upd/bez-nds")
    
    return templates.TemplateResponse(
        request=request,
        name="public/upd/landing.html",
        context={
            "content": content,
            "breadcrumbs": [
                {"title": "Главная", "url": "/"},
                {"title": "УПД", "url": "/upd/"},
                {"title": "Без НДС", "url": None},
            ]
        }
    )


@router.get("/usn/", response_class=HTMLResponse)
async def upd_usn(request: Request):
    """УПД на УСН"""
    content = load_content("upd/usn")
    
    return templates.TemplateResponse(
        request=request,
        name="public/upd/landing.html",
        context={
            "content": content,
            "breadcrumbs": [
                {"title": "Главная", "url": "/"},
                {"title": "УПД", "url": "/upd/"},
                {"title": "На УСН", "url": None},
            ]
        }
    )


@router.get("/2026/", response_class=HTMLResponse)
async def upd_2026(request: Request):
    """УПД 2026 - новая форма"""
    content = load_content("upd/2026")
    
    return templates.TemplateResponse(
        request=request,
        name="public/upd/landing.html",
        context={
            "content": content,
            "breadcrumbs": [
                {"title": "Главная", "url": "/"},
                {"title": "УПД", "url": "/upd/"},
                {"title": "Форма 2026", "url": None},
            ]
        }
    )


@router.get("/obrazec/", response_class=HTMLResponse)
@router.get("/obrazec-zapolneniya/", response_class=HTMLResponse)
async def upd_obrazec(request: Request):
    """Образец заполнения УПД"""
    content = load_content("upd/obrazec-zapolneniya")
    
    return templates.TemplateResponse(
        request=request,
        name="public/upd/info.html",
        context={
            "content": content,
            "breadcrumbs": [
                {"title": "Главная", "url": "/"},
                {"title": "УПД", "url": "/upd/"},
                {"title": "Образец заполнения", "url": None},
            ]
        }
    )


@router.get("/blank-excel/", response_class=HTMLResponse)
async def upd_blank_excel(request: Request):
    """Скачать бланк УПД Excel"""
    return templates.TemplateResponse(
        request=request,
        name="public/upd/download.html",
        context={
            "meta": {
                "title": "Скачать бланк УПД Excel бесплатно — Documatica",
                "description": "Скачайте пустой бланк УПД в формате Excel (.xlsx) бесплатно. Актуальная форма 2026 года.",
            },
            "page": {
                "h1": "Скачать бланк УПД Excel",
                "format": "Excel (.xlsx)",
                "file_url": "/static/blanks/upd-blank-2026.xlsx",
            },
            "breadcrumbs": [
                {"title": "Главная", "url": "/"},
                {"title": "УПД", "url": "/upd/"},
                {"title": "Скачать Excel", "url": None},
            ]
        }
    )


@router.get("/blank-word/", response_class=HTMLResponse)
async def upd_blank_word(request: Request):
    """Скачать бланк УПД Word"""
    return templates.TemplateResponse(
        request=request,
        name="public/upd/download.html",
        context={
            "meta": {
                "title": "Скачать бланк УПД Word бесплатно — Documatica",
                "description": "Скачайте пустой бланк УПД в формате Word (.docx) бесплатно. Актуальная форма 2026 года.",
            },
            "page": {
                "h1": "Скачать бланк УПД Word",
                "format": "Word (.docx)",
                "file_url": "/static/blanks/upd-blank-2026.docx",
            },
            "breadcrumbs": [
                {"title": "Главная", "url": "/"},
                {"title": "УПД", "url": "/upd/"},
                {"title": "Скачать Word", "url": None},
            ]
        }
    )


@router.get("/xml-edo/", response_class=HTMLResponse)
async def upd_xml_edo(request: Request):
    """УПД XML для ЭДО"""
    content = load_content("upd/xml-edo")
    
    return templates.TemplateResponse(
        request=request,
        name="public/upd/landing.html",
        context={
            "content": content,
            "breadcrumbs": [
                {"title": "Главная", "url": "/"},
                {"title": "УПД", "url": "/upd/"},
                {"title": "XML для ЭДО", "url": None},
            ]
        }
    )


# ============== РЕДИРЕКТЫ СО СТАРЫХ URL ==============

@router.get("/s-nds", response_class=RedirectResponse)
async def redirect_upd_s_nds():
    """Редирект: /upd/s-nds → /upd/s-nds/"""
    return RedirectResponse(url="/upd/s-nds/", status_code=301)


@router.get("/bez-nds", response_class=RedirectResponse)
async def redirect_upd_bez_nds():
    """Редирект: /upd/bez-nds → /upd/bez-nds/"""
    return RedirectResponse(url="/upd/bez-nds/", status_code=301)


@router.get("/ooo", response_class=RedirectResponse)
async def redirect_upd_ooo():
    """Редирект: /upd/ooo → /upd/ooo/"""
    return RedirectResponse(url="/upd/ooo/", status_code=301)


@router.get("/ip", response_class=RedirectResponse)
async def redirect_upd_ip():
    """Редирект: /upd/ip → /upd/ip/"""
    return RedirectResponse(url="/upd/ip/", status_code=301)


@router.get("/samozanyatye", response_class=RedirectResponse)
async def redirect_upd_samozanyatye():
    """Редирект: /upd/samozanyatye → /upd/samozanyatye/"""
    return RedirectResponse(url="/upd/samozanyatye/", status_code=301)


@router.get("/usn", response_class=RedirectResponse)
async def redirect_upd_usn():
    """Редирект: /upd/usn → /upd/usn/"""
    return RedirectResponse(url="/upd/usn/", status_code=301)


@router.get("/2026", response_class=RedirectResponse)
async def redirect_upd_2026():
    """Редирект: /upd/2026 → /upd/2026/"""
    return RedirectResponse(url="/upd/2026/", status_code=301)


@router.get("/obrazec-zapolneniya", response_class=RedirectResponse)
async def redirect_upd_obrazec():
    """Редирект: /upd/obrazec-zapolneniya → /upd/obrazec-zapolneniya/"""
    return RedirectResponse(url="/upd/obrazec-zapolneniya/", status_code=301)


@router.get("/xml-edo", response_class=RedirectResponse)
async def redirect_upd_xml_edo():
    """Редирект: /upd/xml-edo → /upd/xml-edo/"""
    return RedirectResponse(url="/upd/xml-edo/", status_code=301)


@router.get("/blank-excel", response_class=RedirectResponse)
async def redirect_upd_blank_excel():
    """Редирект: /upd/blank-excel → /upd/blank-excel/"""
    return RedirectResponse(url="/upd/blank-excel/", status_code=301)


@router.get("/blank-word", response_class=RedirectResponse)
async def redirect_upd_blank_word():
    """Редирект: /upd/blank-word → /upd/blank-word/"""
    return RedirectResponse(url="/upd/blank-word/", status_code=301)
