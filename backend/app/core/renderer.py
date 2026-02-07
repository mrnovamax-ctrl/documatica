"""
Система рендеринга страниц из БД
ВАЖНО: Все стили через CSS классы, никаких инлайн стилей!
"""

from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models import Page, PageSection, ContentBlock


def render_page(page_id: int, db: Session) -> str:
    """
    Рендеринг страницы из БД в HTML
    Возвращает готовый HTML код страницы
    """
    page = db.query(Page).filter(Page.id == page_id).first()
    
    if not page:
        return "<div class='error'>Page not found</div>"
    
    # Рендерим все секции
    sections_html = []
    for section in page.sections:
        if section.is_visible:
            sections_html.append(render_section(section))
    
    return "\n\n".join(sections_html)


def render_section(section: PageSection) -> str:
    """
    Рендеринг секции
    ВАЖНО: Используем только CSS классы из Terminal v12.0
    """
    # Определяем CSS классы для секции
    section_classes = get_section_classes(section)
    
    # Рендерим блоки внутри секции
    blocks_html = []
    for block in section.blocks:
        if block.is_visible:
            blocks_html.append(render_block(block))
    
    # Определяем контейнер
    container_class = get_container_class(section.container_width)
    
    # Формируем HTML секции (БЕЗ инлайн стилей!)
    html = f'''<section class="{section_classes}">
  <div class="{container_class}">
    {chr(10).join(blocks_html)}
  </div>
</section>'''
    
    return html


def get_section_classes(section: PageSection) -> str:
    """Получение CSS классов для секции"""
    classes = []
    
    # Базовый класс секции
    if section.section_type == "hero":
        classes.append("hero-section")
    elif section.section_type == "features":
        classes.append("section section-light")
    elif section.section_type == "about":
        classes.append("about-section-v12")
    elif section.section_type == "pricing":
        classes.append("pricing-section-v12")
    elif section.section_type == "cta":
        classes.append("section")
    elif section.section_type == "faq":
        classes.append("faq-section")
    elif section.section_type == "seo_text":
        classes.append("seo-text-section-v12")
    elif section.section_type == "form_section":
        classes.append("form-section-v12")
    elif section.section_type == "upd_types":
        classes.append("upd-types-section")
    elif section.section_type == "useful_materials":
        classes.append("useful-materials-section")
    else:
        classes.append("section")
    
    # Фон секции
    if section.background_style == "pattern_light":
        classes.append("pattern-light")
    elif section.background_style == "pattern_dark":
        classes.append("pattern-dots-dark")
    elif section.background_style == "dark":
        classes.append("bg-slate-900 text-white")
    elif section.background_style == "gradient_blue":
        classes.append("bg-gradient-blue")
    elif section.background_style == "gradient_gold":
        classes.append("bg-gradient-gold")
    
    # Дополнительные классы
    if section.css_classes:
        classes.append(section.css_classes)
    
    return " ".join(classes)


def get_container_class(width: str) -> str:
    """Получение класса контейнера"""
    if width == "wide":
        return "container container-wide"
    elif width == "full":
        return "container-fluid"
    elif width == "narrow":
        return "container container-narrow"
    else:
        return "container"


def render_block(block: ContentBlock) -> str:
    """
    Рендеринг блока контента
    ВАЖНО: Только CSS классы, никаких инлайн стилей!
    """
    content = block.content
    css_classes = block.css_classes or ""
    
    if block.block_type == "heading":
        return render_heading(content, css_classes)
    elif block.block_type == "paragraph":
        return render_paragraph(content, css_classes)
    elif block.block_type == "button":
        return render_button(content, css_classes)
    elif block.block_type == "label":
        return render_label(content, css_classes)
    elif block.block_type == "note":
        return render_note(content, css_classes)
    elif block.block_type == "feature_card":
        return render_feature_card(content, css_classes)
    elif block.block_type == "stat_card":
        return render_stat_card(content, css_classes)
    elif block.block_type == "pricing_table":
        return render_pricing_table(content, css_classes)
    elif block.block_type == "upd_types_grid":
        return render_upd_types_grid(content, css_classes)
    elif block.block_type == "faq_item":
        return render_faq_item(content, css_classes)
    elif block.block_type == "contact_form":
        return '<div class="contact-form-v12"><!-- Contact form rendered by Jinja --></div>'
    elif block.block_type == "useful_materials":
        return render_useful_materials(content, css_classes)
    elif block.block_type == "link_group":
        return render_link_group(content, css_classes)
    else:
        return f"<!-- Unknown block type: {block.block_type} -->"


def render_heading(content: Dict, css_classes: str) -> str:
    """Рендеринг заголовка"""
    level = content.get("level", 2)
    text = content.get("text", "")
    accent = content.get("accent")
    
    # Если есть акцент, выделяем его
    if accent and accent in text:
        text = text.replace(accent, f'<span class="accent">{accent}</span>')
    
    return f'<h{level} class="{css_classes}">{text}</h{level}>'


def render_paragraph(content: Dict, css_classes: str) -> str:
    """Рендеринг параграфа"""
    text = content.get("text", "")
    return f'<p class="{css_classes}">{text}</p>'


