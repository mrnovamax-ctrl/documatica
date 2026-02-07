"""
Шорткоды: подстановка блоков из шаблонов в контент.
В контенте [имя_шорткода] заменяется на HTML секции.
"""

import re
from typing import Optional

from app.core.templates import templates


def build_section_view(shortcode) -> object:
    """Строит объект section для Jinja из модели Shortcode."""
    settings = dict(shortcode.section_settings or {})
    settings.setdefault("grid_columns", 2)
    settings.setdefault("grid_gap", "medium")
    settings.setdefault("grid_style", "grid")
    blocks_data = shortcode.blocks or []
    block_views = []
    for i, b in enumerate(blocks_data):
        if not isinstance(b, dict):
            continue
        block_views.append(type("BlockView", (), {
            "block_type": b.get("block_type", "paragraph"),
            "content": b.get("content", {}),
            "css_classes": b.get("css_classes") or "",
            "is_visible": b.get("is_visible", True),
            "position": i,
        })())
    section_view = type("SectionView", (), {
        "section_type": shortcode.section_type or "seo_text",
        "settings": settings,
        "blocks": block_views,
        "background_style": (shortcode.section_settings or {}).get("background_style", "light"),
        "css_classes": (shortcode.section_settings or {}).get("css_classes") or "",
        "is_visible": True,
    })()
    return section_view


def render_shortcode_to_html(shortcode, request, db) -> str:
    """Рендерит шорткод в HTML. Если задан page_section_id — секция из БД, иначе legacy JSON."""
    from sqlalchemy.orm import joinedload
    from app.core.heroicons import get_icon_paths_html
    from app.models import PageSection

    section = None
    if getattr(shortcode, "page_section_id", None):
        section_orm = (
            db.query(PageSection)
            .options(joinedload(PageSection.blocks))
            .filter(PageSection.id == shortcode.page_section_id)
            .first()
        )
        if section_orm:
            section = _section_view_from_orm(section_orm)
    if section is None:
        section = build_section_view(shortcode)

    template = templates.env.get_template("components/shortcode_section.html")
    html = template.render(
        request=request,
        section=section,
        heroicon_paths=get_icon_paths_html(),
    )
    # Обёртка по системе классов: изоляция от стилей контента статьи
    return f'<div class="shortcode-block">{html}</div>'


def process_shortcodes(html: str, request, db) -> str:
    """
    Заменяет в тексте вхождения [имя_шорткода] на HTML блока.
    Имя: латиница, цифры, подчёркивание.
    """
    if not html or "[" not in html:
        return html

    from app.models import Shortcode

    # Совпадение [имя] или \[имя] (редактор может экранировать скобку)
    pattern = re.compile(r"\\?\[([a-zA-Z0-9_-]+)\]")
    seen = set()

    def repl(match):
        name = match.group(1).strip()
        if name in seen:
            return match.group(0)
        seen.add(name)
        shortcode = db.query(Shortcode).filter(
            Shortcode.name == name,
            Shortcode.is_active.is_(True),
        ).first()
        if not shortcode:
            return match.group(0)
        try:
            return render_shortcode_to_html(shortcode, request, db)
        except Exception:
            return match.group(0)

    return pattern.sub(repl, html)
