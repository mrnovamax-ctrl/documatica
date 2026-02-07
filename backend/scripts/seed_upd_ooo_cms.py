#!/usr/bin/env python3
"""
Создаёт или обновляет страницу /upd/ooo/ в CMS (конструктор).
Контент берётся из content/upd/ooo.yaml — блоки наполняются из YAML, не хардкод.
После запуска страница доступна в админке для редактирования и отображается по URL /upd/ooo/.

Запуск: из корня backend: python3 scripts/seed_upd_ooo_cms.py
"""

import sys
import yaml
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal
from app.models import Page, PageSection, ContentBlock


YAML_PATH = Path(__file__).parent.parent / "content" / "upd" / "ooo.yaml"


def load_ooo_yaml():
    with open(YAML_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def icon_from_mdi(mdi: str) -> str:
    """mdi:database-search -> search, mdi:printer -> download"""
    if not mdi:
        return "check-circle"
    if "database" in mdi or "search" in mdi:
        return "search"
    if "list" in mdi or "format" in mdi:
        return "document"
    if "printer" in mdi:
        return "download"
    return "check-circle"


def create_or_update_page(db, content: dict):
    meta = content.get("meta", {})
    page_data = content.get("page", {})
    features = content.get("features", [])
    faq = content.get("faq", [])
    cta = content.get("cta", {})
    related = content.get("related", [])

    page = db.query(Page).filter(Page.slug == "upd/ooo").first()
    if not page:
        page = Page(
            slug="upd/ooo",
            title=page_data.get("h1", "Генератор УПД для ООО"),
            meta_title=meta.get("title"),
            meta_description=meta.get("description"),
            meta_keywords=meta.get("keywords"),
            canonical_url=meta.get("canonical"),
            status="published",
        )
        db.add(page)
        db.flush()
    else:
        page.title = page_data.get("h1", page.title)
        page.meta_title = meta.get("title") or page.meta_title
        page.meta_description = meta.get("description") or page.meta_description
        page.meta_keywords = meta.get("keywords") or page.meta_keywords
        page.canonical_url = meta.get("canonical") or page.canonical_url
        page.status = "published"

    # Удаляем старые секции (блоки каскадно)
    for section in list(page.sections):
        db.delete(section)
    db.flush()

    # —— 1. Hero ——
    hero = PageSection(
        page_id=page.id,
        section_type="hero",
        position=0,
        background_style="pattern_radial_blue",
        container_width="default",
        is_visible=True,
        settings={"hero_variant": "default"},
    )
    db.add(hero)
    db.flush()

    tag = page_data.get("tag") or "Генератор документов"
    db.add(ContentBlock(section_id=hero.id, block_type="label", position=0, content={"text": tag}, css_classes="", is_visible=True))
    db.add(ContentBlock(section_id=hero.id, block_type="heading", position=1, content={"text": page_data.get("h1", "Генератор УПД для ООО"), "accent": ""}, css_classes="", is_visible=True))
    db.add(ContentBlock(section_id=hero.id, block_type="paragraph", position=2, content={"text": page_data.get("intro", "").replace("\r\n", " ").strip()}, css_classes="", is_visible=True))
    db.add(ContentBlock(section_id=hero.id, block_type="button", position=3, content={"text": cta.get("text", "Создать УПД для ООО"), "url": cta.get("url", "/dashboard/upd/create/?preset=ooo")}, css_classes="btn btn-primary btn-lg", is_visible=True))
    links = [{"text": r["title"], "url": r["url"]} for r in related]
    if not links:
        links = [{"text": "УПД для ИП", "url": "/upd/ip/"}, {"text": "УПД с НДС", "url": "/upd/s-nds/"}, {"text": "УПД без НДС", "url": "/upd/bez-nds/"}, {"text": "Образец заполнения УПД", "url": "/upd/obrazec/"}]
    db.add(ContentBlock(section_id=hero.id, block_type="link_group", position=4, content={"links": links}, css_classes="", is_visible=True))

    # —— 2. Features ——
    features_sec = PageSection(
        page_id=page.id,
        section_type="features",
        position=1,
        background_style="white",
        container_width="default",
        is_visible=True,
        grid_columns=3,
        grid_gap="medium",
        grid_style="grid",
    )
    db.add(features_sec)
    db.flush()

    db.add(ContentBlock(section_id=features_sec.id, block_type="heading", position=0, content={"text": "Преимущества", "accent": ""}, css_classes="", is_visible=True))
    for i, f in enumerate(features):
        icon = icon_from_mdi(f.get("icon"))
        db.add(ContentBlock(
            section_id=features_sec.id,
            block_type="feature_card",
            position=i + 1,
            content={"title": f.get("title", ""), "description": f.get("description", ""), "icon": icon},
            css_classes="",
            is_visible=True,
        ))

    # —— 3. FAQ ——
    faq_sec = PageSection(
        page_id=page.id,
        section_type="faq",
        position=2,
        background_style="surface_light",
        container_width="default",
        is_visible=True,
        settings={"accordion_variant": "basic"},
    )
    db.add(faq_sec)
    db.flush()

    db.add(ContentBlock(section_id=faq_sec.id, block_type="heading", position=0, content={"text": "Частые вопросы", "accent": ""}, css_classes="", is_visible=True))
    for i, item in enumerate(faq):
        db.add(ContentBlock(
            section_id=faq_sec.id,
            block_type="faq_item",
            position=i + 1,
            content={"question": item.get("question", ""), "answer": item.get("answer", ""), "button_text": None, "button_url": None, "badge_text": ""},
            css_classes="",
            is_visible=True,
        ))

    # —— 4. CTA ——
    cta_sec = PageSection(
        page_id=page.id,
        section_type="cta",
        position=3,
        background_style="gradient_blue",
        container_width="default",
        is_visible=True,
    )
    db.add(cta_sec)
    db.flush()

    db.add(ContentBlock(section_id=cta_sec.id, block_type="label", position=0, content={"text": "Начните сейчас", "badge_style": "primary"}, css_classes="", is_visible=True))
    db.add(ContentBlock(section_id=cta_sec.id, block_type="heading", position=1, content={"text": cta.get("title", "Готовы создать УПД?"), "accent": ""}, css_classes="", is_visible=True))
    db.add(ContentBlock(section_id=cta_sec.id, block_type="paragraph", position=2, content={"text": cta.get("description", "Зарегистрируйтесь бесплатно и создайте первый документ за 2 минуты")}, css_classes="", is_visible=True))
    db.add(ContentBlock(section_id=cta_sec.id, block_type="button", position=3, content={"text": cta.get("text", "Создать УПД для ООО"), "url": cta.get("url", "/dashboard/upd/create/?preset=ooo")}, css_classes="btn btn-primary btn-lg", is_visible=True))

    db.commit()
    return page


def main():
    content = load_ooo_yaml()
    if not content:
        print("Не удалось загрузить content/upd/ooo.yaml")
        sys.exit(1)

    db = SessionLocal()
    try:
        page = create_or_update_page(db, content)
        print(f"Страница /upd/ooo/ создана/обновлена (id={page.id}). Контент из ooo.yaml.")
        print("Редактирование: /admin/pages/ и выберите страницу «Генератор УПД для ООО» (slug: upd/ooo).")
    finally:
        db.close()


if __name__ == "__main__":
    main()
