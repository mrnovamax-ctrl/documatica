"""
API endpoints для работы с документами
"""

import base64
import io
import json
import os
from pathlib import Path
from datetime import datetime
import uuid
from typing import Optional

from fastapi import APIRouter, HTTPException, Header, Cookie, Request, Depends
from fastapi.responses import StreamingResponse, JSONResponse, HTMLResponse
from jinja2 import Environment, FileSystemLoader
import jwt
from sqlalchemy.orm import Session

# Попытка импорта WeasyPrint (может не работать на Windows без GTK)
try:
    from weasyprint import HTML as WeasyHTML
    WEASYPRINT_AVAILABLE = True
except OSError:
    WEASYPRINT_AVAILABLE = False
    print("WeasyPrint не доступен (требуется GTK3). Будет возвращаться HTML для печати.")

from app.schemas.upd import UPDRequest, UPDResponse, UPDPreviewRequest
from app.database import get_db
from app.models import User
from app.services.billing import BillingService

router = APIRouter()

# Настройки JWT (должны совпадать с auth.py)
SECRET_KEY = os.getenv("SECRET_KEY", "documatica-secret-key-change-in-production")
ALGORITHM = "HS256"

# Путь к шаблонам и сохранённым документам
TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
DOCUMENTS_DIR = Path(__file__).parent.parent.parent / "documents"
DOCUMENTS_DIR.mkdir(exist_ok=True)

# Настройка Jinja2
jinja_env = Environment(
    loader=FileSystemLoader(TEMPLATES_DIR),
    autoescape=True
)


def get_user_id_from_token(authorization: Optional[str] = None, cookie_token: Optional[str] = None) -> Optional[int]:
    """Извлекает user_id из JWT токена (Header или Cookie). Возвращает None если токен отсутствует или невалиден."""
    token = None
    
    # Сначала пробуем Header Authorization
    if authorization and authorization.startswith("Bearer "):
        token = authorization.replace("Bearer ", "")
    # Если нет Header, берём из cookie
    elif cookie_token:
        token = cookie_token
    
    if not token:
        return None
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return int(payload.get("sub"))
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, ValueError):
        return None


def format_date(date_obj) -> str:
    """Форматирование даты в русский формат"""
    if date_obj is None:
        return ""
    if isinstance(date_obj, str):
        return date_obj
    months = [
        "января", "февраля", "марта", "апреля", "мая", "июня",
        "июля", "августа", "сентября", "октября", "ноября", "декабря"
    ]
    return f"{date_obj.day} {months[date_obj.month - 1]} {date_obj.year} г."


def format_date_short(date_obj) -> str:
    """Форматирование даты в короткий формат DD.MM.YYYY"""
    if date_obj is None:
        return ""
    if isinstance(date_obj, str):
        return date_obj
    return date_obj.strftime("%d.%m.%Y")


@router.get("/upd/demo")
async def demo_upd():
    """
    Демо-превью УПД - возвращает HTML для главной страницы с тем же шаблоном что и preview
    """
    try:
        template = jinja_env.get_template("upd_template.html")
        
        # Демо-данные
        template_data = {
            "document_number": "125",
            "document_date": "18.01.2026",
            "correction_number": None,
            "correction_date": None,
            "status": "1",
            
            "seller": {
                "name": "ООО \"Ромашка\"",
                "inn": "7712345678",
                "kpp": "771201001",
                "address": "123456, г. Москва, ул. Примерная, д. 1, оф. 101"
            },
            
            "buyer": {
                "name": "ООО \"Василек\"",
                "inn": "7845678901",
                "kpp": "784501001",
                "address": "654321, г. СПб, пр. Невский, 100"
            },
            
            "consignor": "он же",
            "consignee": "ООО \"Василек\", г. СПб, пр. Невский, 100",
            
            "items": [
                {
                    "name": "Консультационные услуги по ведению бухгалтерского учета",
                    "unit": "796",
                    "unit_name": "шт",
                    "quantity": 20,
                    "price": 50000.00,
                    "amount_without_vat": 50000.00,
                    "vat_rate": "Без налога",
                    "vat_amount": 0,
                    "amount_with_vat": 50000.00,
                    "country_code": "",
                    "country_name": "",
                    "customs_declaration": ""
                },
                {
                    "name": "Подготовка налоговой отчетности за квартал",
                    "unit": "796",
                    "unit_name": "шт",
                    "quantity": 1,
                    "price": 25000.00,
                    "amount_without_vat": 25000.00,
                    "vat_rate": "20%",
                    "vat_amount": 5000.00,
                    "amount_with_vat": 30000.00,
                    "country_code": "",
                    "country_name": "",
                    "customs_declaration": ""
                }
            ],
            
            "total_amount_without_vat": 75000.00,
            "total_vat_amount": 5000.00,
            "total_amount_with_vat": 80000.00,
            
            "currency_code": "643",
            "currency_name": "Российский рубль",
            "government_contract_id": "",
            "payment_document": "№ 1-2 №125 от 18.01.2026",
            "shipping_document": "Накладная",
            "contract_info": "Договор № 15 от 01.01.2026",
            "transport_info": "",
            
            "shipping_date": "18.01.2026",
            "other_shipping_info": "",
            "seller_signer": {
                "title": "Директор",
                "name": "Иванов И.И."
            },
            "seller_responsible": None,
            "economic_entity": "ООО \"Ромашка\"",
            
            "receiving_date": "18.01.2026",
            "other_receiving_info": "",
            "buyer_signer": {
                "title": "Менеджер",
                "name": "Сидоров С.С."
            },
            "buyer_responsible": None,
            "buyer_economic_entity": "ООО \"Василек\""
        }
        
        html_content = template.render(**template_data)
        return HTMLResponse(content=html_content)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка демо-превью: {str(e)}"
        )


