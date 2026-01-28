"""
API для ИИ анализа документов через OpenAI
"""

import httpx
import logging
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List, Any, Union

from app.database import get_db
from app.models import User
from app.api.auth import get_current_user_db
from app.core.config import settings

router = APIRouter(prefix="/ai", tags=["ai"])

logger = logging.getLogger(__name__)


class AnalyzeUPDRequest(BaseModel):
    """Запрос на анализ УПД"""
    model_config = {"extra": "ignore"}  # Игнорировать неизвестные поля
    
    # Данные документа (поддержка обоих форматов) - принимаем str или int
    upd_status: Optional[Union[str, int]] = "1"
    upd_number: Optional[str] = ""
    upd_date: Optional[str] = ""
    # Альтернативные имена полей
    status: Optional[Union[str, int]] = None
    document_number: Optional[str] = None
    document_date: Optional[str] = None
    
    correction_number: Optional[str] = None
    correction_date: Optional[str] = None
    
    # Продавец (поддержка вложенного объекта seller или отдельных полей)
    seller_name: Optional[str] = ""
    seller_inn: Optional[str] = ""
    seller_kpp: Optional[str] = None
    seller_address: Optional[str] = ""
    seller: Optional[dict] = None  # Альтернативный формат
    
    # Покупатель (поддержка вложенного объекта buyer или отдельных полей)
    buyer_name: Optional[str] = ""
    buyer_inn: Optional[str] = ""
    buyer_kpp: Optional[str] = None
    buyer_address: Optional[str] = ""
    buyer: Optional[dict] = None  # Альтернативный формат
    
    # Грузоотправитель/грузополучатель
    shipper_name: Optional[str] = None
    shipper_address: Optional[str] = None
    consignee_name: Optional[str] = None
    consignee_address: Optional[str] = None
    cargo_sender: Optional[str] = None  # Альтернативное имя
    cargo_receiver: Optional[str] = None  # Альтернативное имя
    
    # НДС
    vat_rate: Optional[str] = "20%"
    vat_type: Optional[str] = "included"
    
    # Товары/услуги
    items: Optional[List[dict]] = []
    
    # Итоги
    total_amount: Optional[float] = None
    total_vat: Optional[float] = None
    
    # Дополнительные поля
    payment_document: Optional[str] = None
    contract_info: Optional[str] = None
    currency: Optional[dict] = None
    
    def get_status(self) -> str:
        status = self.status if self.status is not None else self.upd_status
        return str(status) if status is not None else "1"
    
    def get_number(self) -> str:
        return self.document_number or self.upd_number or ""
    
    def get_date(self) -> str:
        return self.document_date or self.upd_date or ""
    
    def get_seller_name(self) -> str:
        if self.seller and isinstance(self.seller, dict):
            return self.seller.get('name', '')
        return self.seller_name or ""
    
    def get_seller_inn(self) -> str:
        if self.seller and isinstance(self.seller, dict):
            return self.seller.get('inn', '')
        return self.seller_inn or ""
    
    def get_seller_kpp(self) -> str:
        if self.seller and isinstance(self.seller, dict):
            return self.seller.get('kpp', '')
        return self.seller_kpp or ""
    
    def get_seller_address(self) -> str:
        if self.seller and isinstance(self.seller, dict):
            return self.seller.get('address', '')
        return self.seller_address or ""
    
    def get_buyer_name(self) -> str:
        if self.buyer and isinstance(self.buyer, dict):
            return self.buyer.get('name', '')
        return self.buyer_name or ""
    
    def get_buyer_inn(self) -> str:
        if self.buyer and isinstance(self.buyer, dict):
            return self.buyer.get('inn', '')
        return self.buyer_inn or ""
    
    def get_buyer_kpp(self) -> str:
        if self.buyer and isinstance(self.buyer, dict):
            return self.buyer.get('kpp', '')
        return self.buyer_kpp or ""
    
    def get_buyer_address(self) -> str:
        if self.buyer and isinstance(self.buyer, dict):
            return self.buyer.get('address', '')
        return self.buyer_address or ""
    
    def get_shipper_name(self) -> str:
        return self.shipper_name or self.cargo_sender or ""
    
    def get_consignee_name(self) -> str:
        return self.consignee_name or self.cargo_receiver or ""


