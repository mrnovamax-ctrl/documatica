"""
Admin Shortcodes — создание шорткодов по шаблону секции и заполнение данных в форме.
Пользователь: выбирает шаблон (тип секции) → заполняет поля → сохраняет → получает шорткод.
"""

import json
import re
from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session, joinedload

from app.core.templates import templates
from app.core.shortcode_defaults import (
    SECTION_TYPES,
    default_blocks_for_section_type,
    default_settings_for_section_type,
    cta_blocks_from_form,
    cta_form_from_blocks,
)
from app.database import get_db
from app.models import Shortcode, PageSection
from app.admin.context import require_admin, get_admin_context

router = APIRouter()


def _slug_from_name(s: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_-]", "", (s or "").strip().lower().replace(" ", "_"))


@router.get("/", response_class=HTMLResponse)
async def shortcodes_list(request: Request, db: Session = Depends(get_db)):
    auth_check = require_admin(request)
    if auth_check:
        return auth_check
    items = db.query(Shortcode).options(joinedload(Shortcode.page_section)).order_by(Shortcode.name).all()
    return templates.TemplateResponse(
        request=request,
        name="admin/shortcodes/list.html",
        context=get_admin_context(
            request=request,
            title="Шорткоды",
            active_menu="shortcodes",
            shortcodes=items,
        ),
    )


@router.get("/create/", response_class=HTMLResponse)
async def shortcode_create(request: Request, db: Session = Depends(get_db)):
    auth_check = require_admin(request)
    if auth_check:
        return auth_check
    ctx = get_admin_context(
        request=request,
        title="Новый шорткод",
        active_menu="shortcodes",
        shortcode=None,
        section_types=SECTION_TYPES,
        is_new=True,
    )
    return templates.TemplateResponse(request=request, name="admin/shortcodes/edit.html", context=ctx)


@router.post("/create/", response_class=HTMLResponse)
async def shortcode_create_post(
    request: Request,
    db: Session = Depends(get_db),
    title: str = Form(...),
    name: str = Form(""),
    section_type: str = Form(...),
):
    auth_check = require_admin(request)
    if auth_check:
        return auth_check
    slug = _slug_from_name(name) or _slug_from_name(title)
    if not slug:
        return RedirectResponse(url="/admin/shortcodes/create/?error=name", status_code=303)
    if db.query(Shortcode).filter(Shortcode.name == slug).first():
        return RedirectResponse(url="/admin/shortcodes/create/?error=duplicate", status_code=303)
    blocks = default_blocks_for_section_type(section_type)
    settings = default_settings_for_section_type(section_type)
    sc = Shortcode(
        name=slug,
        title=title.strip(),
        page_section_id=None,
        section_type=section_type,
        section_settings=settings,
        blocks=blocks,
        is_active=True,
    )
    db.add(sc)
    db.commit()
    return RedirectResponse(url=f"/admin/shortcodes/{sc.id}/?saved=1", status_code=303)


@router.get("/{shortcode_id}/", response_class=HTMLResponse)
async def shortcode_edit(request: Request, shortcode_id: int, db: Session = Depends(get_db)):
    auth_check = require_admin(request)
    if auth_check:
        return auth_check
    sc = db.query(Shortcode).filter(Shortcode.id == shortcode_id).first()
    if not sc:
        return RedirectResponse(url="/admin/shortcodes/", status_code=303)
    cta_form = None
    if sc.section_type == "cta" and (sc.blocks or sc.page_section_id is None):
        cta_form = cta_form_from_blocks(sc.blocks or [])
    ctx = get_admin_context(
        request=request,
        title=f"Шорткод: {sc.title}",
        active_menu="shortcodes",
        shortcode=sc,
        section_types=SECTION_TYPES,
        is_new=False,
        cta_form=cta_form,
    )
    return templates.TemplateResponse(request=request, name="admin/shortcodes/edit.html", context=ctx)


@router.post("/{shortcode_id}/", response_class=HTMLResponse)
async def shortcode_edit_post(
    request: Request,
    shortcode_id: int,
    db: Session = Depends(get_db),
    title: str = Form(...),
    name: str = Form(""),
    section_type: str = Form(""),
    # CTA
    cta_variant: str = Form("basic"),
    cta_label: str = Form(""),
    cta_heading: str = Form(""),
    cta_heading_level: str = Form("2"),
    cta_paragraph: str = Form(""),
    cta_button_text: str = Form("Перейти"),
    cta_button_url: str = Form("/dashboard/"),
    # Прочие типы — JSON
    blocks_json: str = Form(""),
    section_settings_json: str = Form("{}"),
    is_active: str = Form("0"),
):
    auth_check = require_admin(request)
    if auth_check:
        return auth_check
    sc = db.query(Shortcode).filter(Shortcode.id == shortcode_id).first()
    if not sc:
        return RedirectResponse(url="/admin/shortcodes/", status_code=303)
    slug = _slug_from_name(name) or _slug_from_name(title) or sc.name
    other = db.query(Shortcode).filter(Shortcode.name == slug, Shortcode.id != shortcode_id).first()
    if other:
        return RedirectResponse(url=f"/admin/shortcodes/{shortcode_id}/?error=duplicate", status_code=303)

    st = section_type or sc.section_type or "cta"
    try:
        level = int(cta_heading_level)
    except ValueError:
        level = 2

    if st == "cta":
        blocks = cta_blocks_from_form(
            label_text=cta_label,
            heading_text=cta_heading,
            heading_level=level,
            paragraph_text=cta_paragraph,
            button_text=cta_button_text,
            button_url=cta_button_url,
            cta_variant=cta_variant,
        )
        settings = {"cta_variant": cta_variant, "background_style": "light"}
    else:
        try:
            blocks = json.loads(blocks_json) if blocks_json.strip() else default_blocks_for_section_type(st)
        except json.JSONDecodeError:
            blocks = default_blocks_for_section_type(st)
        try:
            settings = json.loads(section_settings_json) if section_settings_json.strip() else default_settings_for_section_type(st)
        except json.JSONDecodeError:
            settings = default_settings_for_section_type(st)
        # Варианты из выпадающих списков (те же ключи, что в редакторе страниц)
        if st == "hero":
            settings["hero_variant"] = hero_variant or "default"
        elif st == "faq":
            settings["accordion_variant"] = accordion_variant or "basic"
        elif st == "pricing":
            settings["pricing_variant"] = pricing_variant or "basic"

    sc.name = slug
    sc.title = title.strip()
    sc.page_section_id = None
    sc.section_type = st
    sc.section_settings = settings
    sc.blocks = blocks
    sc.is_active = is_active in ("1", "on", "true", True)
    db.commit()
    return RedirectResponse(url=f"/admin/shortcodes/{shortcode_id}/?saved=1", status_code=303)


@router.post("/{shortcode_id}/delete/", response_class=RedirectResponse)
async def shortcode_delete(request: Request, shortcode_id: int, db: Session = Depends(get_db)):
    auth_check = require_admin(request)
    if auth_check:
        return auth_check
    sc = db.query(Shortcode).filter(Shortcode.id == shortcode_id).first()
    if sc:
        db.delete(sc)
        db.commit()
    return RedirectResponse(url="/admin/shortcodes/", status_code=303)
