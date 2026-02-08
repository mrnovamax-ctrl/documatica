"""
Google reCAPTCHA v2 Invisible - проверка капчи на сервере
"""

import json
import os

import httpx


RECAPTCHA_SECRET_KEY = os.getenv("RECAPTCHA_SECRET_KEY", "")
VERIFY_URL = "https://www.google.com/recaptcha/api/siteverify"


def verify_recaptcha(token: str, ip: str | None = None) -> bool:
    """
    Проверяет токен Google reCAPTCHA (v2 invisible или v3).
    Возвращает True, если капча пройдена или если reCAPTCHA не настроена (ключ не задан).
    """
    if not RECAPTCHA_SECRET_KEY:
        return True  # Капча отключена

    if not token or not token.strip():
        return False

    try:
        resp = httpx.post(
            VERIFY_URL,
            data={
                "secret": RECAPTCHA_SECRET_KEY,
                "response": token.strip(),
                **({"remoteip": ip} if ip else {}),
            },
            timeout=10,
        )
        if resp.status_code != 200:
            return True  # При ошибке API — fail-open
        data = resp.json()
        return data.get("success") is True
    except Exception:
        return True  # При исключении — fail-open