class AnalyzeUPDResponse(BaseModel):
    """Ответ анализа УПД"""
    success: bool
    errors: List[dict] = []      # Критические ошибки
    warnings: List[dict] = []    # Предупреждения
    suggestions: List[dict] = [] # Рекомендации
    summary: str = ""            # Общее заключение
    raw_response: Optional[str] = None


def format_document_for_analysis(data: AnalyzeUPDRequest) -> str:
    """Форматирование документа для отправки в GPT"""
    
    items_text = ""
    if data.items:
        for i, item in enumerate(data.items, 1):
            items_text += f"""
  {i}. {item.get('name', 'Без названия')}
     - Количество: {item.get('quantity', '?')} {item.get('unit', 'шт')}
     - Цена: {item.get('price', '?')} руб.
     - Сумма: {item.get('amount', '?')} руб.
     - НДС: {item.get('vat', '?')} руб.
"""
    else:
        items_text = "  (товары не указаны)"
    
    status = data.get_status()
    status_text = '(счёт-фактура + передаточный документ)' if status == '1' else '(только передаточный документ)'
    
    document_text = f"""
УНИВЕРСАЛЬНЫЙ ПЕРЕДАТОЧНЫЙ ДОКУМЕНТ (УПД)
==========================================

СТАТУС ДОКУМЕНТА: {status} {status_text}

РЕКВИЗИТЫ ДОКУМЕНТА:
- Номер: {data.get_number() or '(не указан)'}
- Дата: {data.get_date() or '(не указана)'}
- Исправление: {data.correction_number or 'нет'}

ПРОДАВЕЦ:
- Наименование: {data.get_seller_name() or '(не указано)'}
- ИНН: {data.get_seller_inn() or '(не указан)'}
- КПП: {data.get_seller_kpp() or '(не указан)'}
- Адрес: {data.get_seller_address() or '(не указан)'}

ПОКУПАТЕЛЬ:
- Наименование: {data.get_buyer_name() or '(не указано)'}
- ИНН: {data.get_buyer_inn() or '(не указан)'}
- КПП: {data.get_buyer_kpp() or '(не указан)'}
- Адрес: {data.get_buyer_address() or '(не указан)'}

ГРУЗООТПРАВИТЕЛЬ: {data.get_shipper_name() or 'совпадает с продавцом'}
ГРУЗОПОЛУЧАТЕЛЬ: {data.get_consignee_name() or 'совпадает с покупателем'}

ПЛАТЕЖНЫЙ ДОКУМЕНТ: {data.payment_document or '(не указан)'}
ДОГОВОР: {data.contract_info or '(не указан)'}

НАСТРОЙКИ НДС:
- Ставка: {data.vat_rate}
- Расчёт: {data.vat_type}

ТОВАРЫ/УСЛУГИ:
{items_text}

ИТОГО:
- Сумма: {data.total_amount or '(не рассчитано)'} руб.
- НДС: {data.total_vat or '(не рассчитано)'} руб.
"""
    return document_text


SYSTEM_PROMPT = """Ты — эксперт по бухгалтерскому и налоговому учёту в России, специализирующийся на первичных документах. 
Твоя задача — проанализировать Универсальный Передаточный Документ (УПД) и найти:

1. КРИТИЧЕСКИЕ ОШИБКИ (errors) — нарушения, которые могут привести к отказу в вычете НДС или претензиям налоговой:
   - Отсутствие обязательных реквизитов
   - Неверный формат ИНН/КПП
   - Логические противоречия в данных
   - Арифметические ошибки

2. ПРЕДУПРЕЖДЕНИЯ (warnings) — потенциальные проблемы:
   - Орфографические ошибки в названиях
   - Подозрительные значения (нулевые суммы, странные количества)
   - Несоответствия в адресах

3. РЕКОМЕНДАЦИИ (suggestions) — улучшения для документа:
   - Лучшие практики заполнения
   - Советы по оформлению

Отвечай СТРОГО в формате JSON:
{
  "errors": [
    {"field": "название_поля", "message": "описание ошибки", "severity": "critical"}
  ],
  "warnings": [
    {"field": "название_поля", "message": "описание проблемы", "severity": "medium"}
  ],
  "suggestions": [
    {"field": "название_поля", "message": "рекомендация", "severity": "low"}
  ],
  "summary": "Краткое общее заключение о документе на 1-2 предложения"
}

Будь конкретен и укажи ТОЧНО какое поле содержит ошибку. Не выдумывай проблем, если их нет."""


