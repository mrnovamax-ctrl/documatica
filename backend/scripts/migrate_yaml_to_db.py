#!/usr/bin/env python3
"""
Скрипт миграции контента из YAML файлов в PostgreSQL
ВАЖНО: Сохраняет все существующие URL без изменений!
"""

import sys
import os
import yaml
import argparse
from pathlib import Path
from datetime import datetime

# Добавляем путь к app
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal
from app.models import Page, PageSection, ContentBlock

# Путь к контенту
CONTENT_DIR = Path(__file__).parent.parent / "content"


def extract_slug_from_path(yaml_path: str) -> str:
    """
    Извлекает slug из пути к YAML файлу
    ВАЖНО: Сохраняет структуру URL без изменений!
    
    Примеры:
    - home.yaml → "" (главная страница /)
    - upd/index.yaml → "upd" (URL /upd/)
    - upd/ooo.yaml → "upd/ooo" (URL /upd/ooo/)
    - schet/ip.yaml → "schet/ip" (URL /schet/ip/)
    """
    path = yaml_path.replace(".yaml", "").replace(".yml", "")
    
    if path == "home":
        return ""  # Главная страница
    elif path.endswith("/index"):
        return path.replace("/index", "")  # upd/index → upd
    else:
        return path  # Остальные как есть


