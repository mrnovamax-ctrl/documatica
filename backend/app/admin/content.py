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


# Кастомный Dumper для корректного экранирования строк
class SafeStringDumper(yaml.SafeDumper):
    pass

def str_representer(dumper, data):
    """Используем кавычки для строк со спецсимволами или длинных строк"""
    # Всегда используем кавычки для строк с проблемными символами
    needs_quotes = (
        ':' in data or          # Двоеточие - ключевой символ YAML
        '\n' in data or         # Перенос строки
        '#' in data or          # Комментарий
        '&' in data or          # Anchor
        '*' in data or          # Alias
        '!' in data or          # Tag
        '|' in data or          # Literal block
        '>' in data or          # Folded block
        "'" in data or          # Кавычка
        '"' in data or          # Двойная кавычка
        '[' in data or          # Начало списка
        ']' in data or          # Конец списка
        '{' in data or          # Начало словаря
        '}' in data or          # Конец словаря
        ',' in data or          # Запятая
        len(data) > 80 or       # Длинные строки (YAML может их разбить)
        data.startswith(' ') or # Пробел в начале
        data.endswith(' ')      # Пробел в конце
    )
    if needs_quotes:
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='"')
    return dumper.represent_scalar('tag:yaml.org,2002:str', data)

SafeStringDumper.add_representer(str, str_representer)


def safe_yaml_dump(data, stream=None, **kwargs):
    """Безопасный YAML dump с кавычками для строк с двоеточиями"""
    kwargs.setdefault('allow_unicode', True)
    kwargs.setdefault('default_flow_style', False)
    kwargs.setdefault('sort_keys', False)
    return yaml.dump(data, stream, Dumper=SafeStringDumper, **kwargs)

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
        safe_yaml_dump(data, f)
    
    # Очищаем кэш контента
    reload_content()
    
    return True


@router.get("/", response_class=HTMLResponse)
async def content_list(request: Request, q: str = ""):
    """Список страниц для редактирования"""
    auth_check = require_admin(request)
    if auth_check:
        return auth_check
    
    files = get_content_files()
    query = (q or "").strip().lower()
    if query:
        files = [
            f for f in files
            if query in f["path"].lower()
            or query in f["filename"].lower()
            or query in f["title"].lower()
            or query in f["public_url"].lower()
        ]
    
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
            search_query=query,
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
        content = {}
    # Гарантируем ключи, к которым обращается edit.html
    defaults = {
        "meta": {"title": "", "description": "", "keywords": "", "canonical": ""},
        "page": {"h1": "", "intro": "", "tag": ""},
        "features": [],
        "faq": [],
        "cta": {"title": "", "text": "", "url": "", "subtext": "", "description": ""},
        "related": [],
        "about": {"label": "", "title": "", "title_accent": "", "description": "", "mission": "", "stats": []},
    }
    for key, default_val in defaults.items():
        if key not in content:
            content[key] = default_val
        elif key == "about" and isinstance(content[key], dict) and "stats" not in content[key]:
            content[key].setdefault("stats", [])
    
    return templates.TemplateResponse(
        request=request,
        name="admin/content/edit.html",
        context=get_admin_context(
            request=request,
            title=f"Редактирование: {path} — Админ-панель",
            active_menu="content",
            content_path=path,
            content=content,
            content_yaml=safe_yaml_dump(content),
        )
    )


