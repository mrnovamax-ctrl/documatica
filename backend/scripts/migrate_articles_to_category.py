#!/usr/bin/env python3
"""
Миграция статей в новую структуру категорий.
Создаёт категорию «Старые статьи» в БД и проставляет её всем статьям в articles.json.

Запуск из корня backend: python3 scripts/migrate_articles_to_category.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal
from app.models import ArticleCategory

DATA_DIR = Path(__file__).parent.parent / "data"
ARTICLES_FILE = DATA_DIR / "articles.json"

CATEGORY_SLUG = "starye-stati"
CATEGORY_NAME = "Старые статьи"


def ensure_category(db):
    """Создаёт категорию «Старые статьи» в БД, если её ещё нет."""
    cat = db.query(ArticleCategory).filter(ArticleCategory.full_slug == CATEGORY_SLUG).first()
    if cat:
        print(f"Категория уже есть: id={cat.id}, full_slug={cat.full_slug}")
        return cat
    cat = ArticleCategory(
        parent_id=None,
        slug=CATEGORY_SLUG,
        full_slug=CATEGORY_SLUG,
        name=CATEGORY_NAME,
        layout="no_sidebar",
    )
    db.add(cat)
    db.flush()
    print(f"Создана категория: id={cat.id}, full_slug={cat.full_slug}, name={cat.name}")
    return cat


def migrate_articles_json():
    """Читает articles.json, проставляет всем статьям category=CATEGORY_SLUG, сохраняет."""
    if not ARTICLES_FILE.exists():
        print(f"Файл не найден: {ARTICLES_FILE}")
        return 0
    with open(ARTICLES_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    articles = data.get("articles", [])
    if isinstance(data, list):
        articles = data
        data = {"articles": articles, "categories": []}
    updated = 0
    for art in articles:
        if art.get("category") != CATEGORY_SLUG:
            art["category"] = CATEGORY_SLUG
            updated += 1
    with open(ARTICLES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"В articles.json обновлено статей: {updated} (всего статей: {len(articles)})")
    return updated


def main():
    db = SessionLocal()
    try:
        ensure_category(db)
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Ошибка БД: {e}")
        raise
    finally:
        db.close()
    migrate_articles_json()
    print("Готово.")


if __name__ == "__main__":
    main()
