"""
API для скачивания образцов документов
"""

from fastapi import APIRouter, HTTPException, Header, Cookie, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import Optional
from pathlib import Path
import logging

from app.database import get_db
from app.api.auth import get_current_user_optional

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents/samples", tags=["samples"])

# Путь к директории с образцами
SAMPLES_DIR = Path(__file__).parent.parent / "static" / "samples"


@router.get("/{sample_type}")
async def download_sample(
    sample_type: str,
    authorization: Optional[str] = Header(None),
    access_token: Optional[str] = Cookie(None),
    db: Session = Depends(get_db)
):
    """
    Скачивание образца документа в PDF.
    Требуется авторизация.
    """
    # Проверка авторизации
    user = await get_current_user_optional(authorization, access_token, db)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Требуется авторизация для скачивания образцов"
        )
    
    # Маппинг типов образцов на файлы
    sample_files = {
        "upd-nds": "upd-obrazec-s-nds.pdf",
        "upd-bez-nds": "upd-obrazec-bez-nds.pdf",
        "upd-ip": "upd-obrazec-ip.pdf",
        "schet": "schet-obrazec.pdf",
        "akt": "akt-obrazec.pdf",
    }
    
    if sample_type not in sample_files:
        raise HTTPException(
            status_code=404,
            detail="Образец не найден"
        )
    
    file_path = SAMPLES_DIR / sample_files[sample_type]
    
    # Проверяем существование файла
    if not file_path.exists():
        logger.error(f"Sample file not found: {file_path}")
        raise HTTPException(
            status_code=404,
            detail="Файл образца не найден. Обратитесь в поддержку."
        )
    
    # Логируем скачивание
    logger.info(f"User {user.id} ({user.email}) downloaded sample: {sample_type}")
    
    return FileResponse(
        path=str(file_path),
        media_type="application/pdf",
        filename=sample_files[sample_type]
    )