@router.post("/upd/generate", response_model=UPDResponse)
async def generate_upd(request: UPDRequest, return_base64: bool = False):
    """
    Генерация УПД (Универсальный Передаточный Документ) в формате PDF
    
    - **return_base64**: Если True, возвращает PDF как base64 в JSON ответе
    """
    try:
        # Загружаем шаблон
        template = jinja_env.get_template("upd_template.html")
        
        # Подготовка данных для шаблона
        template_data = {
            # Основные реквизиты
            "document_number": request.document_number,
            "document_date": format_date_short(request.document_date),
            "correction_number": request.correction_number,
            "correction_date": format_date_short(request.correction_date) if request.correction_date else None,
            "status": request.status,
            
            # Продавец
            "seller": request.seller.model_dump(),
            
            # Покупатель
            "buyer": request.buyer.model_dump(),
            
            # Грузоотправитель/грузополучатель (теперь строки)
            "consignor": request.consignor,
            "consignee": request.consignee,
            
            # Товары/услуги (конвертируем Decimal в float для Jinja2)
            "items": [
                {
                    **item.model_dump(),
                    "quantity": float(item.quantity),
                    "price": float(item.price),
                    "amount_without_vat": float(item.amount_without_vat),
                    "vat_amount": float(item.vat_amount),
                    "amount_with_vat": float(item.amount_with_vat),
                }
                for item in request.items
            ],
            
            # Итоги
            "total_amount_without_vat": float(request.total_amount_without_vat),
            "total_vat_amount": float(request.total_vat_amount),
            "total_amount_with_vat": float(request.total_amount_with_vat),
            
            # Дополнительные сведения
            "currency_code": request.currency_code,
            "currency_name": request.currency_name,
            "government_contract_id": request.gov_contract_id,
            "payment_document": request.payment_document,
            "shipping_document": request.shipping_document,
            "contract_info": request.contract_info,
            "transport_info": request.transport_info,
            
            # Подписант продавца
            "shipping_date": format_date_short(request.shipping_date) if request.shipping_date else None,
            "other_shipping_info": request.other_shipping_info,
            "seller_signer": request.seller_signer.model_dump() if request.seller_signer else None,
            "seller_responsible": request.seller_responsible.model_dump() if request.seller_responsible else None,
            "economic_entity": request.economic_entity,
            "seller_stamp_image": request.seller_stamp_image,
            
            # Подписант покупателя
            "receiving_date": format_date_short(request.receiving_date) if request.receiving_date else None,
            "other_receiving_info": request.other_receiving_info,
            "buyer_signer": request.buyer_signer.model_dump() if request.buyer_signer else None,
            "buyer_responsible": request.buyer_responsible.model_dump() if request.buyer_responsible else None,
            "buyer_economic_entity": request.buyer_economic_entity,
        }
        
        # Рендерим HTML
        html_content = template.render(**template_data)
        
        # Формируем имя файла
        filename = f"UPD_{request.document_number}_{request.document_date.strftime('%Y%m%d')}"
        
        # Если WeasyPrint доступен - генерируем PDF
        if WEASYPRINT_AVAILABLE:
            pdf_buffer = io.BytesIO()
            WeasyHTML(string=html_content).write_pdf(pdf_buffer)
            pdf_buffer.seek(0)
            
            if return_base64:
                pdf_base64 = base64.b64encode(pdf_buffer.read()).decode('utf-8')
                return UPDResponse(
                    success=True,
                    message="УПД успешно сгенерирован",
                    document_number=request.document_number,
                    filename=filename + ".pdf",
                    pdf_base64=pdf_base64
                )
            else:
                from urllib.parse import quote
                filename_encoded = quote(filename + ".pdf")
                return StreamingResponse(
                    pdf_buffer,
                    media_type="application/pdf",
                    headers={
                        "Content-Disposition": f"attachment; filename*=UTF-8''{filename_encoded}"
                    }
                )
        else:
            # Без WeasyPrint возвращаем чистый HTML
            from urllib.parse import quote
            filename_encoded = quote(filename + ".html")
            return HTMLResponse(
                content=html_content,
                headers={
                    "Content-Disposition": f"inline; filename*=UTF-8''{filename_encoded}"
                }
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка генерации УПД: {str(e)}"
        )


@router.post("/upd/preview")
async def preview_upd(request: UPDPreviewRequest):
    """
    Предпросмотр УПД - возвращает HTML (для отладки)
    """
    try:
        template = jinja_env.get_template("upd_template.html")
        
        # Подготовка данных с безопасными значениями по умолчанию
        seller_data = request.seller.model_dump() if request.seller else {"name": "", "inn": "", "kpp": "", "address": ""}
        buyer_data = request.buyer.model_dump() if request.buyer else {"name": "", "inn": "", "kpp": "", "address": ""}
        
        items_data = []
        if request.items:
            for item in request.items:
                items_data.append({
                    **item.model_dump(),
                    "quantity": float(item.quantity or 0),
                    "price": float(item.price or 0),
                    "amount_without_vat": float(item.amount_without_vat or 0),
                    "vat_amount": float(item.vat_amount or 0),
                    "amount_with_vat": float(item.amount_with_vat or 0),
                })
        
        template_data = {
            "document_number": request.document_number or "1",
            "document_date": format_date_short(request.document_date) if request.document_date else "",
            "correction_number": request.correction_number,
            "correction_date": format_date_short(request.correction_date) if request.correction_date else None,
            "status": request.status or 1,
            "seller": seller_data,
            "buyer": buyer_data,
            "consignor": request.consignor,
            "consignee": request.consignee,
            "items": items_data,
            "total_amount_without_vat": float(request.total_amount_without_vat or 0),
            "total_vat_amount": float(request.total_vat_amount or 0),
            "total_amount_with_vat": float(request.total_amount_with_vat or 0),
            "currency_code": request.currency_code or "643",
            "currency_name": request.currency_name or "Российский рубль",
            "payment_document": request.payment_document,
            "contract_info": request.contract_info,
            "transport_info": request.transport_info,
            "government_contract_id": request.gov_contract_id,
            "shipping_date": format_date_short(request.shipping_date) if request.shipping_date else None,
            "other_shipping_info": request.other_shipping_info,
            "seller_signer": request.seller_signer.model_dump() if request.seller_signer else None,
            "seller_responsible": request.seller_responsible.model_dump() if request.seller_responsible else None,
            "economic_entity": request.economic_entity,
            "seller_stamp_image": request.seller_stamp_image,
            "accountant_name": request.accountant_name,
            "accountant_signature": request.accountant_signature,
            "receiving_date": format_date_short(request.receiving_date) if request.receiving_date else None,
            "other_receiving_info": request.other_receiving_info,
            "buyer_signer": request.buyer_signer.model_dump() if request.buyer_signer else None,
            "buyer_responsible": request.buyer_responsible.model_dump() if request.buyer_responsible else None,
            "buyer_economic_entity": request.buyer_economic_entity,
        }
        
        html_content = template.render(**template_data)
        
        return StreamingResponse(
            io.BytesIO(html_content.encode('utf-8')),
            media_type="text/html; charset=utf-8"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка предпросмотра: {str(e)}"
        )


