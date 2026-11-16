#!/usr/bin/env python3
"""Convert repository PDFs and DOCX files into searchable, responsive HTML readers."""
from pathlib import Path
from html import escape
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "html"
OUT.mkdir(exist_ok=True)

def extract_pdf(path):
    result = subprocess.run(
        ["pdftotext", "-layout", "-enc", "UTF-8", str(path), "-"],
        check=True, capture_output=True, text=True
    )
    text = result.stdout.strip()
    if text:
        return text
    # OCR fallback for image-only PDFs. Only invoked when normal text extraction is empty.
    pages = []
    with tempfile.TemporaryDirectory() as tmp:
        prefix = str(Path(tmp) / "page")
        subprocess.run(["pdftoppm", "-r", "160", "-png", str(path), prefix],
                       check=True, capture_output=True)
        for image in sorted(Path(tmp).glob("page-*.png")):
            page = subprocess.run(["tesseract", str(image), "stdout"],
                                  check=True, capture_output=True, text=True)
            pages.append(page.stdout.strip())
    return "\n\f\n".join(pages)

def extract_docx(path):
    from docx import Document
    doc = Document(path)
    blocks = []
    for paragraph in doc.paragraphs:
        value = paragraph.text.strip()
        if value:
            style = paragraph.style.name if paragraph.style else ""
            blocks.append(("heading" if style.lower().startswith("heading") or style == "Title" else "text", value))
    for table in doc.tables:
        blocks.append(("table", [[cell.text.strip() for cell in row.cells] for row in table.rows]))
    return blocks

def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-") or "section"

def looks_like_heading(line):
    line = line.strip()
    if not line or len(line) > 100 or len(line) < 3:
        return False
    if line.startswith(("#", "•", "-", "–", "—")):
        return False
    words = line.split()
    if len(words) <= 9 and (line.isupper() or (line.istitle() and not line.endswith((".", ",", ";", ":")))):
        return True
    return False

def render_pdf_blocks(text):
    pages = text.replace("\r\n", "\n").replace("\r", "\n").split("\f")
    rendered, toc, used = [], [], set()
    for number, raw in enumerate(pages, 1):
        lines = [re.sub(r"[ \t]+", " ", x).strip() for x in raw.splitlines()]
        lines = [x for x in lines if x]
        if not lines:
            continue
        parts, paragraph = [], []
        def flush():
            if paragraph:
                parts.append("<p>" + escape(" ".join(paragraph)) + "</p>")
                paragraph.clear()
        for line in lines:
            if looks_like_heading(line):
                flush()
                heading = line.lstrip("# ").strip()
                base = slug(heading)
                anchor, suffix = base, 2
                while anchor in used:
                    anchor, suffix = base + "-" + str(suffix), suffix + 1
                used.add(anchor)
                toc.append((anchor, heading))
                parts.append('<h2 id="' + anchor + '">' + escape(heading) + '</h2>')
            else:
                paragraph.append(line)
        flush()
        rendered.append('<section class="page" id="page-' + str(number) + '"><div class="page-label">PAGE ' + str(number) + '</div>' + "\n".join(parts) + '</section>')
    return rendered, toc

def render_docx_blocks(blocks):
    parts, toc, used = [], [], set()
    for kind, value in blocks:
        if kind == "heading":
            base = slug(value)
            anchor, suffix = base, 2
            while anchor in used:
                anchor, suffix = base + "-" + str(suffix), suffix + 1
            used.add(anchor)
            toc.append((anchor, value))
            parts.append('<h2 id="' + anchor + '">' + escape(value) + '</h2>')
        elif kind == "table":
            rows = "".join("<tr>" + "".join("<td>" + escape(c) + "</td>" for c in row) + "</tr>" for row in value)
            parts.append('<div class="table-wrap"><table>' + rows + '</table></div>')
        else:
            parts.append("<p>" + escape(value) + "</p>")
    return ['<section class="page">' + "\n".join(parts) + '</section>'], toc

