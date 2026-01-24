"""
Jinja2 Templates Configuration
"""

from pathlib import Path
from fastapi.templating import Jinja2Templates
from datetime import datetime

from app.core.content import load_navigation

# Путь к шаблонам
TEMPLATES_DIR = Path(__file__).parent.parent / "templates"

# Инициализация Jinja2
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Добавляем глобальные переменные и фильтры
templates.env.globals["current_year"] = datetime.now().year
templates.env.globals["site_name"] = "Documatica"
templates.env.globals["site_url"] = "https://new.oplatanalogov.ru"

# Функция для загрузки навигации (будет вызываться в шаблонах)
def get_navigation():
    """Получение конфигурации навигации для меню"""
    return load_navigation()

templates.env.globals["get_navigation"] = get_navigation


# Кастомные фильтры
def format_number(value):
    """Форматирование чисел с разделителями тысяч"""
    if value is None:
        return ""
    try:
        return "{:,.0f}".format(float(value)).replace(",", " ")
    except (ValueError, TypeError):
        return str(value)


def format_currency(value, currency="₽"):
    """Форматирование денежных сумм"""
    if value is None:
        return ""
    try:
        formatted = "{:,.2f}".format(float(value)).replace(",", " ")
        return f"{formatted} {currency}"
    except (ValueError, TypeError):
        return str(value)


def format_date(value, fmt="%d.%m.%Y"):
    """Форматирование даты"""
    if value is None:
        return ""
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value)
        except ValueError:
            return value
    return value.strftime(fmt)


def pluralize(value, forms):
    """
    Склонение слов по числу
    forms = "документ,документа,документов"
    """
    form_list = forms.split(",")
    if len(form_list) != 3:
        return forms
    
    try:
        n = abs(int(value))
    except (ValueError, TypeError):
        return form_list[2]
    
    if n % 10 == 1 and n % 100 != 11:
        return form_list[0]
    elif 2 <= n % 10 <= 4 and (n % 100 < 10 or n % 100 >= 20):
        return form_list[1]
    else:
        return form_list[2]


# Регистрируем фильтры
templates.env.filters["format_number"] = format_number
templates.env.filters["format_currency"] = format_currency
templates.env.filters["format_date"] = format_date
templates.env.filters["pluralize"] = pluralize