@router.post("/analyze-upd-debug")
async def analyze_upd_debug(request: Request):
    """Debug endpoint to see raw request body"""
    body = await request.json()
    logger.info(f"Raw request body: {body}")
    return {"received": body, "keys": list(body.keys()) if isinstance(body, dict) else "not a dict"}


@router.post("/analyze-upd", response_model=AnalyzeUPDResponse)
async def analyze_upd(
    request: AnalyzeUPDRequest,
    current_user: User = Depends(get_current_user_db),
    db: Session = Depends(get_db)
):
    """Анализ УПД через OpenAI GPT"""
    import logging
    logging.info(f"AI Analysis request received: {request}")
    
    api_key = getattr(settings, 'OPENAI_API_KEY', None)
    
    if not api_key:
        raise HTTPException(status_code=500, detail="OpenAI API не настроен")
    
    # Форматируем документ
    document_text = format_document_for_analysis(request)
    
    # Запрос к OpenAI
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-4o-mini",
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": f"Проанализируй этот УПД:\n\n{document_text}"}
                    ],
                    "temperature": 0.3,
                    "max_tokens": 2000
                },
                timeout=60.0
            )
            
            if response.status_code != 200:
                error_text = response.text
                raise HTTPException(
                    status_code=502, 
                    detail=f"OpenAI API вернул ошибку: {response.status_code}"
                )
            
            result = response.json()
            
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Превышено время ожидания ответа от ИИ")
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Ошибка соединения с OpenAI: {str(e)}")
    
    # Парсим ответ
    try:
        content = result["choices"][0]["message"]["content"]
        
        # Извлекаем JSON из ответа
        import json
        import re
        
        # Пытаемся найти JSON в ответе
        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            parsed = json.loads(json_match.group())
        else:
            parsed = json.loads(content)
        
        return AnalyzeUPDResponse(
            success=True,
            errors=parsed.get("errors", []),
            warnings=parsed.get("warnings", []),
            suggestions=parsed.get("suggestions", []),
            summary=parsed.get("summary", "Анализ завершён"),
            raw_response=content
        )
        
    except (json.JSONDecodeError, KeyError, IndexError) as e:
        # Если не удалось распарсить, возвращаем сырой ответ
        return AnalyzeUPDResponse(
            success=True,
            errors=[],
            warnings=[],
            suggestions=[{"field": "general", "message": content, "severity": "info"}],
            summary="Анализ завершён (формат ответа нестандартный)",
            raw_response=content
        )


# ============== АКТ АНАЛИЗ ==============

class AnalyzeAktRequest(BaseModel):
    """Запрос на анализ Акта выполненных работ"""
    model_config = {"extra": "ignore"}
    
    akt_number: Optional[str] = ""
    akt_date: Optional[str] = ""
    contract_number: Optional[str] = ""
    contract_date: Optional[str] = ""
    
    executor_name: Optional[str] = ""
    executor_inn: Optional[str] = ""
    executor_kpp: Optional[str] = ""
    executor_address: Optional[str] = ""
    
    customer_name: Optional[str] = ""
    customer_inn: Optional[str] = ""
    customer_kpp: Optional[str] = ""
    customer_address: Optional[str] = ""
    
    items: Optional[List[dict]] = []
    notes: Optional[str] = ""


