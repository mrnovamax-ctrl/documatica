#!/usr/bin/env python3
"""
Скрипт для создания бэкапа PostgreSQL базы данных
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from decimal import Decimal

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal
from app.models import (
    User, INNUsage, Payment, GlobalINNLimit, 
    Promocode, PromocodeUsage, GuestDraft,
    Page, PageSection, ContentBlock, AnalyticsEvent, Document, Redirect
)


def serialize_model(obj):
    """Сериализация модели в dict"""
    result = {}
    for column in obj.__table__.columns:
        value = getattr(obj, column.name)
        if isinstance(value, datetime):
            value = value.isoformat()
        elif isinstance(value, Decimal):
            value = float(value)
        result[column.name] = value
    return result


def backup_database():
    """Создание полного бэкапа БД в JSON"""
    db = SessionLocal()
    
    backup_data = {
        "backup_date": datetime.utcnow().isoformat(),
        "tables": {}
    }
    
    # Список всех моделей для бэкапа
    models = [
        ("users", User),
        ("inn_usage", INNUsage),
        ("payments", Payment),
        ("global_inn_limits", GlobalINNLimit),
        ("promocodes", Promocode),
        ("promocode_usages", PromocodeUsage),
        ("guest_drafts", GuestDraft),
        ("pages", Page),
        ("page_sections", PageSection),
        ("content_blocks", ContentBlock),
        ("analytics_events", AnalyticsEvent),
        ("documents", Document),
        ("redirects", Redirect),
    ]
    
    print("🔄 Создание бэкапа базы данных...\n")
    
    total_records = 0
    for table_name, model in models:
        try:
            records = db.query(model).all()
            backup_data["tables"][table_name] = [serialize_model(r) for r in records]
            count = len(records)
            total_records += count
            print(f"✅ {table_name:25} {count:6} записей")
        except Exception as e:
            print(f"⚠️  {table_name:25} ошибка: {e}")
            backup_data["tables"][table_name] = []
    
    db.close()
    
    # Сохраняем в файл
    backup_dir = Path(__file__).parent.parent.parent / "backups"
    backup_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = backup_dir / f"documatica_full_backup_{timestamp}.json"
    
    with open(backup_file, "w", encoding="utf-8") as f:
        json.dump(backup_data, f, ensure_ascii=False, indent=2)
    
    file_size = backup_file.stat().st_size / 1024 / 1024  # MB
    
    print(f"\n{'='*60}")
    print(f"✅ Бэкап создан успешно!")
    print(f"   Файл: {backup_file}")
    print(f"   Размер: {file_size:.2f} MB")
    print(f"   Всего записей: {total_records}")
    print(f"{'='*60}\n")
    
    return backup_file


if __name__ == "__main__":
    backup_database()
