#!/usr/bin/env python3
"""
Создание страниц Счет и Акт в CMS: хабы + все внутренние (лендинги и инфо).
Секции заполняются из YAML; все редактируемые в админке.

Запуск: из корня backend: python3 scripts/seed_schet_akt_hub_pages.py
"""

import sys
import yaml
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal
from app.models import Page, PageSection, ContentBlock
from app.core.content import load_content

CONTENT_DIR = Path(__file__).parent.parent / "content"


def _clear_page_sections(db, page):
    """Удаляет все секции страницы (блоки каскадно)."""
    for section in list(page.sections):
        db.delete(section)
    db.flush()


def seed_schet_page(db):
    """Страница /schet/ — Генератор счета на оплату."""
    page = db.query(Page).filter(Page.slug == "schet").first()
    if not page:
        page = Page(
            slug="schet",
            title="Генератор счета на оплату",
            status="published",
            meta_title="Генератор счета на оплату онлайн бесплатно — Documatica",
            meta_description="Создайте счет на оплату онлайн за 1 минуту. Автозаполнение реквизитов по ИНН, QR-код для быстрой оплаты. Бесплатно.",
            meta_keywords="счет на оплату онлайн, генератор счетов, счет бесплатно, счет для ИП, счет для ООО",
            canonical_url="/schet/",
        )
        db.add(page)
        db.flush()
    else:
        _clear_page_sections(db, page)

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
    db.add(ContentBlock(section_id=hero.id, block_type="label", position=0, content={"text": "Генератор документов"}, css_classes="hero-tag docu-tag-muted", is_visible=True))
    db.add(ContentBlock(section_id=hero.id, block_type="heading", position=1, content={"text": "Генератор счета на оплату", "level": 1}, css_classes="hero-title type-h1", is_visible=True))
    db.add(ContentBlock(section_id=hero.id, block_type="paragraph", position=2, content={"text": "Создайте счет на оплату за 1 минуту. Автозаполнение реквизитов по ИНН, QR-код для быстрой оплаты через мобильный банк."}, css_classes="hero-subtitle", is_visible=True))
    db.add(ContentBlock(section_id=hero.id, block_type="button", position=3, content={"text": "Создать счет", "url": "/dashboard/invoice/create/"}, css_classes="docu-btn-primary", is_visible=True))
    db.add(ContentBlock(section_id=hero.id, block_type="button", position=4, content={"text": "Смотреть образец", "url": "/schet/obrazec/"}, css_classes="header-btn-outline-v12", is_visible=True))
    db.add(ContentBlock(section_id=hero.id, block_type="link_group", position=5, content={
        "links": [
            {"text": "Счет для ИП", "url": "/schet/ip/"},
            {"text": "Счет для ООО", "url": "/schet/ooo/"},
            {"text": "Счет с НДС", "url": "/schet/s-nds/"},
            {"text": "Счет без НДС", "url": "/schet/bez-nds/"},
            {"text": "С QR-кодом", "url": "/schet/qr-kod/"},
        ]
    }, css_classes="", is_visible=True))

    # ——— 2. Features ———
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
    db.add(ContentBlock(section_id=features_sec.id, block_type="heading", position=0, content={"text": "Возможности генератора счетов", "level": 2}, css_classes="section-title", is_visible=True))
    for i, f in enumerate([
        {"title": "1 минута", "description": "Заполните форму и скачайте готовый счет в PDF", "icon": "clock"},
        {"title": "Автозаполнение по ИНН", "description": "Реквизиты контрагента подтягиваются автоматически", "icon": "search"},
        {"title": "QR-код для оплаты", "description": "Клиент оплатит счет за секунды через мобильный банк", "icon": "qr-code"},
        {"title": "История документов", "description": "Все счета сохраняются в личном кабинете", "icon": "save"},
    ]):
        db.add(ContentBlock(section_id=features_sec.id, block_type="feature_card", position=i + 1, content=f, css_classes="feature-card", is_visible=True))

    # ——— 3. Document types (Выберите тип счета) ———
    cards_sec = PageSection(
        page_id=page.id,
        section_type="document_types",
        position=2,
        background_style="white",
        container_width="default",
        is_visible=True,
        grid_columns=3,
        grid_gap="medium",
        grid_style="grid",
    )
    db.add(cards_sec)
    db.flush()
    db.add(ContentBlock(section_id=cards_sec.id, block_type="heading", position=0, content={"text": "Выберите тип счета", "accent": ""}, css_classes="section-title", is_visible=True))
    schet_cards = [
        {"tag": "Индивидуальный предприниматель", "name": "Счет для ИП", "description": "Для индивидуальных предпринимателей на любой системе налогообложения", "url": "/schet/ip/", "icon": "user", "card_style": "feature"},
        {"tag": "Организации", "name": "Счет для ООО", "description": "Для юридических лиц с любой системой налогообложения", "url": "/schet/ooo/", "icon": "briefcase", "card_style": "feature"},
        {"tag": "НПД", "name": "Счет для самозанятых", "description": "Для плательщиков налога на профессиональный доход", "url": "/schet/samozanyatye/", "icon": "home", "card_style": "feature"},
        {"tag": "Налогообложение", "name": "Счет с НДС", "description": "Для плательщиков НДС на общей системе", "url": "/schet/s-nds/", "icon": "dollar-sign", "card_style": "feature"},
        {"tag": "УСН / Патент", "name": "Счет без НДС", "description": "Для неплательщиков НДС на спецрежимах", "url": "/schet/bez-nds/", "icon": "document-text", "card_style": "feature"},
        {"tag": "Быстрая оплата", "name": "Счет с QR-кодом", "description": "Мгновенная оплата через мобильный банк", "url": "/schet/qr-kod/", "icon": "qr-code", "card_style": "feature"},
    ]
    for i, card in enumerate(schet_cards):
        db.add(ContentBlock(section_id=cards_sec.id, block_type="document_type_card", position=i + 1, content=card, css_classes="", is_visible=True))

    # ——— 4. FAQ ———
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
    db.add(ContentBlock(section_id=faq_sec.id, block_type="heading", position=0, content={"text": "Часто задаваемые вопросы", "level": 2}, css_classes="faq-block-title-v12", is_visible=True))
    faq_items = [
        {"question": "Как создать счет на оплату онлайн?", "answer": "<p>Зарегистрируйтесь, заполните реквизиты организации, добавьте товары или услуги и скачайте готовый счет в PDF.</p>"},
        {"question": "Счет бесплатный?", "answer": "<p>Да, создание счетов полностью бесплатно. Ограничений по количеству нет.</p>"},
        {"question": "Можно добавить QR-код для оплаты?", "answer": "<p>Да, QR-код генерируется автоматически на основе банковских реквизитов и суммы счета.</p>"},
        {"question": "Какие реквизиты нужны для счета?", "answer": "<p>ИНН, название организации, банковские реквизиты (БИК, расчетный счет). Для ИП также нужен ОГРНИП.</p>"},
    ]
    for i, item in enumerate(faq_items):
        db.add(ContentBlock(section_id=faq_sec.id, block_type="faq_item", position=i + 1, content=item, css_classes="", is_visible=True))

    # ——— 5. CTA ———
    cta_sec = PageSection(
        page_id=page.id,
        section_type="cta",
        position=4,
        background_style="gradient_blue",
        container_width="default",
        is_visible=True,
    )
    db.add(cta_sec)
    db.flush()
    db.add(ContentBlock(section_id=cta_sec.id, block_type="label", position=0, content={"text": "Начните сейчас", "badge_style": "primary"}, css_classes="cta-block-tag-v12", is_visible=True))
    db.add(ContentBlock(section_id=cta_sec.id, block_type="heading", position=1, content={"text": "Готовы создать документ?", "level": 2}, css_classes="cta-block-title-v12", is_visible=True))
    db.add(ContentBlock(section_id=cta_sec.id, block_type="paragraph", position=2, content={"text": "Зарегистрируйтесь бесплатно и создайте первый счет за 2 минуты"}, css_classes="cta-block-desc-v12", is_visible=True))
    db.add(ContentBlock(section_id=cta_sec.id, block_type="button", position=3, content={"text": "Создать счет", "url": "/dashboard/invoice/create/"}, css_classes="cta-btn-v12", is_visible=True))

    print("  [schet] Страница /schet/ создана/обновлена: hero, features, document_types, faq, cta.")
    return page


