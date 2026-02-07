"""
API для формы обратной связи.
Принимает произвольный JSON; маппит типичные имена полей (name/email/phone/subject/message и русские аналоги).
"""

import re
import logging
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Request
from app.services.email import send_email

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/contact", tags=["contact"])

# Маппинг возможных имён полей (ключ формы -> наш атрибут)
NAME_KEYS = ("name", "username", "user_name", "имя", "имя_", "fio", "фио", "fullname", "full_name")
EMAIL_KEYS = ("email", "e-mail", "e_mail", "mail", "почта", "email_address")
PHONE_KEYS = ("phone", "tel", "telephone", "телефон", "phone_number", "телефон_")
SUBJECT_KEYS = ("subject", "topic", "тема", "title", "заголовок")
MESSAGE_KEYS = ("message", "msg", "body", "text", "comment", "сообщение", "комментарий", "описание")


def _normalize_key(k: str) -> str:
    return (k or "").strip().lower().replace("-", "_").replace(" ", "_")


def _get_mapped(body: dict[str, Any], key_groups: tuple[str, ...]) -> Optional[str]:
    keys_normalized = {_normalize_key(k): k for k in body.keys()}
    for candidate in key_groups:
        if _normalize_key(candidate) in keys_normalized:
            val = body.get(keys_normalized[_normalize_key(candidate)])
            if val is not None and str(val).strip():
                return str(val).strip()
    return None


def _find_email(body: dict[str, Any]) -> Optional[str]:
    for key in EMAIL_KEYS:
        nk = _normalize_key(key)
        for form_key, form_val in body.items():
            if _normalize_key(form_key) == nk and form_val and str(form_val).strip():
                return str(form_val).strip()
    email_re = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")
    for v in body.values():
        if v and isinstance(v, str) and email_re.search(v):
            return v.strip()
    return None


def _first_value_except(body: dict[str, Any], exclude_val: Optional[str], min_len: int = 0) -> Optional[str]:
    for k, v in body.items():
        if v is None or str(v).strip() == "":
            continue
        s = str(v).strip()
        if exclude_val and s == exclude_val:
            continue
        if min_len and len(s) < min_len:
            continue
        return s
    return None


@router.post("/send")
async def send_contact_message(request: Request):
    """
    Отправка сообщения с формы обратной связи.
    Принимает любой JSON; маппит name/email/phone/subject/message (и русские аналоги).
    В письме выводятся все переданные поля.
    """
    try:
        raw = await request.json()
        if not isinstance(raw, dict):
            raise HTTPException(status_code=422, detail="Ожидается JSON-объект с полями формы")

        body = {k: v for k, v in raw.items() if k and not k.startswith("_")}
        for k, v in list(body.items()):
            if v is not None and not isinstance(v, (str, int, float, bool)):
                body[k] = str(v)
            elif v is not None and isinstance(v, str):
                body[k] = v.strip()

        email = _find_email(body)
        if not email:
            raise HTTPException(status_code=422, detail="Укажите email для связи")

        name = _get_mapped(body, NAME_KEYS) or _first_value_except(body, email) or "Не указано"
        phone = _get_mapped(body, PHONE_KEYS) or ""
        subject = _get_mapped(body, SUBJECT_KEYS) or "Сообщение с сайта"
        message = _get_mapped(body, MESSAGE_KEYS) or ""

        # Блоки для письма: все поля по порядку
        fields_html = []
        field_order = ["name", "email", "phone", "subject", "message"]
        for key in field_order:
            val = (name if key == "name" else email if key == "email" else phone if key == "phone" else subject if key == "subject" else message)
            if key == "email" and val:
                fields_html.append(
                    f'<div class="field"><div class="field-label">Email:</div>'
                    f'<div class="field-value"><a href="mailto:{val}" style="color: #3b82f6;">{val}</a></div></div>'
                )
            elif val and key != "email":
                label = {"name": "Имя", "phone": "Телефон", "subject": "Тема", "message": "Сообщение"}.get(key, key)
                esc = str(val).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                if key == "message":
                    fields_html.append(f'<div class="field"><div class="field-label">{label}:</div><div class="message-box">{esc}</div></div>')
                else:
                    fields_html.append(f'<div class="field"><div class="field-label">{label}:</div><div class="field-value">{esc}</div></div>')

        for k, v in body.items():
            kn = _normalize_key(k)
            if kn in (_normalize_key(x) for x in NAME_KEYS + EMAIL_KEYS + PHONE_KEYS + SUBJECT_KEYS + MESSAGE_KEYS):
                continue
            if v is None or str(v).strip() == "":
                continue
            esc = str(v).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            fields_html.append(f'<div class="field"><div class="field-label">{k}:</div><div class="field-value">{esc}</div></div>')

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); padding: 30px; text-align: center; border-radius: 12px 12px 0 0; }}
                .header h1 {{ color: white; margin: 0; font-size: 24px; }}
                .content {{ background: #fff; padding: 30px; border: 1px solid #e2e8f0; border-top: none; }}
                .field {{ margin-bottom: 20px; }}
                .field-label {{ font-weight: 600; color: #475569; font-size: 12px; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 6px; }}
                .field-value {{ color: #0f172a; font-size: 15px; padding: 12px; background: #f8fafc; border-radius: 8px; }}
                .message-box {{ background: #f8fafc; padding: 20px; border-radius: 8px; border-left: 4px solid #3b82f6; white-space: pre-wrap; word-wrap: break-word; }}
                .footer {{ text-align: center; padding: 20px; color: #64748b; font-size: 13px; border-top: 1px solid #e2e8f0; }}
            </style>
        </head>
        <body>
            <div class="header"><h1>Новое сообщение с формы обратной связи</h1></div>
            <div class="content">
                {"".join(fields_html)}
            </div>
            <div class="footer">Ответьте клиенту напрямую на указанный email.</div>
        </body>
        </html>
        """

        subject = f"[Обратная связь] {subject} от {name}"
        success = send_email(
            to_email="hello@novatechno.ru",
            subject=subject,
            html_content=html_content
        )

        if not success:
            logger.error("Failed to send contact email from %s", email)
            raise HTTPException(
                status_code=500,
                detail="Не удалось отправить сообщение. Попробуйте позже или свяжитесь с нами в Telegram."
            )

        logger.info("Contact email sent from %s (%s)", email, name)
        return {"success": True, "message": "Сообщение успешно отправлено"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error sending contact email: %s", e)
        raise HTTPException(status_code=500, detail="Произошла ошибка при отправке сообщения")