def render_button(content: Dict, css_classes: str) -> str:
    """Рендеринг кнопки"""
    text = content.get("text", "")
    url = content.get("url", "#")
    
    # Добавляем SVG стрелку для CTA кнопок
    arrow_svg = '''<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
      <line x1="5" y1="12" x2="19" y2="12"></line>
      <polyline points="12 5 19 12 12 19"></polyline>
    </svg>'''
    
    if "cta" in css_classes or "hero" in css_classes:
        return f'<a href="{url}" class="{css_classes}">{text}{arrow_svg}</a>'
    else:
        return f'<a href="{url}" class="{css_classes}">{text}</a>'


def render_label(content: Dict, css_classes: str) -> str:
    """Рендеринг метки/тега"""
    text = content.get("text", "")
    
    # AI node для меток
    ai_node = '<span class="ai-node"></span>'
    
    return f'<div class="{css_classes}">{ai_node}{text}</div>'


def render_note(content: Dict, css_classes: str) -> str:
    """Рендеринг заметки"""
    text = content.get("text", "")
    accent = content.get("accent")
    
    if accent:
        return f'<div class="{css_classes}">{text} • <span class="hero-note-accent">{accent}</span></div>'
    else:
        return f'<div class="{css_classes}">{text}</div>'


def render_feature_card(content: Dict, css_classes: str) -> str:
    """Рендеринг карточки фичи"""
    title = content.get("title", "")
    description = content.get("description", "")
    icon = content.get("icon", "check-circle")
    
    # SVG иконки (из Terminal v12.0)
    icon_paths = {
        'check-circle': '<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline>',
        'alert-triangle': '<path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line>',
        'code': '<polyline points="16 18 22 12 16 6"></polyline><polyline points="8 6 2 12 8 18"></polyline>',
        'download': '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line>',
        'history': '<circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline>',
        'gift': '<polyline points="20 12 20 22 4 22 4 12"></polyline><rect x="2" y="7" width="20" height="5"></rect><line x1="12" y1="22" x2="12" y2="7"></line><path d="M12 7H7.5a2.5 2.5 0 0 1 0-5C11 2 12 7 12 7z"></path><path d="M12 7h4.5a2.5 2.5 0 0 0 0-5C13 2 12 7 12 7z"></path>',
    }
    
    icon_path = icon_paths.get(icon, icon_paths['check-circle'])
    
    return f'''<div class="{css_classes}">
  <div class="feature-icon">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      {icon_path}
    </svg>
  </div>
  <h3 class="feature-title">{title}</h3>
  <p class="feature-text">{description}</p>
</div>'''


def render_stat_card(content: Dict, css_classes: str) -> str:
    """Рендеринг статистической карточки"""
    value = content.get("value", "")
    label = content.get("label", "")
    
    return f'''<div class="{css_classes}">
  <div class="about-stat-value">{value}</div>
  <div class="about-stat-label">{label}</div>
</div>'''


def render_pricing_table(content: Dict, css_classes: str) -> str:
    """Рендеринг таблицы тарифов (сложная структура)"""
    # Здесь используем существующий шаблон из home.html
    # Возвращаем placeholder - полный рендеринг будет в Jinja2 компоненте
    return f'<!-- Pricing table: {len(content.get("plans", []))} plans -->'


def render_upd_types_grid(content: Dict, css_classes: str) -> str:
    """Рендеринг сетки типов УПД"""
    # Placeholder - полный рендеринг в Jinja2 компоненте
    return f'<!-- UPD types grid: {len(content.get("cards", []))} cards -->'


def render_faq_item(content: Dict, css_classes: str) -> str:
    """Рендеринг FAQ элемента"""
    question = content.get("question", "")
    answer = content.get("answer", "")
    
    return f'''<div class="{css_classes}">
  <h4 class="faq-question">{question}</h4>
  <div class="faq-answer">{answer}</div>
</div>'''


def render_useful_materials(content: Dict, css_classes: str) -> str:
    """Рендеринг блока «Полезные материалы» (ссылки)"""
    title = content.get("title", "Полезные материалы")
    links = content.get("links", [])
    items = "".join(
        f'<a href="{item.get("url", "#")}" class="useful-materials-link">{item.get("title", "")}</a>'
        for item in links
    )
    return f'<div class="{css_classes}"><div class="useful-materials-label">{title}</div><div class="useful-materials-grid">{items}</div></div>'


def render_link_group(content: Dict, css_classes: str) -> str:
    """Рендеринг группы ссылок (hero quick links)"""
    links = content.get("links", [])
    items = "".join(
        f'<a href="{item.get("url", "#")}" class="upd-quick-link-v12">{item.get("text", "")}</a>'
        for item in links
    )
    return f'<div class="hero-quick-links upd-quick-links-v12 {css_classes}">{items}</div>'


def render_page_by_slug(slug: str, db: Session) -> Optional[str]:
    """
    Рендеринг страницы по slug
    ВАЖНО: slug сохраняет оригинальную структуру URL!
    """
    page = db.query(Page).filter(Page.slug == slug).first()
    
    if not page:
        return None
    
    return render_page(page.id, db)


def get_page_meta(page_id: int, db: Session) -> Dict[str, Any]:
    """Получение meta-данных страницы для SEO"""
    page = db.query(Page).filter(Page.id == page_id).first()
    
    if not page:
        return {}
    
    return {
        "title": page.meta_title or page.title,
        "description": page.meta_description,
        "keywords": page.meta_keywords,
        "canonical": page.canonical_url,
    }