def seed_akt_page(db):
    """Страница /akt/ — Генератор Акта выполненных работ."""
    page = db.query(Page).filter(Page.slug == "akt").first()
    if not page:
        page = Page(
            slug="akt",
            title="Генератор Акта выполненных работ онлайн",
            status="published",
            meta_title="Генератор Акта выполненных работ онлайн бесплатно 2026 — Documatica",
            meta_description="Создайте акт выполненных работ онлайн за 2 минуты. Автозаполнение реквизитов по ИНН, актуальная форма 2026 года. Для ИП, ООО и самозанятых. Бесплатно.",
            meta_keywords="акт выполненных работ онлайн, генератор акта, акт оказанных услуг, акт бесплатно, акт 2026",
            canonical_url="/akt/",
        )
        db.add(page)
        db.flush()
    else:
        _clear_page_sections(db, page)

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
    db.add(ContentBlock(section_id=hero.id, block_type="label", position=0, content={"text": "Генератор документов"}, css_classes="hero-tag docu-tag-muted", is_visible=True))
    db.add(ContentBlock(section_id=hero.id, block_type="heading", position=1, content={"text": "Генератор Акта выполненных работ онлайн", "level": 1}, css_classes="hero-title type-h1", is_visible=True))
    db.add(ContentBlock(section_id=hero.id, block_type="paragraph", position=2, content={"text": "Создайте акт выполненных работ или оказанных услуг за 2 минуты. Автозаполнение реквизитов по ИНН, соответствие законодательству 2026 года. Бесплатно для ИП, ООО и самозанятых."}, css_classes="hero-subtitle", is_visible=True))
    db.add(ContentBlock(section_id=hero.id, block_type="button", position=3, content={"text": "Создать Акт бесплатно", "url": "/dashboard/akt/create/"}, css_classes="docu-btn-primary", is_visible=True))
    db.add(ContentBlock(section_id=hero.id, block_type="button", position=4, content={"text": "Смотреть образец", "url": "/akt/obrazec-zapolneniya/"}, css_classes="header-btn-outline-v12", is_visible=True))
    db.add(ContentBlock(section_id=hero.id, block_type="link_group", position=5, content={
        "links": [
            {"text": "Акт для ООО", "url": "/akt/ooo/"},
            {"text": "Акт для ИП", "url": "/akt/ip/"},
            {"text": "Акт услуг", "url": "/akt/uslug/"},
            {"text": "Акт работ", "url": "/akt/rabot/"},
            {"text": "Для самозанятых", "url": "/akt/samozanyatye/"},
        ]
    }, css_classes="", is_visible=True))

    # ——— 2. Features ———
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
    db.add(ContentBlock(section_id=features_sec.id, block_type="heading", position=0, content={"text": "Возможности генератора Акта", "level": 2}, css_classes="section-title", is_visible=True))
    for i, f in enumerate([
        {"title": "Автозаполнение по ИНН", "description": "Введите ИНН организации — мы подтянем все реквизиты из ЕГРЮЛ/ЕГРИП автоматически", "icon": "search"},
        {"title": "Актуальная форма 2026", "description": "Документ соответствует требованиям законодательства РФ", "icon": "check-circle"},
        {"title": "Экспорт в PDF", "description": "Скачайте документ для печати или отправки по email", "icon": "download"},
        {"title": "Сохранение шаблонов", "description": "Сохраняйте часто используемые данные для быстрого создания документов", "icon": "document"},
        {"title": "История документов", "description": "Все созданные документы сохраняются в личном кабинете", "icon": "history"},
        {"title": "Бесплатный тариф", "description": "Создавайте до 10 документов в месяц бесплатно, без ограничений функций", "icon": "gift"},
    ]):
        db.add(ContentBlock(section_id=features_sec.id, block_type="feature_card", position=i + 1, content=f, css_classes="feature-card", is_visible=True))

    # ——— 3. Document types (Выберите тип Акта) ———
    cards_sec = PageSection(
        page_id=page.id,
        section_type="document_types",
        position=2,
        background_style="white",
        container_width="default",
        is_visible=True,
        grid_columns=3,
        grid_gap="medium",
        grid_style="grid",
    )
    db.add(cards_sec)
    db.flush()
    db.add(ContentBlock(section_id=cards_sec.id, block_type="heading", position=0, content={"text": "Выберите тип Акта", "accent": ""}, css_classes="section-title", is_visible=True))
    akt_cards = [
        {"tag": "Организации", "name": "Акт для ООО", "description": "Для организаций с любой системой налогообложения", "url": "/akt/ooo/", "icon": "briefcase", "card_style": "feature"},
        {"tag": "Предприниматели", "name": "Акт для ИП", "description": "Для индивидуальных предпринимателей", "url": "/akt/ip/", "icon": "user", "card_style": "feature"},
        {"tag": "НПД", "name": "Акт для самозанятых", "description": "Для плательщиков налога на профессиональный доход", "url": "/akt/samozanyatye/", "icon": "home", "card_style": "feature"},
        {"tag": "Услуги", "name": "Акт оказанных услуг", "description": "Консалтинг, IT, маркетинг, аудит", "url": "/akt/uslug/", "icon": "check-circle", "card_style": "feature"},
        {"tag": "Работы", "name": "Акт выполненных работ", "description": "Строительство, ремонт, монтаж", "url": "/akt/rabot/", "icon": "wrench", "card_style": "feature"},
        {"tag": "ОСНО", "name": "Акт с НДС", "description": "Для плательщиков НДС", "url": "/akt/s-nds/", "icon": "dollar-sign", "card_style": "feature"},
        {"tag": "УСН / Патент", "name": "Акт без НДС", "description": "Для неплательщиков НДС", "url": "/akt/bez-nds/", "icon": "document-text", "card_style": "feature"},
        {"tag": "Актуально", "name": "Форма 2026", "description": "Актуальная форма акта", "url": "/akt/2026/", "icon": "calendar", "card_style": "feature"},
    ]
    for i, card in enumerate(akt_cards):
        db.add(ContentBlock(section_id=cards_sec.id, block_type="document_type_card", position=i + 1, content=card, css_classes="", is_visible=True))

    # ——— 4. FAQ ———
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
    db.add(ContentBlock(section_id=faq_sec.id, block_type="heading", position=0, content={"text": "Вопросы об Акте выполненных работ", "level": 2}, css_classes="faq-block-title-v12", is_visible=True))
    faq_items = [
        {"question": "Что такое «акт выполненных работ онлайн» и зачем он нужен заказчику?", "answer": "<p>Акт выполненных работ — это документ, который фиксирует факты выполнения работ и оказания услуг, подтверждает приемку результатов и имеет юридическую силу для расчетов и учета.</p><p>Он нужен заказчику, исполнителю и подрядчику как основание для закрытия обязательств по договору, подтверждения оплаты и отражения операций к учету.</p>"},
        {"question": "Как создать акт онлайн на сайте и что делает сервис автоматически?", "answer": "<p>Вы создаете акт онлайн: вводите минимум данных, выбираете шаблоны и форматы, после чего сервис автоматически проверяет заполнение и формирует документ.</p><p>Такие сервисы помогают быстрее пройти путь создания и оформления, особенно когда нужно оформить много актов по разным контрагентам.</p>"},
        {"question": "Можно ли скачать акт бланком, в PDF и распечатать?", "answer": "<p>Да. Готовый акт можно скачать бланком в PDF, затем распечатать — в том числе в удобных форматах для архива.</p><p>При необходимости документ можно заверить печатями или подготовить версию с подписью, если так принято у сторон.</p>"},
        {"question": "Какие обязательные реквизиты нужно указать при заполнении?", "answer": "<p>При заполнении и составлении акта важно указать все обязательные сведения: реквизиты сторон, предмет работ/услуг, объемы, стоимость, даты, номер документа и основание (договор/заказ).</p><p>В тексте акта также указываются условия приемки, а при необходимости — требования по качеству и срокам.</p>"},
        {"question": "Что подтверждают акт и приемка-сдача: объемы, результаты, стоимость?", "answer": "<p>Акт подтверждает факты выполненных работ и результаты оказания услуги: объемы, работы со стоимостью, соответствие качеству, а также факт сдачи и приемки результата.</p><p>В формулировках можно отразить этапность и привязку к сроку выполнения — это полезно при спорах и при работе с бухгалтерией.</p>"},
        {"question": "Чем отличаются акт сдачи-приемки, приемки-сдачи и акт приема-передачи?", "answer": "<p>В практике используют разные названия: «акт сдачи-приемки», «акт приемки-сдачи», «акт о сдаче-приемке» и «акт приема-передачи».</p><p>Суть одна: документ фиксирует передачу результата работ/услуг и принятие заказчиком.</p>"},
        {"question": "Кто подписывает акт и как фиксируется дата подписания?", "answer": "<p>Акт обычно подписывают обе стороны: исполнитель (или подрядчик) и заказчик.</p><p>В документе фиксируют даты и момент подписания: это важно для оплаты по счету, закрытия работ и корректного отражения в учете.</p><p>Когда акт уже подписан, он становится ключевым подтверждением приемки и сдачи.</p>"},
        {"question": "Как акт помогает при претензиях и спорах по качеству?", "answer": "<p>Корректно составленный акт снижает риски по претензиям: если есть замечания, их можно описать; если замечаний нет — зафиксировать отсутствие.</p><p>Документ подтверждает факт выполнения, объемы и соответствие качеству, а также служит основанием в случае конфликтов с контрагентом.</p>"},
        {"question": "Подходит ли акт для любых работ и как он связан с КС-2 и КС-3?", "answer": "<p>Акт можно использовать для любых услуг и работ, но в строительстве часто применяют специализированные формы: КС-2 и КС-3.</p><p>При этом общий акт может дополнять комплект, если так предусмотрено договором или нужно для внутреннего учета и подтверждения фактов выполненных работ.</p>"},
        {"question": "Какие форматы и программы поддерживаются, и как правильно оформить документ?", "answer": "<p>Сервис формирует документ в разных форматах для хранения и обмена: печатные версии, электронные файлы и экспорт под учетные программы.</p><p>Чтобы правильно оформить акт, составьте его по шаблону: формируйте документ с полным набором необходимых реквизитов, укажите основания по договору и срок, проверьте номер и даты.</p>"},
    ]
    for i, item in enumerate(faq_items):
        db.add(ContentBlock(section_id=faq_sec.id, block_type="faq_item", position=i + 1, content=item, css_classes="", is_visible=True))

    # ——— 5. CTA ———
    cta_sec = PageSection(
        page_id=page.id,
        section_type="cta",
        position=4,
        background_style="gradient_blue",
        container_width="default",
        is_visible=True,
    )
    db.add(cta_sec)
    db.flush()
    db.add(ContentBlock(section_id=cta_sec.id, block_type="label", position=0, content={"text": "Начните сейчас", "badge_style": "primary"}, css_classes="cta-block-tag-v12", is_visible=True))
    db.add(ContentBlock(section_id=cta_sec.id, block_type="heading", position=1, content={"text": "Готовы создать Акт?", "level": 2}, css_classes="cta-block-title-v12", is_visible=True))
    db.add(ContentBlock(section_id=cta_sec.id, block_type="paragraph", position=2, content={"text": "Зарегистрируйтесь бесплатно и создайте первый документ за 2 минуты"}, css_classes="cta-block-desc-v12", is_visible=True))
    db.add(ContentBlock(section_id=cta_sec.id, block_type="button", position=3, content={"text": "Создать Акт бесплатно", "url": "/dashboard/akt/create/"}, css_classes="cta-btn-v12", is_visible=True))

    print("  [akt] Страница /akt/ создана/обновлена: hero, features, document_types, faq, cta.")
    return page


