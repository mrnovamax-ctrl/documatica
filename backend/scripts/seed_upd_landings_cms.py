#!/usr/bin/env python3
"""
Создаёт или обновляет лендинги УПД в CMS из YAML: ip, s-nds, bez-nds, samozanyatye.
Контент берётся из content/upd/{slug}.yaml. После запуска страницы отдаются по /upd/ip/, /upd/s-nds/ и т.д.

Запуск:
  python3 scripts/seed_upd_landings_cms.py                    # все 4 страницы
  python3 scripts/seed_upd_landings_cms.py ip samozanyatye   # только указанные
"""

import sys
import yaml
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal
from app.models import Page, PageSection, ContentBlock


CONTENT_DIR = Path(__file__).parent.parent / "content" / "upd"
DEFAULT_SLUGS = ["ip", "s-nds", "bez-nds", "samozanyatye"]


def load_yaml(slug: str) -> dict:
    path = CONTENT_DIR / f"{slug}.yaml"
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def icon_from_mdi(mdi: str) -> str:
    if not mdi:
        return "check-circle"
    m = (mdi or "").lower()
    if "database" in m or "search" in m or "account" in m:
        return "search"
    if "list" in m or "format" in m or "calculator" in m:
        return "document"
    if "printer" in m or "print" in m:
        return "download"
    if "percent" in m:
        return "document"
    if "file" in m or "edit" in m:
        return "document"
    if "handshake" in m:
        return "user"
    return "check-circle"


def create_or_update_page(db, slug: str, content: dict):
    page_slug = f"upd/{slug}"
    meta = content.get("meta", {})
    page_data = content.get("page", {})
    features = content.get("features", [])
    faq = content.get("faq", [])
    cta = content.get("cta", {})
    related = content.get("related", [])

    default_h1 = page_data.get("h1", "Генератор УПД")
    default_cta_url = f"/dashboard/upd/create/?preset={slug}"

    page = db.query(Page).filter(Page.slug == page_slug).first()
    if not page:
        page = Page(
            slug=page_slug,
            title=default_h1,
            meta_title=meta.get("title"),
            meta_description=meta.get("description"),
            meta_keywords=meta.get("keywords"),
            canonical_url=meta.get("canonical"),
            status="published",
        )
        db.add(page)
        db.flush()
    else:
        page.title = default_h1
        page.meta_title = meta.get("title") or page.meta_title
        page.meta_description = meta.get("description") or page.meta_description
        page.meta_keywords = meta.get("keywords") or page.meta_keywords
        page.canonical_url = meta.get("canonical") or page.canonical_url
        page.status = "published"

    for section in list(page.sections):
        db.delete(section)
    db.flush()

    # Hero
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
    intro = (page_data.get("intro") or "").replace("\r\n", " ").strip()
    db.add(ContentBlock(section_id=hero.id, block_type="label", position=0, content={"text": tag}, css_classes="", is_visible=True))
    db.add(ContentBlock(section_id=hero.id, block_type="heading", position=1, content={"text": default_h1, "accent": ""}, css_classes="", is_visible=True))
    db.add(ContentBlock(section_id=hero.id, block_type="paragraph", position=2, content={"text": intro}, css_classes="", is_visible=True))
    db.add(ContentBlock(section_id=hero.id, block_type="button", position=3, content={"text": cta.get("text", "Создать УПД"), "url": cta.get("url", default_cta_url)}, css_classes="btn btn-primary btn-lg", is_visible=True))
    links = [{"text": r["title"], "url": r["url"]} for r in related] if related else []
    if not links:
        links = [{"text": "УПД для ООО", "url": "/upd/ooo/"}, {"text": "УПД для ИП", "url": "/upd/ip/"}, {"text": "УПД с НДС", "url": "/upd/s-nds/"}, {"text": "УПД без НДС", "url": "/upd/bez-nds/"}, {"text": "Образец заполнения", "url": "/upd/obrazec/"}]
    db.add(ContentBlock(section_id=hero.id, block_type="link_group", position=4, content={"links": links}, css_classes="", is_visible=True))

    # Features
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

    # FAQ
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

    # CTA
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
    db.add(ContentBlock(section_id=cta_sec.id, block_type="heading", position=1, content={"text": cta.get("title", "Готовы создать документ?"), "accent": ""}, css_classes="", is_visible=True))
    db.add(ContentBlock(section_id=cta_sec.id, block_type="paragraph", position=2, content={"text": cta.get("description", "Зарегистрируйтесь бесплатно и создайте первый документ за 2 минуты")}, css_classes="", is_visible=True))
    db.add(ContentBlock(section_id=cta_sec.id, block_type="button", position=3, content={"text": cta.get("text", "Создать УПД"), "url": cta.get("url", default_cta_url)}, css_classes="btn btn-primary btn-lg", is_visible=True))

    return page


def main():
    slugs = sys.argv[1:] if len(sys.argv) > 1 else DEFAULT_SLUGS
    db = SessionLocal()
    try:
        for slug in slugs:
            content = load_yaml(slug)
            if not content:
                print(f"Пропуск {slug}: не найден content/upd/{slug}.yaml")
                continue
            page = create_or_update_page(db, slug, content)
            db.commit()
            print(f"  /upd/{slug}/ — id={page.id}")
        print("Готово. Редактирование: /admin/pages/")
    finally:
        db.close()


if __name__ == "__main__":
    main()
