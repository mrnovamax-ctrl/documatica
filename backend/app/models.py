"""
Модели базы данных
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Float, ForeignKey, Numeric, JSON, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB

Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=True)  # Nullable for OAuth users
    name = Column(String(255), nullable=True)
    phone = Column(String(32), nullable=True)
    
    # Статус верификации
    is_verified = Column(Boolean, default=False)
    verification_token = Column(String(255), nullable=True)
    verification_token_expires = Column(DateTime, nullable=True)
    
    # Сброс пароля
    reset_token = Column(String(255), nullable=True)
    reset_token_expires = Column(DateTime, nullable=True)
    
    # OAuth провайдеры
    yandex_id = Column(String(100), unique=True, nullable=True, index=True)
    google_id = Column(String(100), unique=True, nullable=True, index=True)
    auth_provider = Column(String(50), default="email")  # email, yandex, google
    
    # Метаданные
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    # Тарифы и лимиты
    subscription_plan = Column(String(50), default="free")  # free, subscription, pay_per_doc
    subscription_expires = Column(DateTime, nullable=True)
    
    # Счётчики использования
    free_generations_used = Column(Integer, default=0)  # Использовано бесплатных генераций (макс 5)
    subscription_docs_used = Column(Integer, default=0)  # Использовано документов по подписке в текущем месяце
    purchased_docs_remaining = Column(Integer, default=0)  # Остаток купленных поштучно документов
    
    # Связи
    inn_usages = relationship("INNUsage", back_populates="user")
    payments = relationship("Payment", back_populates="user")
    pages = relationship("Page", foreign_keys="Page.created_by_user_id")
    analytics_events = relationship("AnalyticsEvent")
    documents = relationship("Document")
    redirects = relationship("Redirect", foreign_keys="Redirect.created_by_user_id")
    
    def __repr__(self):
        return f"<User {self.email}>"


class INNUsage(Base):
    """Отслеживание использования ИНН для защиты от мультиаккаунтности"""
    __tablename__ = "inn_usage"
    
    id = Column(Integer, primary_key=True, index=True)
    inn = Column(String(12), index=True, nullable=False)  # ИНН (10 или 12 цифр)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Счётчик бесплатных генераций для этого ИНН (глобально)
    free_generations_count = Column(Integer, default=0)
    
    first_used_at = Column(DateTime, default=datetime.utcnow)
    last_used_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="inn_usages")
    
    def __repr__(self):
        return f"<INNUsage inn={self.inn} user_id={self.user_id}>"


class Payment(Base):
    """История платежей"""
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Тинькофф данные
    tbank_payment_id = Column(String(100), unique=True, nullable=True)
    tbank_order_id = Column(String(100), unique=True, nullable=False)
    
    # Детали платежа
    amount = Column(Numeric(10, 2), nullable=False)  # Сумма в рублях
    payment_type = Column(String(50), nullable=False)  # subscription, documents
    documents_count = Column(Integer, nullable=True)  # Кол-во документов (для pay_per_doc)
    
    # Статус
    status = Column(String(50), default="pending")  # pending, confirmed, rejected, refunded
    
    # Метаданные
    created_at = Column(DateTime, default=datetime.utcnow)
    confirmed_at = Column(DateTime, nullable=True)
    
    user = relationship("User", back_populates="payments")
    
    def __repr__(self):
        return f"<Payment {self.id} user={self.user_id} amount={self.amount}>"


class GlobalINNLimit(Base):
    """Глобальный лимит по ИНН (независимо от аккаунта)"""
    __tablename__ = "global_inn_limits"
    
    id = Column(Integer, primary_key=True, index=True)
    inn = Column(String(12), unique=True, index=True, nullable=False)
    free_generations_used = Column(Integer, default=0)  # Сколько бесплатных генераций сделано по этому ИНН
    first_used_at = Column(DateTime, default=datetime.utcnow)
    last_used_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<GlobalINNLimit inn={self.inn} used={self.free_generations_used}>"


class Promocode(Base):
    """Промокоды"""
    __tablename__ = "promocodes"
    
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, index=True, nullable=False)  # Код промокода
    
    # Тип промокода
    promo_type = Column(String(50), nullable=False)  # subscription, discount, documents
    
    # Параметры
    subscription_days = Column(Integer, nullable=True)  # Дней подписки (для subscription)
    subscription_price = Column(Integer, nullable=True)  # Цена подписки по промокоду
    discount_percent = Column(Integer, nullable=True)  # Процент скидки (для discount)
    documents_count = Column(Integer, nullable=True)  # Кол-во документов (для documents)
    
    # Ограничения
    is_active = Column(Boolean, default=True)
    is_reusable = Column(Boolean, default=True)  # Многоразовый (можно на разных аккаунтах)
    max_uses = Column(Integer, nullable=True)  # Макс. использований (null = без лимита)
    uses_count = Column(Integer, default=0)  # Текущее кол-во использований
    valid_from = Column(DateTime, nullable=True)
    valid_until = Column(DateTime, nullable=True)
    
    # Метаданные
    description = Column(String(255), nullable=True)  # Описание для админки
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Связи
    usages = relationship("PromocodeUsage", back_populates="promocode")
    
    def __repr__(self):
        return f"<Promocode {self.code} type={self.promo_type}>"


class PromocodeUsage(Base):
    """История использования промокодов"""
    __tablename__ = "promocode_usages"
    
    id = Column(Integer, primary_key=True, index=True)
    promocode_id = Column(Integer, ForeignKey("promocodes.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    activated_at = Column(DateTime, default=datetime.utcnow)
    
    promocode = relationship("Promocode", back_populates="usages")
    user = relationship("User")
    
    def __repr__(self):
        return f"<PromocodeUsage promo={self.promocode_id} user={self.user_id}>"


class GuestDraft(Base):
    """Черновики документов гостей (неавторизованных пользователей)"""
    __tablename__ = "guest_drafts"
    
    id = Column(Integer, primary_key=True, index=True)
    draft_token = Column(String(64), unique=True, index=True, nullable=False)  # Уникальный токен для доступа
    
    # Тип документа
    document_type = Column(String(50), nullable=False)  # upd, akt, invoice
    
    # Данные документа (JSON)
    document_data = Column(Text, nullable=False)
    
    # Связь с пользователем (после регистрации)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Идентификация гостя
    session_id = Column(String(100), nullable=True)  # Для связи с сессией браузера
    ip_address = Column(String(45), nullable=True)  # IPv4/IPv6
    
    # Статус
    is_claimed = Column(Boolean, default=False)  # Привязан к пользователю
    is_converted = Column(Boolean, default=False)  # Сгенерирован PDF
    
    # Метаданные
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)  # Когда истечёт (7 дней)
    
    user = relationship("User")
    
    def __repr__(self):
        return f"<GuestDraft {self.draft_token[:8]}... type={self.document_type}>"


# ============================================================================
# CMS Models - для Block Builder и управления контентом
# ============================================================================

class Page(Base):
    """Страницы сайта (CMS)"""
    __tablename__ = "pages"
    
    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String(500), unique=True, index=True, nullable=False)  # URL страницы (БЕЗ изменений!)
    title = Column(String(500), nullable=False)
    
    # SEO
    meta_title = Column(String(255), nullable=True)
    meta_description = Column(Text, nullable=True)
    meta_keywords = Column(String(500), nullable=True)
    canonical_url = Column(String(500), nullable=True)
    
    # Статус
    status = Column(String(50), default="draft")  # draft, published, archived
    page_type = Column(String(50), default="custom")  # home, service, blog, custom
    
    # Маппинг для миграции
    legacy_yaml_path = Column(String(500), nullable=True)  # Путь к старому YAML файлу
    
    # Метаданные
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    published_at = Column(DateTime, nullable=True)
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Связи (parent_id и parent — после применения миграции 20260204_add_page_parent_id)
    sections = relationship("PageSection", back_populates="page", cascade="all, delete-orphan", order_by="PageSection.position")
    created_by = relationship("User")
    
    def __repr__(self):
        return f"<Page {self.slug} status={self.status}>"


class PageSection(Base):
    """Секции страниц (контейнеры для блоков)"""
    __tablename__ = "page_sections"
    
    id = Column(Integer, primary_key=True, index=True)
    page_id = Column(Integer, ForeignKey("pages.id"), nullable=False, index=True)
    
    # Тип секции
    section_type = Column(String(100), nullable=False)  # hero, features, pricing, about, cta, faq, custom
    position = Column(Integer, default=0)  # Порядок на странице
    
    # Стили (ТОЛЬКО CSS классы, НЕ инлайн!)
    background_style = Column(String(100), default="light")  # light, dark, pattern_light, pattern_dark, gradient_blue, gradient_gold
    css_classes = Column(Text, nullable=True)  # Дополнительные CSS классы
    container_width = Column(String(50), default="default")  # default, wide, full, narrow
    padding_y = Column(String(50), default="default")  # default, none, sm, lg, xl
    
    # Сетка (отдельные колонки — сохраняются как фон/ширина, не в JSON)
    grid_columns = Column(Integer, default=2)  # 1, 2, 3, 4
    grid_gap = Column(String(20), default="medium")  # small, medium, large
    grid_style = Column(String(20), default="grid")  # grid, masonry
    
    # Настройки секции (JSON)
    settings = Column(JSON, nullable=True)  # Дополнительные настройки (НЕ стили!)
    
    # Видимость
    is_visible = Column(Boolean, default=True)
    
    # Метаданные
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Связи
    page = relationship("Page", back_populates="sections")
    blocks = relationship("ContentBlock", back_populates="section", cascade="all, delete-orphan", order_by="ContentBlock.position", lazy="joined")
    
    def __repr__(self):
        return f"<PageSection {self.section_type} page_id={self.page_id} pos={self.position}>"


class ContentBlock(Base):
    """Блоки контента внутри секций"""
    __tablename__ = "content_blocks"
    
    id = Column(Integer, primary_key=True, index=True)
    section_id = Column(Integer, ForeignKey("page_sections.id"), nullable=False, index=True)
    
    # Тип блока
    block_type = Column(String(100), nullable=False)  # heading, paragraph, button, image, card, stat, etc.
    position = Column(Integer, default=0)  # Порядок в секции
    
    # Контент блока (JSON)
    content = Column(JSON, nullable=False)  # {"text": "...", "url": "...", "alt": "...", etc.}
    
    # Стили (ТОЛЬКО CSS классы, НЕ инлайн!)
    css_classes = Column(Text, nullable=True)  # Например: "btn btn-primary btn-lg"
    
    # Видимость
    is_visible = Column(Boolean, default=True)
    
    # Метаданные
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Связи
    section = relationship("PageSection", back_populates="blocks")
    
    def __repr__(self):
        return f"<ContentBlock {self.block_type} section_id={self.section_id} pos={self.position}>"


# ============================================================================
# Article categories (hierarchical, with layout and sections)
# ============================================================================

class ArticleCategory(Base):
    """Категории статей (иерархия, мета, макет: с сайдбаром / без)"""
    __tablename__ = "article_categories"

    id = Column(Integer, primary_key=True, index=True)
    parent_id = Column(Integer, ForeignKey("article_categories.id"), nullable=True, index=True)

    slug = Column(String(255), nullable=False)  # slug внутри уровня (без пути)
    full_slug = Column(String(500), unique=True, index=True, nullable=False)  # путь: "usn" или "tax/usn"
    name = Column(String(255), nullable=False)

    # SEO
    meta_title = Column(String(255), nullable=True)
    meta_description = Column(Text, nullable=True)
    meta_keywords = Column(String(500), nullable=True)
    canonical_url = Column(String(500), nullable=True)

    # Макет страницы категории (как в layout v12)
    layout = Column(String(50), default="no_sidebar")  # with_sidebar | no_sidebar

    position = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    parent = relationship("ArticleCategory", remote_side=[id], back_populates="children")
    children = relationship("ArticleCategory", back_populates="parent", order_by="ArticleCategory.position")
    sections = relationship(
        "CategorySection",
        back_populates="category",
        cascade="all, delete-orphan",
        order_by="CategorySection.position",
    )

    articles = relationship("Article", back_populates="category", cascade="all, delete-orphan", order_by="Article.updated_at")
    def __repr__(self):
        return f"<ArticleCategory {self.full_slug}>"


class Article(Base):
    """Статья блога/новостей. Хранится в БД."""
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("article_categories.id"), nullable=True, index=True)

    slug = Column(String(255), unique=True, nullable=False, index=True)
    title = Column(String(500), nullable=False)
    excerpt = Column(Text, nullable=True)
    content = Column(Text, nullable=True)
    image = Column(String(500), nullable=True)

    meta_title = Column(String(255), nullable=True)
    meta_description = Column(Text, nullable=True)
    meta_keywords = Column(String(500), nullable=True)

    is_published = Column(Boolean, default=False)
    views = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    category = relationship("ArticleCategory", back_populates="articles")
    hub_section_links = relationship(
        "HubSectionArticle",
        back_populates="article",
        foreign_keys="HubSectionArticle.article_id",
    )

    def __repr__(self):
        return f"<Article {self.slug}>"


class ContentHub(Base):
    """Контентный хаб: тема + контент главной страницы хаба."""
    __tablename__ = "content_hubs"

    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String(255), unique=True, nullable=False, index=True)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=True)

    meta_title = Column(String(255), nullable=True)
    meta_description = Column(Text, nullable=True)
    meta_keywords = Column(String(500), nullable=True)

    position = Column(Integer, default=0)
    is_published = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    sections = relationship(
        "ContentHubSection",
        back_populates="hub",
        cascade="all, delete-orphan",
        order_by="ContentHubSection.position",
    )

    def __repr__(self):
        return f"<ContentHub {self.slug}>"


class ContentHubSection(Base):
    """Раздел хаба: свой текст + привязка статей."""
    __tablename__ = "content_hub_sections"

    id = Column(Integer, primary_key=True, index=True)
    hub_id = Column(Integer, ForeignKey("content_hubs.id"), nullable=False, index=True)

    slug = Column(String(255), nullable=False)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=True)

    meta_title = Column(String(255), nullable=True)
    meta_description = Column(Text, nullable=True)
    meta_keywords = Column(String(500), nullable=True)

    position = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    hub = relationship("ContentHub", back_populates="sections")
    article_links = relationship(
        "HubSectionArticle",
        back_populates="section",
        cascade="all, delete-orphan",
        order_by="HubSectionArticle.position",
    )

    __table_args__ = (UniqueConstraint("hub_id", "slug", name="uq_content_hub_section_hub_slug"),)

    def __repr__(self):
        return f"<ContentHubSection {self.hub_id}/{self.slug}>"


class HubSectionArticle(Base):
    """Связь раздела хаба с существующей статьёй (с порядком)."""
    __tablename__ = "hub_section_articles"

    id = Column(Integer, primary_key=True, index=True)
    section_id = Column(Integer, ForeignKey("content_hub_sections.id"), nullable=False, index=True)
    article_id = Column(Integer, ForeignKey("articles.id"), nullable=False, index=True)
    position = Column(Integer, default=0)

    section = relationship("ContentHubSection", back_populates="article_links")
    article = relationship("Article", back_populates="hub_section_links", foreign_keys=[article_id])

    __table_args__ = (UniqueConstraint("section_id", "article_id", name="uq_hub_section_article_section_article"),)

    def __repr__(self):
        return f"<HubSectionArticle section={self.section_id} article={self.article_id}>"


class CategorySection(Base):
    """Секции страницы категории (те же типы, что у PageSection)"""
    __tablename__ = "category_sections"

    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("article_categories.id"), nullable=False, index=True)

    section_type = Column(String(100), nullable=False)
    position = Column(Integer, default=0)

    background_style = Column(String(100), default="light")
    css_classes = Column(Text, nullable=True)
    container_width = Column(String(50), default="default")
    padding_y = Column(String(50), default="default")
    grid_columns = Column(Integer, default=2)
    grid_gap = Column(String(20), default="medium")
    grid_style = Column(String(20), default="grid")
    settings = Column(JSON, nullable=True)
    is_visible = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    category = relationship("ArticleCategory", back_populates="sections")
    blocks = relationship(
        "CategoryBlock",
        back_populates="section",
        cascade="all, delete-orphan",
        order_by="CategoryBlock.position",
        lazy="joined",
    )

    def __repr__(self):
        return f"<CategorySection {self.section_type} category_id={self.category_id} pos={self.position}>"


class CategoryBlock(Base):
    """Блоки контента внутри секций категории"""
    __tablename__ = "category_blocks"

    id = Column(Integer, primary_key=True, index=True)
    section_id = Column(Integer, ForeignKey("category_sections.id"), nullable=False, index=True)

    block_type = Column(String(100), nullable=False)
    position = Column(Integer, default=0)
    content = Column(JSON, nullable=False)
    css_classes = Column(Text, nullable=True)
    is_visible = Column(Boolean, default=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    section = relationship("CategorySection", back_populates="blocks")

    def __repr__(self):
        return f"<CategoryBlock {self.block_type} section_id={self.section_id} pos={self.position}>"


class AnalyticsEvent(Base):
    """События для аналитики"""
    __tablename__ = "analytics_events"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Тип события
    event_type = Column(String(100), nullable=False, index=True)  # page_view, document_created, payment, etc.
    
    # Пользователь (если авторизован)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    session_id = Column(String(100), nullable=True, index=True)  # Для гостей
    
    # Данные события (JSON) - переименовано из metadata (зарезервировано в SQLAlchemy)
    event_data = Column(JSON, nullable=True)  # Любые данные события
    
    # Технические данные
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    referrer = Column(String(500), nullable=True)
    
    # Метаданные
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Связи
    user = relationship("User")
    
    def __repr__(self):
        return f"<AnalyticsEvent {self.event_type} user_id={self.user_id}>"


class Document(Base):
    """Метаданные созданных документов (для аналитики)"""
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Пользователь
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    guest_draft_id = Column(Integer, ForeignKey("guest_drafts.id"), nullable=True)
    
    # Тип документа
    document_type = Column(String(50), nullable=False, index=True)  # upd, akt, schet
    document_subtype = Column(String(100), nullable=True)  # ooo, ip, s-nds, bez-nds, etc.
    
    # Идентификатор документа (папка на диске)
    document_id = Column(String(100), unique=True, index=True, nullable=False)
    
    # Статус
    status = Column(String(50), default="draft")  # draft, saved, exported, deleted
    
    # Данные документа (JSON) - переименовано из metadata (зарезервировано в SQLAlchemy)
    document_data = Column(JSON, nullable=True)  # Любые данные документа
    
    # Размер файла
    file_size_bytes = Column(Integer, nullable=True)
    
    # Метаданные
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    exported_at = Column(DateTime, nullable=True)  # Когда экспортирован в PDF
    
    # Связи
    user = relationship("User")
    guest_draft = relationship("GuestDraft")
    
    def __repr__(self):
        return f"<Document {self.document_id} type={self.document_type}>"


class Shortcode(Base):
    """Шорткоды: переиспользуемые блоки из шаблонов секций для вставки в контент."""
    __tablename__ = "shortcodes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)  # slug для [name]
    title = Column(String(255), nullable=False)  # название в админке

    # Ссылка на секцию страницы (созданную в визуальном редакторе)
    page_section_id = Column(Integer, ForeignKey("page_sections.id"), nullable=True, index=True)

    # Legacy: если page_section_id не задан, рендер из этих полей
    section_type = Column(String(100), nullable=True)
    section_settings = Column(JSON, nullable=True)
    blocks = Column(JSON, nullable=True)

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    page_section = relationship("PageSection", backref="shortcodes", foreign_keys=[page_section_id])

    def __repr__(self):
        return f"<Shortcode {self.name}>"


class NewsSidebarItem(Base):
    """Элемент сайдбара раздела «Новости»: порядок и тип (встроенный блок или шорткод)."""
    __tablename__ = "news_sidebar_items"

    id = Column(Integer, primary_key=True, index=True)
    position = Column(Integer, nullable=False, default=0)  # порядок вывода (меньше — выше)
    block_type = Column(String(50), nullable=False)  # cta_card | related_articles | shortcode
    shortcode_id = Column(Integer, ForeignKey("shortcodes.id"), nullable=True, index=True)  # только при block_type == shortcode

    shortcode = relationship("Shortcode", foreign_keys=[shortcode_id])

    def __repr__(self):
        return f"<NewsSidebarItem {self.block_type} pos={self.position}>"


class Redirect(Base):
    """301/302 редиректы для SEO"""
    __tablename__ = "redirects"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # URL
    from_url = Column(String(500), nullable=False, index=True)  # Старый URL
    to_url = Column(String(500), nullable=False)  # Новый URL
    
    # Тип редиректа
    status_code = Column(Integer, default=301)  # 301 (permanent) или 302 (temporary)
    
    # Статус
    is_active = Column(Boolean, default=True)
    
    # Метаданные
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Связи
    created_by = relationship("User")
    
    def __repr__(self):
        return f"<Redirect {self.from_url} → {self.to_url} ({self.status_code})>"
