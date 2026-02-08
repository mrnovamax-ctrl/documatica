"""
Admin SEO Tools - инструменты для сеошников
"""

from datetime import datetime
import re
from typing import Optional
from fastapi import APIRouter, Request, Depends, Form, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models import Article, Page, Redirect
from app.core.templates import templates
from app.admin.context import require_admin, get_admin_context

router = APIRouter()


# Теги, внутри которых НЕ вставляем ссылки (заголовки, ячейки таблиц и т.д.)
EXCLUDED_TAGS = ("h1", "h2", "h3", "h4", "h5", "h6", "th", "figcaption", "caption", "label", "nav", "header")


def _is_inside_link(content: str, pos: int) -> bool:
    """
    Проверяет, находится ли позиция pos внутри тега <a>...</a>.
    """
    before = content[:pos]
    open_count = len(re.findall(r"<a\s", before, re.I))
    close_count = len(re.findall(r"</a\s*>", before, re.I))
    return open_count > close_count


def _is_inside_excluded_tag(content: str, pos: int) -> bool:
    """
    Проверяет, находится ли позиция pos внутри заголовка (h1-h6), th,
    figcaption, caption, label, nav, header. Ссылки вставляем только в текст (p, div, li и т.д.).
    """
    i = 0
    stack = []  # стек открытых исключённых тегов
    tag_re = re.compile(r"</?([a-zA-Z][a-zA-Z0-9]*)\b[^>]*>", re.I)

    while i < pos:
        m = tag_re.search(content, i)
        if not m:
            break
        i = m.end()
        tag_name = m.group(1).lower()
        if m.group(0).startswith("</"):
            if stack and stack[-1] == tag_name:
                stack.pop()
        elif tag_name in EXCLUDED_TAGS:
            stack.append(tag_name)

    return len(stack) > 0


def _count_links_to_url(content: str, target_url: str) -> int:
    """Считает количество ссылок на target_url в content (href равен или начинается с url)."""
    if not content or not target_url:
        return 0
    url = target_url.strip()
    if not url.startswith("/") and not url.startswith("http"):
        url = "/" + url
    escaped = re.escape(url)
    matches = re.findall(rf'href\s*=\s*["\']([^"\']+)["\']', content, re.I)
    return sum(1 for m in matches if m == url or m.startswith(url + "?") or m.startswith(url + "#"))


def _add_internal_links(
    content: str, phrase: str, target_url: str, max_per_article: int
) -> tuple[str, int]:
    """
    Ищет точные вхождения фразы в content (только в теле, не внутри ссылок),
    заменяет на ссылку. Учитывает уже существующие ссылки на этот URL.
    Возвращает (новый content, количество добавленных ссылок).
    """
    if not content or not phrase or not target_url:
        return content, 0
    phrase = phrase.strip()
    if not phrase:
        return content, 0

    # Нормализуем URL
    url = target_url.strip()
    if not url.startswith("/") and not url.startswith("http"):
        url = "/" + url

    # Сколько уже ссылок на этот URL
    existing = _count_links_to_url(content, url)
    slots = max(0, max_per_article - existing)
    if slots == 0:
        return content, 0

    added = 0
    pos = 0
    # Экранируем для regex
    escaped = re.escape(phrase)

    while added < slots:
        m = re.search(escaped, content[pos:], re.IGNORECASE)
        if not m:
            break
        start = pos + m.start()
        end = pos + m.end()
        matched_text = content[start:end]

        if _is_inside_link(content, start):
            pos = end
            continue
        if _is_inside_excluded_tag(content, start):
            pos = end
            continue

        link = f'<a href="{url}">{matched_text}</a>'
        content = content[:start] + link + content[end:]
        added += 1
        pos = start + len(link)

    return content, added


@router.get("/", response_class=HTMLResponse)
async def seo_tools_index(request: Request):
    """Главная страница SEO-инструментов"""
    auth_check = require_admin(request)
    if auth_check:
        return auth_check

    return templates.TemplateResponse(
        request=request,
        name="admin/seo_tools/index.html",
        context=get_admin_context(
            request=request,
            title="SEO-инструменты — Админ-панель",
            active_menu="seo_tools",
        ),
    )