def make_reader(source, title, kind, sections, toc):
    safe_title = escape(title)
    source_rel = "../" + source.relative_to(ROOT).as_posix()
    nav = "".join('<a href="#' + escape(anchor) + '">' + escape(label) + '</a>' for anchor, label in toc)
    body = "\n".join(sections)
    toc_block = '<nav class="toc"><div class="toc-title">ON THIS PAGE</div>' + nav + '</nav>' if nav else ""
    return """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="Accessible HTML reading edition of """ + safe_title + """.">
<title>""" + safe_title + """ — Reading Edition</title>
<style>
:root{color-scheme:light;--bg:#f5f3ee;--paper:#fffefa;--ink:#252923;--muted:#687168;--line:#e2e0d8;--accent:#356b68;--soft:#eaf0ed}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.75 system-ui,-apple-system,Segoe UI,sans-serif}
header{background:var(--paper);border-bottom:1px solid var(--line);position:sticky;top:0;z-index:5}
.top{max-width:1180px;margin:auto;padding:12px 22px;display:flex;align-items:center;gap:14px}.brand{font-size:12px;font-weight:750;letter-spacing:.12em;text-transform:uppercase;color:var(--accent);white-space:nowrap}
.search{flex:1;min-width:120px;border:1px solid var(--line);border-radius:8px;padding:9px 12px;font:inherit;font-size:14px;background:var(--bg);color:var(--ink)}
button,.link{border:1px solid var(--line);border-radius:8px;padding:8px 11px;background:var(--paper);color:var(--ink);font:inherit;font-size:13px;text-decoration:none;cursor:pointer}
button:hover,.link:hover{border-color:var(--accent)}.layout{max-width:1180px;margin:30px auto;padding:0 22px;display:grid;grid-template-columns:230px minmax(0,1fr);gap:30px}
.toc{position:sticky;top:82px;align-self:start;max-height:calc(100vh - 110px);overflow:auto;padding:16px;background:var(--paper);border:1px solid var(--line);border-radius:12px}
.toc-title,.page-label{font-size:10px;font-weight:750;letter-spacing:.14em;color:var(--muted)}.toc a{display:block;color:var(--muted);font-size:13px;text-decoration:none;padding:5px 0;border-bottom:1px solid var(--line)}.toc a:hover{color:var(--accent)}
article{min-width:0}.hero{padding:26px 30px;background:var(--paper);border:1px solid var(--line);border-radius:14px;margin-bottom:18px}
.kicker{font-size:11px;letter-spacing:.13em;text-transform:uppercase;color:var(--accent);font-weight:750}.hero h1{font-size:clamp(26px,4vw,40px);line-height:1.2;letter-spacing:-.03em;margin:9px 0 8px}.meta{font-size:13px;color:var(--muted)}
.page{background:var(--paper);border:1px solid var(--line);border-radius:12px;padding:28px 34px;margin:14px 0;overflow-wrap:anywhere}
.page-label{margin-bottom:12px}h2{font-size:22px;line-height:1.3;margin:24px 0 10px;scroll-margin-top:90px}p{margin:0 0 14px}p:last-child{margin-bottom:0}
.table-wrap{overflow-x:auto}table{border-collapse:collapse;width:100%;font-size:14px}td{border:1px solid var(--line);padding:8px;vertical-align:top}
.empty{color:var(--muted);padding:18px;text-align:center}.footer{color:var(--muted);font-size:12px;padding:18px 4px}
@media(max-width:760px){.top{padding:10px 14px;gap:8px;flex-wrap:wrap}.brand{width:100%}.search{order:2;flex-basis:100%}.layout{display:block;margin:16px auto;padding:0 12px}.toc{position:static;max-height:220px;margin-bottom:14px}.hero{padding:20px}.page{padding:20px 18px}body{font-size:15px}}
@media(prefers-color-scheme:dark){:root{color-scheme:dark;--bg:#151816;--paper:#1d211e;--ink:#e8ece6;--muted:#a0aaa1;--line:#343b35;--accent:#8bc5b5;--soft:#27332e}.search{background:#151816}}
</style></head><body>
<header><div class="top"><a class="brand" href="index.html" style="text-decoration:none">THE READING ARCHIVE</a>
<input id="search" class="search" type="search" placeholder="Search within this document…" aria-label="Search within this document">
<a class="link" href=""" + '"' + escape(source_rel) + '"' + """ target="_blank" rel="noopener">Original """ + kind + """ ↗</a></div></header>
<div class="layout">""" + toc_block + """<article><section class="hero"><div class="kicker">HTML READING EDITION · """ + kind + """</div><h1>""" + safe_title + """</h1><div class="meta">Converted from the original source · Text may require review against the original document</div></section>
<div id="content">""" + body + """</div><div class="footer">Reading edition generated from <a href=""" + '"' + escape(source_rel) + '"' + """>""" + escape(source.name) + """</a>. The original file is preserved unchanged.</div></article></div>
<script>
const q=document.getElementById('search'), pages=[...document.querySelectorAll('.page')];
q.addEventListener('input',()=>{const term=q.value.trim().toLowerCase();pages.forEach(p=>{p.hidden=!!term&&!p.innerText.toLowerCase().includes(term)})});
</script></body></html>"""

