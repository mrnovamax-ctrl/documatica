"""
API для формы обратной связи
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from app.services.email import send_email
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/contact", tags=["contact"])


class ContactRequest(BaseModel):
    """Запрос обратной связи"""
    name: str
    email: EmailStr
    phone: str = ""
    subject: str
    message: str


@router.post("/send")
async def send_contact_message(request: ContactRequest):
    """
    Отправка сообщения с формы обратной связи
    """
    try:
        # HTML шаблон письма
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
                    padding: 30px;
                    text-align: center;
                    border-radius: 12px 12px 0 0;
                }}
                .header h1 {{
                    color: white;
                    margin: 0;
                    font-size: 24px;
                }}
                .content {{
                    background: #ffffff;
                    padding: 30px;
                    border: 1px solid #e2e8f0;
                    border-top: none;
                }}
                .field {{
                    margin-bottom: 20px;
                }}
                .field-label {{
                    font-weight: 600;
                    color: #475569;
                    font-size: 12px;
                    text-transform: uppercase;
                    letter-spacing: 0.05em;
                    margin-bottom: 6px;
                }}
                .field-value {{
                    color: #0f172a;
                    font-size: 15px;
                    padding: 12px;
                    background: #f8fafc;
                    border-radius: 8px;
                }}
                .message-box {{
                    background: #f8fafc;
                    padding: 20px;
                    border-radius: 8px;
                    border-left: 4px solid #3b82f6;
                    white-space: pre-wrap;
                    word-wrap: break-word;
                }}
                .footer {{
                    text-align: center;
                    padding: 20px;
                    color: #64748b;
                    font-size: 13px;
                    border-top: 1px solid #e2e8f0;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>📧 Новое сообщение с формы обратной связи</h1>
            </div>
            <div class="content">
                <div class="field">
                    <div class="field-label">От кого:</div>
                    <div class="field-value">{request.name}</div>
                </div>
                
                <div class="field">
                    <div class="field-label">Email:</div>
                    <div class="field-value">
                        <a href="mailto:{request.email}" style="color: #3b82f6; text-decoration: none;">
                            {request.email}
                        </a>
                    </div>
                </div>
                
                {f'''
                <div class="field">
                    <div class="field-label">Телефон:</div>
                    <div class="field-value">{request.phone}</div>
                </div>
                ''' if request.phone else ''}
                
                <div class="field">
                    <div class="field-label">Тема:</div>
                    <div class="field-value">{request.subject}</div>
                </div>
                
                <div class="field">
                    <div class="field-label">Сообщение:</div>
                    <div class="message-box">{request.message}</div>
                </div>
            </div>
            <div class="footer">
                Это автоматическое сообщение с сайта oplatanalogov.ru<br>
                Ответьте клиенту напрямую на указанный email
            </div>
        </body>
        </html>
        """
        
        # Отправляем письмо
        subject = f"[Обратная связь] {request.subject} от {request.name}"
        success = send_email(
            to_email="hello@novatechno.ru",
            subject=subject,
            html_content=html_content
        )
        
        if not success:
            logger.error(f"Failed to send contact email from {request.email}")
            raise HTTPException(
                status_code=500,
                detail="Не удалось отправить сообщение. Попробуйте позже или свяжитесь с нами в Telegram."
            )
        
        logger.info(f"Contact email sent from {request.email} ({request.name})")
        
        return {
            "success": True,
            "message": "Сообщение успешно отправлено"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending contact email: {e}")
        raise HTTPException(
            status_code=500,
            detail="Произошла ошибка при отправке сообщения"
        )