@router.get("/interlinker/", response_class=HTMLResponse)
async def interlinker_form(request: Request):
    """Форма автоматического перелинковщика"""
    auth_check = require_admin(request)
    if auth_check:
        return auth_check

    return templates.TemplateResponse(
        request=request,
        name="admin/seo_tools/interlinker.html",
        context=get_admin_context(
            request=request,
            title="Перелинковщик — SEO-инструменты",
            active_menu="seo_tools",
        ),
    )


@router.post("/interlinker/", response_class=HTMLResponse)
async def interlinker_run(
    request: Request,
    db: Session = Depends(get_db),
    phrase: str = Form(""),
    target_url: str = Form(""),
    max_per_article: int = Form(1),
):
    """
    Выполнить перелинковку: найти фразу в content статей,
    вставить ссылку (не более max_per_article на статью).
    """
    auth_check = require_admin(request)
    if auth_check:
        return auth_check

    phrase = (phrase or "").strip()
    target_url = (target_url or "").strip()
    if max_per_article < 1:
        max_per_article = 1
    if max_per_article > 5:
        max_per_article = 5

    errors = []
    if not phrase:
        errors.append("Укажите ключевую фразу")
    if not target_url:
        errors.append("Укажите URL страницы для ссылки")

    if errors:
        return templates.TemplateResponse(
            request=request,
            name="admin/seo_tools/interlinker.html",
            context=get_admin_context(
                request=request,
                title="Перелинковщик — SEO-инструменты",
                active_menu="seo_tools",
                errors=errors,
                phrase=phrase,
                target_url=target_url,
                max_per_article=max_per_article,
            ),
        )

    # Статьи с непустым content
    articles = (
        db.query(Article)
        .filter(Article.content.isnot(None), Article.content != "")
        .all()
    )

    results = []
    total_added = 0

    for article in articles:
        if phrase.lower() not in (article.content or "").lower():
            continue
        new_content, added = _add_internal_links(
            article.content, phrase, target_url, max_per_article
        )
        if added > 0:
            article.content = new_content
            article.updated_at = datetime.utcnow()
            results.append(
                {
                    "id": article.id,
                    "title": article.title,
                    "slug": article.slug,
                    "added": added,
                }
            )
            total_added += added

    if results:
        db.commit()

    return templates.TemplateResponse(
        request=request,
        name="admin/seo_tools/interlinker.html",
        context=get_admin_context(
            request=request,
            title="Перелинковщик — SEO-инструменты",
            active_menu="seo_tools",
            success=True,
            phrase=phrase,
            target_url=target_url,
            max_per_article=max_per_article,
            results=results,
            total_added=total_added,
            articles_updated=len(results),
        ),
    )


# === Meta Editor ===
@router.get("/meta-editor/", response_class=HTMLResponse)
async def meta_editor(
    request: Request,
    db: Session = Depends(get_db),
    q: str = "",
    filter_empty: bool = False,
):
    auth_check = require_admin(request)
    if auth_check:
        return auth_check
    qry = db.query(Article).order_by(Article.updated_at.desc())
    if q:
        from sqlalchemy import or_
        qry = qry.filter(
            or_(
                Article.title.ilike(f"%{q}%"),
                Article.meta_title.ilike(f"%{q}%"),
                Article.meta_description.ilike(f"%{q}%"),
            )
        )
    articles = qry.all()
    if filter_empty:
        articles = [a for a in articles if not (a.meta_title and a.meta_description)]
    return templates.TemplateResponse(
        request=request,
        name="admin/seo_tools/meta_editor.html",
        context=get_admin_context(
            request=request,
            title="Редактор meta — SEO",
            active_menu="seo_tools",
            articles=articles,
            search_query=q,
            filter_empty=filter_empty,
        ),
    )


