#!/usr/bin/env python3
"""
Создание страницы /news/ в CMS: hero + секция «Список статей» + CTA.
Список статей (articles_list) подтягивает данные из data/articles.json при рендере.

Запуск: из корня backend: python3 scripts/seed_news_page.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal
from app.models import Page, PageSection, ContentBlock


def seed_news_page(db):
    """Страница /news/ — Статьи и новости."""
    page = db.query(Page).filter(Page.slug == "news").first()
    if not page:
        page = Page(
            slug="news",
            title="Статьи и новости",
            status="published",
            meta_title="Статьи и новости — Documatica",
            meta_description="Полезные статьи о налогах, бухгалтерии и документообороте для ИП и ООО.",
            meta_keywords="статьи для ИП, УСН, налоги, бухгалтерия, документооборот",
            canonical_url="/news/",
        )
        db.add(page)
        db.flush()
    else:
        for section in list(page.sections):
            db.delete(section)
        db.flush()

    # ——— 1. Hero ———
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
    db.add(ContentBlock(section_id=hero.id, block_type="label", position=0, content={"text": "База знаний // Knowledge Hub"}, css_classes="hero-tag docu-tag-muted", is_visible=True))
    db.add(ContentBlock(section_id=hero.id, block_type="heading", position=1, content={"text": "Статьи", "accent": "и новости", "level": 1}, css_classes="hero-title type-h1", is_visible=True))
    db.add(ContentBlock(section_id=hero.id, block_type="paragraph", position=2, content={"text": "Полезные материалы о налогах, УСН и документообороте для предпринимателей."}, css_classes="hero-subtitle", is_visible=True))
    db.add(ContentBlock(section_id=hero.id, block_type="link_group", position=3, content={"links": [{"text": "Все статьи", "url": "/news/"}]}, css_classes="", is_visible=True))

    # ——— 2. Список статей (данные подставляются при рендере из news.py) ———
    list_sec = PageSection(
        page_id=page.id,
        section_type="articles_list",
        position=1,
        background_style="white",
        container_width="default",
        is_visible=True,
    )
    db.add(list_sec)
    db.flush()

    # ——— 3. CTA ———
    cta_sec = PageSection(
        page_id=page.id,
        section_type="cta",
        position=2,
        background_style="gradient_blue",
        container_width="default",
        is_visible=True,
    )
    db.add(cta_sec)
    db.flush()
    db.add(ContentBlock(section_id=cta_sec.id, block_type="label", position=0, content={"text": "Начните сейчас", "badge_style": "primary"}, css_classes="cta-block-tag-v12", is_visible=True))
    db.add(ContentBlock(section_id=cta_sec.id, block_type="heading", position=1, content={"text": "Готовы автоматизировать?", "level": 2}, css_classes="cta-block-title-v12", is_visible=True))
    db.add(ContentBlock(section_id=cta_sec.id, block_type="paragraph", position=2, content={"text": "Создайте первый УПД за 2 минуты. Бесплатно."}, css_classes="cta-block-desc-v12", is_visible=True))
    db.add(ContentBlock(section_id=cta_sec.id, block_type="button", position=3, content={"text": "Создать документ", "url": "/dashboard/upd/create/"}, css_classes="cta-btn-v12", is_visible=True))

    print("  [news] Страница /news/ создана/обновлена: hero, articles_list, cta.")
    return page


def ensure_home_articles_preview(db):
    """Добавляет секцию «Последние статьи» на главную, если её ещё нет (конвертация блока в секцию)."""
    home = db.query(Page).filter(Page.slug == "").first()
    if not home:
        return
    has_preview = any(getattr(s, "section_type", None) == "articles_preview" for s in home.sections)
    if has_preview:
        print("  [home] Секция «Последние статьи» уже есть.")
        return
    from sqlalchemy import func
    max_pos = db.query(func.coalesce(func.max(PageSection.position), -1)).filter(PageSection.page_id == home.id).scalar() or -1
    new_pos = max_pos + 1
    sec = PageSection(
        page_id=home.id,
        section_type="articles_preview",
        position=new_pos,
        background_style="pattern_light",
        container_width="default",
        is_visible=True,
    )
    db.add(sec)
    print("  [home] Добавлена секция «Последние статьи» (articles_preview).")


def main():
    db = SessionLocal()
    try:
        print("Seed: страница Новости (CMS) + блок статей на главную...")
        seed_news_page(db)
        ensure_home_articles_preview(db)
        db.commit()
        print("Готово. /news/ из CMS; блок «Последние статьи» — секция в админке.")
    except Exception as e:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