@router.get("/templates")
async def list_templates():
    """Список доступных шаблонов документов"""
    return {
        "templates": [
            {
                "id": "upd",
                "name": "УПД (Универсальный передаточный документ)",
                "description": "Счёт-фактура и передаточный документ по форме ПП РФ № 1137",
                "endpoint": "/api/v1/documents/upd/generate"
            }
        ]
    }


@router.post("/upd/save")
async def save_upd(
    request: UPDRequest,
    authorization: Optional[str] = Header(None),
    access_token: Optional[str] = Cookie(None),
    db: Session = Depends(get_db)
):
    """
    Сохранение УПД в личном кабинете.
    Проверяет лимиты пользователя и списывает генерацию.
    """
    try:
        # Получаем user_id из токена (может быть None для неавторизованных)
        user_id = get_user_id_from_token(authorization, access_token)
        
        # Если пользователь авторизован - проверяем и списываем лимит
        if user_id:
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                billing = BillingService(db)
                seller_inn = request.seller.inn if request.seller else None
                
                # Проверяем возможность генерации
                check = billing.check_can_generate(user, seller_inn)
                if not check["can_generate"]:
                    return JSONResponse(
                        status_code=402,  # Payment Required
                        content={
                            "success": False,
                            "error": "limit_exceeded",
                            "message": check["message"],
                            "limits": check["limits"]
                        }
                    )
                
                # Списываем генерацию
                success, source = billing.consume_generation(user, seller_inn)
                if not success:
                    return JSONResponse(
                        status_code=402,
                        content={
                            "success": False,
                            "error": source,
                            "message": "Не удалось списать генерацию"
                        }
                    )
        
        # Генерируем уникальный ID документа
        doc_id = str(uuid.uuid4())
        
        # Создаём папку для документа
        doc_folder = DOCUMENTS_DIR / doc_id
        doc_folder.mkdir(exist_ok=True)
        
        # Генерируем HTML
        template = jinja_env.get_template("upd_template.html")
        template_data = {
            "document_number": request.document_number,
            "document_date": format_date_short(request.document_date),
            "correction_number": request.correction_number,
            "correction_date": format_date_short(request.correction_date) if request.correction_date else None,
            "status": request.status,
            "seller": request.seller.model_dump(),
            "buyer": request.buyer.model_dump(),
            "consignor": request.consignor,
            "consignee": request.consignee,
            "items": [
                {
                    **item.model_dump(),
                    "quantity": float(item.quantity),
                    "price": float(item.price),
                    "amount_without_vat": float(item.amount_without_vat),
                    "vat_amount": float(item.vat_amount),
                    "amount_with_vat": float(item.amount_with_vat),
                }
                for item in request.items
            ],
            "total_amount_without_vat": float(request.total_amount_without_vat),
            "total_vat_amount": float(request.total_vat_amount),
            "total_amount_with_vat": float(request.total_amount_with_vat),
            "currency_code": request.currency_code,
            "currency_name": request.currency_name,
            "payment_document": request.payment_document,
            "contract_info": request.contract_info,
            "transport_info": request.transport_info,
            "government_contract_id": request.gov_contract_id,
            "transfer_date": format_date_short(request.shipping_date) if request.shipping_date else None,
            "transfer_basis": request.contract_info,
            "seller_signer": request.seller_signer.model_dump() if request.seller_signer else None,
            "seller_stamp_image": getattr(request, 'seller_stamp_image', None),
            "buyer_signer": request.buyer_signer.model_dump() if request.buyer_signer else None,
            "additional_info": request.other_shipping_info,
            "receipt_date": format_date_short(request.receiving_date) if request.receiving_date else None,
            "responsible_person": None,
        }
        
        html_content = template.render(**template_data)
        
        # Сохраняем HTML
        html_path = doc_folder / "document.html"
        html_path.write_text(html_content, encoding='utf-8')
        
        # Сохраняем исходные данные формы для редактирования
        form_data = request.model_dump(mode='json')
        form_data_path = doc_folder / "form_data.json"
        form_data_path.write_text(json.dumps(form_data, ensure_ascii=False, indent=2, default=str), encoding='utf-8')
        
        # Сохраняем метаданные
        metadata = {
            "id": doc_id,
            "type": "upd",
            "user_id": user_id,  # Привязка к пользователю
            "document_number": request.document_number,
            "document_date": str(request.document_date),
            "created_at": datetime.now().isoformat(),
            "seller_name": request.seller.name,
            "buyer_name": request.buyer.name,
            "total_amount": float(request.total_amount_with_vat),
            "status": request.status
        }
        
        metadata_path = doc_folder / "metadata.json"
        metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding='utf-8')
        
        return {
            "success": True,
            "message": "Документ успешно сохранён",
            "document_id": doc_id,
            "document_number": request.document_number
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка сохранения документа: {str(e)}"
        )


@router.get("/")
@router.get("/saved")
async def list_saved_documents(
    authorization: Optional[str] = Header(None),
    access_token: Optional[str] = Cookie(None)
):
    """
    Получение списка сохранённых документов текущего пользователя
    """
    try:
        # Получаем user_id из токена (Header или Cookie)
        user_id = get_user_id_from_token(authorization, access_token)
        
        if user_id is None:
            # Неавторизованный пользователь - возвращаем пустой список
            return {
                "success": True,
                "documents": [],
                "count": 0
            }
        
        documents = []
        
        for doc_folder in DOCUMENTS_DIR.iterdir():
            if doc_folder.is_dir():
                metadata_path = doc_folder / "metadata.json"
                if metadata_path.exists():
                    metadata = json.loads(metadata_path.read_text(encoding='utf-8'))
                    # Фильтруем по user_id
                    if metadata.get('user_id') == user_id:
                        documents.append(metadata)
        
        # Сортируем по дате создания (новые первые)
        documents.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        return {
            "success": True,
            "documents": documents,
            "count": len(documents)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка получения списка документов: {str(e)}"
        )


