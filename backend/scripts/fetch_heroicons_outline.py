#!/usr/bin/env python3
"""
Fetch all Heroicons v2 outline SVGs from GitHub and build heroicons-outline.json.
Run from backend: python scripts/fetch_heroicons_outline.py
Requires: requests (pip install requests)
"""
import json
import re
import sys
from pathlib import Path

try:
    import requests
except ImportError:
    print("Install requests: pip install requests")
    sys.exit(1)

API_LIST = "https://api.github.com/repos/tailwindlabs/heroicons/contents/optimized/24/outline"
OUT_PATH = Path(__file__).resolve().parent.parent / "app" / "static" / "data" / "heroicons-outline.json"


def extract_paths(svg_content: str) -> list:
    """Extract all path d="..." from SVG."""
    # Match <path ... d="..." ...> or <path d="...">
    pattern = r'<path[^>]*\sd="([^"]+)"'
    return re.findall(pattern, svg_content)


def main():
    print("Fetching icon list from GitHub...")
    r = requests.get(API_LIST, timeout=30)
    r.raise_for_status()
    files = [f for f in r.json() if f.get("name", "").endswith(".svg")]
    print(f"Found {len(files)} outline icons")

    result = []
    for i, f in enumerate(files):
        name = f["name"]
        icon_id = name.replace(".svg", "")
        download_url = f.get("download_url")
        if not download_url:
            print(f"  Skip {name}: no download_url")
            continue
        try:
            r2 = requests.get(download_url, timeout=10)
            r2.raise_for_status()
            paths = extract_paths(r2.text)
            if not paths:
                print(f"  Skip {name}: no paths found")
                continue
            if len(paths) == 1:
                result.append({"id": icon_id, "d": paths[0]})
            else:
                result.append({"id": icon_id, "paths": paths})
        except Exception as e:
            print(f"  Error {name}: {e}")
            continue
        if (i + 1) % 50 == 0:
            print(f"  Processed {i + 1}/{len(files)}")

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as out:
        json.dump(result, out, ensure_ascii=False, indent=2)
    print(f"Written {len(result)} icons to {OUT_PATH}")


if __name__ == "__main__":
    main()
