"""
Сервис отправки email
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

# Настройки SMTP (будут браться из переменных окружения)
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM = os.getenv("SMTP_FROM", "noreply@documatica.ru")
SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "Documatica")

BASE_URL = os.getenv("BASE_URL", "https://oplatanalogov.ru")


def send_email(to_email: str, subject: str, html_content: str) -> bool:
    """Отправка email"""
    if not SMTP_HOST:
        print(f"[EMAIL] SMTP не настроен. Письмо для {to_email}: {subject}")
        print(f"[EMAIL] Содержимое: {html_content[:200]}...")
        return True  # Возвращаем True чтобы не блокировать регистрацию
    
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{SMTP_FROM_NAME} <{SMTP_FROM}>"
        msg["To"] = to_email
        
        html_part = MIMEText(html_content, "html", "utf-8")
        msg.attach(html_part)
        
        print(f"[EMAIL] Подключаемся к SMTP: {SMTP_HOST}:{SMTP_PORT}")
        
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as server:
            # Для локального postfix без авторизации
            if SMTP_USER and SMTP_PASSWORD:
                try:
                    server.starttls()
                except smtplib.SMTPNotSupportedError:
                    print("[EMAIL] TLS не поддерживается, продолжаем без шифрования")
                server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_FROM, to_email, msg.as_string())
        
        print(f"[EMAIL] Письмо отправлено: {to_email}")
        return True
    except Exception as e:
        print(f"[EMAIL] Ошибка отправки: {e}")
        import traceback
        traceback.print_exc()
        return False


def send_verification_email(to_email: str, token: str, name: Optional[str] = None) -> bool:
    """Отправка письма для подтверждения email"""
    verify_url = f"{BASE_URL}/verify-email?token={token}"
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: #4361ee; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
            .content {{ background: #f8f9fa; padding: 30px; border-radius: 0 0 8px 8px; }}
            .btn {{ display: inline-block; background: #4361ee; color: white; padding: 12px 30px; text-decoration: none; border-radius: 6px; margin: 20px 0; }}
            .footer {{ text-align: center; color: #666; font-size: 12px; margin-top: 20px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Documatica</h1>
            </div>
            <div class="content">
                <h2>Подтвердите ваш email</h2>
                <p>Здравствуйте{f', {name}' if name else ''}!</p>
                <p>Спасибо за регистрацию в Documatica. Для завершения регистрации подтвердите ваш email, нажав на кнопку ниже:</p>
                <p style="text-align: center;">
                    <a href="{verify_url}" class="btn">Подтвердить email</a>
                </p>
                <p>Или скопируйте эту ссылку в браузер:</p>
                <p style="word-break: break-all; color: #666;">{verify_url}</p>
                <p>Ссылка действительна 24 часа.</p>
            </div>
            <div class="footer">
                <p>Если вы не регистрировались в Documatica, просто проигнорируйте это письмо.</p>
                <p>&copy; 2026 Documatica</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return send_email(to_email, "Подтвердите ваш email - Documatica", html)


def send_password_reset_email(to_email: str, token: str) -> bool:
    """Отправка письма для сброса пароля"""
    reset_url = f"{BASE_URL}/reset-password?token={token}"
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: #4361ee; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
            .content {{ background: #f8f9fa; padding: 30px; border-radius: 0 0 8px 8px; }}
            .btn {{ display: inline-block; background: #4361ee; color: white; padding: 12px 30px; text-decoration: none; border-radius: 6px; margin: 20px 0; }}
            .footer {{ text-align: center; color: #666; font-size: 12px; margin-top: 20px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Documatica</h1>
            </div>
            <div class="content">
                <h2>Сброс пароля</h2>
                <p>Вы запросили сброс пароля. Нажмите на кнопку ниже, чтобы создать новый пароль:</p>
                <p style="text-align: center;">
                    <a href="{reset_url}" class="btn">Сбросить пароль</a>
                </p>
                <p>Или скопируйте эту ссылку в браузер:</p>
                <p style="word-break: break-all; color: #666;">{reset_url}</p>
                <p>Ссылка действительна 1 час.</p>
            </div>
            <div class="footer">
                <p>Если вы не запрашивали сброс пароля, проигнорируйте это письмо.</p>
                <p>&copy; 2026 Documatica</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return send_email(to_email, "Сброс пароля - Documatica", html)
