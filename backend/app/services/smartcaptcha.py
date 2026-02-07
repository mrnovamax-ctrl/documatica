"""
Yandex SmartCaptcha - проверка капчи на сервере
"""

import json
import os

import httpx


SMARTCAPTCHA_SERVER_KEY = os.getenv("SMARTCAPTCHA_SERVER_KEY", "")
VALIDATE_URL = "https://smartcaptcha.yandexcloud.net/validate"


def check_captcha(token: str, ip: str) -> bool:
    """
    Проверяет токен SmartCaptcha.
    Возвращает True если капча пройдена или если сервер капчи недоступен (fail-open при ошибках).
    """
    if not SMARTCAPTCHA_SERVER_KEY:
        return True  # Капча отключена, если ключ не задан

    if not token or not token.strip():
        return False

    try:
        resp = httpx.get(
            VALIDATE_URL,
            params={
                "secret": SMARTCAPTCHA_SERVER_KEY,
                "token": token.strip(),
                "ip": ip or "127.0.0.1",
            },
            timeout=5,
        )
        server_output = resp.text
        if resp.status_code != 200:
            return True  # При ошибке API разрешаем доступ (fail-open)
        data = json.loads(server_output)
        return data.get("status") == "ok"
    except Exception:
        return True  # При исключении разрешаем доступ (fail-open)
