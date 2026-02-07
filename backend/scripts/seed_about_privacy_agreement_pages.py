#!/usr/bin/env python3
"""
Создание страниц О нас, Политика конфиденциальности, Согласие на обработку ПД в CMS.
После запуска /about, /privacy, /agreement отдаются из БД (редактируемы в админке).
Если страница уже есть — обновляется title/meta, секции не трогаем.

Запуск из корня backend: python3 scripts/seed_about_privacy_agreement_pages.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal
from app.models import Page, PageSection, ContentBlock

PAGES = [
    {
        "slug": "about",
        "title": "О сервисе",
        "meta_title": "О сервисе Documatica — Генератор документов для бизнеса",
        "meta_description": "Documatica — современный онлайн-сервис для автоматической генерации бухгалтерских документов. УПД, счета, акты, договоры.",
        "meta_keywords": "Documatica, о сервисе, генератор документов, УПД, счета, акты",
        "canonical_url": "/about/",
        "intro": "Современный онлайн-сервис для автоматической генерации бухгалтерских документов.",
    },
    {
        "slug": "privacy",
        "title": "Политика конфиденциальности",
        "meta_title": "Политика конфиденциальности — Documatica",
        "meta_description": "Политика конфиденциальности сервиса Documatica. Обработка персональных данных.",
        "meta_keywords": "политика конфиденциальности, Documatica, персональные данные",
        "canonical_url": "/privacy/",
        "intro": "Настоящая политика конфиденциальности определяет порядок обработки персональных данных пользователей сервиса Documatica.",
    },
    {
        "slug": "agreement",
        "title": "Согласие на обработку персональных данных",
        "meta_title": "Согласие на обработку персональных данных — Documatica",
        "meta_description": "Согласие на обработку персональных данных при использовании сервиса Documatica.",
        "meta_keywords": "согласие на обработку ПД, персональные данные, Documatica",
        "canonical_url": "/agreement/",
        "intro": "Настоящее согласие даётся на обработку моих персональных данных в соответствии с политикой конфиденциальности сервиса Documatica.",
    },
]


def ensure_page(db, data):
    """Создаёт страницу и одну секцию seo_text с абзацем, если страницы ещё нет."""
    page = db.query(Page).filter(Page.slug == data["slug"]).first()
    if page:
        page.title = data["title"]
        page.meta_title = data["meta_title"]
        page.meta_description = data["meta_description"]
        page.meta_keywords = data.get("meta_keywords", "")
        page.canonical_url = data.get("canonical_url", "")
        page.status = "published"
        print(f"Обновлена страница: {data['slug']}")
        return page
    page = Page(
        slug=data["slug"],
        title=data["title"],
        status="published",
        meta_title=data["meta_title"],
        meta_description=data["meta_description"],
        meta_keywords=data.get("meta_keywords", ""),
        canonical_url=data.get("canonical_url", ""),
    )
    db.add(page)
    db.flush()
    # Одна секция seo_text с одним параграфом — контент можно дописать в админке
    section = PageSection(
        page_id=page.id,
        section_type="seo_text",
        position=0,
        background_style="light",
        container_width="default",
        is_visible=True,
    )
    db.add(section)
    db.flush()
    db.add(ContentBlock(
        section_id=section.id,
        block_type="paragraph",
        position=0,
        content={"text": data["intro"]},
        is_visible=True,
    ))
    print(f"Создана страница: {data['slug']} (id={page.id})")
    return page


def main():
    db = SessionLocal()
    try:
        for data in PAGES:
            ensure_page(db, data)
        db.commit()
        print("Готово. Страницы /about, /privacy, /agreement отдаются из CMS.")
    except Exception as e:
        db.rollback()
        print(f"Ошибка: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
