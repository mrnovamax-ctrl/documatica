#!/usr/bin/env python3
"""
Перенос контента из YAML (privacy, agreement) и из статичного about в страницы CMS.
Создаёт/обновляет Page с slug about, privacy, agreement; заполняет секции и блоки.
После запуска about.py и legal.py должны отдавать страницы из БД (верните проверку CMS в коде).

Запуск: python3 scripts/migrate_legal_about_to_cms.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import markdown
from app.database import SessionLocal
from app.models import Page, PageSection, ContentBlock
from app.core.content import load_content

CONTENT_DIR = Path(__file__).parent.parent / "content"


def markdown_to_html(text: str) -> str:
    if not text or not text.strip():
        return ""
    return markdown.markdown(text.strip(), extensions=["extra", "nl2br"])


def clear_page_sections(db, page):
    for s in list(page.sections):
        db.delete(s)
    db.flush()


def migrate_privacy(db):
    content = load_content("privacy")
    page = db.query(Page).filter(Page.slug == "privacy").first()
    if not page:
        page = Page(
            slug="privacy",
            title=content.get("page", {}).get("title", "Политика конфиденциальности"),
            status="published",
            meta_title=content.get("meta", {}).get("title", "Политика конфиденциальности — Documatica"),
            meta_description=content.get("meta", {}).get("description", ""),
            meta_keywords=content.get("meta", {}).get("keywords", ""),
            canonical_url="/privacy/",
        )
        db.add(page)
        db.flush()
    else:
        page.title = content.get("page", {}).get("title", page.title)
        page.meta_title = content.get("meta", {}).get("title", page.meta_title)
        page.meta_description = content.get("meta", {}).get("description", page.meta_description or "")
        page.meta_keywords = content.get("meta", {}).get("keywords", page.meta_keywords or "")
        page.status = "published"
        clear_page_sections(db, page)

    # Hero: заголовок и дата обновления
    hero = PageSection(
        page_id=page.id,
        section_type="hero",
        position=0,
        background_style="light",
        container_width="default",
        is_visible=True,
    )
    db.add(hero)
    db.flush()
    db.add(ContentBlock(section_id=hero.id, block_type="label", position=0, content={"text": "Юридическая информация"}, css_classes="hero-tag docu-tag-muted", is_visible=True))
    db.add(ContentBlock(section_id=hero.id, block_type="heading", position=1, content={"text": content.get("page", {}).get("title", "Политика конфиденциальности"), "level": 1}, is_visible=True))
    updated = content.get("page", {}).get("updated", "")
    if updated:
        db.add(ContentBlock(section_id=hero.id, block_type="paragraph", position=2, content={"text": f"Последнее обновление: {updated}"}, css_classes="text-muted", is_visible=True))

    # SEO-текст: контент из YAML (markdown -> HTML)
    raw_content = content.get("content", "") or ""
    html_content = markdown_to_html(raw_content)
    seo_sec = PageSection(
        page_id=page.id,
        section_type="seo_text",
        position=1,
        background_style="white",
        container_width="default",
        is_visible=True,
    )
    db.add(seo_sec)
    db.flush()
    db.add(ContentBlock(section_id=seo_sec.id, block_type="paragraph", position=0, content={"text": html_content}, is_visible=True))
    print("privacy: OK")


def migrate_agreement(db):
    content = load_content("agreement")
    page = db.query(Page).filter(Page.slug == "agreement").first()
    if not page:
        page = Page(
            slug="agreement",
            title=content.get("page", {}).get("title", "Согласие на обработку персональных данных"),
            status="published",
            meta_title=content.get("meta", {}).get("title", "Согласие на обработку ПД — Documatica"),
            meta_description=content.get("meta", {}).get("description", ""),
            meta_keywords=content.get("meta", {}).get("keywords", ""),
            canonical_url="/agreement/",
        )
        db.add(page)
        db.flush()
    else:
        page.title = content.get("page", {}).get("title", page.title)
        page.meta_title = content.get("meta", {}).get("title", page.meta_title)
        page.meta_description = content.get("meta", {}).get("description", page.meta_description or "")
        page.meta_keywords = content.get("meta", {}).get("keywords", page.meta_keywords or "")
        page.status = "published"
        clear_page_sections(db, page)

    hero = PageSection(
        page_id=page.id,
        section_type="hero",
        position=0,
        background_style="light",
        container_width="default",
        is_visible=True,
    )
    db.add(hero)
    db.flush()
    db.add(ContentBlock(section_id=hero.id, block_type="label", position=0, content={"text": "Юридическая информация"}, css_classes="hero-tag docu-tag-muted", is_visible=True))
    db.add(ContentBlock(section_id=hero.id, block_type="heading", position=1, content={"text": content.get("page", {}).get("title", "Согласие на обработку ПД"), "level": 1}, is_visible=True))
    updated = content.get("page", {}).get("updated", "")
    if updated:
        db.add(ContentBlock(section_id=hero.id, block_type="paragraph", position=2, content={"text": f"Последнее обновление: {updated}"}, css_classes="text-muted", is_visible=True))

    raw_content = content.get("content", "") or ""
    html_content = markdown_to_html(raw_content)
    seo_sec = PageSection(
        page_id=page.id,
        section_type="seo_text",
        position=1,
        background_style="white",
        container_width="default",
        is_visible=True,
    )
    db.add(seo_sec)
    db.flush()
    db.add(ContentBlock(section_id=seo_sec.id, block_type="paragraph", position=0, content={"text": html_content}, is_visible=True))
    print("agreement: OK")


def migrate_about(db):
    """О нас: hero + один блок seo_text с основным текстом (миссия + кратко возможности)."""
    page = db.query(Page).filter(Page.slug == "about").first()
    if not page:
        page = Page(
            slug="about",
            title="О сервисе",
            status="published",
            meta_title="О сервисе Documatica — Генератор документов для бизнеса",
            meta_description="Documatica — современный онлайн-сервис для автоматической генерации бухгалтерских документов. УПД, счета, акты, договоры.",
            meta_keywords="Documatica, о сервисе, генератор документов, УПД, счета, акты",
            canonical_url="/about/",
        )
        db.add(page)
        db.flush()
    else:
        page.title = "О сервисе"
        page.meta_title = "О сервисе Documatica — Генератор документов для бизнеса"
        page.meta_description = "Documatica — современный онлайн-сервис для автоматической генерации бухгалтерских документов. УПД, счета, акты, договоры."
        page.status = "published"
        clear_page_sections(db, page)

    # Hero
    hero = PageSection(
        page_id=page.id,
        section_type="hero",
        position=0,
        background_style="light",
        container_width="default",
        is_visible=True,
    )
    db.add(hero)
    db.flush()
    db.add(ContentBlock(section_id=hero.id, block_type="label", position=0, content={"text": "О сервисе"}, css_classes="hero-tag docu-tag-muted", is_visible=True))
    db.add(ContentBlock(section_id=hero.id, block_type="heading", position=1, content={"text": "Documatica", "level": 1}, is_visible=True))
    db.add(ContentBlock(section_id=hero.id, block_type="paragraph", position=2, content={"text": "Современный онлайн-сервис для автоматической генерации бухгалтерских документов"}, css_classes="hero-subtitle", is_visible=True))

    # Миссия + возможности одним SEO-блоком (HTML)
    about_html = """
