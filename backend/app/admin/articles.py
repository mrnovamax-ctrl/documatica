"""
Admin Articles - управление статьями
"""

import json
import uuid
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse

from app.core.templates import templates
from app.admin.context import require_admin, get_admin_context

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


def save_articles(data: Dict[str, Any]):
    """Сохранение статей в JSON"""
    filepath = DATA_DIR / "articles.json"
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_article_by_id(article_id: str) -> Optional[Dict]:
    """Получение статьи по ID"""
    data = load_articles()
    for article in data.get("articles", []):
        if article.get("id") == article_id:
            return article
    return None


def generate_slug(title: str) -> str:
    """Генерация slug из заголовка"""
    import re
    # Транслитерация
    translit_map = {
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo',
        'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
        'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
        'ф': 'f', 'х': 'h', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch', 'ъ': '',
        'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya'
    }
    result = title.lower()
    for ru, en in translit_map.items():
        result = result.replace(ru, en)
    # Оставляем только буквы, цифры и дефисы
    result = re.sub(r'[^a-z0-9]+', '-', result)
    result = re.sub(r'-+', '-', result)
    result = result.strip('-')
    return result[:100]


@router.get("/", response_class=HTMLResponse)
async def articles_list(request: Request, page: int = 1):
    """Список статей"""
    auth_check = require_admin(request)
    if auth_check:
        return auth_check
    
    data = load_articles()
    articles = data.get("articles", [])
    categories = data.get("categories", [])
    
    # Сортировка по дате (новые сначала)
    articles.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    
    # Пагинация
    per_page = 20
    total = len(articles)
    total_pages = (total + per_page - 1) // per_page
    start = (page - 1) * per_page
    end = start + per_page
    articles_page = articles[start:end]
    
    return templates.TemplateResponse(
        request=request,
        name="admin/articles/list.html",
        context=get_admin_context(
            request=request,
            title="Статьи — Админ-панель",
            active_menu="articles",
            articles=articles_page,
            categories=categories,
            page=page,
            total_pages=total_pages,
            total=total,
        )
    )


@router.get("/create/", response_class=HTMLResponse)
async def article_create(request: Request):
    """Форма создания статьи"""
    auth_check = require_admin(request)
    if auth_check:
        return auth_check
    
    data = load_articles()
    categories = data.get("categories", [])
    
    return templates.TemplateResponse(
        request=request,
        name="admin/articles/edit.html",
        context=get_admin_context(
            request=request,
            title="Новая статья — Админ-панель",
            active_menu="articles",
            article=None,
            categories=categories,
            is_new=True,
        )
    )


@router.post("/create/", response_class=HTMLResponse)
async def article_create_post(
    request: Request,
    title: str = Form(...),
    slug: str = Form(""),
    excerpt: str = Form(""),
    content: str = Form(""),
    category: str = Form(""),
    image: str = Form(""),
    meta_title: str = Form(""),
    meta_description: str = Form(""),
    meta_keywords: str = Form(""),
    is_published: bool = Form(False),
):
    """Создание статьи"""
    auth_check = require_admin(request)
    if auth_check:
        return auth_check
    
    data = load_articles()
    
    # Генерируем slug если не указан
    if not slug:
        slug = generate_slug(title)
    
    # Проверяем уникальность slug
    existing_slugs = [a.get("slug") for a in data.get("articles", [])]
    if slug in existing_slugs:
        slug = f"{slug}-{str(uuid.uuid4())[:8]}"
    
    new_article = {
        "id": str(uuid.uuid4()),
        "slug": slug,
        "title": title,
        "excerpt": excerpt,
        "content": content,
        "category": category,
        "image": image,
        "meta_title": meta_title or title,
        "meta_description": meta_description or excerpt[:160],
        "meta_keywords": meta_keywords,
        "is_published": is_published,
        "views": 0,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }
    
    data["articles"].append(new_article)
    save_articles(data)
    
    return RedirectResponse(url=f"/admin/articles/{new_article['id']}/", status_code=303)


@router.get("/{article_id}/", response_class=HTMLResponse)
async def article_edit(request: Request, article_id: str):
    """Форма редактирования статьи"""
    auth_check = require_admin(request)
    if auth_check:
        return auth_check
    
    article = get_article_by_id(article_id)
    if not article:
        return RedirectResponse(url="/admin/articles/", status_code=303)
    
    data = load_articles()
    categories = data.get("categories", [])
    
    return templates.TemplateResponse(
        request=request,
        name="admin/articles/edit.html",
        context=get_admin_context(
            request=request,
            title=f"Редактировать: {article['title'][:50]} — Админ-панель",
            active_menu="articles",
            article=article,
            categories=categories,
            is_new=False,
        )
    )


@router.post("/{article_id}/", response_class=HTMLResponse)
async def article_edit_post(
    request: Request,
    article_id: str,
    title: str = Form(...),
    slug: str = Form(""),
    excerpt: str = Form(""),
    content: str = Form(""),
    category: str = Form(""),
    image: str = Form(""),
    meta_title: str = Form(""),
    meta_description: str = Form(""),
    meta_keywords: str = Form(""),
    is_published: bool = Form(False),
):
    """Сохранение статьи"""
    auth_check = require_admin(request)
    if auth_check:
        return auth_check
    
    data = load_articles()
    
    for i, article in enumerate(data.get("articles", [])):
        if article.get("id") == article_id:
            # Обновляем поля
            data["articles"][i].update({
                "title": title,
                "slug": slug or generate_slug(title),
                "excerpt": excerpt,
                "content": content,
                "category": category,
                "image": image,
                "meta_title": meta_title or title,
                "meta_description": meta_description or excerpt[:160],
                "meta_keywords": meta_keywords,
                "is_published": is_published,
                "updated_at": datetime.now().isoformat(),
            })
            break
    
    save_articles(data)
    
    return RedirectResponse(url=f"/admin/articles/{article_id}/?saved=1", status_code=303)


@router.post("/{article_id}/delete/")
async def article_delete(request: Request, article_id: str):
    """Удаление статьи"""
    auth_check = require_admin(request)
    if auth_check:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    
    data = load_articles()
    data["articles"] = [a for a in data.get("articles", []) if a.get("id") != article_id]
    save_articles(data)
    
    return RedirectResponse(url="/admin/articles/", status_code=303)


@router.post("/{article_id}/toggle-publish/")
async def article_toggle_publish(request: Request, article_id: str):
    """Переключение публикации"""
    auth_check = require_admin(request)
    if auth_check:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    
    data = load_articles()
    
    for article in data.get("articles", []):
        if article.get("id") == article_id:
            article["is_published"] = not article.get("is_published", False)
            article["updated_at"] = datetime.now().isoformat()
            break
    
    save_articles(data)
    
    return JSONResponse({"success": True})