def _icon_name(icon: str) -> str:
    """Нормализация иконки: mdi:database-search -> database-search."""
    if not icon:
        return "document"
    return icon.replace("mdi:", "", 1).strip() or "document"


def _add_inner_page_sections(db, page, content: dict, cta_url: str, cta_text: str):
    """Добавляет секции на страницу из словаря content (YAML)."""
    meta = content.get("meta") or {}
    page_data = content.get("page") or {}
    cta_data = content.get("cta") or {}
    cta_url = cta_data.get("url") or cta_url
    cta_text = cta_data.get("text") or cta_text
    related = content.get("related") or []
    features = content.get("features") or []
    benefits = content.get("benefits") or []
    faq_list = content.get("faq") or []
    pos = 0

    # Hero
    hero = PageSection(
        page_id=page.id,
        section_type="hero",
        position=pos,
        background_style="pattern_radial_blue",
        container_width="default",
        is_visible=True,
    )
    db.add(hero)
    db.flush()
    tag = page_data.get("tag") or ""
    h1 = page_data.get("h1") or page.title
    intro = page_data.get("intro") or ""
    db.add(ContentBlock(section_id=hero.id, block_type="label", position=0, content={"text": tag}, css_classes="hero-tag docu-tag-muted", is_visible=True))
    db.add(ContentBlock(section_id=hero.id, block_type="heading", position=1, content={"text": h1, "level": 1}, css_classes="hero-title type-h1", is_visible=True))
    db.add(ContentBlock(section_id=hero.id, block_type="paragraph", position=2, content={"text": intro}, css_classes="hero-subtitle", is_visible=True))
    db.add(ContentBlock(section_id=hero.id, block_type="button", position=3, content={"text": cta_text, "url": cta_url}, css_classes="docu-btn-primary", is_visible=True))
    if related:
        links = [{"text": r.get("title", ""), "url": r.get("url", "")} for r in related]
        db.add(ContentBlock(section_id=hero.id, block_type="link_group", position=4, content={"links": links}, css_classes="", is_visible=True))
    pos += 1

    # Features (из features или benefits)
    feats = features if features else benefits
    if feats:
        sec = PageSection(
            page_id=page.id,
            section_type="features",
            position=pos,
            background_style="white",
            container_width="default",
            is_visible=True,
            grid_columns=3,
            grid_gap="medium",
            grid_style="grid",
        )
        db.add(sec)
        db.flush()
        for i, f in enumerate(feats):
            item = {"title": f.get("title", ""), "description": f.get("description", ""), "icon": _icon_name(f.get("icon", ""))}
            db.add(ContentBlock(section_id=sec.id, block_type="feature_card", position=i, content=item, css_classes="feature-card", is_visible=True))
        pos += 1

    # SEO text (page.content или sections)
    html_parts = []
    if page_data.get("content"):
        html_parts.append(("", page_data["content"]))
    for s in content.get("sections") or []:
        title = s.get("title", "")
        body = s.get("content", "")
        if title:
            html_parts.append((title, body))
        elif body:
            html_parts.append(("", body))
    if html_parts:
        seo_sec = PageSection(
            page_id=page.id,
            section_type="seo_text",
            position=pos,
            background_style="surface_light",
            container_width="default",
            is_visible=True,
        )
        db.add(seo_sec)
        db.flush()
        block_pos = 0
        for title, body in html_parts:
            if title:
                db.add(ContentBlock(section_id=seo_sec.id, block_type="heading", position=block_pos, content={"text": title, "level": 2}, css_classes="", is_visible=True))
                block_pos += 1
            if body:
                db.add(ContentBlock(section_id=seo_sec.id, block_type="paragraph", position=block_pos, content={"text": body}, css_classes="", is_visible=True))
                block_pos += 1
        pos += 1

    # FAQ
    if faq_list:
        faq_sec = PageSection(
            page_id=page.id,
            section_type="faq",
            position=pos,
            background_style="surface_light",
            container_width="default",
            is_visible=True,
        )
        db.add(faq_sec)
        db.flush()
        db.add(ContentBlock(section_id=faq_sec.id, block_type="heading", position=0, content={"text": "Часто задаваемые вопросы", "level": 2}, css_classes="faq-block-title-v12", is_visible=True))
        for i, item in enumerate(faq_list):
            db.add(ContentBlock(section_id=faq_sec.id, block_type="faq_item", position=i + 1, content={"question": item.get("question", ""), "answer": item.get("answer", "")}, css_classes="", is_visible=True))
        pos += 1

    # CTA
    cta_sec = PageSection(
        page_id=page.id,
        section_type="cta",
        position=pos,
        background_style="gradient_blue",
        container_width="default",
        is_visible=True,
    )
    db.add(cta_sec)
    db.flush()
    cta_title = cta_data.get("title") or "Готовы создать документ?"
    cta_desc = cta_data.get("description") or "Зарегистрируйтесь бесплатно и создайте документ за 2 минуты"
    db.add(ContentBlock(section_id=cta_sec.id, block_type="label", position=0, content={"text": "Начните сейчас", "badge_style": "primary"}, css_classes="cta-block-tag-v12", is_visible=True))
    db.add(ContentBlock(section_id=cta_sec.id, block_type="heading", position=1, content={"text": cta_title, "level": 2}, css_classes="cta-block-title-v12", is_visible=True))
    db.add(ContentBlock(section_id=cta_sec.id, block_type="paragraph", position=2, content={"text": cta_desc}, css_classes="cta-block-desc-v12", is_visible=True))
    db.add(ContentBlock(section_id=cta_sec.id, block_type="button", position=3, content={"text": cta_text, "url": cta_url}, css_classes="cta-btn-v12", is_visible=True))