<p><strong>Наша миссия</strong></p>
<p>Мы создали Documatica, чтобы избавить предпринимателей и бухгалтеров от рутинной работы с документами. Наша цель — автоматизировать создание бухгалтерских документов, сделать этот процесс быстрым, удобным и доступным для всех.</p>

<p><strong>Что мы предлагаем</strong></p>
<ul>
<li><strong>УПД</strong> — универсальный передаточный документ с НДС и без. Полностью соответствует требованиям ФНС.</li>
<li><strong>Счета</strong> — создание счетов на оплату за секунды. Профессиональный дизайн и все необходимые реквизиты.</li>
<li><strong>Акты</strong> — акты выполненных работ и оказанных услуг. Автоматическое заполнение на основе счёта.</li>
<li><strong>Договоры</strong> — шаблоны типовых договоров с возможностью кастомизации под ваши нужды.</li>
<li><strong>Автозаполнение</strong> — поиск реквизитов компании по ИНН. Интеграция с базой данных ФНС через DaData.</li>
<li><strong>AI-помощник</strong> — искусственный интеллект помогает заполнять документы и исправлять ошибки.</li>
</ul>

<p><strong>Почему выбирают нас</strong></p>
<p>Бесплатный старт, без обязательной регистрации для создания документов, соответствие требованиям ФНС, облачное хранение документов.</p>
"""
    seo_sec = PageSection(
        page_id=page.id,
        section_type="seo_text",
        position=1,
        background_style="white",
        container_width="default",
        is_visible=True,
    )
    db.add(seo_sec)
    db.flush()
    db.add(ContentBlock(section_id=seo_sec.id, block_type="paragraph", position=0, content={"text": about_html.strip()}, is_visible=True))
    print("about: OK")


def main():
    db = SessionLocal()
    try:
        migrate_privacy(db)
        migrate_agreement(db)
        migrate_about(db)
        db.commit()
        print("Готово. Контент перенесён в CMS. Верните в about.py и legal.py отдачу из БД (проверку CMS первым).")
    except Exception as e:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
