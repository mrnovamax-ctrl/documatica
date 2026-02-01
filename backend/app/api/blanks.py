"""
API для скачивания бланков документов (Excel/Word)
Требуется авторизация.
"""

from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Header, Cookie, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.api.auth import get_current_user_optional

router = APIRouter(prefix="/documents/blanks", tags=["blanks"])

# Файлы бланков лежат в static/blanks внутри приложения
BLANKS_DIR = Path(__file__).parent.parent / "static" / "blanks"


@router.get("/{blank_type}")
async def download_blank(
    blank_type: str,
    authorization: Optional[str] = Header(None),
    access_token: Optional[str] = Cookie(None),
    db: Session = Depends(get_db),
):
    """
    Скачивание бланка (Excel/Word).
    Требуется авторизация.
    """
    user = await get_current_user_optional(authorization, access_token, db)
    if not user:
        raise HTTPException(status_code=401, detail="Требуется авторизация для скачивания бланков")

    blank_files = {
        "upd-blank-excel": ("upd-blank-2026.xls", "application/vnd.ms-excel"),
        "upd-blank-word": ("upd-blank-2026.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
        "schet-blank-excel": ("schet-blank-2026.xls", "application/vnd.ms-excel"),
        "akt-blank-excel": ("akt-blank-2026.xls", "application/vnd.ms-excel"),
        "akt-blank-word": ("akt-blank-2026.doc", "application/msword"),
    }

    if blank_type not in blank_files:
        raise HTTPException(status_code=404, detail="Бланк не найден")

    filename, media_type = blank_files[blank_type]
    file_path = BLANKS_DIR / filename
    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Файл бланка не найден: {filename}. Добавьте файл в /static/blanks/.",
        )

    return FileResponse(path=str(file_path), media_type=media_type, filename=filename)

