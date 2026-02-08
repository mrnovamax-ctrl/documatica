"""
Admin Articles - управление статьями
"""

import uuid
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Request, Form, UploadFile, Depends
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from sqlalchemy.orm import Session, joinedload

from app.core.templates import templates
from app.database import get_db
from app.models import ArticleCategory, Article, Redirect
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


def _category_slug_to_id(db: Session, category_slug: str) -> Optional[int]:
    """Возвращает id категории по slug/full_slug."""
    if not category_slug:
        return None
    cat = db.query(ArticleCategory).filter(
        (ArticleCategory.full_slug == category_slug) | (ArticleCategory.slug == category_slug)
    ).first()
    return cat.id if cat else None


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
async def articles_list(
    request: Request,
    db: Session = Depends(get_db),
    page: int = 1,
    q: str = "",
):
    """Список статей"""
    auth_check = require_admin(request)
    if auth_check:
        return auth_check

    query = (q or "").strip().lower()
    qry = db.query(Article).options(joinedload(Article.category)).order_by(Article.updated_at.desc(), Article.id.desc())
    if query:
        qry = qry.filter(
            Article.title.ilike(f"%{query}%")
            | Article.slug.ilike(f"%{query}%")
            | (Article.excerpt.isnot(None) & Article.excerpt.ilike(f"%{query}%"))
            | (Article.content.isnot(None) & Article.content.ilike(f"%{query}%"))
        )
    total = qry.count()
    per_page = 20
    total_pages = max(1, (total + per_page - 1) // per_page)
    articles_page = qry.offset((page - 1) * per_page).limit(per_page).all()
    categories = db.query(ArticleCategory).order_by(ArticleCategory.name).all()

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
async def article_create(request: Request, db: Session = Depends(get_db)):
    """Форма создания статьи"""
    auth_check = require_admin(request)
    if auth_check:
        return auth_check
    
    categories = db.query(ArticleCategory).order_by(ArticleCategory.name).all()
    
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
            saved=False,
        )
    )


@router.post("/create/", response_class=HTMLResponse)
async def article_create_post(
    request: Request,
    db: Session = Depends(get_db),
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

    slug = (slug or generate_slug(title)).strip()
    if db.query(Article).filter(Article.slug == slug).first():
        slug = f"{slug}-{uuid.uuid4().hex[:8]}"

    now = datetime.utcnow()
    new_article = Article(
        category_id=_category_slug_to_id(db, category),
        slug=slug,
        title=title,
        excerpt=excerpt or None,
        content=content or None,
        image=image or None,
        meta_title=meta_title or title,
        meta_description=meta_description or ((excerpt or "")[:160] if excerpt else None),
        meta_keywords=meta_keywords or None,
        is_published=is_published,
        views=0,
        created_at=now,
        updated_at=now,
    )
    db.add(new_article)
    db.commit()
    db.refresh(new_article)
    return RedirectResponse(url=f"/admin/articles/{new_article.id}/", status_code=303)


def _is_upload_file(obj) -> bool:
    """Проверка: объект похож на Starlette UploadFile (есть read)."""
    if obj is None:
        return False
    return callable(getattr(obj, "read", None))


def _take_first_file(val) -> Optional[UploadFile]:
    """Берёт первый файл из значения (один объект или список)."""
    if val is None:
        return None
    if isinstance(val, (list, tuple)) and val:
        val = val[0]
    return val if _is_upload_file(val) else None


def _get_upload_file_from_form(form) -> Optional[UploadFile]:
    """Извлекает первый загруженный файл из multipart form."""
    for field_name in ("file", "blobid0", "imagetools0", "blobid1", "imagetools1"):
        try:
            if hasattr(form, "getlist"):
                v = _take_first_file(form.getlist(field_name))
            else:
                v = _take_first_file(form.get(field_name))
            if v:
                return v
        except (KeyError, TypeError, IndexError):
            continue
    try:
        keys = list(form.keys()) if hasattr(form, "keys") else [k for k in form]
        for key in keys:
            try:
                if hasattr(form, "getlist"):
                    v = _take_first_file(form.getlist(key))
                else:
                    v = _take_first_file(form.get(key))
                if v:
                    return v
            except (KeyError, TypeError, IndexError):
                continue
    except Exception:
        pass
    if hasattr(form, "items"):
        try:
            for _key, val in form.items():
                v = _take_first_file(val)
                if v:
                    return v
        except Exception:
            pass
    return None


@router.post("/upload-image/")
async def upload_image(request: Request):
    """Загрузка изображения статьи. multipart/form-data, поле «file»."""
    auth_check = require_admin(request)
    if auth_check:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    try:
        form = await request.form()
    except Exception as e:
        return JSONResponse({"error": "Не удалось прочитать форму: %s" % str(e)}, status_code=422)
    file = _get_upload_file_from_form(form)
    if not file:
        ct = (request.headers.get("content-type") or "").split(";")[0].strip().lower()
        return JSONResponse({
            "error": "Файл не передан. Поле «file», запрос multipart/form-data (Content-Type: %s)." % (ct or "(пусто)")
        }, status_code=422)
    allowed_types = ["image/jpeg", "image/jpg", "image/png", "image/gif", "image/webp"]
    allowed_ext = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
    ext = Path(getattr(file, "filename", "") or "").suffix.lower()
    if getattr(file, "content_type", None) and file.content_type not in allowed_types and ext not in allowed_ext:
        return JSONResponse({"error": "Недопустимый формат файла"}, status_code=400)
    if ext not in allowed_ext:
        ext = ".jpg"
    unique_filename = f"{uuid.uuid4()}{ext}"
    file_path = UPLOAD_DIR / unique_filename
    try:
        content = await file.read()
        file_path.write_bytes(content)
    except Exception as e:
        return JSONResponse({"error": f"Ошибка сохранения: {str(e)}"}, status_code=500)
    image_url = f"/static/uploads/articles/{unique_filename}"
    return JSONResponse({"success": True, "url": image_url})


@router.post("/tinymce-upload/")
async def tinymce_upload_image(request: Request):
    """Загрузка изображения через TinyMCE (поля blobid0, imagetools0 или file)."""
    auth_check = require_admin(request)
    if auth_check:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)
    try:
        form = await request.form()
    except Exception as e:
        return JSONResponse({"error": "Не удалось прочитать форму"}, status_code=422)
    file = _get_upload_file_from_form(form)
    if not file:
        return JSONResponse({"error": "Файл не передан"}, status_code=422)
    allowed_types = ["image/jpeg", "image/jpg", "image/png", "image/gif", "image/webp"]
    allowed_ext = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
    ext = Path(getattr(file, "filename", "") or "").suffix.lower()
    if getattr(file, "content_type", None) and file.content_type not in allowed_types and ext not in allowed_ext:
        return JSONResponse({"error": "Недопустимый формат файла"}, status_code=400)
    if ext not in allowed_ext:
        ext = ".jpg"
    unique_filename = f"{uuid.uuid4()}{ext}"
    file_path = UPLOAD_DIR / unique_filename
    try:
        content = await file.read()
        file_path.write_bytes(content)
    except Exception as e:
        return JSONResponse({"error": f"Ошибка сохранения: {str(e)}"}, status_code=500)
    return JSONResponse({"location": f"/static/uploads/articles/{unique_filename}"})


