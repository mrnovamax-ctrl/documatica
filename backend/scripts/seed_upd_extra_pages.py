#!/usr/bin/env python3
"""Create UPD pages: upd/xml-edo, upd/obrazec-zapolneniya, upd/2025. Run: python3 scripts/seed_upd_extra_pages.py"""

import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal
from app.models import Page, PageSection, ContentBlock


def create_page(db, slug, title, meta_title, meta_description, meta_keywords, canonical_url):
    existing = db.query(Page).filter(Page.slug == slug).first()
    if existing:
        for s in list(existing.sections):
            db.delete(s)
        db.flush()
        existing.title = title
        existing.meta_title = meta_title
        existing.meta_description = meta_description
        existing.meta_keywords = meta_keywords or ""
        existing.canonical_url = canonical_url or ""
        existing.status = "published"
        existing.updated_at = datetime.utcnow()
        return existing
    page = Page(slug=slug, title=title, meta_title=meta_title, meta_description=meta_description,
                meta_keywords=meta_keywords or "", canonical_url=canonical_url or "", status="published",
                page_type="service", published_at=datetime.utcnow())
    db.add(page)
    db.flush()
    return page


def add_hero(db, page_id, pos, label, title, subtitle, btn_text, btn_url, links):
    s = PageSection(page_id=page_id, section_type="hero", position=pos, background_style="pattern_radial_blue", container_width="default", is_visible=True)
    db.add(s)
    db.flush()
    db.add(ContentBlock(section_id=s.id, block_type="label", position=0, content={"text": label}, css_classes="hero-tag docu-tag-muted", is_visible=True))
    db.add(ContentBlock(section_id=s.id, block_type="heading", position=1, content={"text": title, "level": 1}, css_classes="hero-title type-h1", is_visible=True))
    db.add(ContentBlock(section_id=s.id, block_type="paragraph", position=2, content={"text": subtitle}, css_classes="hero-subtitle", is_visible=True))
    db.add(ContentBlock(section_id=s.id, block_type="button", position=3, content={"text": btn_text, "url": btn_url}, css_classes="docu-btn-primary", is_visible=True))
    if links:
        db.add(ContentBlock(section_id=s.id, block_type="link_group", position=4, content={"links": links}, is_visible=True))


def add_features(db, page_id, pos, heading_text, items):
    s = PageSection(page_id=page_id, section_type="features", position=pos, background_style="white", container_width="default", is_visible=True, grid_columns=3, grid_gap="medium", grid_style="grid")
    db.add(s)
    db.flush()
    db.add(ContentBlock(section_id=s.id, block_type="heading", position=0, content={"text": heading_text, "level": 2}, css_classes="section-title", is_visible=True))
    for i, item in enumerate(items):
        db.add(ContentBlock(section_id=s.id, block_type="feature_card", position=i + 1, content=item, css_classes="feature-card", is_visible=True))


def add_faq(db, page_id, pos, heading_text, items):
    s = PageSection(page_id=page_id, section_type="faq", position=pos, background_style="surface_light", container_width="default", is_visible=True)
    db.add(s)
    db.flush()
    db.add(ContentBlock(section_id=s.id, block_type="heading", position=0, content={"text": heading_text, "level": 2}, css_classes="faq-block-title-v12", is_visible=True))
    for i, item in enumerate(items):
        db.add(ContentBlock(section_id=s.id, block_type="faq_item", position=i + 1, content=item, is_visible=True))


def add_cta(db, page_id, pos, tag, title, desc, btn_text, btn_url):
    s = PageSection(page_id=page_id, section_type="cta", position=pos, background_style="gradient_blue", container_width="default", is_visible=True)
    db.add(s)
    db.flush()
    db.add(ContentBlock(section_id=s.id, block_type="label", position=0, content={"text": tag, "badge_style": "primary"}, css_classes="cta-block-tag-v12", is_visible=True))
    db.add(ContentBlock(section_id=s.id, block_type="heading", position=1, content={"text": title, "level": 2}, css_classes="cta-block-title-v12", is_visible=True))
    db.add(ContentBlock(section_id=s.id, block_type="paragraph", position=2, content={"text": desc}, css_classes="cta-block-desc-v12", is_visible=True))
    db.add(ContentBlock(section_id=s.id, block_type="button", position=3, content={"text": btn_text, "url": btn_url}, css_classes="cta-btn-v12", is_visible=True))


