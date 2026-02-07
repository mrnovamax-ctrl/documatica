"""
Статьи/Новости - публичные страницы.
Список /news/ отдаётся из CMS, если есть опубликованная страница с slug=news.
"""

import json
import time
from functools import lru_cache
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session, joinedload

from app.core.templates import templates
from app.core.heroicons import get_icon_paths_html
from app.database import get_db
from app.models import Page, ArticleCategory, CategorySection, NewsSidebarItem, Shortcode
from app.pages.cms_dynamic import _build_sections_for_template

router = APIRouter()

# Путь к данным
DATA_DIR = Path(__file__).parent.parent.parent / "data"

# TTL кэша статей (секунды)
ARTICLES_CACHE_TTL = 60


def _get_cache_key() -> int:
    """Ключ кэша с учетом TTL (меняется каждые ARTICLES_CACHE_TTL секунд)"""
    return int(time.time() // ARTICLES_CACHE_TTL)


@lru_cache(maxsize=4)
def _load_articles_cached(cache_key: int) -> Tuple[str, ...]:
    """Внутренняя функция с кэшем. Возвращает JSON как строку для hashability"""
    filepath = DATA_DIR / "articles.json"
    if filepath.exists():
        with open(filepath, "r", encoding="utf-8") as f:
            return (f.read(),)
    return ('{"articles": [], "categories": []}',)


def load_articles() -> Dict[str, Any]:
    """Загрузка статей из JSON с кэшированием (TTL: 60 сек)"""
    cache_key = _get_cache_key()
    raw = _load_articles_cached(cache_key)[0]
    data = json.loads(raw)
    # Поддержка старого формата (массив статей)
    if isinstance(data, list):
        return {"articles": data, "categories": []}
    return data


def get_published_articles() -> List[Dict]:
    """Получение опубликованных статей"""
    data = load_articles()
    articles = [a for a in data.get("articles", []) if a.get("is_published", False)]
    # Сортировка по дате (новые сначала)
    articles.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return articles


def get_article_by_slug(slug: str) -> Optional[Dict]:
    """Получение статьи по slug"""
    data = load_articles()
    for article in data.get("articles", []):
        if article.get("slug") == slug and article.get("is_published", False):
            return article
    return None


def clear_articles_cache():
    """Очистка кэша статей (вызывать при CRUD операциях)"""
    _load_articles_cached.cache_clear()


def get_categories() -> List[Dict]:
    """Получение категорий"""
    data = load_articles()
    return data.get("categories", [])


def get_category_by_slug(slug: str) -> Optional[Dict]:
    """Получение категории по slug"""
    categories = get_categories()
    for cat in categories:
        if cat.get("slug") == slug:
            return cat
    return None


def increment_views(slug: str):
    """Увеличение счетчика просмотров"""
    filepath = DATA_DIR / "articles.json"
    data = load_articles()
    for article in data.get("articles", []):
        if article.get("slug") == slug:
            article["views"] = article.get("views", 0) + 1
            break
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    # Очистка кэша после записи
    clear_articles_cache()


def _get_articles_for_category(category_slug: str, limit: int = 100) -> List[Dict]:
    """Статьи для категории (по полю category в JSON = slug категории)."""
    data = load_articles()
    articles = data.get("articles", [])
    published = [a for a in articles if a.get("is_published", False) or a.get("status") == "published"]
    filtered = [a for a in published if a.get("category") == category_slug]
    filtered.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return filtered[:limit]


def _get_latest_articles(limit: int = 5) -> List[Dict]:
    """Последние статьи для секции articles_preview (импорт из home не делаем во избежание циклических зависимостей)."""
    filepath = DATA_DIR / "articles.json"
    if not filepath.exists():
        return []
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        articles = data
    else:
        articles = data.get("articles", [])
    published = [a for a in articles if a.get("is_published", False) or a.get("status") == "published"]
    published.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return published[:limit]


@router.get("/category/{category_path:path}", response_class=HTMLResponse)
async def news_category_page(
    request: Request,
    category_path: str,
    db: Session = Depends(get_db),
    page: int = 1,
):
    """Страница категории статей из БД (мета, макет с/без сайдбара, секции)."""
    path_slug = (category_path or "").strip().strip("/")
    if not path_slug:
        raise HTTPException(status_code=404, detail="Категория не найдена")
    cat = (
        db.query(ArticleCategory)
        .options(joinedload(ArticleCategory.sections).joinedload(CategorySection.blocks))
        .filter(ArticleCategory.full_slug == path_slug)
        .first()
    )
    if not cat:
        raise HTTPException(status_code=404, detail="Категория не найдена")
    # Секции для шаблона (как у Page)
    sections_for_template = []
    for s in sorted(cat.sections, key=lambda x: x.position):
        if not getattr(s, "is_visible", True):
            continue
        settings = dict(s.settings or {})
        settings.setdefault("grid_columns", getattr(s, "grid_columns", 2))
        settings.setdefault("grid_gap", getattr(s, "grid_gap", "medium"))
        settings.setdefault("grid_style", getattr(s, "grid_style", "grid"))
        section_view = type("SectionView", (), {
            "id": s.id,
            "section_type": s.section_type,
            "blocks": s.blocks,
            "background_style": getattr(s, "background_style", "light"),
            "css_classes": getattr(s, "css_classes", None),
            "container_width": getattr(s, "container_width", "default"),
            "is_visible": True,
            "settings": settings,
            "is_dark_bg": (getattr(s, "background_style", None) or "").lower() in ("dark", "primary", "gold", "pattern_dots_dark"),
        })()
        sections_for_template.append(section_view)
    articles = _get_articles_for_category(cat.slug)
    per_page = 12
    total = len(articles)
    total_pages = max(1, (total + per_page - 1) // per_page)
    start = (page - 1) * per_page
    end = start + per_page
    articles_page = articles[start:end]
    # Дочерние категории (для сайдбара и для фильтра в articles_list)
    children = db.query(ArticleCategory).filter(ArticleCategory.parent_id == cat.id).order_by(ArticleCategory.position).all()
    latest_in_category = _get_articles_for_category(cat.slug, limit=5)
    all_cats_for_page = [cat] + list(children)
    categories_for_filter = [
        {"name": c.name, "slug": c.slug, "url": f"/news/category/{c.full_slug}/"}
        for c in all_cats_for_page
    ]
    ctx = {
        "category": cat,
        "page_sections": sections_for_template,
        "layout": cat.layout,
        "articles": articles_page,
        "total": total,
        "total_pages": total_pages,
        "page": page,
        "current_page": page,
        "children": children,
        "latest_articles_sidebar": latest_in_category,
        "categories": categories_for_filter,
        "current_category": cat,
        "title": cat.meta_title or cat.name,
        "description": cat.meta_description or "",
        "heroicon_paths": get_icon_paths_html(),
        "is_home_page": False,
    }
    return templates.TemplateResponse(
        request=request,
        name="public/category_page.html",
        context=ctx,
    )


@router.get("/", response_class=HTMLResponse)
async def news_index(request: Request, db: Session = Depends(get_db), category: Optional[str] = None, page: int = 1):
    """Список статей: из CMS (slug=news), иначе статичный шаблон."""
    cms_page = (
        db.query(Page)
        .options(joinedload(Page.sections))
        .filter(Page.slug == "news", Page.status == "published")
        .first()
    )
    if cms_page:
        articles = get_published_articles()
        categories = get_categories()
        current_category = None
        if category:
            current_category = get_category_by_slug(category)
            articles = [a for a in articles if a.get("category") == category]
        per_page = 12
        total = len(articles)
        total_pages = max(1, (total + per_page - 1) // per_page)
        start = (page - 1) * per_page
        end = start + per_page
        articles_page = articles[start:end]
        sections_for_template = _build_sections_for_template(cms_page)
        page_view = type("PageView", (), {
            "id": cms_page.id,
            "title": cms_page.title,
            "meta_title": getattr(cms_page, "meta_title", None),
            "meta_description": getattr(cms_page, "meta_description", None),
            "meta_keywords": getattr(cms_page, "meta_keywords", None),
            "canonical_url": getattr(cms_page, "canonical_url", None),
            "sections": sections_for_template,
        })()
        ctx = {
            "page": page_view,
            "latest_articles": [],
            "title": cms_page.meta_title or cms_page.title,
            "description": cms_page.meta_description or "",
            "is_home_page": False,
            "heroicon_paths": get_icon_paths_html(),
            "articles": articles_page,
            "categories": categories,
            "current_category": current_category,
            "current_page": page,
            "total_pages": total_pages,
            "total": total,
        }
        if any(s.section_type == "articles_preview" for s in cms_page.sections):
            ctx["latest_articles"] = _get_latest_articles(5)
        return templates.TemplateResponse(request=request, name="public/dynamic_page.html", context=ctx)

    articles = get_published_articles()
    categories = get_categories()
    current_category = None
    if category:
        current_category = get_category_by_slug(category)
        articles = [a for a in articles if a.get("category") == category]
    per_page = 12
    total = len(articles)
    total_pages = (total + per_page - 1) // per_page
    start = (page - 1) * per_page
    end = start + per_page
    articles_page = articles[start:end]
    return templates.TemplateResponse(
        request=request,
        name="public/news/index.html",
        context={
            "title": current_category["name"] if current_category else "Статьи и новости",
            "description": "Полезные статьи о налогах, бухгалтерии и документообороте для ИП и ООО",
            "articles": articles_page,
            "categories": categories,
            "current_category": current_category,
            "page": page,
            "total_pages": total_pages,
            "total": total,
            "breadcrumbs": [
                {"title": "Главная", "url": "/"},
                {"title": "Статьи", "url": None if not current_category else "/news/"},
                {"title": current_category["name"], "url": None} if current_category else None,
            ]
        }
    )


@router.get("/{slug}", response_class=RedirectResponse, include_in_schema=False)
async def news_article_redirect_trailing_slash(request: Request, slug: str):
    """Редирект /news/slug → /news/slug/ (301) для единообразия URL."""
    return RedirectResponse(url=f"/news/{slug}/", status_code=301)


@router.get("/{slug}/", response_class=HTMLResponse)
async def news_article(request: Request, slug: str, db: Session = Depends(get_db)):
    """Страница статьи. В контенте поддерживаются шорткоды [имя]."""
    article = get_article_by_slug(slug)

    if not article:
        raise HTTPException(status_code=404, detail="Статья не найдена")

    increment_views(slug)
    category = get_category_by_slug(article.get("category", ""))

    all_articles = get_published_articles()
    related = [
        a for a in all_articles
        if a.get("category") == article.get("category") and a.get("slug") != slug
    ][:3]

    breadcrumb_list = [{"title": "Новости", "url": "/news/"}]
    if category:
        breadcrumb_list.append({
            "title": category.get("name", ""),
            "url": f"/news/?category={article.get('category', '')}",
        })
    breadcrumb_list.append({"title": article.get("title", ""), "url": None})

    base_url = str(request.base_url).rstrip("/")

    from app.core.shortcodes import process_shortcodes, render_shortcode_to_html
    article_content = process_shortcodes(article.get("content") or "", request, db)

    # Сайдбар новостей: порядок и блоки из админки (CTA, похожие статьи, шорткоды)
    sidebar_items = (
        db.query(NewsSidebarItem)
        .options(joinedload(NewsSidebarItem.shortcode))
        .order_by(NewsSidebarItem.position, NewsSidebarItem.id)
        .all()
    )
    sidebar_blocks = []
    for si in sidebar_items:
        if si.block_type == "shortcode" and si.shortcode and si.shortcode.is_active:
            try:
                html = render_shortcode_to_html(si.shortcode, request, db)
                sidebar_blocks.append({"type": "shortcode", "html": html})
            except Exception:
                pass
        else:
            sidebar_blocks.append({"type": si.block_type})

    return templates.TemplateResponse(
        request=request,
        name="public/news/article.html",
        context={
            "title": article.get("meta_title") or article.get("title"),
            "description": article.get("meta_description") or article.get("excerpt"),
            "article": article,
            "article_content": article_content,
            "category": category,
            "related": related,
            "sidebar_blocks": sidebar_blocks,
            "breadcrumbs": breadcrumb_list,
            "base_url": base_url,
            "use_custom_breadcrumbs": True,
        }
    )
