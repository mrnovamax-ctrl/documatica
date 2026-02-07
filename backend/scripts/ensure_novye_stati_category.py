#!/usr/bin/env python3
"""
Создаёт категорию «Новые статьи» в БД, если её ещё нет.
После запуска в админке в выпадающем списке категорий при создании/редактировании статьи
появится выбор «Новые статьи» (slug: novye-stati).

Запуск из корня backend: python3 scripts/ensure_novye_stati_category.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal
from app.models import ArticleCategory

SLUG = "novye-stati"
NAME = "Новые статьи"


def main():
    db = SessionLocal()
    try:
        cat = db.query(ArticleCategory).filter(ArticleCategory.slug == SLUG).first()
        if cat:
            print(f"Категория уже есть: id={cat.id}, slug={cat.slug}, name={cat.name}")
            return
        cat = ArticleCategory(
            parent_id=None,
            slug=SLUG,
            full_slug=SLUG,
            name=NAME,
            layout="no_sidebar",
        )
        db.add(cat)
        db.commit()
        print(f"Создана категория: id={cat.id}, slug={cat.slug}, name={cat.name}")
    except Exception as e:
        db.rollback()
        print(f"Ошибка: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
