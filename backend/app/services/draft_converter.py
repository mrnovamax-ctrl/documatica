"""
Сервис конвертации черновика гостя в готовый документ
"""

import json
import uuid
from pathlib import Path
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.models import GuestDraft, User


# Путь к сохранённым документам
DOCUMENTS_DIR = Path(__file__).parent.parent.parent / "documents"
DOCUMENTS_DIR.mkdir(exist_ok=True)


def convert_draft_to_document(
    draft: GuestDraft,
    user: User,
    db: Session
) -> Optional[str]:
    """
    Конвертирует черновик гостя в готовый документ.
    Возвращает document_id или None при ошибке.
    
    Документ сохраняется в файловую систему (как и другие документы).
    """
    try:
        # Парсим данные из черновика
        document_data = json.loads(draft.document_data)
        
        # Генерируем ID документа
        doc_id = str(uuid.uuid4())
        
        # Создаём папку для документа
        doc_folder = DOCUMENTS_DIR / doc_id
        doc_folder.mkdir(exist_ok=True)
        
        # Определяем тип документа
        doc_type = draft.document_type  # upd, akt, invoice
        
        # Извлекаем данные для метаданных
        document_number = document_data.get('document_number', '-')
        document_date = document_data.get('document_date', datetime.now().strftime('%Y-%m-%d'))
        
        # Продавец и покупатель (разные поля для разных типов документов)
        if doc_type == 'akt':
            # Акт использует executor/customer
            seller = document_data.get('executor', {})
            buyer = document_data.get('customer', {})
        else:
            # УПД и счёт используют seller/buyer
            seller = document_data.get('seller', {})
            buyer = document_data.get('buyer', {})
        
        seller_name = seller.get('name', 'Не указано')
        buyer_name = buyer.get('name', 'Не указано')
        
        # Сумма (разные поля для разных типов документов)
        total_amount = document_data.get('total_amount_with_vat', 0)
        
        # Если суммы нет, считаем из items
        if not total_amount:
            items = document_data.get('items', [])
            for item in items:
                amount = item.get('amount', 0) or item.get('sum_with_vat', 0) or 0
                if isinstance(amount, str):
                    try:
                        amount = float(amount.replace(' ', '').replace(',', '.'))
                    except:
                        amount = 0
                total_amount += float(amount)
        
        if isinstance(total_amount, str):
            try:
                total_amount = float(total_amount)
            except:
                total_amount = 0
        
        # Сохраняем исходные данные формы
        form_data_path = doc_folder / "form_data.json"
        form_data_path.write_text(
            json.dumps(document_data, ensure_ascii=False, indent=2, default=str),
            encoding='utf-8'
        )
        
        # Сохраняем метаданные
        metadata = {
            "id": doc_id,
            "type": doc_type,
            "user_id": user.id,
            "document_number": document_number,
            "document_date": str(document_date),
            "created_at": datetime.now().isoformat(),
            "seller_name": seller_name,
            "buyer_name": buyer_name,
            "total_amount": float(total_amount),
            "status": document_data.get('status', 1),
            "from_draft": True,  # Помечаем что из черновика
            "draft_token": draft.draft_token[:8] + "..."
        }
        
        metadata_path = doc_folder / "metadata.json"
        metadata_path.write_text(
            json.dumps(metadata, ensure_ascii=False, indent=2),
            encoding='utf-8'
        )
        
        # Помечаем черновик как сконвертированный
        draft.is_converted = True
        draft.updated_at = datetime.now()
        db.commit()
        
        print(f"[DRAFT] Converted draft {draft.draft_token[:8]}... to document {doc_id} for user {user.email}")
        
        return doc_id
        
    except Exception as e:
        print(f"[DRAFT] Error converting draft to document: {e}")
        import traceback
        traceback.print_exc()
        return None


def convert_user_drafts_to_documents(user: User, db: Session) -> int:
    """
    Конвертирует все незавершённые черновики пользователя в документы.
    Возвращает количество сконвертированных документов.
    """
    count = 0
    
    # Находим все привязанные но не сконвертированные черновики
    drafts = db.query(GuestDraft).filter(
        GuestDraft.user_id == user.id,
        GuestDraft.is_claimed == True,
        GuestDraft.is_converted == False
    ).all()
    
    for draft in drafts:
        doc_id = convert_draft_to_document(draft, user, db)
        if doc_id:
            count += 1
    
    return count