@router.post("/meta-editor/", response_class=RedirectResponse)
async def meta_editor_save(
    request: Request,
    db: Session = Depends(get_db),
):
    auth_check = require_admin(request)
    if auth_check:
        return auth_check
    form = await request.form()
    for key, val in form.items():
        if key.startswith("meta_title_"):
            aid = key.replace("meta_title_", "")
            if aid.isdigit():
                a = db.query(Article).filter(Article.id == int(aid)).first()
                if a:
                    a.meta_title = (val or "").strip() or None
                    a.updated_at = datetime.utcnow()
        elif key.startswith("meta_desc_"):
            aid = key.replace("meta_desc_", "")
            if aid.isdigit():
                a = db.query(Article).filter(Article.id == int(aid)).first()
                if a:
                    a.meta_description = (val or "").strip() or None
    db.commit()
    return RedirectResponse(url="/admin/seo-tools/meta-editor/?saved=1", status_code=303)


# === Redirect Manager ===
@router.get("/redirects/", response_class=HTMLResponse)
async def redirects_list(request: Request, db: Session = Depends(get_db)):
    auth_check = require_admin(request)
    if auth_check:
        return auth_check
    items = db.query(Redirect).order_by(Redirect.from_url).all()
    return templates.TemplateResponse(
        request=request,
        name="admin/seo_tools/redirects.html",
        context=get_admin_context(
            request=request,
            title="Менеджер редиректов — SEO",
            active_menu="seo_tools",
            redirects=items,
        ),
    )


@router.post("/redirects/add/", response_class=RedirectResponse)
async def redirects_add(
    request: Request,
    db: Session = Depends(get_db),
    from_url: str = Form(""),
    to_url: str = Form(""),
    status_code: int = Form(301),
):
    auth_check = require_admin(request)
    if auth_check:
        return auth_check
    from_url = (from_url or "").strip()
    to_url = (to_url or "").strip()
    if not from_url or not to_url:
        return RedirectResponse(url="/admin/seo-tools/redirects/?error=empty", status_code=303)
    if not from_url.startswith("/"):
        from_url = "/" + from_url
    if not to_url.startswith("/") and not to_url.startswith("http"):
        to_url = "/" + to_url
    if not from_url.endswith("/") and "?" not in from_url:
        from_url = from_url + "/"
    r = Redirect(from_url=from_url, to_url=to_url, status_code=status_code, is_active=True)
    db.add(r)
    db.commit()
    return RedirectResponse(url="/admin/seo-tools/redirects/?added=1", status_code=303)


@router.get("/redirects/delete/{rid}/", response_class=RedirectResponse)
async def redirects_delete(
    request: Request,
    rid: int,
    db: Session = Depends(get_db),
):
    auth_check = require_admin(request)
    if auth_check:
        return auth_check
    r = db.query(Redirect).filter(Redirect.id == rid).first()
    if r:
        db.delete(r)
        db.commit()
    return RedirectResponse(url="/admin/seo-tools/redirects/?deleted=1", status_code=303)


# === Internal Link Checker ===
def _extract_internal_links(content: str) -> list[str]:
    if not content:
        return []
    matches = re.findall(r'href\s*=\s*["\']([^"\']+)["\']', content, re.I)
    result = []
    for m in matches:
        m = m.split("?")[0].split("#")[0]
        if m.startswith("/") and not m.startswith("//") and not m.startswith("/static"):
            result.append(m.rstrip("/") or "/")
        elif m.startswith("https://oplatanalogov.ru/"):
            path = m.replace("https://oplatanalogov.ru", "").split("?")[0].split("#")[0]
            result.append(path.rstrip("/") or "/")
    return result


def _resolve_internal_path(path: str, db: Session) -> bool:
    path = path.strip("/") or ""
    if not path:
        return True
    parts = path.split("/")
    if parts[0] == "news":
        slug = "/".join(parts[1:]) if len(parts) > 1 else ""
        if not slug:
            return True
        return db.query(Article).filter(Article.slug == slug).first() is not None
    page = db.query(Page).filter(Page.slug == path, Page.status == "published").first()
    if page:
        return True
    if path in ("upd", "schet", "akt", "news", "about", "contact", "privacy", "agreement"):
        return True
    return False