@router.get("/saved/{document_id}")
async def get_saved_document(document_id: str):
    """
    Получение сохранённого документа по ID (метаданные)
    """
    try:
        doc_folder = DOCUMENTS_DIR / document_id
        
        if not doc_folder.exists():
            raise HTTPException(status_code=404, detail="Документ не найден")
        
        metadata_path = doc_folder / "metadata.json"
        if not metadata_path.exists():
            raise HTTPException(status_code=404, detail="Метаданные документа не найдены")
        
        metadata = json.loads(metadata_path.read_text(encoding='utf-8'))
        return metadata
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка получения документа: {str(e)}"
        )


@router.get("/saved/{document_id}/form-data")
async def get_saved_document_form_data(document_id: str):
    """
    Получение исходных данных формы для редактирования
    """
    try:
        doc_folder = DOCUMENTS_DIR / document_id
        
        if not doc_folder.exists():
            raise HTTPException(status_code=404, detail="Документ не найден")
        
        form_data_path = doc_folder / "form_data.json"
        if not form_data_path.exists():
            raise HTTPException(status_code=404, detail="Данные формы не найдены (документ создан до обновления)")
        
        form_data = json.loads(form_data_path.read_text(encoding='utf-8'))
        return form_data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка получения данных формы: {str(e)}"
        )


@router.get("/saved/{document_id}/html")
async def get_saved_document_html(document_id: str):
    """
    Получение HTML сохранённого документа
    """
    try:
        doc_folder = DOCUMENTS_DIR / document_id
        
        if not doc_folder.exists():
            raise HTTPException(status_code=404, detail="Документ не найден")
        
        html_path = doc_folder / "document.html"
        if not html_path.exists():
            raise HTTPException(status_code=404, detail="Файл документа не найден")
        
        html_content = html_path.read_text(encoding='utf-8')
        
        return HTMLResponse(content=html_content)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка получения документа: {str(e)}"
        )


@router.get("/saved/{document_id}/pdf")
async def get_saved_document_pdf(document_id: str):
    """
    Скачивание PDF сохранённого документа
    """
    try:
        doc_folder = DOCUMENTS_DIR / document_id
        
        if not doc_folder.exists():
            raise HTTPException(status_code=404, detail="Документ не найден")
        
        html_path = doc_folder / "document.html"
        if not html_path.exists():
            raise HTTPException(status_code=404, detail="Файл документа не найден")
        
        html_content = html_path.read_text(encoding='utf-8')
        
        # Получаем метаданные для имени файла
        metadata_path = doc_folder / "metadata.json"
        filename = f"UPD_{document_id[:8]}"
        if metadata_path.exists():
            metadata = json.loads(metadata_path.read_text(encoding='utf-8'))
            doc_num = metadata.get('document_number', '')
            doc_date = metadata.get('document_date', '').replace('-', '')
            if doc_num and doc_date:
                filename = f"UPD_{doc_num}_{doc_date}"
        
        # Если WeasyPrint доступен - генерируем PDF
        if WEASYPRINT_AVAILABLE:
            pdf_buffer = io.BytesIO()
            WeasyHTML(string=html_content).write_pdf(pdf_buffer)
            pdf_buffer.seek(0)
            
            return StreamingResponse(
                pdf_buffer,
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f'attachment; filename="{filename}.pdf"'
                }
            )
        else:
            # Без WeasyPrint возвращаем HTML
            return HTMLResponse(
                content=html_content,
                headers={
                    "Content-Disposition": f'inline; filename="{filename}.html"'
                }
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка генерации PDF: {str(e)}"
        )


@router.delete("/saved/{document_id}")
async def delete_saved_document(document_id: str):
    """
    Удаление сохранённого документа
    """
    try:
        doc_folder = DOCUMENTS_DIR / document_id
        
        if not doc_folder.exists():
            raise HTTPException(status_code=404, detail="Документ не найден")
        
        import shutil
        shutil.rmtree(doc_folder)
        
        return {
            "success": True,
            "message": "Документ успешно удалён"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка удаления документа: {str(e)}"
        )


# ===== СЧЁТ НА ОПЛАТУ API =====

