#!/usr/bin/env python3
"""
Замена контента страницы «Контакты» (slug=contact) на блочную структуру:
Hero, Форма (form_section с contact_form), Контактная информация (Features).
Запуск из корня backend: python scripts/replace_contact_page_content.py
"""

import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal
from app.models import Page, PageSection, ContentBlock


def _add_contact_sections_and_blocks(page, db):
    """Добавляет секции и блоки к странице contact (после удаления старых)."""
    # Секция 1: Hero
    hero = PageSection(
        page_id=page.id,
        section_type="hero",
        position=0,
        background_style="pattern_radial_blue",
        container_width="default",
        is_visible=True,
    )
    db.add(hero)
    db.flush()

    db.add(ContentBlock(section_id=hero.id, block_type="label", position=0, content={"text": "Контакты", "badge_style": "primary"}, css_classes="docu-tag", is_visible=True))
    db.add(ContentBlock(section_id=hero.id, block_type="heading", position=1, content={"text": "Свяжитесь с нами", "level": 1, "accent": "нами"}, css_classes="hero-title", is_visible=True))
    db.add(ContentBlock(section_id=hero.id, block_type="paragraph", position=2, content={"text": "Мы всегда рады помочь вам с любыми вопросами о Documatica"}, css_classes="hero-subtitle", is_visible=True))

    # Секция 2: Form (form_section)
    form_sec = PageSection(
        page_id=page.id,
        section_type="form_section",
        position=1,
        background_style="surface_light",
        container_width="default",
        is_visible=True,
    )
    db.add(form_sec)
    db.flush()

    db.add(ContentBlock(section_id=form_sec.id, block_type="heading", position=0, content={"text": "Напишите нам", "level": 2}, css_classes="form-section-title-v12", is_visible=True))
    db.add(ContentBlock(section_id=form_sec.id, block_type="paragraph", position=1, content={"text": "Заполните форму, и мы ответим вам в течение 24 часов"}, css_classes="form-section-desc-v12", is_visible=True))
    db.add(ContentBlock(section_id=form_sec.id, block_type="contact_form", position=2, content={}, css_classes="contact-form-v12", is_visible=True))

    # Секция 3: Контактная информация (Features)
    features_sec = PageSection(
        page_id=page.id,
        section_type="features",
        position=2,
        background_style="white",
        container_width="default",
        is_visible=True,
        grid_columns=2,
        grid_gap="medium",
        grid_style="grid",
    )
    db.add(features_sec)
    db.flush()

    db.add(ContentBlock(section_id=features_sec.id, block_type="heading", position=0, content={"text": "Контактная информация", "level": 2}, css_classes="section-title", is_visible=True))
    db.add(ContentBlock(section_id=features_sec.id, block_type="paragraph", position=1, content={"text": "Выберите удобный способ связи"}, css_classes="section-subtitle", is_visible=True))
    db.add(ContentBlock(section_id=features_sec.id, block_type="feature_card", position=2, content={"title": "Email", "description": "hello@oplatanalogov.ru. Ответим в течение 24 часов", "icon": "check-circle"}, css_classes="feature-card", is_visible=True))
    db.add(ContentBlock(section_id=features_sec.id, block_type="feature_card", position=3, content={"title": "Telegram", "description": "@mrnovamax — техподдержка онлайн", "icon": "check-circle"}, css_classes="feature-card", is_visible=True))
    db.add(ContentBlock(section_id=features_sec.id, block_type="feature_card", position=4, content={"title": "Режим работы", "description": "Пн-Пт: 9:00 - 18:00 (МСК). Суббота и воскресенье — выходные", "icon": "history"}, css_classes="feature-card", is_visible=True))
    db.add(ContentBlock(section_id=features_sec.id, block_type="feature_card", position=5, content={"title": "Справочный центр", "description": "Часто задаваемые вопросы — найдите ответ на ваш вопрос", "icon": "code"}, css_classes="feature-card", is_visible=True))


def replace_contact_page_content(db):
    page = db.query(Page).filter(Page.slug == "contact").first()
    if not page:
        print("Страница со slug=contact не найдена. Создайте её или запустите create_contact_page.py")
        return None

    # Удаляем все секции (блоки удалятся каскадно)
    for section in list(page.sections):
        db.delete(section)
    db.flush()

    # Добавляем новую структуру
    _add_contact_sections_and_blocks(page, db)

    # Обновляем meta страницы на случай если их не было
    page.meta_title = page.meta_title or "Контакты — Documatica"
    page.meta_description = page.meta_description or "Свяжитесь с нами для получения помощи по работе с документами"
    page.updated_at = datetime.utcnow()

    db.commit()
    print("Контент страницы «Контакты» (ID: {}) заменён: hero, form_section, features.".format(page.id))
    return page


def main():
    db = SessionLocal()
    try:
        replace_contact_page_content(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()
