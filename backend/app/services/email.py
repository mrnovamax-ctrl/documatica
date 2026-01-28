"""
Сервис отправки email
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from email.utils import formataddr
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
        msg["Subject"] = Header(subject, "utf-8")
        msg["From"] = formataddr((str(Header(SMTP_FROM_NAME, "utf-8")), SMTP_FROM))
        msg["To"] = to_email
        
        html_part = MIMEText(html_content, "html", "utf-8")
        msg.attach(html_part)
        
        print(f"[EMAIL] Подключаемся к SMTP: {SMTP_HOST}:{SMTP_PORT}")
        
        # Порт 465 = SSL, порт 587 = STARTTLS
        if SMTP_PORT == 465:
            # SSL соединение (Mail.ru, Gmail и др.)
            with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=30) as server:
                if SMTP_USER and SMTP_PASSWORD:
                    server.login(SMTP_USER, SMTP_PASSWORD)
                server.sendmail(SMTP_FROM, to_email, msg.as_string())
        else:
            # STARTTLS соединение (Yandex и др.)
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as server:
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
    user_name = name if name else "пользователь"
    
    html = f"""
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Подтверждение email - Documatica</title>
    </head>
    <body style="margin: 0; padding: 0; background-color: #e2e8f0; font-family: Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; -webkit-font-smoothing: antialiased;">
        
        <!-- Outer Container -->
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background-color: #e2e8f0;">
            <tr>
                <td align="center" style="padding: 40px 20px;">
                    
                    <!-- Email Container -->
                    <table role="presentation" width="600" cellspacing="0" cellpadding="0" border="0" style="max-width: 600px; width: 100%; background-color: #0f172a; border-radius: 56px; overflow: hidden; box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);">
                        
                        <!-- Pattern Header with Logo -->
                        <tr>
                            <td style="background-color: #0f172a; background-image: url('data:image/svg+xml,%3Csvg width=\'24\' height=\'24\' xmlns=\'http://www.w3.org/2000/svg\'%3E%3Ccircle cx=\'12\' cy=\'12\' r=\'1\' fill=\'%233b82f6\' opacity=\'0.3\'/%3E%3C/svg%3E'); padding: 48px 20px; text-align: center;">
                                <!-- Inline SVG Logo -->
                                <table role="presentation" cellspacing="0" cellpadding="0" border="0" align="center" style="margin-bottom: 24px;">
                                    <tr>
                                        <td style="background-color: rgba(255, 255, 255, 0.05); padding: 20px; border-radius: 24px;">
                                            <svg viewBox="0 0 64 64" width="48" height="48" style="display: block;">
                                                <path d="M12 16H48V48H12V16Z" fill="#3b82f6" fill-opacity="0.2"/>
                                                <path d="M18 24H46M18 32H46M18 40H34" stroke="#3b82f6" stroke-width="5" stroke-linecap="round"/>
                                                <circle cx="48" cy="40" r="5" fill="#FBBF24"/>
                                            </svg>
                                        </td>
                                    </tr>
                                </table>
                                <!-- Status Tag -->
                                <table role="presentation" cellspacing="0" cellpadding="0" border="0" align="center">
                                    <tr>
                                        <td style="background-color: rgba(251, 191, 36, 0.3); width: 8px; height: 8px; border-radius: 50%;"></td>
                                        <td style="padding-left: 10px; font-size: 10px; font-weight: 900; color: #3b82f6; text-transform: uppercase; letter-spacing: 0.3em;">Подтверждение аккаунта</td>
                                    </tr>
                                </table>
                            </td>
                        </tr>
                        
                        <!-- Content -->
                        <tr>
                            <td style="padding: 48px; text-align: center;">
                                
                                <!-- Title -->
                                <h1 style="margin: 0 0 24px 0; font-size: 36px; font-weight: 900; text-transform: uppercase; letter-spacing: -0.05em; line-height: 0.95; color: #ffffff;">
                                    Подтверждение<br><span style="color: #3b82f6;">аккаунта</span>
                                </h1>
                                
                                <p style="margin: 0 0 40px 0; font-size: 16px; font-weight: 500; color: #94a3b8; line-height: 1.6; max-width: 320px; margin-left: auto; margin-right: auto;">
                                    Здравствуйте, {user_name}! Для завершения активации вашего профиля в Documatica v12.0, пожалуйста, подтвердите владение данным адресом почты.
                                </p>
                                
                                <!-- CTA Button -->
                                <table role="presentation" cellspacing="0" cellpadding="0" border="0" align="center" style="margin-bottom: 48px;">
                                    <tr>
                                        <td style="background-color: #3b82f6; border-radius: 32px; box-shadow: 0 20px 25px -5px rgba(59, 130, 246, 0.4);">
                                            <a href="{verify_url}" target="_blank" style="display: inline-block; padding: 24px 48px; font-size: 12px; font-weight: 900; color: #ffffff; text-decoration: none; text-transform: uppercase; letter-spacing: 0.3em;">Подтвердить почту</a>
                                        </td>
                                    </tr>
                                </table>
                                
                                <!-- Fallback Link Box -->
                                <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="margin-bottom: 40px;">
                                    <tr>
                                        <td style="background-color: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 40px; padding: 32px; text-align: left;">
                                            <p style="margin: 0 0 12px 0; font-size: 8px; font-weight: 900; color: #64748b; text-transform: uppercase; letter-spacing: 0.2em;">Manual protocol entry:</p>
                                            <p style="margin: 0; font-size: 10px; font-family: monospace; color: rgba(59, 130, 246, 0.6); word-break: break-all; line-height: 1.6;">
                                                Если кнопка не работает, скопируйте эту ссылку в браузер:<br>
                                                <span style="color: #3b82f6;">{verify_url}</span>
                                            </p>
                                        </td>
                                    </tr>
                                </table>
                                
                                <!-- Footer Info -->
                                <p style="margin: 0 0 24px 0; font-size: 9px; font-weight: 700; color: #64748b; text-transform: uppercase; letter-spacing: 0.5em;">Ссылка действительна 24 часа</p>
                                <div style="width: 80px; height: 1px; background-color: rgba(255, 255, 255, 0.1); margin: 0 auto 24px auto;"></div>
                                <p style="margin: 0; font-size: 9px; font-weight: 500; color: #475569; text-transform: uppercase; letter-spacing: 0.2em; line-height: 1.6; max-width: 280px; margin-left: auto; margin-right: auto;">
                                    Security Notice: Это письмо сформировано автоматически ядром DocuAI.
                                </p>
                            </td>
                        </tr>
                        
                        <!-- Bottom Branding -->
                        <tr>
                            <td style="background-color: rgba(0, 0, 0, 0.2); padding: 32px; text-align: center; border-top: 1px solid rgba(255, 255, 255, 0.05);">
                                <span style="font-size: 10px; font-weight: 900; color: #334155; text-transform: uppercase; letter-spacing: 1em;">Grid Core v12.0</span>
                            </td>
                        </tr>
                        
                    </table>
                    
                </td>
            </tr>
        </table>
        
    </body>
    </html>
    """
    
    return send_email(to_email, "Подтвердите ваш email - Documatica", html)


def send_password_reset_email(to_email: str, token: str) -> bool:
    """Отправка письма для сброса пароля"""
    reset_url = f"{BASE_URL}/reset-password?token={token}"
    
    html = f"""
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Сброс пароля - Documatica</title>
    </head>
    <body style="margin: 0; padding: 0; background-color: #e2e8f0; font-family: Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; -webkit-font-smoothing: antialiased;">
        
        <!-- Outer Container -->
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background-color: #e2e8f0;">
            <tr>
                <td align="center" style="padding: 40px 20px;">
                    
                    <!-- Email Container -->
                    <table role="presentation" width="600" cellspacing="0" cellpadding="0" border="0" style="max-width: 600px; width: 100%; background-color: #ffffff; border-radius: 56px; overflow: hidden; box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.15); border: 1px solid #f1f5f9;">
                        
                        <!-- Pattern Header -->
                        <tr>
                            <td style="background-color: #f8fafc; background-image: url('data:image/svg+xml,%3Csvg width=\'32\' height=\'32\' xmlns=\'http://www.w3.org/2000/svg\'%3E%3Ccircle cx=\'16\' cy=\'16\' r=\'1\' fill=\'%233b82f6\' opacity=\'0.25\'/%3E%3C/svg%3E'); padding: 48px; text-align: center; border-bottom: 1px solid #f1f5f9;">
                                <!-- Logo Box with inline SVG -->
                                <table role="presentation" cellspacing="0" cellpadding="0" border="0" align="center">
                                    <tr>
                                        <td style="background-color: #ffffff; padding: 24px; border-radius: 32px; box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);">
                                            <!-- Inline SVG Logo -->
                                            <svg viewBox="0 0 64 64" width="48" height="48" style="display: block;">
                                                <path d="M12 16H48V48H12V16Z" fill="#3b82f6" fill-opacity="0.1"/>
                                                <path d="M18 24H46M18 32H46M18 40H34" stroke="#3b82f6" stroke-width="6" stroke-linecap="round"/>
                                                <circle cx="48" cy="40" r="6" fill="#FBBF24"/>
                                            </svg>
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>
                        
                        <!-- Content -->
                        <tr>
                            <td style="padding: 64px 48px; text-align: left;">
                                
                                <!-- Status Indicator -->
                                <table role="presentation" cellspacing="0" cellpadding="0" border="0" style="margin-bottom: 32px;">
                                    <tr>
                                        <td style="width: 10px; height: 10px; background-color: #f59e0b; border-radius: 50%; box-shadow: 0 0 10px rgba(245, 158, 11, 0.6);"></td>
                                        <td style="padding-left: 12px; font-size: 10px; font-weight: 900; color: #3b82f6; text-transform: uppercase; letter-spacing: 0.4em;">Password Reset Protocol</td>
                                    </tr>
                                </table>
                                
                                <!-- Title -->
                                <h1 style="margin: 0 0 40px 0; font-size: 42px; font-weight: 900; text-transform: uppercase; letter-spacing: -0.05em; line-height: 0.9; color: #0f172a;">
                                    Сброс<br><span style="color: #3b82f6;">пароля</span>
                                </h1>
                                
                                <p style="margin: 0 0 48px 0; font-size: 18px; font-weight: 500; color: #64748b; line-height: 1.6;">
                                    Вы запросили сброс пароля для вашего аккаунта. Нажмите на кнопку ниже, чтобы создать новый пароль.
                                </p>
                                
                                <!-- Action Box -->
                                <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="margin-bottom: 48px;">
                                    <tr>
                                        <td style="background-color: #f8fafc; border: 1px solid #f1f5f9; border-radius: 40px; padding: 40px;">
                                            <p style="margin: 0 0 16px 0; font-size: 9px; font-weight: 900; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.2em;">Следующий этап протокола</p>
                                            <h3 style="margin: 0 0 32px 0; font-size: 18px; font-weight: 900; color: #0f172a; text-transform: uppercase; letter-spacing: -0.02em;">Создайте новый пароль</h3>
                                            <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0">
                                                <tr>
                                                    <td style="background-color: #3b82f6; border-radius: 16px; text-align: center; box-shadow: 0 20px 25px -5px rgba(59, 130, 246, 0.3);">
                                                        <a href="{reset_url}" target="_blank" style="display: block; padding: 24px; font-size: 11px; font-weight: 900; color: #ffffff; text-decoration: none; text-transform: uppercase; letter-spacing: 0.3em;">Сбросить пароль</a>
                                                    </td>
                                                </tr>
                                            </table>
                                        </td>
                                    </tr>
                                </table>
                                
                                <!-- Fallback Link -->
                                <p style="margin: 0 0 8px 0; font-size: 10px; font-weight: 700; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.1em;">Или скопируйте ссылку:</p>
                                <p style="margin: 0 0 32px 0; font-size: 11px; font-family: monospace; color: #3b82f6; word-break: break-all; line-height: 1.6; background-color: #f8fafc; padding: 16px; border-radius: 12px;">{reset_url}</p>
                                
                                <p style="margin: 0; font-size: 12px; font-weight: 500; color: #f59e0b;">Ссылка действительна 1 час.</p>
                            </td>
                        </tr>
                        
                        <!-- Footer -->
                        <tr>
                            <td style="padding: 32px 48px; border-top: 1px solid #f1f5f9;">
                                <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0">
                                    <tr>
                                        <td style="font-size: 9px; font-weight: 900; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.2em;">Grid Core v12.0</td>
                                        <td style="text-align: right; font-size: 9px; font-weight: 900; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.2em;">&copy; 2026</td>
                                    </tr>
                                </table>
                            </td>
                        </tr>
                        
                    </table>
                    
                    <!-- Security Notice -->
                    <table role="presentation" width="600" cellspacing="0" cellpadding="0" border="0" style="max-width: 600px; width: 100%; margin-top: 24px;">
                        <tr>
                            <td style="text-align: center; font-size: 10px; font-weight: 500; color: #94a3b8; line-height: 1.6;">
                                Если вы не запрашивали сброс пароля, проигнорируйте это письмо.
                            </td>
                        </tr>
                    </table>
                    
                </td>
            </tr>
        </table>
        
    </body>
    </html>
    """
    
    return send_email(to_email, "Сброс пароля - Documatica", html)


def send_welcome_email(to_email: str, name: Optional[str] = None) -> bool:
    """Отправка приветственного письма после регистрации"""
    user_name = name if name else "пользователь"
    dashboard_url = f"{BASE_URL}/dashboard/"
    
    html = f"""
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Добро пожаловать в Documatica</title>
    </head>
    <body style="margin: 0; padding: 0; background-color: #e2e8f0; font-family: Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; -webkit-font-smoothing: antialiased;">
        
        <!-- Outer Container -->
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="background-color: #e2e8f0;">
            <tr>
                <td align="center" style="padding: 40px 20px;">
                    
                    <!-- Email Container -->
                    <table role="presentation" width="600" cellspacing="0" cellpadding="0" border="0" style="max-width: 600px; width: 100%; background-color: #ffffff; border-radius: 56px; overflow: hidden; box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.15); border: 1px solid #f1f5f9;">
                        
                        <!-- Pattern Header -->
                        <tr>
                            <td style="background-color: #f8fafc; background-image: url('data:image/svg+xml,%3Csvg width=\'32\' height=\'32\' xmlns=\'http://www.w3.org/2000/svg\'%3E%3Ccircle cx=\'16\' cy=\'16\' r=\'1\' fill=\'%233b82f6\' opacity=\'0.25\'/%3E%3C/svg%3E'); height: 180px; text-align: center; border-bottom: 1px solid #f1f5f9; position: relative;">
                                <!-- Logo Box -->
                                <table role="presentation" cellspacing="0" cellpadding="0" border="0" align="center" style="height: 100%;">
                                    <tr>
                                        <td style="vertical-align: middle;">
                                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" align="center">
                                                <tr>
                                                    <td style="background-color: #ffffff; padding: 24px; border-radius: 32px; box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1);">
                                                        <img src="{BASE_URL}/static/images/favicon.svg" alt="Documatica" width="48" height="48" style="display: block;">
                                                    </td>
                                                </tr>
                                            </table>
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>
                        
                        <!-- Content -->
                        <tr>
                            <td style="padding: 64px 48px; text-align: left;">
                                
                                <!-- Status Indicator -->
                                <table role="presentation" cellspacing="0" cellpadding="0" border="0" style="margin-bottom: 32px;">
                                    <tr>
                                        <td style="width: 10px; height: 10px; background-color: #10b981; border-radius: 50%; box-shadow: 0 0 10px rgba(16, 185, 129, 0.6);"></td>
                                        <td style="padding-left: 12px; font-size: 10px; font-weight: 900; color: #3b82f6; text-transform: uppercase; letter-spacing: 0.4em;">Account Deployed Successfully</td>
                                    </tr>
                                </table>
                                
                                <!-- Title -->
                                <h1 style="margin: 0 0 40px 0; font-size: 42px; font-weight: 900; text-transform: uppercase; letter-spacing: -0.05em; line-height: 0.9; color: #0f172a;">
                                    Добро пожаловать<br>в <span style="color: #3b82f6;">Documatica</span>
                                </h1>
                                
                                <p style="margin: 0 0 48px 0; font-size: 18px; font-weight: 500; color: #64748b; line-height: 1.6;">
                                    Здравствуйте, {user_name}! Ваш узел в системе v12.0 успешно активирован. Теперь вам доступны все инструменты интеллектуального управления документами.
                                </p>
                                
                                <!-- Action Box -->
                                <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="margin-bottom: 48px;">
                                    <tr>
                                        <td style="background-color: #f8fafc; border: 1px solid #f1f5f9; border-radius: 40px; padding: 40px;">
                                            <p style="margin: 0 0 16px 0; font-size: 9px; font-weight: 900; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.2em;">Следующий этап протокола</p>
                                            <h3 style="margin: 0 0 32px 0; font-size: 18px; font-weight: 900; color: #0f172a; text-transform: uppercase; letter-spacing: -0.02em;">Настройте свой дашборд</h3>
                                            <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0">
                                                <tr>
                                                    <td style="background-color: #3b82f6; border-radius: 16px; text-align: center; box-shadow: 0 20px 25px -5px rgba(59, 130, 246, 0.3);">
                                                        <a href="{dashboard_url}" target="_blank" style="display: block; padding: 24px; font-size: 11px; font-weight: 900; color: #ffffff; text-decoration: none; text-transform: uppercase; letter-spacing: 0.3em;">Перейти в терминал</a>
                                                    </td>
                                                </tr>
                                            </table>
                                        </td>
                                    </tr>
                                </table>
                                
                                <!-- Features -->
                                <p style="margin: 0 0 16px 0; font-size: 10px; font-weight: 900; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.2em;">Доступные модули:</p>
                                <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="margin-bottom: 32px;">
                                    <tr>
                                        <td style="padding: 12px 0; border-bottom: 1px solid #f1f5f9;">
                                            <span style="font-size: 14px; font-weight: 700; color: #0f172a;">УПД</span>
                                            <span style="font-size: 12px; color: #64748b; margin-left: 8px;">Универсальный передаточный документ</span>
                                        </td>
                                    </tr>
                                    <tr>
                                        <td style="padding: 12px 0; border-bottom: 1px solid #f1f5f9;">
                                            <span style="font-size: 14px; font-weight: 700; color: #0f172a;">Счета</span>
                                            <span style="font-size: 12px; color: #64748b; margin-left: 8px;">Счета на оплату</span>
                                        </td>
                                    </tr>
                                    <tr>
                                        <td style="padding: 12px 0;">
                                            <span style="font-size: 14px; font-weight: 700; color: #0f172a;">Контрагенты</span>
                                            <span style="font-size: 12px; color: #64748b; margin-left: 8px;">База клиентов и поставщиков</span>
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>
                        
                        <!-- Footer -->
                        <tr>
                            <td style="padding: 32px 48px; border-top: 1px solid #f1f5f9;">
                                <table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0">
                                    <tr>
                                        <td style="font-size: 9px; font-weight: 900; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.2em;">Grid Core v12.0</td>
                                        <td style="text-align: right; font-size: 9px; font-weight: 900; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.2em;">&copy; 2026</td>
                                    </tr>
                                </table>
                            </td>
                        </tr>
                        
                    </table>
                    
                </td>
            </tr>
        </table>
        
    </body>
    </html>
    """
    
    return send_email(to_email, "Добро пожаловать в Documatica!", html)