def number_to_words_ru(number: float) -> str:
    """Преобразует число в текст (сумма прописью)"""
    units = ['', 'один', 'два', 'три', 'четыре', 'пять', 'шесть', 'семь', 'восемь', 'девять']
    units_f = ['', 'одна', 'две', 'три', 'четыре', 'пять', 'шесть', 'семь', 'восемь', 'девять']
    teens = ['десять', 'одиннадцать', 'двенадцать', 'тринадцать', 'четырнадцать', 
             'пятнадцать', 'шестнадцать', 'семнадцать', 'восемнадцать', 'девятнадцать']
    tens = ['', '', 'двадцать', 'тридцать', 'сорок', 'пятьдесят', 
            'шестьдесят', 'семьдесят', 'восемьдесят', 'девяносто']
    hundreds = ['', 'сто', 'двести', 'триста', 'четыреста', 
                'пятьсот', 'шестьсот', 'семьсот', 'восемьсот', 'девятьсот']
    
    def get_form(n, forms):
        """Выбор формы слова по числительному: рубль/рубля/рублей"""
        n = abs(n) % 100
        if 11 <= n <= 19:
            return forms[2]
        n = n % 10
        if n == 1:
            return forms[0]
        if 2 <= n <= 4:
            return forms[1]
        return forms[2]
    
    def convert_group(n, feminine=False):
        """Конвертация трёхзначной группы"""
        if n == 0:
            return ''
        result = []
        
        h = n // 100
        if h > 0:
            result.append(hundreds[h])
        
        d = (n % 100) // 10
        u = n % 10
        
        if d == 1:
            result.append(teens[u])
        else:
            if d > 0:
                result.append(tens[d])
            if u > 0:
                result.append(units_f[u] if feminine else units[u])
        
        return ' '.join(result)
    
    if number == 0:
        return 'ноль рублей 00 копеек'
    
    rubles = int(number)
    kopeks = round((number - rubles) * 100)
    
    if rubles == 0:
        rubles_text = 'ноль'
    else:
        parts = []
        
        # Миллионы
        millions = (rubles // 1000000) % 1000
        if millions > 0:
            parts.append(convert_group(millions, False))
            parts.append(get_form(millions, ['миллион', 'миллиона', 'миллионов']))
        
        # Тысячи (женский род)
        thousands = (rubles // 1000) % 1000
        if thousands > 0:
            parts.append(convert_group(thousands, True))
            parts.append(get_form(thousands, ['тысяча', 'тысячи', 'тысяч']))
        
        # Единицы
        remainder = rubles % 1000
        if remainder > 0 or not parts:
            parts.append(convert_group(remainder, False))
        
        rubles_text = ' '.join(parts)
    
    rubles_form = get_form(rubles, ['рубль', 'рубля', 'рублей'])
    kopeks_form = get_form(kopeks, ['копейка', 'копейки', 'копеек'])
    
    return f'{rubles_text} {rubles_form} {kopeks:02d} {kopeks_form}'.strip()


@router.post("/invoice/preview")
async def invoice_preview(request: dict):
    """
    Предпросмотр счёта на оплату - возвращает HTML
    """
    try:
        template = jinja_env.get_template("invoice_template.html")
        
        # Подготовка данных для шаблона (поддержка обоих форматов)
        total_with_vat = float(request.get('total_amount_with_vat', request.get('total_with_vat', 0)))
        total_without_vat = float(request.get('total_amount_without_vat', request.get('total_without_vat', 0)))
        total_vat = float(request.get('total_vat_amount', request.get('vat_amount', 0)))
        
        # Получаем supplier и buyer (поддержка разных названий)
        supplier = request.get('supplier', {})
        buyer = request.get('buyer', request.get('client', {}))
        bank = request.get('bank', {})
        signers = request.get('signers', {})
        
        template_data = {
            "invoice_number": request.get('document_number', request.get('invoice_number', '')),
            "invoice_date": request.get('document_date', request.get('invoice_date', '')),
            "contract_info": request.get('contract_info', ''),
            "payment_due": request.get('payment_due'),
            "invoice_note": request.get('invoice_note', ''),
            "supplier": supplier,
            "bank": bank,
            "signers": signers,
            "client": buyer,
            "items": request.get('items', []),
            "vat_rate": request.get('vat_rate', 'Без НДС'),
            "vat_amount": total_vat,
            "total_without_vat": total_without_vat,
            "total_with_vat": total_with_vat,
            "amount_in_words": number_to_words_ru(total_with_vat).capitalize(),
        }
        
        html_content = template.render(**template_data)
        return HTMLResponse(content=html_content)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка генерации предпросмотра: {str(e)}"
        )


@router.post("/invoice/generate")
async def generate_invoice(
    request: dict,
    authorization: Optional[str] = Header(None),
    access_token: Optional[str] = Cookie(None),
    db: Session = Depends(get_db)
):
    """
    Генерация счёта на оплату и сохранение в системе
    """
    try:
        # Получаем user_id из токена
        user_id = get_user_id_from_token(authorization, access_token)
        
        # Если пользователь авторизован - проверяем и списываем лимит
        if user_id:
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                billing = BillingService(db)
                supplier_inn = request.get('supplier', {}).get('inn')
                
                # Проверяем возможность генерации
                check = billing.check_can_generate(user, supplier_inn)
                if not check["can_generate"]:
                    return JSONResponse(
                        status_code=402,  # Payment Required
                        content={
                            "success": False,
                            "error": "limit_exceeded",
                            "message": check["message"],
                            "limits": check["limits"]
                        }
                    )
                
                # Списываем генерацию
                success, source = billing.consume_generation(user, supplier_inn)
                if not success:
                    return JSONResponse(
                        status_code=402,
                        content={
                            "success": False,
                            "error": source,
                            "message": "Не удалось списать генерацию"
                        }
                    )
        
        # Загружаем шаблон
        template = jinja_env.get_template("invoice_template.html")
        
        # Подготовка данных (поддержка обоих форматов полей)
        total_with_vat = float(request.get('total_amount_with_vat', request.get('total_with_vat', 0)))
        total_without_vat = float(request.get('total_amount_without_vat', request.get('total_without_vat', 0)))
        total_vat = float(request.get('total_vat_amount', request.get('vat_amount', 0)))
        
        supplier = request.get('supplier', {})
        buyer = request.get('buyer', request.get('client', {}))
        bank = request.get('bank', {})
        signers = request.get('signers', {})
        
        template_data = {
            "invoice_number": request.get('document_number', request.get('invoice_number', '')),
            "invoice_date": request.get('document_date', request.get('invoice_date', '')),
            "contract_info": request.get('contract_info', ''),
            "payment_due": request.get('payment_due'),
            "invoice_note": request.get('invoice_note', ''),
            "supplier": supplier,
            "bank": bank,
            "signers": signers,
            "client": buyer,
            "items": request.get('items', []),
            "vat_rate": request.get('vat_rate', 'Без НДС'),
            "vat_amount": total_vat,
            "total_without_vat": total_without_vat,
            "total_with_vat": total_with_vat,
            "amount_in_words": number_to_words_ru(total_with_vat).capitalize(),
        }
        
        # Рендерим HTML
        html_content = template.render(**template_data)
        
        # Формируем имя файла
        doc_number = request.get('document_number', request.get('invoice_number', '1'))
        doc_date = request.get('document_date', request.get('invoice_date', ''))
        filename = f"Schet_{doc_number}_{doc_date.replace('.', '').replace('-', '')}"
        
        # Создаём папку для документа
        document_id = str(uuid.uuid4())
        doc_folder = DOCUMENTS_DIR / document_id
        doc_folder.mkdir(exist_ok=True)
        
        # Сохраняем HTML
        html_path = doc_folder / "document.html"
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        
        # Сохраняем данные формы для редактирования
        form_data_path = doc_folder / "form_data.json"
        with open(form_data_path, "w", encoding="utf-8") as f:
            json.dump(request, f, ensure_ascii=False, indent=2)
        
        # Сохраняем метаданные (как в УПД)
        metadata = {
            "id": document_id,
            "type": "invoice",
            "user_id": user_id,
            "document_number": doc_number,
            "document_date": doc_date,
            "created_at": datetime.now().isoformat(),
            "seller_name": supplier.get('name', ''),
            "buyer_name": buyer.get('name', ''),
            "total_amount": total_with_vat,
        }
        
        metadata_path = doc_folder / "metadata.json"
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        # Генерируем PDF если доступен WeasyPrint
        if WEASYPRINT_AVAILABLE:
            pdf_path = doc_folder / "document.pdf"
            WeasyHTML(string=html_content).write_pdf(str(pdf_path))
            
            # Возвращаем PDF напрямую
            pdf_buffer = io.BytesIO()
            WeasyHTML(string=html_content).write_pdf(pdf_buffer)
            pdf_buffer.seek(0)
            
            from urllib.parse import quote
            filename_encoded = quote(filename + ".pdf")
            return StreamingResponse(
                pdf_buffer,
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f"attachment; filename*=UTF-8''{filename_encoded}"
                }
            )
        else:
            # Без WeasyPrint возвращаем чистый HTML для печати
            from urllib.parse import quote
            filename_encoded = quote(filename + ".html")
            return HTMLResponse(
                content=html_content,
                headers={
                    "Content-Disposition": f"inline; filename*=UTF-8''{filename_encoded}"
                }
            )
        
    except Exception as e:
        import traceback
        print(f"Invoice generate error: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка генерации счёта: {str(e)}"
        )


