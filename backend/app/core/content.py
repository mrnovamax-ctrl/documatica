"""
Content Loader - загрузка YAML-контента для страниц
"""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from functools import lru_cache

# Путь к контенту
CONTENT_DIR = Path(__file__).parent.parent.parent / "content"


class ContentNotFoundError(Exception):
    """Контент не найден"""
    pass


@lru_cache(maxsize=256)
def load_content(path: str) -> Dict[str, Any]:
    """
    Загрузка YAML-контента по пути
    
    Args:
        path: Путь к файлу без расширения (например, "upd/ooo")
        
    Returns:
        Словарь с контентом
        
    Raises:
        ContentNotFoundError: Если файл не найден
    """
    file_path = CONTENT_DIR / f"{path}.yaml"
    
    if not file_path.exists():
        # Пробуем .yml
        file_path = CONTENT_DIR / f"{path}.yml"
        
    if not file_path.exists():
        # Возвращаем пустой контент с дефолтными значениями
        return get_default_content(path)
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = yaml.safe_load(f) or {}
            return content
    except yaml.YAMLError as e:
        raise ContentNotFoundError(f"Error parsing {file_path}: {e}")


def get_default_content(path: str) -> Dict[str, Any]:
    """
    Дефолтный контент, если файл не найден
    Полезно при разработке - страница рендерится даже без YAML
    """
    parts = path.split("/")
    
    return {
        "meta": {
            "title": f"{parts[-1].upper()} — Documatica",
            "description": "Генератор документов для бизнеса",
        },
        "page": {
            "h1": f"Страница {parts[-1]}",
            "intro": "Контент в разработке...",
        },
        "features": [],
        "faq": [],
        "cta": {
            "text": "Создать документ",
            "url": "/dashboard/",
        },
        "related": [],
        "_default": True,  # Маркер что это дефолтный контент
    }


def reload_content():
    """Очистка кэша контента (для hot-reload в dev)"""
    load_content.cache_clear()


def get_all_content_paths() -> list:
    """Получить список всех YAML-файлов контента"""
    paths = []
    for file_path in CONTENT_DIR.rglob("*.yaml"):
        relative = file_path.relative_to(CONTENT_DIR)
        path = str(relative.with_suffix(""))
        paths.append(path)
    for file_path in CONTENT_DIR.rglob("*.yml"):
        relative = file_path.relative_to(CONTENT_DIR)
        path = str(relative.with_suffix(""))
        if path not in paths:
            paths.append(path)
    return sorted(paths)
