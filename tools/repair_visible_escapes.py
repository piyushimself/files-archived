#!/usr/bin/env python3
"""Repair escaped newlines/tabs in visible HTML text nodes, preserving script/style/code."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
TOKEN_RE = re.compile(
    r'(?is)(<(script|style|pre|code|textarea)\b[^>]*>.*?</\2\s*>'
    r'|<!--.*?-->|<[^>]+>|[^<]+)'
)

def repair_text_node(value):
    return (value.replace("\\r\\n", "\n")
                 .replace("\\n", "\n")
                 .replace("\\r", "\n")
                 .replace("\\t", " "))

def repair_html(source):
    changed = 0
    def replace_token(match):
        nonlocal changed
        token = match.group(0)
        if token.startswith("<"):
            return token
        updated = repair_text_node(token)
        if updated != token:
            changed += 1
        return updated
    return TOKEN_RE.sub(replace_token, source), changed

def main():
    files = sorted(p for p in ROOT.rglob("*.html") if ".git" not in p.parts and "node_modules" not in p.parts)
    total, changed_files = 0, []
    for path in files:
        original = path.read_text(encoding="utf-8", errors="replace")
        updated, count = repair_html(original)
        if count:
            path.write_text(updated, encoding="utf-8")
            total += count
            changed_files.append((path.relative_to(ROOT).as_posix(), count))
    print("Visible escaped sequences repaired:", total, "in", len(changed_files), "HTML files")
    for name, count in changed_files:
        print(" -", name, ":", count)

if __name__ == "__main__":
    main()