@router.get("/invoice/{document_id}/pdf")
async def download_invoice_pdf(document_id: str):
    """
    Скачивание PDF счёта
    """
    try:
        doc_folder = DOCUMENTS_DIR / document_id
        
        if not doc_folder.exists():
            raise HTTPException(status_code=404, detail="Документ не найден")
        
        # Читаем metadata.json
        meta_path = doc_folder / "metadata.json"
        if meta_path.exists():
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
        else:
            meta = {}
        
        invoice_number = meta.get('document_number', document_id)
        invoice_date = meta.get('document_date', '')
        filename = f"Schet_{invoice_number}_{invoice_date.replace('.', '')}"
        
        # Проверяем PDF
        pdf_path = doc_folder / "document.pdf"
        if pdf_path.exists():
            from urllib.parse import quote
            filename_encoded = quote(filename + ".pdf")
            return StreamingResponse(
                open(pdf_path, "rb"),
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f"attachment; filename*=UTF-8''{filename_encoded}"
                }
            )
        
        # Если PDF нет - генерируем из HTML
        html_path = doc_folder / "document.html"
        if not html_path.exists():
            raise HTTPException(status_code=404, detail="HTML документа не найден")
        
        with open(html_path, "r", encoding="utf-8") as f:
            html_content = f.read()
        
        if WEASYPRINT_AVAILABLE:
            pdf_buffer = io.BytesIO()
            WeasyHTML(string=html_content).write_pdf(pdf_buffer)
            pdf_buffer.seek(0)
            
            from urllib.parse import quote
            filename_encoded = quote(filename + ".pdf")
            return StreamingResponse(
                pdf_buffer,
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f"attachment; filename*=UTF-8''{filename_encoded}"
                }
            )
        else:
            # Возвращаем HTML для печати
            return HTMLResponse(
                content=html_content,
                headers={
                    "Content-Disposition": f'inline; filename="{filename}.html"'
                }
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка скачивания: {str(e)}"
        )


@router.get("/invoice/{document_id}/preview")
async def invoice_preview_saved(document_id: str):
    """
    Просмотр HTML сохранённого счёта
    """
    try:
        doc_folder = DOCUMENTS_DIR / document_id
        
        if not doc_folder.exists():
            raise HTTPException(status_code=404, detail="Документ не найден")
        
        html_path = doc_folder / "document.html"
        if not html_path.exists():
            raise HTTPException(status_code=404, detail="HTML документа не найден")
        
        with open(html_path, "r", encoding="utf-8") as f:
            html_content = f.read()
        
        return HTMLResponse(content=html_content)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка просмотра: {str(e)}"
        )


# ==================== АКТ ВЫПОЛНЕННЫХ РАБОТ ====================

def number_to_words_ru(number: float) -> str:
    """Преобразование числа в слова (упрощенная версия для рублей)"""
    if number == 0:
        return "ноль"
    
    units = ['', 'один', 'два', 'три', 'четыре', 'пять', 'шесть', 'семь', 'восемь', 'девять']
    teens = ['десять', 'одиннадцать', 'двенадцать', 'тринадцать', 'четырнадцать', 
             'пятнадцать', 'шестнадцать', 'семнадцать', 'восемнадцать', 'девятнадцать']
    tens = ['', '', 'двадцать', 'тридцать', 'сорок', 'пятьдесят', 
            'шестьдесят', 'семьдесят', 'восемьдесят', 'девяносто']
    hundreds = ['', 'сто', 'двести', 'триста', 'четыреста', 'пятьсот',
                'шестьсот', 'семьсот', 'восемьсот', 'девятьсот']
    
    def three_digits(n, feminine=False):
        if n == 0:
            return ''
        result = []
        h = n // 100
        t = (n % 100) // 10
        u = n % 10
        
        if h > 0:
            result.append(hundreds[h])
        
        if t == 1:
            result.append(teens[u])
        else:
            if t > 0:
                result.append(tens[t])
            if u > 0:
                if feminine and u in [1, 2]:
                    result.append('одна' if u == 1 else 'две')
                else:
                    result.append(units[u])
        
        return ' '.join(result)
    
    integer_part = int(number)
    
    if integer_part == 0:
        return "ноль"
    
    result = []
    
    # Миллионы
    millions = integer_part // 1000000
    if millions > 0:
        result.append(three_digits(millions))
        if millions % 10 == 1 and millions % 100 != 11:
            result.append('миллион')
        elif 2 <= millions % 10 <= 4 and (millions % 100 < 10 or millions % 100 >= 20):
            result.append('миллиона')
        else:
            result.append('миллионов')
    
    # Тысячи
    thousands = (integer_part % 1000000) // 1000
    if thousands > 0:
        result.append(three_digits(thousands, feminine=True))
        if thousands % 10 == 1 and thousands % 100 != 11:
            result.append('тысяча')
        elif 2 <= thousands % 10 <= 4 and (thousands % 100 < 10 or thousands % 100 >= 20):
            result.append('тысячи')
        else:
            result.append('тысяч')
    
    # Единицы
    remainder = integer_part % 1000
    if remainder > 0:
        result.append(three_digits(remainder))
    
    return ' '.join(result).strip()


