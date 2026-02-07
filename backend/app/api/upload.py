"""
API endpoints для загрузки файлов (логотипы, печати и т.д.)
"""

import os
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, UploadFile, File, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse

router = APIRouter()


def _require_admin_api(request: Request):
    from app.admin.context import require_admin
    check = require_admin(request)
    if check:
        return JSONResponse({"error": "Unauthorized", "success": 0}, status_code=401)
    return None

# Директория для загрузки файлов (backend/data/uploads)
UPLOAD_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "uploads"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Разрешенные расширения
ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB


@router.post("/upload/tinymce-image")
async def upload_tinymce_image(request: Request, file: UploadFile = File(..., description="file")):
    """Загрузка изображений для TinyMCE. Возвращает { location: url }."""
    auth_err = _require_admin_api(request)
    if auth_err:
        return auth_err
    file_ext = Path(file.filename or "image.png").suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Недопустимый формат. Разрешены: {', '.join(ALLOWED_EXTENSIONS)}")
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="Файл слишком большой. Макс: 5 МБ")
    filename = f"{uuid.uuid4()}{file_ext}"
    file_path = UPLOAD_DIR / filename
    with open(file_path, "wb") as f:
        f.write(contents)
    url = f"/static/uploads/{filename}"
    return {"location": url}


@router.post("/upload/logo")
async def upload_logo(file: UploadFile = File(...)):
    """Загрузка логотипа организации или контрагента"""
    
    # Проверка расширения
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Недопустимый формат файла. Разрешены: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Проверка размера
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail="Файл слишком большой. Максимальный размер: 5 МБ"
        )
    
    # Генерация уникального имени
    filename = f"{uuid.uuid4()}{file_ext}"
    file_path = UPLOAD_DIR / filename
    
    # Сохранение файла
    with open(file_path, "wb") as f:
        f.write(contents)
    
    # Возвращаем URL для доступа к файлу
    return {
        "url": f"/static/uploads/{filename}",
        "filename": filename
    }


@router.get("/uploads/{filename}")
async def get_uploaded_file(filename: str):
    """Получение загруженного файла"""
    file_path = UPLOAD_DIR / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Файл не найден")
    
    return FileResponse(file_path)


@router.delete("/upload/{filename}")
async def delete_uploaded_file(filename: str):
    """Удаление загруженного файла"""
    file_path = UPLOAD_DIR / filename
    
    if file_path.exists():
        file_path.unlink()
        return {"message": "Файл удален"}
    
    raise HTTPException(status_code=404, detail="Файл не найден")
