"""
Single source of truth for Heroicons outline (v12 icon library).
Icons are stored in static/data/heroicons-outline.json.
Use get_icon_paths_html() for Jinja templates; frontend picker fetches the same JSON.
"""
import json
from pathlib import Path
from typing import Dict, List, Any, Optional

# Path to the single JSON file (relative to app package)
_STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
_ICONS_JSON = _STATIC_DIR / "data" / "heroicons-outline.json"

_icon_paths_html_cache: Optional[Dict[str, str]] = None


def _load_icons_raw() -> List[Dict[str, Any]]:
    """Load the icons array from JSON. Raises if file missing."""
    with open(_ICONS_JSON, "r", encoding="utf-8") as f:
        return json.load(f)


def _icon_to_html(icon: Dict[str, Any]) -> str:
    """Convert one icon record to full path HTML (stroke-linecap/join round)."""
    attrs = ' stroke-linecap="round" stroke-linejoin="round"'
    if icon.get("paths"):
        return "".join(
            f'<path d="{d}"{attrs}></path>' for d in icon["paths"]
        )
    d = icon.get("d", "")
    return f'<path d="{d}"{attrs}></path>'


def get_icon_paths_html() -> Dict[str, str]:
    """
    Returns a dict: icon_id -> full HTML string for <path>(s).
    Used by Jinja in features.html and document_types.html.
    Cached after first load.
    """
    global _icon_paths_html_cache
    if _icon_paths_html_cache is not None:
        return _icon_paths_html_cache
    icons = _load_icons_raw()
    _icon_paths_html_cache = {
        item["id"]: _icon_to_html(item)
        for item in icons
    }
    return _icon_paths_html_cache


def get_icons_list() -> List[Dict[str, Any]]:
    """Return raw list of icon objects (for API or inline JSON)."""
    return _load_icons_raw()