@router.get("/{article_id}/", response_class=HTMLResponse)
async def article_edit(request: Request, article_id: str, db: Session = Depends(get_db)):
    """Форма редактирования статьи"""
    auth_check = require_admin(request)
    if auth_check:
        return auth_check

    try:
        aid = int(article_id)
    except ValueError:
        return RedirectResponse(url="/admin/articles/", status_code=303)
    article = db.query(Article).filter(Article.id == aid).options(joinedload(Article.category)).first()
    if not article:
        return RedirectResponse(url="/admin/articles/", status_code=303)

    categories = db.query(ArticleCategory).order_by(ArticleCategory.name).all()
    saved = bool(request.query_params.get("saved"))
    return templates.TemplateResponse(
        request=request,
        name="admin/articles/edit.html",
        context=get_admin_context(
            request=request,
            title=f"Редактировать: {(article.title or '')[:50]} — Админ-панель",
            active_menu="articles",
            article=article,
            categories=categories,
            is_new=False,
            saved=saved,
        )
    )


@router.post("/{article_id}/", response_class=HTMLResponse)
async def article_edit_post(
    request: Request,
    article_id: str,
    db: Session = Depends(get_db),
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
    """Сохранение статьи. При смене slug создаётся 301 редирект со старого URL на новый."""
    auth_check = require_admin(request)
    if auth_check:
        return auth_check

    try:
        aid = int(article_id)
    except ValueError:
        return RedirectResponse(url="/admin/articles/", status_code=303)
    article = db.query(Article).filter(Article.id == aid).first()
    if not article:
        return RedirectResponse(url="/admin/articles/", status_code=303)

    new_slug = (slug or generate_slug(title)).strip()
    old_slug = (article.slug or "").strip()
    article.title = title
    article.slug = new_slug
    article.excerpt = excerpt or None
    article.content = content or None
    article.category_id = _category_slug_to_id(db, category)
    article.image = image or None
    article.meta_title = meta_title or title
    article.meta_description = meta_description or ((excerpt or "")[:160] if excerpt else None)
    article.meta_keywords = meta_keywords or None
    article.is_published = is_published
    article.updated_at = datetime.utcnow()

    if old_slug and old_slug != new_slug:
        from_url = f"/news/{old_slug}/"
        to_url = f"/news/{new_slug}/"
        existing = db.query(Redirect).filter(
            Redirect.from_url == from_url,
            Redirect.is_active.is_(True),
        ).first()
        if not existing:
            db.add(Redirect(from_url=from_url, to_url=to_url, status_code=301))
    db.commit()
    return RedirectResponse(url=f"/admin/articles/{article_id}/?saved=1", status_code=303)


@router.post("/{article_id}/delete/")
async def article_delete(request: Request, article_id: str, db: Session = Depends(get_db)):
    """Удаление статьи"""
    auth_check = require_admin(request)
    if auth_check:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    try:
        aid = int(article_id)
    except ValueError:
        return RedirectResponse(url="/admin/articles/", status_code=303)
    article = db.query(Article).filter(Article.id == aid).first()
    if article:
        db.delete(article)
        db.commit()
    return RedirectResponse(url="/admin/articles/", status_code=303)


@router.post("/{article_id}/toggle-publish/")
async def article_toggle_publish(request: Request, article_id: str, db: Session = Depends(get_db)):
    """Переключение публикации"""
    auth_check = require_admin(request)
    if auth_check:
        return JSONResponse({"error": "Unauthorized"}, status_code=401)

    try:
        aid = int(article_id)
    except ValueError:
        return JSONResponse({"error": "Invalid id"}, status_code=400)
    article = db.query(Article).filter(Article.id == aid).first()
    if not article:
        return JSONResponse({"error": "Not found"}, status_code=404)
    article.is_published = not article.is_published
    article.updated_at = datetime.utcnow()
    db.commit()
    return JSONResponse({"success": True})