@router.post("/akt/preview")
async def akt_preview(request: Request):
    """
    Предпросмотр Акта выполненных работ - возвращает HTML
    """
    try:
        data = await request.json()
        template = jinja_env.get_template("akt_template.html")
        
        # Парсим дату документа
        doc_date = data.get('document_date', '')
        doc_date_day = ''
        doc_date_month = ''
        doc_date_year = ''
        
        if doc_date:
            parts = doc_date.split('.')
            if len(parts) == 3:
                doc_date_day = parts[0]
                months_ru = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
                             'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря']
                month_idx = int(parts[1]) - 1
                doc_date_month = months_ru[month_idx] if 0 <= month_idx < 12 else parts[1]
                doc_date_year = parts[2]
        
        # Подготовка данных
        items = data.get('items', [])
        vat_rate = data.get('vat_rate', '20')
        
        total_without_vat = sum(float(item.get('amount', 0)) for item in items)
        
        if vat_rate == 'none':
            total_vat = 0
            total_amount = total_without_vat
        else:
            vat_percent = float(vat_rate)
            if data.get('vat_type') == 'included':
                # НДС включен в цену
                total_amount = total_without_vat
                total_vat = total_amount * vat_percent / (100 + vat_percent)
                total_without_vat = total_amount - total_vat
            else:
                # НДС сверху
                total_vat = total_without_vat * vat_percent / 100
                total_amount = total_without_vat + total_vat
        
        # Сумма прописью
        total_amount_words = number_to_words_ru(total_amount)
        total_vat_words = number_to_words_ru(total_vat)
        
        template_data = {
            'document_number': data.get('document_number', ''),
            'document_date_day': doc_date_day,
            'document_date_month': doc_date_month,
            'document_date_year': doc_date_year,
            'contract_number': data.get('contract_number', ''),
            'contract_date': data.get('contract_date', ''),
            
            'executor': {
                'name': data.get('executor', {}).get('name', ''),
                'inn': data.get('executor', {}).get('inn', ''),
                'kpp': data.get('executor', {}).get('kpp', ''),
                'address': data.get('executor', {}).get('address', ''),
            },
            
            'customer': {
                'name': data.get('customer', {}).get('name', ''),
                'inn': data.get('customer', {}).get('inn', ''),
                'kpp': data.get('customer', {}).get('kpp', ''),
                'address': data.get('customer', {}).get('address', ''),
            },
            
            'executor_signatory': data.get('executor_signatory', ''),
            'customer_signatory': data.get('customer_signatory', ''),
            
            'items': items,
            'vat_rate': vat_rate,
            'total_without_vat': total_without_vat,
            'total_vat': total_vat,
            'total_amount': total_amount,
            'total_amount_words': total_amount_words,
            'total_vat_words': total_vat_words,
            'notes': data.get('notes', ''),
        }
        
        html_content = template.render(**template_data)
        return HTMLResponse(content=html_content)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка предпросмотра: {str(e)}"
        )


@router.post("/akt/save")
async def akt_save(
    request: Request,
    authorization: Optional[str] = Header(None),
    access_token: Optional[str] = Cookie(None),
    db: Session = Depends(get_db)
):
    """
    Сохранение Акта выполненных работ
    """
    import traceback
    try:
        data = await request.json()
        print(f"[AKT SAVE] Received data: {list(data.keys())}")
        
        # Проверяем авторизацию
        user_id = get_user_id_from_token(authorization, access_token)
        print(f"[AKT SAVE] User ID: {user_id}")
        
        if not user_id:
            return JSONResponse(
                status_code=401,
                content={"success": False, "message": "Требуется авторизация", "require_auth": True}
            )
        
        # Проверяем лимиты биллинга
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return JSONResponse(
                status_code=401,
                content={"success": False, "message": "Пользователь не найден", "require_auth": True}
            )
        
        billing = BillingService(db)
        check = billing.check_can_generate(user)
        print(f"[AKT SAVE] Billing check: can_generate={check['can_generate']}, message={check['message']}")
        
        if not check["can_generate"]:
            return JSONResponse(
                status_code=402,
                content={"success": False, "message": check["message"], "limit_reached": True, "limits": check["limits"]}
            )
        
        # Генерируем HTML
        template = jinja_env.get_template("akt_template.html")
        print("[AKT SAVE] Template loaded")
        
        # Парсим дату документа
        doc_date = data.get('document_date', '')
        doc_date_day = ''
        doc_date_month = ''
        doc_date_year = ''
        
        if doc_date:
            parts = doc_date.split('.')
            if len(parts) == 3:
                doc_date_day = parts[0]
                months_ru = ['января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
                             'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря']
                month_idx = int(parts[1]) - 1
                doc_date_month = months_ru[month_idx] if 0 <= month_idx < 12 else parts[1]
                doc_date_year = parts[2]
        
        # Подготовка данных
        items = data.get('items', [])
        vat_rate = data.get('vat_rate', '20')
        
        total_without_vat = sum(float(item.get('amount', 0)) for item in items)
        
        if vat_rate == 'none':
            total_vat = 0
            total_amount = total_without_vat
        else:
            vat_percent = float(vat_rate)
            if data.get('vat_type') == 'included':
                total_amount = total_without_vat
                total_vat = total_amount * vat_percent / (100 + vat_percent)
                total_without_vat = total_amount - total_vat
            else:
                total_vat = total_without_vat * vat_percent / 100
                total_amount = total_without_vat + total_vat
        
        total_amount_words = number_to_words_ru(total_amount)
        total_vat_words = number_to_words_ru(total_vat)
        
        template_data = {
            'document_number': data.get('document_number', ''),
            'document_date_day': doc_date_day,
            'document_date_month': doc_date_month,
            'document_date_year': doc_date_year,
            'contract_number': data.get('contract_number', ''),
            'contract_date': data.get('contract_date', ''),
            
            'executor': {
                'name': data.get('executor', {}).get('name', ''),
                'inn': data.get('executor', {}).get('inn', ''),
                'kpp': data.get('executor', {}).get('kpp', ''),
                'address': data.get('executor', {}).get('address', ''),
            },
            
            'customer': {
                'name': data.get('customer', {}).get('name', ''),
                'inn': data.get('customer', {}).get('inn', ''),
                'kpp': data.get('customer', {}).get('kpp', ''),
                'address': data.get('customer', {}).get('address', ''),
            },
            
            'executor_signatory': data.get('executor_signatory', ''),
            'customer_signatory': data.get('customer_signatory', ''),
            
            'items': items,
            'vat_rate': vat_rate,
            'total_without_vat': total_without_vat,
            'total_vat': total_vat,
            'total_amount': total_amount,
            'total_amount_words': total_amount_words,
            'total_vat_words': total_vat_words,
            'notes': data.get('notes', ''),
        }
        
        html_content = template.render(**template_data)
        
        # Создаём папку для документа
        document_id = str(uuid.uuid4())
        doc_folder = DOCUMENTS_DIR / document_id
        doc_folder.mkdir(parents=True, exist_ok=True)
        
        # Сохраняем HTML
        html_path = doc_folder / "document.html"
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        
        # Сохраняем данные формы
        data_path = doc_folder / "data.json"
        with open(data_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        # Сохраняем метаданные (формат совместимый с УПД для отображения в списке)
        metadata = {
            "id": document_id,
            "type": "akt",
            "document_number": data.get('document_number', ''),
            "document_date": doc_date,
            "seller_name": data.get('executor', {}).get('name', ''),
            "buyer_name": data.get('customer', {}).get('name', ''),
            "total_amount": total_amount,
            "user_id": user_id,
            "created_at": datetime.now().isoformat(),
        }
        
        meta_path = doc_folder / "metadata.json"
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        # Списываем генерацию
        seller_inn = data.get('executor', {}).get('inn', '')
        billing.consume_generation(user, seller_inn)
        
        # Генерируем PDF если возможно
        pdf_url = None
        if WEASYPRINT_AVAILABLE:
            try:
                pdf_path = doc_folder / "document.pdf"
                WeasyHTML(string=html_content).write_pdf(str(pdf_path))
                pdf_url = f"/api/v1/documents/akt/{document_id}/download"
            except Exception as pdf_error:
                print(f"[AKT] Ошибка генерации PDF: {pdf_error}")
        
        return JSONResponse(content={
            "success": True,
            "message": "Акт выполненных работ успешно сохранён",
            "document_id": document_id,
            "pdf_url": pdf_url,
            "html_url": f"/api/v1/documents/akt/{document_id}/preview"
        })
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"[AKT SAVE ERROR] {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка сохранения: {str(e)}"
        )


