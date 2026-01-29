"""
API для черновиков документов гостей
Сохраняет документ на сервере до регистрации пользователя
"""

import secrets
import json
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import GuestDraft, User
from app.api.auth import get_current_user_optional

router = APIRouter(prefix="/api/v1/drafts", tags=["drafts"])


# === Схемы ===

class DraftCreate(BaseModel):
    document_type: str  # upd, akt, invoice
    document_data: dict  # Данные документа


class DraftResponse(BaseModel):
    draft_token: str
    document_type: str
    created_at: str
    expires_at: str
    message: str


class DraftClaimRequest(BaseModel):
    draft_token: str


# === Endpoints ===

@router.post("", response_model=DraftResponse)
async def create_draft(
    data: DraftCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Сохранить черновик документа для гостя.
    Возвращает токен для доступа к черновику.
    Черновик хранится 7 дней.
    """
    # Валидация типа документа
    if data.document_type not in ["upd", "akt", "invoice"]:
        raise HTTPException(status_code=400, detail="Неверный тип документа")
    
    # Генерируем уникальный токен
    draft_token = secrets.token_urlsafe(32)
    
    # Получаем IP
    ip_address = request.client.host if request.client else None
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        ip_address = forwarded_for.split(",")[0].strip()
    
    # Срок действия - 7 дней
    expires_at = datetime.utcnow() + timedelta(days=7)
    
    # Создаём черновик
    draft = GuestDraft(
        draft_token=draft_token,
        document_type=data.document_type,
        document_data=json.dumps(data.document_data, ensure_ascii=False),
        ip_address=ip_address,
        expires_at=expires_at
    )
    
    db.add(draft)
    db.commit()
    db.refresh(draft)
    
    return DraftResponse(
        draft_token=draft_token,
        document_type=data.document_type,
        created_at=draft.created_at.isoformat(),
        expires_at=expires_at.isoformat(),
        message="Черновик сохранён"
    )


@router.get("/{draft_token}")
async def get_draft(
    draft_token: str,
    db: Session = Depends(get_db)
):
    """Получить черновик по токену"""
    draft = db.query(GuestDraft).filter(
        GuestDraft.draft_token == draft_token
    ).first()
    
    if not draft:
        raise HTTPException(status_code=404, detail="Черновик не найден")
    
    # Проверяем срок действия
    if draft.expires_at and draft.expires_at < datetime.utcnow():
        raise HTTPException(status_code=410, detail="Срок действия черновика истёк")
    
    return {
        "draft_token": draft.draft_token,
        "document_type": draft.document_type,
        "document_data": json.loads(draft.document_data),
        "is_claimed": draft.is_claimed,
        "created_at": draft.created_at.isoformat(),
        "expires_at": draft.expires_at.isoformat() if draft.expires_at else None
    }


@router.post("/claim")
async def claim_draft(
    data: DraftClaimRequest,
    current_user: User = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Привязать черновик к авторизованному пользователю и конвертировать в документ.
    Вызывается после регистрации/входа.
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Требуется авторизация")
    
    draft = db.query(GuestDraft).filter(
        GuestDraft.draft_token == data.draft_token
    ).first()
    
    if not draft:
        raise HTTPException(status_code=404, detail="Черновик не найден")
    
    if draft.is_claimed:
        raise HTTPException(status_code=400, detail="Черновик уже привязан")
    
    # Привязываем к пользователю
    draft.user_id = current_user.id
    draft.is_claimed = True
    draft.updated_at = datetime.utcnow()
    db.commit()
    
    # Конвертируем в документ
    from app.services.draft_converter import convert_draft_to_document
    doc_id = convert_draft_to_document(draft, current_user, db)
    
    return {
        "success": True,
        "message": "Документ создан в личном кабинете",
        "document_id": doc_id,
        "document_data": json.loads(draft.document_data)
    }


@router.put("/{draft_token}")
async def update_draft(
    draft_token: str,
    data: DraftCreate,
    db: Session = Depends(get_db)
):
    """Обновить данные черновика"""
    draft = db.query(GuestDraft).filter(
        GuestDraft.draft_token == draft_token
    ).first()
    
    if not draft:
        raise HTTPException(status_code=404, detail="Черновик не найден")
    
    if draft.expires_at and draft.expires_at < datetime.utcnow():
        raise HTTPException(status_code=410, detail="Срок действия черновика истёк")
    
    draft.document_data = json.dumps(data.document_data, ensure_ascii=False)
    draft.updated_at = datetime.utcnow()
    
    db.commit()
    
    return {
        "success": True,
        "message": "Черновик обновлён",
        "draft_token": draft_token
    }