AKT_SYSTEM_PROMPT = """Ты - опытный бухгалтер и юрист, специализирующийся на первичной документации.
Твоя задача - проверить Акт выполненных работ (оказанных услуг) на ошибки и несоответствия.

Проверь:
1. Наличие всех обязательных реквизитов (номер, дата, стороны)
2. Корректность ИНН (10 или 12 цифр)
3. Наличие КПП для юридических лиц
4. Корректность наименований работ/услуг
5. Наличие единиц измерения и цен
6. Соответствие акта договору (если указан)

Ответь ТОЛЬКО в формате JSON:
{
  "errors": [{"field": "название поля", "message": "описание ошибки"}],
  "warnings": [{"field": "название поля", "message": "описание предупреждения"}],
  "suggestions": [{"field": "название поля", "message": "рекомендация"}],
  "summary": "краткое заключение"
}

Если ошибок нет, верни пустые массивы для errors и warnings."""


def format_akt_for_analysis(request: AnalyzeAktRequest) -> str:
    """Форматирует данные акта для анализа"""
    lines = [
        "=== АКТ ВЫПОЛНЕННЫХ РАБОТ (ОКАЗАННЫХ УСЛУГ) ===",
        f"Номер: {request.akt_number}",
        f"Дата: {request.akt_date}",
        f"Договор: № {request.contract_number} от {request.contract_date}" if request.contract_number else "Договор: не указан",
        "",
        "--- ИСПОЛНИТЕЛЬ ---",
        f"Наименование: {request.executor_name}",
        f"ИНН: {request.executor_inn}",
        f"КПП: {request.executor_kpp}" if request.executor_kpp else "",
        f"Адрес: {request.executor_address}" if request.executor_address else "",
        "",
        "--- ЗАКАЗЧИК ---",
        f"Наименование: {request.customer_name}",
        f"ИНН: {request.customer_inn}",
        f"КПП: {request.customer_kpp}" if request.customer_kpp else "",
        f"Адрес: {request.customer_address}" if request.customer_address else "",
        "",
        "--- РАБОТЫ/УСЛУГИ ---"
    ]
    
    total = 0
    for i, item in enumerate(request.items or [], 1):
        name = item.get('name', 'Не указано')
        qty = item.get('quantity', 0)
        unit = item.get('unit', 'шт')
        price = item.get('price', 0)
        amount = item.get('amount', qty * price)
        total += amount
        lines.append(f"{i}. {name} - {qty} {unit} x {price} руб. = {amount} руб.")
    
    lines.append(f"\nИТОГО: {total} руб.")
    
    if request.notes:
        lines.append(f"\nПримечания: {request.notes}")
    
    return "\n".join(lines)


@router.post("/analyze-akt", response_model=AnalyzeUPDResponse)
async def analyze_akt(
    request: AnalyzeAktRequest,
    current_user: User = Depends(get_current_user_db),
    db: Session = Depends(get_db)
):
    """Анализ Акта выполненных работ через OpenAI GPT"""
    api_key = getattr(settings, 'OPENAI_API_KEY', None)
    
    if not api_key:
        raise HTTPException(status_code=500, detail="OpenAI API не настроен")
    
    document_text = format_akt_for_analysis(request)
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-4o-mini",
                    "messages": [
                        {"role": "system", "content": AKT_SYSTEM_PROMPT},
                        {"role": "user", "content": f"Проанализируй этот Акт:\n\n{document_text}"}
                    ],
                    "temperature": 0.3,
                    "max_tokens": 2000
                },
                timeout=60.0
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=502, 
                    detail=f"OpenAI API вернул ошибку: {response.status_code}"
                )
            
            result = response.json()
            
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Превышено время ожидания ответа от ИИ")
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Ошибка соединения с OpenAI: {str(e)}")
    
    try:
        import json
        import re
        
        content = result["choices"][0]["message"]["content"]
        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            parsed = json.loads(json_match.group())
        else:
            parsed = json.loads(content)
        
        return AnalyzeUPDResponse(
            success=True,
            errors=parsed.get("errors", []),
            warnings=parsed.get("warnings", []),
            suggestions=parsed.get("suggestions", []),
            summary=parsed.get("summary", "Анализ завершён"),
            raw_response=content
        )
        
    except (json.JSONDecodeError, KeyError, IndexError) as e:
        return AnalyzeUPDResponse(
            success=True,
            errors=[],
            warnings=[],
            suggestions=[{"field": "general", "message": content, "severity": "info"}],
            summary="Анализ завершён (формат ответа нестандартный)",
            raw_response=content
        )
