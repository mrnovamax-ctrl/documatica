"""
Статьи/Новости - публичные страницы
"""

import json
from pathlib import Path
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse

from app.core.templates import templates

router = APIRouter()

# Путь к данным
DATA_DIR = Path(__file__).parent.parent.parent / "data"


def load_articles() -> Dict[str, Any]:
    """Загрузка статей из JSON"""
    filepath = DATA_DIR / "articles.json"
    if filepath.exists():
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"articles": [], "categories": []}


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


@router.get("/", response_class=HTMLResponse)
async def news_index(request: Request, category: Optional[str] = None, page: int = 1):
    """Список статей"""
    articles = get_published_articles()
    categories = get_categories()
    
    # Фильтрация по категории
    current_category = None
    if category:
        current_category = get_category_by_slug(category)
        articles = [a for a in articles if a.get("category") == category]
    
    # Пагинация
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


@router.get("/{slug}/", response_class=HTMLResponse)
async def news_article(request: Request, slug: str):
    """Страница статьи"""
    article = get_article_by_slug(slug)
    
    if not article:
        raise HTTPException(status_code=404, detail="Статья не найдена")
    
    # Увеличиваем счетчик просмотров
    increment_views(slug)
    
    # Получаем категорию
    category = get_category_by_slug(article.get("category", ""))
    
    # Похожие статьи (из той же категории)
    all_articles = get_published_articles()
    related = [
        a for a in all_articles 
        if a.get("category") == article.get("category") and a.get("slug") != slug
    ][:3]
    
    return templates.TemplateResponse(
        request=request,
        name="public/news/article.html",
        context={
            "title": article.get("meta_title") or article.get("title"),
            "description": article.get("meta_description") or article.get("excerpt"),
            "article": article,
            "category": category,
            "related": related,
            "breadcrumbs": [
                {"title": "Главная", "url": "/"},
                {"title": "Статьи", "url": "/news/"},
                {"title": category["name"] if category else "Статья", "url": f"/news/?category={article.get('category')}" if category else None},
                {"title": article.get("title"), "url": None},
            ]
        }
    )