def main():
    sources = sorted([*ROOT.glob("*.pdf"), *ROOT.glob("*.docx")], key=lambda p:p.name.lower())
    catalogue = []
    for source in sources:
        title = source.stem.replace("_", " ").replace("-", " ")
        kind = source.suffix[1:].upper()
        try:
            if source.suffix.lower() == ".pdf":
                sections, toc = render_pdf_blocks(extract_pdf(source))
            else:
                sections, toc = render_docx_blocks(extract_docx(source))
            if not sections:
                sections = ['<section class="page"><p>No extractable text was found. Please consult the original document.</p></section>']
            filename = source.stem + ".html"
            (OUT / filename).write_text(make_reader(source, title, kind, sections, toc), encoding="utf-8")
            catalogue.append((title, filename, source.name, kind, len(sections)))
            print("Converted:", source.name, "->", filename)
        except Exception as exc:
            print("ERROR:", source.name, str(exc))
            raise
    cards = []
    for title, filename, original, kind, count in catalogue:
        cards.append('<a class="item" href="' + escape(filename) + '"><strong>' + escape(title) + '</strong><span>' + escape(kind) + ' · ' + str(count) + ' content sections</span><small>Original: ' + escape(original) + '</small></a>')
    index = """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Document Reading Archive</title><style>
:root{--bg:#f5f3ee;--paper:#fffefa;--ink:#252923;--muted:#687168;--line:#e2e0d8;--accent:#356b68}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.6 system-ui,sans-serif}.wrap{max-width:1100px;margin:48px auto;padding:0 22px}header{margin-bottom:24px}.k{font-size:11px;letter-spacing:.15em;color:var(--accent);font-weight:800}h1{font-size:clamp(28px,5vw,44px);line-height:1.15;margin:8px 0}.sub{color:var(--muted)}input{width:100%;padding:12px 14px;border:1px solid var(--line);border-radius:9px;background:var(--paper);font:inherit;margin:14px 0 20px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:12px}.item{display:flex;flex-direction:column;gap:5px;text-decoration:none;color:var(--ink);background:var(--paper);border:1px solid var(--line);border-radius:11px;padding:16px}.item:hover{border-color:var(--accent);transform:translateY(-1px)}.item span,.item small{color:var(--muted);font-size:12px}.count{font-size:13px;color:var(--muted)}@media(prefers-color-scheme:dark){:root{--bg:#151816;--paper:#1d211e;--ink:#e8ece6;--muted:#a0aaa1;--line:#343b35;--accent:#8bc5b5}}@media(max-width:600px){.wrap{margin:28px auto;padding:0 14px}.grid{grid-template-columns:1fr}}</style></head><body><main class="wrap"><header><div class="k">THE READING ARCHIVE</div><h1>Document Library</h1><p class="sub">Search and read the HTML editions. Original PDFs and DOCX files remain in the repository.</p><div class="count">""" + str(len(catalogue)) + """ converted documents</div></header><input id="q" type="search" placeholder="Search titles or original filenames…" aria-label="Search documents"><div class="grid" id="grid">""" + "".join(cards) + """</div></main><script>const q=document.getElementById('q');q.addEventListener('input',()=>{const v=q.value.toLowerCase();document.querySelectorAll('.item').forEach(x=>x.hidden=!x.innerText.toLowerCase().includes(v))});</script></body></html>"""
    (OUT / "index.html").write_text(index, encoding="utf-8")
    print("Generated", len(catalogue), "HTML readers and index.")

if __name__ == "__main__":
    main()