def _load_pages_config(prefix: str) -> dict:
    """Загружает _pages.yaml для schet или akt."""
    path = CONTENT_DIR / prefix / "_pages.yaml"
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def seed_schet_inner_pages(db):
    """Все внутренние страницы раздела Счет: лендинги + инфо (из _pages.yaml и YAML)."""
    config = _load_pages_config("schet")
    landings = config.get("landings") or {}
    info_pages = config.get("info_pages") or {}
    created = 0
    for slug, cfg in list(landings.items()) + list(info_pages.items()):
        content_file = cfg.get("content_file", "")
        if not content_file:
            continue
        full_slug = content_file  # e.g. schet/ip
        content = load_content(content_file)
        meta = content.get("meta") or {}
        page_data = content.get("page") or {}
        title = meta.get("title") or page_data.get("h1") or full_slug
        page = db.query(Page).filter(Page.slug == full_slug).first()
        if not page:
            page = Page(
                slug=full_slug,
                title=title[:500],
                status="published",
                meta_title=meta.get("title"),
                meta_description=meta.get("description"),
                meta_keywords=meta.get("keywords"),
                canonical_url=meta.get("canonical") or f"/{full_slug}/",
            )
            db.add(page)
            db.flush()
            created += 1
        else:
            _clear_page_sections(db, page)
            if not page.meta_title and meta.get("title"):
                page.meta_title = meta.get("title")
                page.meta_description = meta.get("description")
                page.meta_keywords = meta.get("keywords")
                page.canonical_url = meta.get("canonical") or f"/{full_slug}/"
        _add_inner_page_sections(db, page, content, "/dashboard/invoice/create/", "Создать счет")
    print(f"  [schet] Внутренние страницы: {len(landings) + len(info_pages)} (лендинги + инфо), создано новых: {created}.")


