"""
Дефолтные блоки и настройки для шорткодов по типу секции.
Используется при создании шорткода по шаблону и для формы CTA.
"""

SECTION_TYPES = [
    ("hero", "Hero"),
    ("features", "Блок преимуществ"),
    ("about", "О нас"),
    ("cta", "Призыв к действию (CTA)"),
    ("faq", "FAQ"),
    ("pricing", "Тарифы"),
    ("seo_text", "SEO-текст"),
    ("form_section", "Форма"),
    ("document_types", "Карточки документов"),
    ("upd_types", "Типы УПД"),
    ("useful_materials", "Полезные материалы"),
    ("articles_list", "Список статей"),
    ("articles_preview", "Последние статьи"),
]


def default_blocks_for_section_type(section_type: str):
    """Блоки по умолчанию для типа секции."""
    if section_type == "cta":
        return [
            {"block_type": "label", "content": {"text": ""}, "css_classes": "", "is_visible": True},
            {"block_type": "heading", "content": {"text": "", "level": 2}, "css_classes": "", "is_visible": True},
            {"block_type": "paragraph", "content": {"text": ""}, "css_classes": "", "is_visible": True},
            {"block_type": "button", "content": {"text": "Перейти", "url": "/dashboard/"}, "css_classes": "btn btn-primary btn-lg", "is_visible": True},
        ]
    if section_type == "hero":
        return [
            {"block_type": "label", "content": {"text": ""}, "css_classes": "", "is_visible": True},
            {"block_type": "heading", "content": {"text": "", "level": 1}, "css_classes": "", "is_visible": True},
            {"block_type": "note", "content": {"text": "", "accent": ""}, "css_classes": "", "is_visible": True},
            {"block_type": "button", "content": {"text": "", "url": "#"}, "css_classes": "", "is_visible": True},
        ]
    if section_type == "seo_text":
        return [
            {"block_type": "heading", "content": {"text": "", "level": 2}, "css_classes": "", "is_visible": True},
            {"block_type": "paragraph", "content": {"text": ""}, "css_classes": "", "is_visible": True},
        ]
    return [
        {"block_type": "heading", "content": {"text": "", "level": 2}, "css_classes": "", "is_visible": True},
        {"block_type": "paragraph", "content": {"text": ""}, "css_classes": "", "is_visible": True},
    ]


def default_settings_for_section_type(section_type: str):
    if section_type == "cta":
        return {"cta_variant": "basic", "background_style": "light"}
    if section_type == "hero":
        return {"hero_variant": "default", "background_style": "light"}
    if section_type == "faq":
        return {"accordion_variant": "basic", "background_style": "light"}
    if section_type == "pricing":
        return {"pricing_variant": "basic", "background_style": "light"}
    return {"background_style": "light"}


def cta_blocks_from_form(
    label_text: str,
    heading_text: str,
    heading_level: int,
    paragraph_text: str,
    button_text: str,
    button_url: str,
    cta_variant: str,
) -> list:
    """Собирает блоки CTA из полей формы."""
    return [
        {"block_type": "label", "content": {"text": label_text}, "css_classes": "", "is_visible": True},
        {"block_type": "heading", "content": {"text": heading_text, "level": heading_level}, "css_classes": "", "is_visible": True},
        {"block_type": "paragraph", "content": {"text": paragraph_text}, "css_classes": "", "is_visible": True},
        {"block_type": "button", "content": {"text": button_text, "url": button_url}, "css_classes": "btn btn-primary btn-lg", "is_visible": True},
    ]


def cta_form_from_blocks(blocks: list) -> dict:
    """Извлекает данные формы CTA из блоков."""
    out = {
        "label_text": "",
        "heading_text": "",
        "heading_level": 2,
        "paragraph_text": "",
        "button_text": "Перейти",
        "button_url": "/dashboard/",
    }
    if not blocks:
        return out
    for b in blocks:
        if not isinstance(b, dict):
            continue
        c = b.get("content") or {}
        if b.get("block_type") == "label":
            out["label_text"] = c.get("text", "")
        elif b.get("block_type") == "heading":
            out["heading_text"] = c.get("text", "")
            out["heading_level"] = int(c.get("level", 2))
        elif b.get("block_type") == "paragraph":
            out["paragraph_text"] = c.get("text", "")
        elif b.get("block_type") == "button":
            out["button_text"] = c.get("text", "Перейти")
            out["button_url"] = c.get("url", "/dashboard/")
    return out