@router.get("/akt/{document_id}/download")
async def akt_download(
    document_id: str,
    authorization: Optional[str] = Header(None),
    access_token: Optional[str] = Cookie(None)
):
    """
    Скачивание Акта выполненных работ в PDF
    """
    user_id = get_user_id_from_token(authorization, access_token)
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Требуется авторизация")
    
    try:
        doc_folder = DOCUMENTS_DIR / document_id
        
        if not doc_folder.exists():
            raise HTTPException(status_code=404, detail="Документ не найден")
        
        # Читаем metadata.json
        meta_path = doc_folder / "metadata.json"
        if meta_path.exists():
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
        else:
            meta = {}
        
        akt_number = meta.get('document_number', document_id)
        akt_date = meta.get('document_date', '')
        filename = f"Akt_{akt_number}_{akt_date.replace('.', '')}"
        
        # Проверяем PDF
        pdf_path = doc_folder / "document.pdf"
        if pdf_path.exists():
            from urllib.parse import quote
            filename_encoded = quote(filename + ".pdf")
            return StreamingResponse(
                open(pdf_path, "rb"),
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f"attachment; filename*=UTF-8''{filename_encoded}"
                }
            )
        
        # Если PDF нет - генерируем из HTML
        html_path = doc_folder / "document.html"
        if not html_path.exists():
            raise HTTPException(status_code=404, detail="HTML документа не найден")
        
        with open(html_path, "r", encoding="utf-8") as f:
            html_content = f.read()
        
        if WEASYPRINT_AVAILABLE:
            pdf_buffer = io.BytesIO()
            WeasyHTML(string=html_content).write_pdf(pdf_buffer)
            pdf_buffer.seek(0)
            
            from urllib.parse import quote
            filename_encoded = quote(filename + ".pdf")
            return StreamingResponse(
                pdf_buffer,
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f"attachment; filename*=UTF-8''{filename_encoded}"
                }
            )
        else:
            # Возвращаем HTML для печати
            return HTMLResponse(
                content=html_content,
                headers={
                    "Content-Disposition": f'inline; filename="{filename}.html"'
                }
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка скачивания: {str(e)}"
        )


@router.get("/akt/{document_id}/preview")
async def akt_preview_saved(document_id: str):
    """
    Просмотр HTML сохранённого Акта
    """
    try:
        doc_folder = DOCUMENTS_DIR / document_id
        
        if not doc_folder.exists():
            raise HTTPException(status_code=404, detail="Документ не найден")
        
        html_path = doc_folder / "document.html"
        if not html_path.exists():
            raise HTTPException(status_code=404, detail="HTML документа не найден")
        
        with open(html_path, "r", encoding="utf-8") as f:
            html_content = f.read()
        
        return HTMLResponse(content=html_content)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка просмотра: {str(e)}"
        )


@router.get("/akt/{document_id}/data")
async def akt_get_data(
    document_id: str,
    authorization: Optional[str] = Header(None),
    access_token: Optional[str] = Cookie(None)
):
    """
    Получение данных Акта для редактирования
    """
    user_id = get_user_id_from_token(authorization, access_token)
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Требуется авторизация")
    
    try:
        doc_folder = DOCUMENTS_DIR / document_id
        
        if not doc_folder.exists():
            raise HTTPException(status_code=404, detail="Документ не найден")
        
        data_path = doc_folder / "data.json"
        if not data_path.exists():
            raise HTTPException(status_code=404, detail="Данные документа не найдены")
        
        with open(data_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        return JSONResponse(content={"success": True, "data": data})
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка получения данных: {str(e)}"
        )


