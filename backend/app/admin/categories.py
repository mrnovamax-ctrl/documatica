"""
Admin Categories - управление категориями статей (иерархия, мета, макет, секции)
"""

from typing import List, Optional
from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from sqlalchemy.orm import Session, joinedload

from app.core.templates import templates
from app.database import get_db
from app.models import ArticleCategory, CategorySection, CategoryBlock
from app.admin.context import require_admin, get_admin_context

router = APIRouter()

SECTION_TYPES = [
    ("hero", "Hero"),
    ("features", "Блок преимуществ"),
    ("about", "О нас"),
    ("cta", "Призыв к действию"),
    ("faq", "FAQ"),
    ("pricing", "Тарифы"),
    ("seo_text", "SEO-текст"),
    ("articles_list", "Список статей"),
    ("articles_preview", "Последние статьи"),
    ("custom", "Произвольная секция"),
]


def _normalize_slug(s: str) -> str:
    return (s or "").strip().lower().replace(" ", "-").strip("/").replace("/", "-")


def _build_full_slug(parent: Optional[ArticleCategory], slug: str) -> str:
    if not parent:
        return slug
    return f"{parent.full_slug.rstrip('/')}/{slug}"


def _tree_categories(db: Session) -> List[dict]:
    """Строит дерево категорий (root -> children)."""
    all_cats = (
        db.query(ArticleCategory)
        .options(joinedload(ArticleCategory.sections))
        .order_by(ArticleCategory.position, ArticleCategory.full_slug)
        .all()
    )
    by_parent: dict = {}
    for c in all_cats:
        pid = c.parent_id
        if pid not in by_parent:
            by_parent[pid] = []
        by_parent[pid].append(c)
    result = []

    def walk(pid: Optional[int], level: int):
        for cat in by_parent.get(pid) or []:
            result.append({"category": cat, "level": level})
            walk(cat.id, level + 1)

    walk(None, 0)
    return result


@router.get("/", response_class=HTMLResponse)
async def categories_list(request: Request, db: Session = Depends(get_db)):
    """Список категорий (дерево)."""
    auth_check = require_admin(request)
    if auth_check:
        return auth_check
    tree = _tree_categories(db)
    return templates.TemplateResponse(
        request=request,
        name="admin/categories/list.html",
        context=get_admin_context(
            request=request,
            title="Категории статей — Админ-панель",
            active_menu="articles",
            tree=tree,
        ),
    )


@router.get("/create/", response_class=HTMLResponse)
async def category_create_form(request: Request, db: Session = Depends(get_db), parent_id: Optional[int] = None):
    """Форма создания категории."""
    auth_check = require_admin(request)
    if auth_check:
        return auth_check
    parents = db.query(ArticleCategory).filter(ArticleCategory.parent_id.is_(None)).order_by(ArticleCategory.position).all()
    parent = db.query(ArticleCategory).filter(ArticleCategory.id == parent_id).first() if parent_id else None
    return templates.TemplateResponse(
        request=request,
        name="admin/categories/create.html",
        context=get_admin_context(
            request=request,
            title="Создать категорию — Админ-панель",
            active_menu="categories",
            parents=parents,
            parent_id=parent_id,
            parent=parent,
        ),
    )


@router.post("/create/", response_class=HTMLResponse)
async def category_create(
    request: Request,
    db: Session = Depends(get_db),
    name: str = Form(...),
    slug: str = Form(...),
    parent_id: Optional[str] = Form(""),
    meta_title: str = Form(""),
    meta_description: str = Form(""),
    meta_keywords: str = Form(""),
    canonical_url: str = Form(""),
    layout: str = Form("no_sidebar"),
):
    """Создание категории."""
    auth_check = require_admin(request)
    if auth_check:
        return auth_check
    seg = _normalize_slug(slug)
    if not seg:
        return RedirectResponse(url="/admin/categories/create/?error=slug", status_code=303)
    pid = int(parent_id) if (parent_id and str(parent_id).strip()) else None
    parent = db.query(ArticleCategory).filter(ArticleCategory.id == pid).first() if pid else None
    full_slug = _build_full_slug(parent, seg)
    if db.query(ArticleCategory).filter(ArticleCategory.full_slug == full_slug).first():
        return RedirectResponse(url="/admin/categories/create/?error=exists", status_code=303)
    cat = ArticleCategory(
        parent_id=pid,
        slug=seg,
        full_slug=full_slug,
        name=name.strip(),
        meta_title=meta_title.strip() or None,
        meta_description=meta_description.strip() or None,
        meta_keywords=meta_keywords.strip() or None,
        canonical_url=canonical_url.strip() or None,
        layout=layout if layout in ("with_sidebar", "no_sidebar") else "no_sidebar",
    )
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return RedirectResponse(url=f"/admin/categories/{cat.id}/edit/", status_code=303)


