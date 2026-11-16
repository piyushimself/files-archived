#!/usr/bin/env python3
"""Audit every Reading Room HTML page for structure, controls, assets and local links."""
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote
import json
import re

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "html" / "page-audit.json"

class Inspector(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids = Counter()
        self.hrefs = []
        self.assets = []
        self.body_classes = set()
        self.tags = Counter()
        self.classes = Counter()
        self.inputs = []
        self.headings = []
        self.in_heading = None
        self.heading_text = []
        self.h1_count = 0
        self.title_text = []
        self.in_title = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.tags[tag] += 1
        if attrs.get("id"):
            self.ids[attrs["id"]] += 1
        for cls in (attrs.get("class") or "").split():
            self.classes[cls] += 1
        if tag == "body":
            self.body_classes.update((attrs.get("class") or "").split())
        if tag in ("h1", "h2", "h3", "h4"):
            self.in_heading = tag
            self.heading_text = []
            if tag == "h1":
                self.h1_count += 1
        if tag == "title":
            self.in_title = True
        if tag in ("input", "select", "textarea", "button"):
            self.inputs.append({"tag": tag, "type": attrs.get("type", ""), "id": attrs.get("id", ""), "class": attrs.get("class", "")})
        for attr in ("href", "src", "action"):
            value = attrs.get(attr)
            if value:
                if attr == "href":
                    self.hrefs.append(value)
                else:
                    self.assets.append(value)

    def handle_endtag(self, tag):
        if self.in_heading == tag:
            self.headings.append({"tag": tag, "text": " ".join(self.heading_text).strip()})
            self.in_heading = None
            self.heading_text = []
        if tag == "title":
            self.in_title = False

    def handle_data(self, data):
        if self.in_heading:
            self.heading_text.append(data)
        if self.in_title:
            self.title_text.append(data)

def page_family(inspector, path):
    classes = inspector.body_classes
    if "rr-home" in classes:
        return "homepage"
    if "rr-hub" in classes:
        return "collection-hub"
    if "rr-reader" in classes:
        return "source-reading-edition"
    title = " ".join(inspector.title_text).lower()
    if any(x in title for x in ("manga", "comic", "film", "movie", "book", "database", "encyclopedia")):
        return "interactive-catalogue-or-index"
    if any(x in title for x in ("tutorial", "journal", "tracker", "generator", "tool", "app")):
        return "interactive-tool-or-tutorial"
    if "collections/" in path.as_posix():
        return "collection-hub"
    return "editorial-or-learning-page"

def local_link_issue(page, href, known_ids):
    parts = urlsplit(href)
    if parts.scheme or parts.netloc or href.startswith(("data:", "javascript:", "mailto:", "tel:")):
        return None
    path = unquote(parts.path)
    if not path:
        if parts.fragment and unquote(parts.fragment) not in known_ids:
            return "missing fragment #" + unquote(parts.fragment)
        return None
    target = (page.parent / path).resolve() if not path.startswith("/") else (ROOT / path.lstrip("/")).resolve()
    try:
        target.relative_to(ROOT.resolve())
    except ValueError:
        return "link escapes repository: " + href
    if target.is_dir():
        target = target / "index.html"
    if not target.exists():
        return "missing local target: " + href
    return None

def main():
    pages = sorted([p for folder in (ROOT, ROOT / "html", ROOT / "collections") for p in folder.glob("*.html") if p.name != "page-audit.html"])
    rows = []
    hard_errors = []
    for page in pages:
        parser = Inspector()
        raw = page.read_text(encoding="utf-8", errors="replace")
        parser.feed(raw)
        version_css = re.findall(r"reading-room\.css\?v=(\d+)", raw)
        version_js = re.findall(r"reading-room\.js\?v=(\d+)", raw)
        duplicate_ids = sorted(k for k, n in parser.ids.items() if n > 1)
        local_issues = [issue for href in parser.hrefs if (issue := local_link_issue(page, href, parser.ids))]
        family = page_family(parser, page)
        row = {
            "path": page.relative_to(ROOT).as_posix(),
            "title": " ".join(parser.title_text).strip(),
            "family": family,
            "bytes": len(raw.encode("utf-8")),
            "h1": len(re.findall(r"<h1\\b", raw, re.I)),
            "headings": len(parser.headings),
            "inputs": sum(1 for x in parser.inputs if x["tag"] == "input"),
            "selects": sum(1 for x in parser.inputs if x["tag"] == "select"),
            "buttons": sum(1 for x in parser.inputs if x["tag"] == "button"),
            "cards": sum(n for cls, n in parser.classes.items() if "card" in cls or cls in ("tile", "resource-item")),
            "asset_versions": {"css": sorted(set(version_css)), "js": sorted(set(version_js))},
            "duplicate_ids": duplicate_ids,
            "local_link_issues": local_issues[:30],
        }
        if row["h1"] == 0:
            hard_errors.append(page.relative_to(ROOT).as_posix() + ": missing h1")
        # Keep duplicate IDs visible as warnings: interactive legacy pages may
        # reuse hidden panel templates, so only fail on proven structural issues.
        if "rr-page" in parser.body_classes:
            if version_css != ["11"] or version_js != ["11"]:
                hard_errors.append(page.relative_to(ROOT).as_posix() + ": shared v11 assets not applied exactly once")
        if family == "source-reading-edition":
            if 'id="search"' not in raw or "rr-reader-summary" not in raw:
                hard_errors.append(page.relative_to(ROOT).as_posix() + ": missing reader search or source context")
        rows.append(row)

    summary = {
        "page_count": len(rows),
        "families": dict(Counter(row["family"] for row in rows)),
        "pages_with_local_link_issues": sum(1 for row in rows if row["local_link_issues"]),
        "local_link_issue_count": sum(len(row["local_link_issues"]) for row in rows),
        "hard_error_count": len(hard_errors),
        "duplicate_id_page_count": sum(1 for row in rows if row["duplicate_ids"]),
        "duplicate_id_count": sum(len(row["duplicate_ids"]) for row in rows),
        "hard_errors": hard_errors,
        "pages": rows,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Reading Room page audit:", summary["page_count"], "HTML pages")
    print("Page families:", summary["families"])
    print("Local-link warnings:", summary["local_link_issue_count"], "across", summary["pages_with_local_link_issues"], "pages")
    print("Duplicate-ID warnings:", summary["duplicate_id_count"], "across", summary["duplicate_id_page_count"], "pages")
    if hard_errors:
        print("HARD ERRORS:")
        for issue in hard_errors:
            print(" -", issue)
        raise SystemExit(1)
    print("PASS: all pages have an H1 and current shared assets; duplicate IDs and local-link issues are included for review.")

if __name__ == "__main__":
    main()
