"""
Статьи/Новости - публичные страницы.
Список /news/ отдаётся из CMS, если есть опубликованная страница с slug=news.
Статьи и категории берутся из БД.
"""

from typing import Optional, List
from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session, joinedload

from app.core.templates import templates
from app.core.heroicons import get_icon_paths_html
from app.database import get_db
from app.models import Page, Article, ArticleCategory, CategorySection, NewsSidebarItem, Shortcode
from app.pages.cms_dynamic import _build_sections_for_template

router = APIRouter()


def get_published_articles(db: Session, category_slug: Optional[str] = None) -> List[Article]:
    """Опубликованные статьи, опционально по категории (slug/full_slug)."""
    q = (
        db.query(Article)
        .options(joinedload(Article.category))
        .filter(Article.is_published.is_(True))
        .order_by(Article.created_at.desc(), Article.id.desc())
    )
    if category_slug:
        cat = db.query(ArticleCategory).filter(
            (ArticleCategory.full_slug == category_slug) | (ArticleCategory.slug == category_slug)
        ).first()
        if cat:
            q = q.filter(Article.category_id == cat.id)
        else:
            q = q.filter(Article.id == -1)
    return q.all()


def get_article_by_slug(db: Session, slug: str) -> Optional[Article]:
    """Статья по slug (только опубликованная)."""
    return (
        db.query(Article)
        .options(joinedload(Article.category))
        .filter(Article.slug == slug, Article.is_published.is_(True))
        .first()
    )


def get_categories(db: Session) -> List[ArticleCategory]:
    """Список категорий из БД."""
    return db.query(ArticleCategory).order_by(ArticleCategory.name).all()


def get_category_by_slug(db: Session, slug: str) -> Optional[ArticleCategory]:
    """Категория по slug или full_slug."""
    return (
        db.query(ArticleCategory)
        .filter((ArticleCategory.full_slug == slug) | (ArticleCategory.slug == slug))
        .first()
    )


def increment_views(db: Session, slug: str) -> None:
    """Увеличить счётчик просмотров статьи по slug."""
    article = db.query(Article).filter(Article.slug == slug).first()
    if article:
        article.views = (article.views or 0) + 1
        db.commit()


def _get_articles_for_category(db: Session, category_slug: str, limit: int = 100) -> List[Article]:
    """Статьи категории по slug/full_slug (опубликованные)."""
    cat = get_category_by_slug(db, category_slug)
    if not cat:
        return []
    return (
        db.query(Article)
        .options(joinedload(Article.category))
        .filter(Article.category_id == cat.id, Article.is_published.is_(True))
        .order_by(Article.created_at.desc(), Article.id.desc())
        .limit(limit)
        .all()
    )


def _get_latest_articles(db: Session, limit: int = 5) -> List[Article]:
    """Последние опубликованные статьи для секции articles_preview."""
    return (
        db.query(Article)
        .options(joinedload(Article.category))
        .filter(Article.is_published.is_(True))
        .order_by(Article.created_at.desc(), Article.id.desc())
        .limit(limit)
        .all()
    )


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
    articles = _get_articles_for_category(db, cat.full_slug, limit=500)
    per_page = 12
    total = len(articles)
    total_pages = max(1, (total + per_page - 1) // per_page)
    start = (page - 1) * per_page
    end = start + per_page
    articles_page = articles[start:end]
    # Дочерние категории (для сайдбара и для фильтра в articles_list)
    children = db.query(ArticleCategory).filter(ArticleCategory.parent_id == cat.id).order_by(ArticleCategory.position).all()
    latest_in_category = _get_articles_for_category(db, cat.full_slug, limit=5)
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
        articles = get_published_articles(db, category_slug=category)
        categories = get_categories(db)
        current_category = get_category_by_slug(db, category) if category else None
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
            ctx["latest_articles"] = _get_latest_articles(db, 5)
        return templates.TemplateResponse(request=request, name="public/dynamic_page.html", context=ctx)

    articles = get_published_articles(db, category_slug=category)
    categories = get_categories(db)
    current_category = get_category_by_slug(db, category) if category else None
    per_page = 12
    total = len(articles)
    total_pages = max(1, (total + per_page - 1) // per_page)
    start = (page - 1) * per_page
    end = start + per_page
    articles_page = articles[start:end]
    return templates.TemplateResponse(
        request=request,
        name="public/news/index.html",
        context={
            "title": current_category.name if current_category else "Статьи и новости",
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
    article = get_article_by_slug(db, slug)
    if not article:
        raise HTTPException(status_code=404, detail="Статья не найдена")

    increment_views(db, slug)
    category = article.category

    all_articles = get_published_articles(db)
    related = [a for a in all_articles if a.category_id == article.category_id and a.slug != slug][:3]

    breadcrumb_list = [{"title": "Новости", "url": "/news/"}]
    if category:
        breadcrumb_list.append({
            "title": category.name,
            "url": f"/news/?category={category.slug}",
        })
    breadcrumb_list.append({"title": article.title, "url": None})

    base_url = str(request.base_url).rstrip("/")

    from app.core.shortcodes import process_shortcodes, render_shortcode_to_html
    from app.core.toc import process_article_toc

    raw_content = process_shortcodes(article.content or "", request, db)
    article_content, toc_items = process_article_toc(raw_content)

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

    canonical_url = f"{base_url}/news/{article.slug}/"

    return templates.TemplateResponse(
        request=request,
        name="public/news/article.html",
        context={
            "title": article.meta_title or article.title,
            "description": article.meta_description or article.excerpt,
            "article": article,
            "article_content": article_content,
            "toc_items": toc_items,
            "category": category,
            "related": related,
            "sidebar_blocks": sidebar_blocks,
            "breadcrumbs": breadcrumb_list,
            "base_url": base_url,
            "canonical_url": canonical_url,
            "use_custom_breadcrumbs": True,
        }
    )
