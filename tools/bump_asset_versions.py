#!/usr/bin/env python3
"""Refresh shared Reading Room asset URLs in every HTML file."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ("reading-room.css", "reading-room.js", "reading-room-context.js")
VERSION = "17"

def main():
    files = sorted(p for p in ROOT.rglob("*.html") if ".git" not in p.parts and "node_modules" not in p.parts)
    updated = 0
    for page in files:
        text = page.read_text(encoding="utf-8", errors="replace")
        before = text
        for asset in ASSETS:
            text = re.sub(
                rf"({re.escape(asset)}\?v=)\d+",
                rf"\g<1>{VERSION}",
                text,
            )
        if text != before:
            page.write_text(text, encoding="utf-8")
            updated += 1
    print(f"Updated shared asset URLs to v{VERSION} in {updated} HTML pages (of {len(files)}).")

if __name__ == "__main__":
    main()
