"""
Admin Content - редактор YAML-контента
"""

import os
import yaml
from pathlib import Path
from typing import List, Dict, Any
from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse

from app.core.templates import templates
from app.core.content import reload_content
from app.admin.context import require_admin, get_admin_context

router = APIRouter()

# Путь к контенту
CONTENT_DIR = Path(__file__).parent.parent.parent / "content"


def get_content_files() -> List[Dict[str, Any]]:
    """Получение списка всех YAML-файлов контента"""
    files = []
    
    if not CONTENT_DIR.exists():
        return files
    
    for yaml_file in sorted(CONTENT_DIR.rglob("*.yaml")):
        rel_path = yaml_file.relative_to(CONTENT_DIR)
        path_str = str(rel_path).replace("\\", "/").replace(".yaml", "")
        
        # Читаем title из файла
        title = path_str
        try:
            with open(yaml_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
                meta_title = data.get("meta", {}).get("title", "")
                if meta_title:
                    title = meta_title
        except Exception:
            pass
        
        # Специальная обработка для главной страницы и index файлов
        if path_str == "home":
            public_url = "/"
        elif path_str.endswith("/index"):
            # upd/index -> /upd/
            public_url = f"/{path_str.replace('/index', '')}/"
        else:
            public_url = f"/{path_str}/"
        
        files.append({
            "path": path_str,
            "filename": yaml_file.name,
            "title": title,
            "url": f"/admin/content/{path_str}/",
            "public_url": public_url,
        })
    
    # Также проверяем .yml файлы
    for yaml_file in sorted(CONTENT_DIR.rglob("*.yml")):
        rel_path = yaml_file.relative_to(CONTENT_DIR)
        path_str = str(rel_path).replace("\\", "/").replace(".yml", "")
        
        title = path_str
        try:
            with open(yaml_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
                meta_title = data.get("meta", {}).get("title", "")
                if meta_title:
                    title = meta_title
        except Exception:
            pass
        
        # Специальная обработка для главной страницы и index файлов
        if path_str == "home":
            public_url = "/"
        elif path_str.endswith("/index"):
            public_url = f"/{path_str.replace('/index', '')}/"
        else:
            public_url = f"/{path_str}/"
        
        files.append({
            "path": path_str,
            "filename": yaml_file.name,
            "title": title,
            "url": f"/admin/content/{path_str}/",
            "public_url": public_url,
        })

    return files


def load_content_file(path: str) -> Dict[str, Any]:
    """Загрузка YAML-файла контента"""
    yaml_path = CONTENT_DIR / f"{path}.yaml"
    if not yaml_path.exists():
        yaml_path = CONTENT_DIR / f"{path}.yml"
    
    if not yaml_path.exists():
        return {}
    
    with open(yaml_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def save_content_file(path: str, data: Dict[str, Any]) -> bool:
    """Сохранение YAML-файла контента"""
    yaml_path = CONTENT_DIR / f"{path}.yaml"
    if not yaml_path.exists():
        yaml_path = CONTENT_DIR / f"{path}.yml"
    
    if not yaml_path.exists():
        # Создаём новый файл
        yaml_path = CONTENT_DIR / f"{path}.yaml"
        yaml_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(yaml_path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
    
    # Очищаем кэш контента
    reload_content()
    
    return True


@router.get("/", response_class=HTMLResponse)
async def content_list(request: Request):
    """Список страниц для редактирования"""
    auth_check = require_admin(request)
    if auth_check:
        return auth_check
    
    files = get_content_files()
    
    # Группируем по категориям
    categories = {}
    for f in files:
        parts = f["path"].split("/")
        if len(parts) > 1:
            category = parts[0]  # upd, schet и т.д.
        elif f["path"] == "home":
            category = "pages"  # Общие страницы
        else:
            category = "other"
        if category not in categories:
            categories[category] = []
        categories[category].append(f)
    
    # Сортируем категории: pages первой, потом остальные
    sorted_categories = {}
    if "pages" in categories:
        sorted_categories["pages"] = categories.pop("pages")
    for cat in sorted(categories.keys()):
        sorted_categories[cat] = categories[cat]
    
    return templates.TemplateResponse(
        request=request,
        name="admin/content/list.html",
        context=get_admin_context(
            request=request,
            title="Редактор контента — Админ-панель",
            active_menu="content",
            files=files,
            categories=sorted_categories,
        )
    )


@router.get("/{path:path}/", response_class=HTMLResponse)
async def content_edit(request: Request, path: str):
    """Страница редактирования контента"""
    auth_check = require_admin(request)
    if auth_check:
        return auth_check
    
    content = load_content_file(path)
    
    if not content:
        # Создаём структуру по умолчанию
        content = {
            "meta": {"title": "", "description": "", "keywords": ""},
            "page": {"h1": "", "intro": ""},
            "features": [],
            "faq": [],
            "cta": {"title": "", "text": "", "url": ""},
            "related": [],
        }
    
    return templates.TemplateResponse(
        request=request,
        name="admin/content/edit.html",
        context=get_admin_context(
            request=request,
            title=f"Редактирование: {path} — Админ-панель",
            active_menu="content",
            content_path=path,
            content=content,
            content_yaml=yaml.dump(content, allow_unicode=True, default_flow_style=False, sort_keys=False),
        )
    )


@router.post("/{path:path}/", response_class=HTMLResponse)
async def content_save(
    request: Request, 
    path: str,
    yaml_content: str = Form(...)
):
    """Сохранение контента"""
    auth_check = require_admin(request)
    if auth_check:
        return auth_check
    
    error = None
    success = None
    
    try:
        # Парсим YAML
        data = yaml.safe_load(yaml_content)
        if data is None:
            data = {}
        
        # Сохраняем
        save_content_file(path, data)
        success = "Контент успешно сохранён"
        
    except yaml.YAMLError as e:
        error = f"Ошибка парсинга YAML: {e}"
    except Exception as e:
        error = f"Ошибка сохранения: {e}"
    
    content = load_content_file(path) if success else {}
    
    return templates.TemplateResponse(
        request=request,
        name="admin/content/edit.html",
        context=get_admin_context(
            request=request,
            title=f"Редактирование: {path} — Админ-панель",
            active_menu="content",
            content_path=path,
            content=content,
            content_yaml=yaml_content,
            error=error,
            success=success,
        )
    )