@router.get("/{category_id}/edit/", response_class=HTMLResponse)
async def category_edit(request: Request, category_id: int, db: Session = Depends(get_db)):
    """Редактирование категории: мета, макет, секции (builder)."""
    auth_check = require_admin(request)
    if auth_check:
        return auth_check
    cat = (
        db.query(ArticleCategory)
        .options(joinedload(ArticleCategory.sections).joinedload(CategorySection.blocks))
        .filter(ArticleCategory.id == category_id)
        .first()
    )
    if not cat:
        return RedirectResponse(url="/admin/categories/", status_code=303)
    sections_for_template = []
    for s in sorted(cat.sections, key=lambda x: x.position):
        settings = dict(s.settings or {})
        settings.setdefault("grid_columns", getattr(s, "grid_columns", 2))
        settings.setdefault("grid_gap", getattr(s, "grid_gap", "medium"))
        settings.setdefault("grid_style", getattr(s, "grid_style", "grid"))
        sections_for_template.append({
            "id": s.id,
            "section_type": s.section_type,
            "position": s.position,
            "blocks": sorted(s.blocks, key=lambda b: b.position),
            "background_style": getattr(s, "background_style", None),
            "container_width": getattr(s, "container_width", None),
            "css_classes": getattr(s, "css_classes", None),
            "is_visible": getattr(s, "is_visible", True),
            "grid_columns": getattr(s, "grid_columns", 2),
            "grid_gap": getattr(s, "grid_gap", "medium"),
            "grid_style": getattr(s, "grid_style", "grid"),
            "settings": settings,
        })
    parents = db.query(ArticleCategory).filter(
        ArticleCategory.parent_id.is_(None),
        ArticleCategory.id != category_id,
    ).order_by(ArticleCategory.position).all()
    return templates.TemplateResponse(
        request=request,
        name="admin/categories/edit.html",
        context=get_admin_context(
            request=request,
            title=f"Категория: {cat.name} — Админ-панель",
            active_menu="categories",
            category=cat,
            sections=sections_for_template,
            section_types=SECTION_TYPES,
            parents=parents,
        ),
    )


@router.post("/{category_id}/edit/", response_class=HTMLResponse)
async def category_update(
    request: Request,
    category_id: int,
    db: Session = Depends(get_db),
    name: str = Form(...),
    slug: str = Form(...),
    parent_id: Optional[str] = Form(""),
    meta_title: str = Form(""),
    meta_description: str = Form(""),
    meta_keywords: str = Form(""),
    canonical_url: str = Form(""),
    layout: str = Form("no_sidebar"),
):
    """Обновление мета и макета категории."""
    auth_check = require_admin(request)
    if auth_check:
        return auth_check
    cat = db.query(ArticleCategory).filter(ArticleCategory.id == category_id).first()
    if not cat:
        return RedirectResponse(url="/admin/categories/", status_code=303)
    seg = _normalize_slug(slug)
    if not seg:
        return RedirectResponse(url=f"/admin/categories/{category_id}/edit/?error=slug", status_code=303)
    pid = int(parent_id) if (parent_id and str(parent_id).strip()) else None
    parent = db.query(ArticleCategory).filter(ArticleCategory.id == pid).first() if pid else None
    full_slug = _build_full_slug(parent, seg)
    existing = db.query(ArticleCategory).filter(ArticleCategory.full_slug == full_slug).first()
    if existing and existing.id != category_id:
        return RedirectResponse(url=f"/admin/categories/{category_id}/edit/?error=exists", status_code=303)
    cat.parent_id = pid
    cat.slug = seg
    cat.full_slug = full_slug
    cat.name = name.strip()
    cat.meta_title = meta_title.strip() or None
    cat.meta_description = meta_description.strip() or None
    cat.meta_keywords = meta_keywords.strip() or None
    cat.canonical_url = canonical_url.strip() or None
    cat.layout = layout if layout in ("with_sidebar", "no_sidebar") else "no_sidebar"
    db.commit()
    return RedirectResponse(url=f"/admin/categories/{category_id}/edit/", status_code=303)


@router.post("/{category_id}/delete/", response_class=JSONResponse)
async def category_delete(request: Request, category_id: int, db: Session = Depends(get_db)):
    """Удаление категории."""
    auth_check = require_admin(request)
    if auth_check:
        return auth_check
    cat = db.query(ArticleCategory).filter(ArticleCategory.id == category_id).first()
    if not cat:
        return JSONResponse({"success": False, "error": "Not found"}, status_code=404)
    if db.query(ArticleCategory).filter(ArticleCategory.parent_id == category_id).first():
        return JSONResponse({"success": False, "error": "Сначала удалите дочерние категории"}, status_code=400)
    db.delete(cat)
    db.commit()
    return JSONResponse({"success": True})
