#!/usr/bin/env python3
"""
Перенос статей из data/articles.json в таблицу articles в БД (однократная миграция).
Категории должны уже существовать в article_categories.
Файл articles.json после миграции удалён; для повторного запуска нужна копия.

Запуск из корня backend: python3 scripts/migrate_articles_json_to_db.py
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal
from app.models import Article, ArticleCategory

DATA_DIR = Path(__file__).parent.parent / "data"
ARTICLES_FILE = DATA_DIR / "articles.json"


def parse_dt(s: Optional[str]):
    if not s:
        return None
    s = s.strip().replace("Z", "+00:00")
    for fmt in ("%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(s[:26] if "." in s else s[:19], fmt)
        except ValueError:
            continue
    return None


def main():
    if not ARTICLES_FILE.exists():
        print(f"Файл не найден: {ARTICLES_FILE}")
        sys.exit(1)

    with open(ARTICLES_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, list):
        articles_data = data
    else:
        articles_data = data.get("articles", [])

    db = SessionLocal()
    try:
        existing_slugs = {r.slug for r in db.query(Article.slug).all()}
        created = 0
        skipped = 0
        for a in articles_data:
            slug = (a.get("slug") or "").strip()
            if not slug:
                skipped += 1
                continue
            if slug in existing_slugs:
                skipped += 1
                continue
            category_slug = (a.get("category") or "").strip()
            category_id = None
            if category_slug:
                cat = (
                    db.query(ArticleCategory)
                    .filter(
                        (ArticleCategory.full_slug == category_slug) | (ArticleCategory.slug == category_slug)
                    )
                    .first()
                )
                if cat:
                    category_id = cat.id

            created_at = parse_dt(a.get("created_at"))
            updated_at = parse_dt(a.get("updated_at")) or created_at
            excerpt = (a.get("excerpt") or "").strip() or None
            meta_desc = (a.get("meta_description") or "").strip()
            if not meta_desc and excerpt:
                meta_desc = excerpt[:160]

            article = Article(
                category_id=category_id,
                slug=slug,
                title=(a.get("title") or "").strip() or "Без названия",
                excerpt=excerpt,
                content=(a.get("content") or "").strip() or None,
                image=(a.get("image") or "").strip() or None,
                meta_title=(a.get("meta_title") or "").strip() or (a.get("title") or "").strip(),
                meta_description=meta_desc or None,
                meta_keywords=(a.get("meta_keywords") or "").strip() or None,
                is_published=bool(a.get("is_published", False)),
                views=int(a.get("views") or 0),
                created_at=created_at,
                updated_at=updated_at,
            )
            db.add(article)
            db.flush()
            existing_slugs.add(slug)
            created += 1
        db.commit()
        print(f"Создано статей: {created}, пропущено (дубли/пустые): {skipped}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
