#!/usr/bin/env python3
"""
Создание страницы УПД в CMS: slug=upd, секции Hero, Features, UPD Types, FAQ, Полезные материалы, CTA.
Контент как с текущей страницы /upd/ (как заполнил бы человек).

Запуск локально: из корня backend: python3 scripts/seed_upd_cms_page.py
На проде (Docker): docker-compose exec backend python3 scripts/seed_upd_cms_page.py
Без этой страницы в БД /upd/ отдаёт старый YAML-шаблон.
"""

import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal
from app.models import Page, PageSection, ContentBlock


def seed_upd_page(db):
    existing = db.query(Page).filter(Page.slug == "upd").first()
    if existing:
        print("Страница upd уже существует (ID: {}). Выход.".format(existing.id))
        return existing

    page = Page(
        slug="upd",
        title="Генератор УПД онлайн",
        meta_title="Генератор УПД онлайн бесплатно 2026 — Documatica",
        meta_description="Создайте УПД онлайн за 2 минуты. Автозаполнение реквизитов по ИНН, актуальная форма 2026 года. Для ИП, ООО и самозанятых. Бесплатно.",
        meta_keywords="упд онлайн, генератор упд, упд бесплатно, упд 2026, создать упд",
        canonical_url="/upd/",
        status="published",
        page_type="service",
        published_at=datetime.utcnow(),
    )
    db.add(page)
    db.flush()

    # ——— Секция 1: Hero ———
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

    db.add(ContentBlock(section_id=hero.id, block_type="label", position=0, content={"text": "Генератор документов"}, css_classes="hero-tag docu-tag-muted", is_visible=True))
    db.add(ContentBlock(section_id=hero.id, block_type="heading", position=1, content={"text": "Генератор УПД онлайн", "level": 1}, css_classes="hero-title type-h1", is_visible=True))
    db.add(ContentBlock(section_id=hero.id, block_type="paragraph", position=2, content={"text": "Создайте универсальный передаточный документ за 2 минуты. Автозаполнение реквизитов по ИНН, соответствие законодательству 2026 года. Бесплатно для ИП, ООО и самозанятых."}, css_classes="hero-subtitle", is_visible=True))
    db.add(ContentBlock(section_id=hero.id, block_type="button", position=3, content={"text": "Создать УПД бесплатно", "url": "/dashboard/upd/create/"}, css_classes="docu-btn-primary", is_visible=True))
    db.add(ContentBlock(section_id=hero.id, block_type="button", position=4, content={"text": "Смотреть образец", "url": "/upd/obrazec/"}, css_classes="header-btn-outline-v12", is_visible=True))
    db.add(ContentBlock(section_id=hero.id, block_type="link_group", position=5, content={
        "links": [
            {"text": "УПД для ООО", "url": "/upd/ooo/"},
            {"text": "УПД для ИП", "url": "/upd/ip/"},
            {"text": "УПД с НДС", "url": "/upd/s-nds/"},
            {"text": "УПД без НДС", "url": "/upd/bez-nds/"},
            {"text": "Для самозанятых", "url": "/upd/samozanyatye/"},
        ]
    }, css_classes="", is_visible=True))

    # ——— Секция 2: Features ———
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

    db.add(ContentBlock(section_id=features_sec.id, block_type="heading", position=0, content={"text": "Возможности генератора УПД", "level": 2}, css_classes="section-title", is_visible=True))
    features_data = [
        {"title": "Автозаполнение по ИНН", "description": "Введите ИНН организации — мы подтянем все реквизиты из ЕГРЮЛ/ЕГРИП автоматически", "icon": "search"},
        {"title": "Актуальная форма 2026", "description": "Документ соответствует требованиям Постановления Правительства РФ № 1137", "icon": "check-circle"},
        {"title": "Экспорт в PDF и XML", "description": "Скачайте документ для печати или отправьте через систему ЭДО", "icon": "download"},
        {"title": "Сохранение шаблонов", "description": "Сохраняйте часто используемые данные для быстрого создания документов", "icon": "document"},
        {"title": "История документов", "description": "Все созданные документы сохраняются в личном кабинете", "icon": "history"},
        {"title": "Бесплатный тариф", "description": "Создавайте до 10 документов в месяц бесплатно, без ограничений функций", "icon": "gift"},
    ]
    for i, f in enumerate(features_data):
        db.add(ContentBlock(section_id=features_sec.id, block_type="feature_card", position=i + 1, content=f, css_classes="feature-card", is_visible=True))

    # ——— Секция 3: UPD Types (карточки типов УПД) ———
    upd_types_sec = PageSection(
        page_id=page.id,
        section_type="upd_types",
        position=2,
        background_style="white",
        container_width="default",
        is_visible=True,
        grid_columns=3,
        grid_gap="medium",
        grid_style="grid",
    )
    db.add(upd_types_sec)
    db.flush()

    upd_cards = [
        {"tag": "Мои компании", "title": "УПД для ООО", "description": "Для организаций с любой системой налогообложения", "url": "/upd/ooo/", "icon": "briefcase"},
        {"tag": "Предприниматели", "title": "УПД для ИП", "description": "Для индивидуальных предпринимателей", "url": "/upd/ip/", "icon": "user"},
        {"tag": "НПД", "title": "УПД для самозанятых", "description": "Для плательщиков налога на профессиональный доход", "url": "/upd/samozanyatye/", "icon": "home"},
        {"tag": "Статус 1", "title": "УПД с НДС", "description": "Со статусом 1 — заменяет счет-фактуру", "url": "/upd/s-nds/", "icon": "dollar-sign"},
        {"tag": "Статус 2", "title": "УПД без НДС", "description": "Со статусом 2 — только первичный документ", "url": "/upd/bez-nds/", "icon": "file-text"},
        {"tag": "Упрощенка", "title": "УПД на УСН", "description": "Для упрощенной системы налогообложения", "url": "/upd/usn/", "icon": "slash"},
    ]
    db.add(ContentBlock(section_id=upd_types_sec.id, block_type="upd_types_grid", position=0, content={
        "label": "Выберите тип УПД",
        "title": "Универсальный передаточный документ",
        "cards": upd_cards,
    }, css_classes="", is_visible=True))

    # ——— Секция 4: FAQ ———
    faq_sec = PageSection(
        page_id=page.id,
        section_type="faq",
        position=3,
        background_style="surface_light",
        container_width="default",
        is_visible=True,
    )
    db.add(faq_sec)
    db.flush()

    faq_items = [
        {
            "question": "Что такое УПД?",
            "answer": "<p>УПД (универсальный передаточный документ) — это документ, который объединяет счет-фактуру и первичный документ (товарную накладную или акт). Введен в 2013 году письмом ФНС России.</p><p>УПД может использоваться вместо:</p><ul><li>Счета-фактуры + товарной накладной ТОРГ-12</li><li>Счета-фактуры + акта выполненных работ</li></ul>",
        },
        {
            "question": "Кто может использовать УПД?",
            "answer": "<p>УПД могут использовать:</p><ul><li>Организации (ООО, АО) на любой системе налогообложения</li><li>Индивидуальные предприниматели</li><li>Самозанятые (плательщики НПД)</li></ul><p>Использование УПД не обязательно — это право, а не обязанность.</p>",
        },
        {
            "question": "Чем отличается статус 1 от статуса 2 в УПД?",
            "answer": "<p><strong>Статус 1</strong> — УПД выполняет функцию и счета-фактуры, и первичного документа. Используется плательщиками НДС.</p><p><strong>Статус 2</strong> — УПД выполняет только функцию первичного документа. Используется на УСН, патенте и неплательщиками НДС.</p>",
        },
        {
            "question": "УПД обязателен или можно использовать обычные документы?",
            "answer": "<p>УПД не обязателен. Вы можете продолжать использовать привычные документы: счет-фактуру + товарную накладную или акт.</p><p>Однако УПД удобнее — один документ вместо двух, меньше бумажной работы.</p>",
        },
    ]
    db.add(ContentBlock(section_id=faq_sec.id, block_type="heading", position=0, content={"text": "Вопросы об УПД", "level": 2}, css_classes="faq-block-title-v12", is_visible=True))
    for i, item in enumerate(faq_items):
        db.add(ContentBlock(section_id=faq_sec.id, block_type="faq_item", position=i + 1, content=item, css_classes="faq-item-v12", is_visible=True))

    # ——— Секция 5: Полезные материалы ———
    useful_sec = PageSection(
        page_id=page.id,
        section_type="useful_materials",
        position=4,
        background_style="white",
        container_width="default",
        is_visible=True,
    )
    db.add(useful_sec)
    db.flush()

    db.add(ContentBlock(section_id=useful_sec.id, block_type="useful_materials", position=0, content={
        "title": "Полезные материалы",
        "links": [
            {"title": "Образец заполнения УПД", "url": "/upd/obrazec/"},
            {"title": "УПД для ООО", "url": "/upd/ooo/"},
            {"title": "УПД для ИП", "url": "/upd/ip/"},
            {"title": "УПД с НДС (статус 1)", "url": "/upd/s-nds/"},
            {"title": "УПД без НДС (статус 2)", "url": "/upd/bez-nds/"},
            {"title": "Скачать бланк УПД Excel", "url": "/upd/blank-excel/"},
        ],
    }, css_classes="", is_visible=True))

    # ——— Секция 6: CTA ———
    cta_sec = PageSection(
        page_id=page.id,
        section_type="cta",
        position=5,
        background_style="gradient_blue",
        container_width="default",
        is_visible=True,
    )
    db.add(cta_sec)
    db.flush()

    db.add(ContentBlock(section_id=cta_sec.id, block_type="label", position=0, content={"text": "Начните сейчас", "badge_style": "primary"}, css_classes="cta-block-tag-v12", is_visible=True))
    db.add(ContentBlock(section_id=cta_sec.id, block_type="heading", position=1, content={"text": "Готовы создать УПД?", "level": 2}, css_classes="cta-block-title-v12", is_visible=True))
    db.add(ContentBlock(section_id=cta_sec.id, block_type="paragraph", position=2, content={"text": "Зарегистрируйтесь бесплатно и создайте первый документ за 2 минуты"}, css_classes="cta-block-desc-v12", is_visible=True))
    db.add(ContentBlock(section_id=cta_sec.id, block_type="button", position=3, content={"text": "Создать УПД бесплатно", "url": "/dashboard/upd/create/"}, css_classes="cta-btn-v12", is_visible=True))

    db.commit()
    print("Создана страница «УПД» (ID: {}), секции: hero, features, upd_types, faq, useful_materials, cta.".format(page.id))
    return page


def main():
    db = SessionLocal()
    try:
        seed_upd_page(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()
