"""
Table of contents: add ids to headings in article HTML and extract TOC items.
"""

import re
import unicodedata
from typing import TypedDict


class TocItem(TypedDict):
    level: int
    text: str
    id: str


def _slug_for_id(text: str) -> str:
    s = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    s = re.sub(r"[^\w\s-]", "", s).lower()
    s = re.sub(r"[-\s]+", "-", s).strip("-")
    return s[:50] if s else "section"


def process_article_toc(html: str) -> tuple[str, list[TocItem]]:
    """
    Add id attributes to h1, h2, h3, h4 headings and return (modified_html, toc_items).
    """
    toc: list[TocItem] = []
    used_ids: set[str] = set()

    def replace_heading(m: re.Match) -> str:
        tag = m.group(1).lower()
        inner = m.group(2)
        text = re.sub(r"<[^>]+>", "", inner).strip()
        level = int(tag[1])
        base = _slug_for_id(text) or "s"
        aid = base
        n = 1
        while aid in used_ids:
            aid = f"{base}-{n}"
            n += 1
        used_ids.add(aid)
        toc.append({"level": level, "text": text[:80], "id": aid})
        return f'<{tag} id="{aid}">{inner}</{tag}>'

    pattern = re.compile(r"<(h[1-4])(?:\s[^>]*)?>(.*?)</\1>", re.DOTALL | re.IGNORECASE)
    result = pattern.sub(replace_heading, html)
    return result, toc