def add_seo(db, page_id, pos, blocks):
    s = PageSection(page_id=page_id, section_type="seo_text", position=pos, background_style="white", container_width="default", is_visible=True)
    db.add(s)
    db.flush()
    for i, b in enumerate(blocks):
        t = b.get("type", "paragraph")
        if t == "heading":
            db.add(ContentBlock(section_id=s.id, block_type="heading", position=i, content={"text": b["text"], "accent": b.get("accent", "")}, css_classes="type-h2 seo-text-title-v12", is_visible=True))
        else:
            db.add(ContentBlock(section_id=s.id, block_type="paragraph", position=i, content={"text": b["text"]}, css_classes="typo-body seo-text-para-v12", is_visible=True))


def seed_xml_edo(db):
    p = create_page(db, "upd/xml-edo", "УПД для ЭДО", "УПД для ЭДО — формат XML для электронного документооборота",
                    "Создайте УПД в формате XML для ЭДО. Совместимость с Контур.Диадок, СБИС, Такском.", "упд эдо, упд xml", "/upd/xml-edo/")
    add_hero(db, p.id, 0, "УПД", "УПД для электронного документооборота",
             "Генератор УПД в формате XML для отправки через системы ЭДО. Совместимость с популярными операторами.",
             "Создать УПД для ЭДО", "/dashboard/upd/create/",
             [{"text": "УПД с НДС", "url": "/upd/s-nds/"}, {"text": "УПД для ООО", "url": "/upd/ooo/"}, {"text": "Образец", "url": "/upd/obrazec-zapolneniya/"}])
    add_features(db, p.id, 1, "Преимущества формата XML", [
        {"title": "Формат XML", "description": "УПД в формате, соответствующем требованиям ФНС для ЭДО", "icon": "code"},
        {"title": "Все операторы ЭДО", "description": "Контур.Диадок, СБИС, Такском, Калуга Астрал и другие", "icon": "share"},
        {"title": "Электронная подпись", "description": "Документ готов к подписанию квалифицированной ЭП", "icon": "shield"}])
    add_faq(db, p.id, 2, "Частые вопросы", [
        {"question": "Как отправить УПД через ЭДО?", "answer": "<p>Создайте УПД, скачайте XML, загрузите в систему ЭДО оператора и подпишите ЭП.</p>"},
        {"question": "Какой формат XML для УПД?", "answer": "<p>Формат соответствует требованиям Приказа ФНС России.</p>"},
        {"question": "Нужна ли бумажная копия при ЭДО?", "answer": "<p>Нет. Электронный документ с КЭП имеет юридическую силу.</p>"},
        {"question": "Какие операторы поддерживаются?", "answer": "<p>Контур.Диадок, СБИС, Такском, Калуга Астрал, Тензор и другие.</p>"}])
    add_cta(db, p.id, 3, "Начните сейчас", "Готовы создать УПД?", "Зарегистрируйтесь бесплатно и создайте документ в XML за 2 минуты", "Создать УПД для ЭДО", "/dashboard/upd/create/")
    print("  upd/xml-edo OK")