@router.post("/{path:path}/", response_class=HTMLResponse)
async def content_save(
    request: Request, 
    path: str,
):
    """Сохранение контента"""
    auth_check = require_admin(request)
    if auth_check:
        return auth_check
    
    error = None
    success = None
    form_data = await request.form()
    edit_mode = form_data.get("edit_mode", "visual")
    
    try:
        if edit_mode == "yaml":
            # YAML режим - парсим как раньше
            yaml_content = form_data.get("yaml_content", "")
            data = yaml.safe_load(yaml_content)
            if data is None:
                data = {}
        else:
            # Visual режим - мержим данные формы с существующими
            existing_data = load_content_file(path)
            form_parsed = parse_form_to_dict(form_data)
            data = merge_content_data(existing_data, form_parsed)
        
        # Сохраняем
        save_content_file(path, data)
        success = "Контент успешно сохранён"
        
    except yaml.YAMLError as e:
        error = f"Ошибка парсинга YAML: {e}"
    except Exception as e:
        error = f"Ошибка сохранения: {e}"
        import traceback
        traceback.print_exc()
    
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
            content_yaml=safe_yaml_dump(content) if content else "",
            error=error,
            success=success,
        )
    )


def merge_content_data(existing: Dict[str, Any], form_data: Dict[str, Any]) -> Dict[str, Any]:
    """Мержит данные из формы с существующими, сохраняя поля которых нет в форме"""
    result = existing.copy() if existing else {}
    
    for key, value in form_data.items():
        if isinstance(value, dict) and key in result and isinstance(result[key], dict):
            # Мержим словари (meta, page, cta)
            result[key].update(value)
        else:
            # Заменяем массивы и простые значения
            result[key] = value
    
    return result


def parse_form_to_dict(form_data) -> Dict[str, Any]:
    """Преобразование данных формы в словарь для YAML"""
    result = {}
    
    # Группируем поля по префиксам
    for key, value in form_data.multi_items():
        if key in ("edit_mode", "yaml_content"):
            continue
        
        # Парсим ключ вида "meta__title" или "features__0__title" или "about__stats__0__value" или "features__cards__0__title"
        parts = key.split("__")
        
        if len(parts) == 2:
            # Простое поле: meta__title -> result["meta"]["title"]
            section, field = parts
            if section not in result:
                result[section] = {}
            result[section][field] = value
            
        elif len(parts) == 3:
            # Массив: features__0__title -> result["features"][0]["title"]
            section, index_or_subsection, field = parts
            
            # Проверяем, это индекс или подсекция
            try:
                index = int(index_or_subsection)
                # Это массив
                if section not in result:
                    result[section] = []
                
                # Расширяем массив если нужно
                while len(result[section]) <= index:
                    result[section].append({})
                
                result[section][index][field] = value
            except ValueError:
                # Это подсекция (например hero__cta_text)
                # Но это не подходит под формат, пропускаем
                pass
            
        elif len(parts) == 4:
            # Вложенный массив: about__stats__0__value -> result["about"]["stats"][0]["value"]
            # ИЛИ features__cards__0__title -> result["features"]["cards"][0]["title"]
            section, subsection, index, field = parts
            
            try:
                index = int(index)
                
                if section not in result:
                    result[section] = {}
                if subsection not in result[section]:
                    result[section][subsection] = []
                
                # Расширяем массив если нужно
                while len(result[section][subsection]) <= index:
                    result[section][subsection].append({})
                
                result[section][subsection][index][field] = value
            except ValueError:
                # Индекс не число, пропускаем
                pass
    
    # Очищаем пустые элементы массивов
    for key in ["features", "benefits", "faq", "related", "sections"]:
        if key in result:
            # Проверяем, это массив объектов или объект с подмассивами
            if isinstance(result[key], list):
                result[key] = [item for item in result[key] if any(v.strip() for v in item.values() if v)]
            elif isinstance(result[key], dict) and "cards" in result[key]:
                # Очищаем cards внутри features/benefits
                result[key]["cards"] = [
                    item for item in result[key]["cards"] 
                    if any(v.strip() for v in item.values() if v)
                ]
    
    # Очищаем пустые элементы вложенных массивов (about.stats)
    if "about" in result and "stats" in result["about"]:
        result["about"]["stats"] = [
            item for item in result["about"]["stats"] 
            if any(v.strip() for v in item.values() if v)
        ]
    
    return result
