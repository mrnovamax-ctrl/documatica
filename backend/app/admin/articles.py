"""
Admin Articles - управление статьями
"""

import json
import uuid
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse

from app.core.templates import templates
from app.admin.context import require_admin, get_admin_context

router = APIRouter()

# Путь к данным
DATA_DIR = Path(__file__).parent.parent.parent / "data"
UPLOAD_DIR = DATA_DIR / "uploads" / "articles"
LEGACY_UPLOAD_DIR = Path(__file__).parent.parent / "static" / "uploads" / "articles"

# Создаём папку для загрузок если её нет
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Миграция: если старые файлы есть, копируем в новое хранилище (без удаления)
try:
    if LEGACY_UPLOAD_DIR.exists():
        legacy_files = list(LEGACY_UPLOAD_DIR.glob("*"))
        if legacy_files:
            for file_path in legacy_files:
                if file_path.is_file():
                    target_path = UPLOAD_DIR / file_path.name
                    if not target_path.exists():
                        shutil.copy2(file_path, target_path)
except Exception:
    pass


def load_articles() -> Dict[str, Any]:
    """Загрузка статей из JSON"""
    filepath = DATA_DIR / "articles.json"
    if filepath.exists():
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Поддержка старого формата (массив статей)
        if isinstance(data, list):
            return {"articles": data, "categories": []}
        return data
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
async def articles_list(request: Request, page: int = 1, q: str = ""):
    """Список статей"""
    auth_check = require_admin(request)
    if auth_check:
        return auth_check
    
    data = load_articles()
    articles = data.get("articles", [])
    categories = data.get("categories", [])

    query = (q or "").strip().lower()
    if query:
        articles = [
            a for a in articles
            if query in (a.get("title", "").lower())
            or query in (a.get("slug", "").lower())
            or query in (a.get("excerpt", "").lower())
            or query in (a.get("content", "").lower())
        ]
    
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
            search_query=query,
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


@router.post("/upload-image/")
async def upload_image(request: Request, file: UploadFile = File(...)):
    """Загрузка изображения статьи"""
    auth_check = require_admin(request)
    if auth_check:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    
    # Проверяем тип файла
    allowed_types = ["image/jpeg", "image/jpg", "image/png", "image/gif", "image/webp"]
    if file.content_type not in allowed_types:
        return JSONResponse({"error": "Недопустимый формат файла"}, status_code=400)
    
    # Генерируем уникальное имя файла
    file_ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
    unique_filename = f"{uuid.uuid4()}.{file_ext}"
    file_path = UPLOAD_DIR / unique_filename
    
    # Сохраняем файл
    try:
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
    except Exception as e:
        return JSONResponse({"error": f"Ошибка сохранения: {str(e)}"}, status_code=500)
    
    # Возвращаем URL
    image_url = f"/static/uploads/articles/{unique_filename}"
    return JSONResponse({"success": True, "url": image_url})


@router.post("/tinymce-upload/")
async def tinymce_upload_image(request: Request, file: UploadFile = File(...)):
    """Загрузка изображения через TinyMCE"""
    auth_check = require_admin(request)
    if auth_check:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    
    # Проверяем тип файла
    allowed_types = ["image/jpeg", "image/jpg", "image/png", "image/gif", "image/webp"]
    if file.content_type not in allowed_types:
        return JSONResponse({"error": "Недопустимый формат файла"}, status_code=400)
    
    # Генерируем уникальное имя файла
    file_ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
    unique_filename = f"{uuid.uuid4()}.{file_ext}"
    file_path = UPLOAD_DIR / unique_filename
    
    # Сохраняем файл
    try:
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
    except Exception as e:
        return JSONResponse({"error": f"Ошибка сохранения: {str(e)}"}, status_code=500)
    
    # Возвращаем URL в формате TinyMCE
    image_url = f"/static/uploads/articles/{unique_filename}"
    return JSONResponse({"location": image_url})