def load_yaml_file(yaml_path: Path) -> dict:
    """Загрузка YAML файла"""
    with open(yaml_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def migrate_page(yaml_path: str, db: SessionLocal) -> Page:
    """
    Миграция одной страницы из YAML в БД
    Возвращает созданную Page
    """
    full_path = CONTENT_DIR / f"{yaml_path}.yaml"
    if not full_path.exists():
        full_path = CONTENT_DIR / f"{yaml_path}.yml"
    
    if not full_path.exists():
        print(f"❌ Файл не найден: {yaml_path}")
        return None
    
    # Загружаем YAML
    data = load_yaml_file(full_path)
    
    # Извлекаем slug (БЕЗ изменений!)
    slug = extract_slug_from_path(yaml_path)
    
    # Проверяем, не существует ли уже
    existing = db.query(Page).filter(Page.slug == slug).first()
    if existing:
        print(f"⚠️  Страница уже существует: {slug}")
        return existing
    
    # Извлекаем meta
    meta = data.get("meta", {})
    
    # Создаём Page
    page = Page(
        slug=slug,
        title=meta.get("title", yaml_path),
        meta_title=meta.get("title"),
        meta_description=meta.get("description"),
        meta_keywords=meta.get("keywords"),
        canonical_url=meta.get("canonical"),
        status="published",
        page_type=determine_page_type(yaml_path),
        legacy_yaml_path=yaml_path,
        published_at=datetime.utcnow()
    )
    
    db.add(page)
    db.flush()  # Получаем ID
    
    print(f"✅ Создана страница: {slug} (ID: {page.id})")
    
    # Мигрируем секции
    migrate_sections(page, data, db)
    
    return page


def determine_page_type(yaml_path: str) -> str:
    """Определяет тип страницы по пути"""
    if yaml_path == "home":
        return "home"
    elif yaml_path.startswith("upd/") or yaml_path.startswith("schet/") or yaml_path.startswith("akt/"):
        return "service"
    elif yaml_path.startswith("news/"):
        return "blog"
    else:
        return "custom"


def migrate_sections(page: Page, data: dict, db: SessionLocal):
    """Миграция секций страницы"""
    position = 0
    
    # Hero секция
    if "hero" in data:
        section = create_hero_section(page.id, data["hero"], position)
        db.add(section)
        position += 1
    
    # Features секция
    if "features" in data:
        section = create_features_section(page.id, data["features"], position)
        db.add(section)
        position += 1
    
    # Document Types секция
    if "document_types" in data:
        section = create_document_types_section(page.id, data["document_types"], position)
        db.add(section)
        position += 1
    
    # UPD Types секция
    if "upd_types" in data:
        section = create_upd_types_section(page.id, data["upd_types"], position)
        db.add(section)
        position += 1
    
    # Pricing секция
    if "pricing" in data:
        section = create_pricing_section(page.id, data["pricing"], position)
        db.add(section)
        position += 1
    
    # About секция
    if "about" in data:
        section = create_about_section(page.id, data["about"], position)
        db.add(section)
        position += 1
    
    # CTA секция
    if "cta" in data:
        section = create_cta_section(page.id, data["cta"], position)
        db.add(section)
        position += 1
    
    # FAQ секция
    if "faq" in data:
        section = create_faq_section(page.id, data["faq"], position)
        db.add(section)
        position += 1
    
    print(f"   └─ Создано секций: {position}")


def create_hero_section(page_id: int, hero_data: dict, position: int) -> PageSection:
    """Создание Hero секции"""
    section = PageSection(
        page_id=page_id,
        section_type="hero",
        position=position,
        background_style="pattern_light",
        css_classes="hero-section"
    )
    
    # Создаём блоки
    blocks = []
    
    # Заголовок
    if "title" in hero_data:
        blocks.append(ContentBlock(
            block_type="heading",
            position=0,
            content={"text": hero_data["title"], "level": 1, "accent": hero_data.get("title_accent")},
            css_classes="hero-title"
        ))
    
    # Подзаголовок
    if "subtitle" in hero_data:
        blocks.append(ContentBlock(
            block_type="paragraph",
            position=1,
            content={"text": hero_data["subtitle"]},
            css_classes="hero-subtitle"
        ))
    
    # Кнопка CTA
    if "cta_text" in hero_data:
        blocks.append(ContentBlock(
            block_type="button",
            position=2,
            content={"text": hero_data["cta_text"], "url": hero_data.get("cta_url", "#")},
            css_classes="hero-cta-btn"
        ))
    
    # Заметка
    if "note" in hero_data:
        blocks.append(ContentBlock(
            block_type="note",
            position=3,
            content={"text": hero_data["note"], "accent": hero_data.get("note_accent")},
            css_classes="hero-note"
        ))
    
    section.blocks = blocks
    return section


def create_features_section(page_id: int, features_data: dict, position: int) -> PageSection:
    """Создание Features секции"""
    section = PageSection(
        page_id=page_id,
        section_type="features",
        position=position,
        background_style="light",
        css_classes="section section-light"
    )
    
    blocks = []
    
    # Заголовок секции
    if "title" in features_data:
        blocks.append(ContentBlock(
            block_type="heading",
            position=0,
            content={"text": features_data["title"], "level": 2},
            css_classes="section-title"
        ))
    
    # Подзаголовок
    if "subtitle" in features_data:
        blocks.append(ContentBlock(
            block_type="paragraph",
            position=1,
            content={"text": features_data["subtitle"]},
            css_classes="section-subtitle"
        ))
    
    # Карточки
    cards = features_data.get("cards", [])
    for idx, card in enumerate(cards):
        blocks.append(ContentBlock(
            block_type="feature_card",
            position=2 + idx,
            content={
                "title": card.get("title"),
                "description": card.get("description"),
                "icon": card.get("icon")
            },
            css_classes="feature-card"
        ))
    
    section.blocks = blocks
    return section


def create_about_section(page_id: int, about_data: dict, position: int) -> PageSection:
    """Создание About секции"""
    section = PageSection(
        page_id=page_id,
        section_type="about",
        position=position,
        background_style="light",
        css_classes="about-section-v12"
    )
    
    blocks = []
    
    # Метка
    if "label" in about_data:
        blocks.append(ContentBlock(
            block_type="label",
            position=0,
            content={"text": about_data["label"]},
            css_classes="about-label-v12"
        ))
    
    # Заголовок
    if "title" in about_data:
        blocks.append(ContentBlock(
            block_type="heading",
            position=1,
            content={"text": about_data["title"], "level": 2, "accent": about_data.get("title_accent")},
            css_classes="about-title-v12"
        ))
    
    # Описание
    if "description" in about_data:
        blocks.append(ContentBlock(
            block_type="paragraph",
            position=2,
            content={"text": about_data["description"]},
            css_classes="about-description"
        ))
    
    # Миссия
    if "mission" in about_data:
        blocks.append(ContentBlock(
            block_type="paragraph",
            position=3,
            content={"text": about_data["mission"]},
            css_classes="about-mission"
        ))
    
    # Статистика
    stats = about_data.get("stats", [])
    for idx, stat in enumerate(stats):
        blocks.append(ContentBlock(
            block_type="stat_card",
            position=4 + idx,
            content={
                "value": stat.get("value"),
                "label": stat.get("label")
            },
            css_classes="about-stat-card"
        ))
    
    section.blocks = blocks
    return section


def create_pricing_section(page_id: int, pricing_data: dict, position: int) -> PageSection:
    """Создание Pricing секции (упрощённая, детали в JSONB)"""
    section = PageSection(
        page_id=page_id,
        section_type="pricing",
        position=position,
        background_style="light",
        css_classes="pricing-section-v12"
    )
    
    # Сохраняем всю структуру тарифов в первом блоке (сложная структура)
    blocks = [
        ContentBlock(
            block_type="pricing_table",
            position=0,
            content=pricing_data,  # Вся структура с планами
            css_classes="pricing-grid-v12"
        )
    ]
    
    section.blocks = blocks
    return section


def create_upd_types_section(page_id: int, upd_data: dict, position: int) -> PageSection:
    """Создание UPD Types секции: один комплексный блок upd_types_grid (редактируется через YAML/Контент)."""
    section = PageSection(
        page_id=page_id,
        section_type="upd_types",
        position=position,
        background_style="pattern_light",
        css_classes="upd-types-section pattern-light"
    )
    blocks = [
        ContentBlock(
            block_type="upd_types_grid",
            position=0,
            content=upd_data,
            css_classes="upd-types-grid"
        )
    ]
    section.blocks = blocks
    return section


def create_document_types_section(page_id: int, doc_data: dict, position: int) -> PageSection:
    """Создание Document Types секции"""
    section = PageSection(
        page_id=page_id,
        section_type="document_types",
        position=position,
        background_style="light",
        css_classes="document-types-section"
    )
    
    blocks = [
        ContentBlock(
            block_type="document_types_grid",
            position=0,
            content=doc_data,
            css_classes="document-types-grid"
        )
    ]
    
    section.blocks = blocks
    return section


def create_cta_section(page_id: int, cta_data: dict, position: int) -> PageSection:
    """Создание CTA секции"""
    section = PageSection(
        page_id=page_id,
        section_type="cta",
        position=position,
        background_style="light",
        css_classes="cta-section-v12"
    )
    
    blocks = []
    
    # Метка
    if "label" in cta_data:
        blocks.append(ContentBlock(
            block_type="label",
            position=0,
            content={"text": cta_data["label"]},
            css_classes="cta-label-v12"
        ))
    
    # Заголовок
    if "title" in cta_data:
        blocks.append(ContentBlock(
            block_type="heading",
            position=1,
            content={"text": cta_data["title"], "level": 2, "accent": cta_data.get("title_accent")},
            css_classes="cta-title-v12"
        ))
    
    # Описание
    if "subtitle" in cta_data:
        blocks.append(ContentBlock(
            block_type="paragraph",
            position=2,
            content={"text": cta_data["subtitle"]},
            css_classes="cta-desc-v12"
        ))
    
    # Кнопка
    if "button_text" in cta_data:
        blocks.append(ContentBlock(
            block_type="button",
            position=3,
            content={"text": cta_data["button_text"], "url": cta_data.get("button_url", "#")},
            css_classes="cta-btn-v12"
        ))
    
    section.blocks = blocks
    return section


def create_faq_section(page_id: int, faq_data: list, position: int) -> PageSection:
    """Создание FAQ секции"""
    section = PageSection(
        page_id=page_id,
        section_type="faq",
        position=position,
        background_style="light",
        css_classes="faq-section"
    )
    
    blocks = []
    for idx, item in enumerate(faq_data):
        blocks.append(ContentBlock(
            block_type="faq_item",
            position=idx,
            content={
                "question": item.get("question"),
                "answer": item.get("answer")
            },
            css_classes="faq-item"
        ))
    
    section.blocks = blocks
    return section


def migrate_all_pages(db: SessionLocal):
    """Миграция всех YAML файлов"""
    if not CONTENT_DIR.exists():
        print(f"❌ Директория контента не найдена: {CONTENT_DIR}")
        return
    
    # Собираем все YAML файлы
    yaml_files = list(CONTENT_DIR.rglob("*.yaml")) + list(CONTENT_DIR.rglob("*.yml"))
    
    # Исключаем служебные файлы
    yaml_files = [f for f in yaml_files if not f.name.startswith("_") and f.name != "navigation.yaml"]
    
    print(f"\n📦 Найдено YAML файлов: {len(yaml_files)}\n")
    
    migrated = 0
    skipped = 0
    errors = 0
    
    for yaml_file in sorted(yaml_files):
        rel_path = yaml_file.relative_to(CONTENT_DIR)
        yaml_path = str(rel_path).replace("\\", "/").replace(".yaml", "").replace(".yml", "")
        
        try:
            page = migrate_page(yaml_path, db)
            if page:
                migrated += 1
            else:
                skipped += 1
        except Exception as e:
            print(f"❌ Ошибка при миграции {yaml_path}: {e}")
            errors += 1
    
    # Сохраняем все изменения
    db.commit()
    
    print(f"\n" + "="*60)
    print(f"✅ Миграция завершена!")
    print(f"   Мигрировано: {migrated}")
    print(f"   Пропущено: {skipped}")
    print(f"   Ошибок: {errors}")
    print(f"="*60 + "\n")
    
    # Проверка сохранения URL
    print("🔍 Проверка сохранения URL...")
    pages = db.query(Page).all()
    for page in pages[:10]:  # Показываем первые 10
        url = f"/{page.slug}/" if page.slug else "/"
        print(f"   {page.legacy_yaml_path:30} → {url}")
    
    if len(pages) > 10:
        print(f"   ...и ещё {len(pages) - 10} страниц")


def migrate_single_page(yaml_path: str, db: SessionLocal):
    """Миграция одной конкретной страницы"""
    print(f"\n📄 Миграция страницы: {yaml_path}\n")
    
    page = migrate_page(yaml_path, db)
    
    if page:
        db.commit()
        url = f"/{page.slug}/" if page.slug else "/"
        print(f"\n✅ Страница успешно мигрирована!")
        print(f"   YAML: {yaml_path}")
        print(f"   Slug: {page.slug}")
        print(f"   URL: {url} (НЕ ИЗМЕНИЛСЯ!)")
        print(f"   Секций: {len(page.sections)}")
        print(f"   Блоков: {sum(len(s.blocks) for s in page.sections)}")
    else:
        print(f"\n❌ Не удалось мигрировать страницу")


def convert_upd_types_section(db: SessionLocal, slug: str = "") -> bool:
    """
    Приводит секцию UPD Types к одному блоку upd_types_grid (данные из home.yaml).
    Вызывать с --convert-upd-types после отката, чтобы вернуть комплексный блок.
    """
    from sqlalchemy.orm import joinedload

    page = db.query(Page).options(joinedload(Page.sections).joinedload(PageSection.blocks)).filter(Page.slug == slug).first()
    if not page:
        print("❌ Страница не найдена")
        return False

    section = next((s for s in page.sections if s.section_type == "upd_types"), None)
    if not section:
        print("❌ Секция UPD Types не найдена")
        return False

    data = load_yaml_file(CONTENT_DIR / "home.yaml") or {}
    upd_data = data.get("upd_types") or {}
    section.blocks = [
        ContentBlock(
            block_type="upd_types_grid",
            position=0,
            content=upd_data,
            css_classes="upd-types-grid"
        )
    ]
    db.commit()
    print("✅ Секция UPD Types: один блок upd_types_grid (данные из home.yaml)")
    return True


def main():
    parser = argparse.ArgumentParser(description="Миграция YAML контента в PostgreSQL")
    parser.add_argument("--page", help="Мигрировать одну страницу (например: home, upd/ooo)")
    parser.add_argument("--section", help="Мигрировать раздел (upd, schet, akt)")
    parser.add_argument("--all", action="store_true", help="Мигрировать все страницы")
    parser.add_argument("--convert-upd-types", action="store_true", help="Конвертировать секцию UPD Types в новый формат (использовать с --page home)")

    args = parser.parse_args()

    db = SessionLocal()

    try:
        if args.convert_upd_types and args.page:
            slug = "" if args.page.strip().lower() == "home" else args.page
            convert_upd_types_section(db, slug)
        elif args.page:
            migrate_single_page(args.page, db)
        elif args.section:
            # Миграция раздела
            yaml_files = list((CONTENT_DIR / args.section).rglob("*.yaml"))
            yaml_files = [f for f in yaml_files if not f.name.startswith("_")]
            
            print(f"\n📦 Миграция раздела: {args.section} ({len(yaml_files)} файлов)\n")
            
            for yaml_file in sorted(yaml_files):
                rel_path = yaml_file.relative_to(CONTENT_DIR)
                yaml_path = str(rel_path).replace("\\", "/").replace(".yaml", "")
                try:
                    migrate_page(yaml_path, db)
                except Exception as e:
                    print(f"❌ Ошибка: {e}")
            
            db.commit()
            print(f"\n✅ Раздел {args.section} мигрирован!")
        elif args.all:
            migrate_all_pages(db)
        else:
            print("❌ Укажите --page, --section или --all")
            parser.print_help()
    finally:
        db.close()


if __name__ == "__main__":
    main()