@router.get("/link-checker/", response_class=HTMLResponse)
async def link_checker(request: Request, db: Session = Depends(get_db)):
    auth_check = require_admin(request)
    if auth_check:
        return auth_check
    broken = []
    articles = db.query(Article).filter(Article.content.isnot(None)).all()
    seen_links = set()
    for a in articles:
        links = _extract_internal_links(a.content)
        for link in links:
            key = (a.id, link)
            if key in seen_links:
                continue
            seen_links.add(key)
            if not _resolve_internal_path(link, db):
                broken.append({"article_id": a.id, "article_title": a.title, "article_slug": a.slug, "broken_url": link})
    return templates.TemplateResponse(
        request=request,
        name="admin/seo_tools/link_checker.html",
        context=get_admin_context(
            request=request,
            title="Проверка ссылок — SEO",
            active_menu="seo_tools",
            broken=broken,
        ),
    )


# === Orphan Pages ===
def _collect_inbound_links(db: Session) -> set[str]:
    from sqlalchemy.orm import joinedload
    out = set()
    articles = db.query(Article).filter(Article.content.isnot(None)).all()
    for a in articles:
        for link in _extract_internal_links(a.content):
            p = link.strip("/") or ""
            out.add(p)
            out.add(f"news/{p}" if not p.startswith("news/") else p)
    pages = (
        db.query(Page)
        .options(joinedload(Page.sections).joinedload("blocks"))
        .filter(Page.status == "published")
        .all()
    )
    for p in pages:
        for s in p.sections:
            for b in getattr(s, "blocks", []) or []:
                c = b.content or {}
                txt = c.get("text", "") if isinstance(c, dict) else str(c)
                for link in _extract_internal_links(txt):
                    pp = link.strip("/") or ""
                    out.add(pp)
    return out


@router.get("/orphans/", response_class=HTMLResponse)
async def orphans(request: Request, db: Session = Depends(get_db)):
    auth_check = require_admin(request)
    if auth_check:
        return auth_check
    inbound = _collect_inbound_links(db)
    orphans_articles = []
    for a in db.query(Article).filter(Article.is_published == True).all():
        slug_path = f"news/{a.slug}"
        if slug_path not in inbound and a.slug not in inbound:
            orphans_articles.append({"type": "article", "title": a.title, "slug": a.slug, "url": f"/news/{a.slug}/"})
    orphans_pages = []
    for p in db.query(Page).filter(Page.status == "published").all():
        if p.slug == "home" or p.slug == "":
            continue
        if p.slug not in inbound and f"/{p.slug}" not in inbound:
            orphans_pages.append({"type": "page", "title": p.title, "slug": p.slug, "url": f"/{p.slug}/"})
    return templates.TemplateResponse(
        request=request,
        name="admin/seo_tools/orphans.html",
        context=get_admin_context(
            request=request,
            title="Страницы-сироты — SEO",
            active_menu="seo_tools",
            orphans_articles=orphans_articles,
            orphans_pages=orphans_pages,
        ),
    )


# === Duplicate Meta ===
@router.get("/duplicates/", response_class=HTMLResponse)
async def duplicates(request: Request, db: Session = Depends(get_db)):
    auth_check = require_admin(request)
    if auth_check:
        return auth_check
    rows = (
        db.query(Article.meta_description, func.count(Article.id).label("cnt"))
        .filter(Article.meta_description.isnot(None), Article.meta_description != "")
        .group_by(Article.meta_description)
        .having(func.count(Article.id) > 1)
        .all()
    )
    groups = []
    for meta_desc, cnt in rows:
        arts = db.query(Article).filter(Article.meta_description == meta_desc).all()
        groups.append({"meta_description": meta_desc[:80] + "..." if len(meta_desc) > 80 else meta_desc, "count": cnt, "articles": arts})
    return templates.TemplateResponse(
        request=request,
        name="admin/seo_tools/duplicates.html",
        context=get_admin_context(
            request=request,
            title="Дубликаты meta description — SEO",
            active_menu="seo_tools",
            groups=groups,
        ),
    )