def seed_akt_inner_pages(db):
    """Все внутренние страницы раздела Акт: лендинги + инфо."""
    config = _load_pages_config("akt")
    landings = config.get("landings") or {}
    info_pages = config.get("info_pages") or {}
    created = 0
    for slug, cfg in list(landings.items()) + list(info_pages.items()):
        content_file = cfg.get("content_file", "")
        if not content_file:
            continue
        full_slug = content_file
        content = load_content(content_file)
        meta = content.get("meta") or {}
        page_data = content.get("page") or {}
        title = meta.get("title") or page_data.get("h1") or full_slug
        page = db.query(Page).filter(Page.slug == full_slug).first()
        if not page:
            page = Page(
                slug=full_slug,
                title=title[:500],
                status="published",
                meta_title=meta.get("title"),
                meta_description=meta.get("description"),
                meta_keywords=meta.get("keywords"),
                canonical_url=meta.get("canonical") or f"/{full_slug}/",
            )
            db.add(page)
            db.flush()
            created += 1
        else:
            _clear_page_sections(db, page)
            if not page.meta_title and meta.get("title"):
                page.meta_title = meta.get("title")
                page.meta_description = meta.get("description")
                page.meta_keywords = meta.get("keywords")
                page.canonical_url = meta.get("canonical") or f"/{full_slug}/"
        _add_inner_page_sections(db, page, content, "/dashboard/akt/create/", "Создать Акт")
    print(f"  [akt] Внутренние страницы: {len(landings) + len(info_pages)} (лендинги + инфо), создано новых: {created}.")


def main():
    db = SessionLocal()
    try:
        print("Seed: хабы + все внутренние страницы Счет и Акт (CMS)...")
        seed_schet_page(db)
        seed_akt_page(db)
        seed_schet_inner_pages(db)
        seed_akt_inner_pages(db)
        db.commit()
        print("Готово. /schet/, /akt/ и все вложенные отдаются из CMS при status=published.")
    except Exception as e:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