def seed_obrazec(db):
    p = create_page(db, "upd/obrazec-zapolneniya", "Образец заполнения УПД",
                    "Образец заполнения УПД 2026 — инструкция с примерами",
                    "Образец заполнения УПД с пояснениями. Примеры для ООО, ИП, с НДС и без НДС.", "образец упд, как заполнить упд", "/upd/obrazec-zapolneniya/")
    add_hero(db, p.id, 0, "Инструкция", "Образец заполнения УПД",
             "Подробные примеры заполнения УПД с пояснениями для разных ситуаций.",
             "Создать УПД по образцу", "/dashboard/upd/create/",
             [{"text": "УПД для ООО", "url": "/upd/ooo/"}, {"text": "УПД для ИП", "url": "/upd/ip/"}, {"text": "УПД с НДС", "url": "/upd/s-nds/"}, {"text": "УПД без НДС", "url": "/upd/bez-nds/"}])
    add_seo(db, p.id, 1, [
        {"type": "paragraph", "text": "<p>УПД объединяет счет-фактуру и первичный документ. Правильное заполнение критически важно для принятия НДС к вычету.</p>"},
        {"type": "heading", "text": "Образец №1: УПД с НДС (Статус 1)", "accent": ""},
        {"type": "paragraph", "text": "<p>Используется плательщиками НДС. Статус 1 — документ заменяет счет-фактуру и первичный документ.</p>"},
        {"type": "heading", "text": "Образец №2: УПД без НДС (Статус 2)", "accent": ""},
        {"type": "paragraph", "text": "<p>Используется на УСН. Статус 2 — только первичный документ.</p>"},
        {"type": "heading", "text": "Важные рекомендации", "accent": ""},
        {"type": "paragraph", "text": "<p><strong>Статус 1</strong> — для плательщиков НДС. <strong>Статус 2</strong> — для УСН и освобожденных. УПД оформляется в течение 5 дней с даты отгрузки (статус 1).</p>"}])
    add_cta(db, p.id, 2, "Начните сейчас", "Готовы создать УПД?", "Зарегистрируйтесь бесплатно и создайте первый документ за 2 минуты", "Создать УПД бесплатно", "/dashboard/upd/create/")
    print("  upd/obrazec-zapolneniya OK (/upd/obrazec/ -> та же)")


def seed_2025(db):
    p = create_page(db, "upd/2025", "УПД в 2025 году", "УПД в 2025 году — актуальный бланк и образец",
                    "Актуальная форма УПД на 2025 год. Скачайте бланк УПД бесплатно.", "упд 2025, бланк упд 2025", "/upd/2025/")
    add_hero(db, p.id, 0, "УПД", "УПД в 2025 году",
             "Актуальная форма УПД на 2025 год. Используйте генератор для создания документов по действующему законодательству.",
             "Создать УПД 2025", "/dashboard/upd/create/",
             [{"text": "Образец заполнения", "url": "/upd/obrazec-zapolneniya/"}, {"text": "УПД с НДС", "url": "/upd/s-nds/"}, {"text": "УПД без НДС", "url": "/upd/bez-nds/"}])
    add_features(db, p.id, 1, "Преимущества", [
        {"title": "Актуальная форма", "description": "Бланк УПД соответствует требованиям на 2025 год", "icon": "check-circle"},
        {"title": "Изменения учтены", "description": "Форма включает последние изменения в законодательстве", "icon": "document"},
        {"title": "Принимается ФНС", "description": "Документы соответствуют требованиям налоговой", "icon": "shield"}])
    add_faq(db, p.id, 2, "Частые вопросы", [
        {"question": "Изменилась ли форма УПД в 2025 году?", "answer": "<p>Форма регулярно обновляется. Генератор использует актуальный бланк.</p>"},
        {"question": "Можно ли использовать старые бланки?", "answer": "<p>Рекомендуется использовать актуальную форму.</p>"},
        {"question": "Как отличить актуальный бланк?", "answer": "<p>Бланк должен соответствовать приложению к письму ФНС. Наш генератор использует правильную форму.</p>"}])
    add_cta(db, p.id, 3, "Начните сейчас", "Готовы создать УПД?", "Зарегистрируйтесь бесплатно и создайте документ за 2 минуты", "Создать УПД 2025", "/dashboard/upd/create/")
    print("  upd/2025 OK")


def main():
    db = SessionLocal()
    try:
        print("Создание страниц УПД (редактируемые в админке)...")
        seed_xml_edo(db)
        seed_obrazec(db)
        seed_2025(db)
        db.commit()
        print("Готово.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
