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
    category, description, _ = classify_resource(title)
    theme = {
        "Film & Cinema": "cinema",
        "Home Learning & Education": "learning",
        "Poetry & Writing": "literary",
        "Music & Listening": "mixed",
        "Music & Cross-Media": "mixed",
        "Cross-Media Discovery": "mixed",
        "Anime & Manga": "manga",
        "Art & Creative Practice": "art",
        "Ideas & Reflection": "literary",
        "Technology & Security": "tools",
        "Interactive Tools": "tools",
        "Personal Journals & Tools": "tools",
        "Writing Tools": "art",
        "Reference & Discovery": "mixed",
        "Explore & Miscellany": "mixed",
    }.get(category, "mixed")
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
</style><link rel="stylesheet" href="../assets/reading-room.css"></head><body class="rr-page rr-reader rr--""" + theme + """">
<nav class="rr-contextbar"><a href="../index.html">← THE READING ROOM</a><span><em>""" + escape(category) + """</em> · """ + escape(description) + """</span></nav>
<header><div class="top"><a class="brand" href="index.html" style="text-decoration:none">THE READING ARCHIVE</a>
<input id="search" class="search" type="search" placeholder="Search within this document…" aria-label="Search within this document">
<a class="link" href=""" + '"' + escape(source_rel) + '"' + """ target="_blank" rel="noopener">Original """ + kind + """ ↗</a></div></header>
<div class="layout">""" + toc_block + """<article><section class="hero"><div class="kicker">HTML READING EDITION · """ + kind + """</div><h1>""" + safe_title + """</h1><div class="meta">Converted from the original source · Text may require review against the original document</div></section>
<div id="content">""" + body + """</div><div class="footer">Reading edition generated from <a href=""" + '"' + escape(source_rel) + '"' + """>""" + escape(source.name) + """</a>. The original file is preserved unchanged.</div></article></div>
<script>
const q=document.getElementById('search'), pages=[...document.querySelectorAll('.page')];
q.addEventListener('input',()=>{const term=q.value.trim().toLowerCase();pages.forEach(p=>{p.hidden=!!term&&!p.innerText.toLowerCase().includes(term)})});
</script></body></html>"""


def classify_resource(name):
    value = name.lower().replace("_", " ").replace("-", " ")
    # Specific collections first: filename meaning takes precedence over broad keywords.
    if "four arcs" in value:
        return ("Music & Cross-Media","A multi-medium journey through films, books, albums, manga and poetry","music albums listening records poems films books")
    if "curator" in value or all(term in value for term in ("film", "book", "art")):
        return ("Cross-Media Discovery","A unified catalogue spanning films, anime, books, poetry and art","film anime books poetry art mixed media")
    if "film" in value and "music" in value:
        return ("Music & Cross-Media","A combined guide to cinema and its musical worlds","film cinema music soundtracks albums directors")
    if "asian cinema" in value or "cinematic" in value or "film" in value or "movie" in value or "animated films" in value or "sensual mood" in value:
        return ("Film & Cinema","Filmographies, world cinema curricula and searchable viewing collections","film cinema movies animation directors countries decades")
    if any(term in value for term in ("human development","life fiction","living curriculum","political comics","anime manga values","education","homeschool","home school","schooling","curriculum","learning","child development","kids","children","three year","3yearold","world stories")):
        return ("Home Learning & Education","Structured curricula, educational resources and guided learning pathways","education homeschooling home learning curriculum stages lessons children")
    if any(term in value for term in ("blackout poetry","poetry","poem","kavita","kavitayen")):
        return ("Poetry & Writing","Poetry collections, lessons and creative language practice","poetry poems kavita kavitayen writing literature")
    if any(term in value for term in ("music","album","playlist","listening")):
        return ("Music & Listening","Album recommendations and listening paths","music albums artists listening records playlists")
    if "marginalia" in value:
        return ("Personal Journals & Tools","A private notebook for reading notes, memories and observations","journal diary notes reading music film")
    if "typewriter" in value:
        return ("Writing Tools","A focused writing surface for drafting and printing","writing typewriter drafting print")
    if any(term in value for term in ("manga","manhwa","anime","comic")):
        return ("Anime & Manga","Illustrated stories, manga indexes and comics reading guides","manga anime comics manhwa graphic novels")
    if any(term in value for term in ("art","watercol","collage","bob ross","creative")):
        return ("Art & Creative Practice","Art resources, painting guides and hands-on creative exercises","art drawing painting collage watercolor creative")
    if any(term in value for term in ("prompt","inspiration","thinker","meditation","memento","life worth","emotion","wonder","mind","values","fictional books")):
        return ("Ideas & Reflection","Prompts, philosophy and resources for thoughtful living","prompts inspiration philosophy reflection thinkers")
    if any(term in value for term in ("security","cyber","crypto","trading","pine")):
        return ("Technology & Security","Cybersecurity, technical learning and market tools","technology security cybersecurity crypto trading")
    if any(term in value for term in ("tracker","generator","app","loom","tasks")):
        return ("Interactive Tools","Trackers, generators and browser-based utilities","interactive tools tracker generator app")
    if any(term in value for term in ("resource","google search","links","atlas","reference","guide")):
        return ("Reference & Discovery","Resource directories and curated indexes","reference discovery resources links guides atlas")
    return ("Explore & Miscellany","Other collections and useful starting points","miscellaneous collection explore")


def build_public_portal():
    originals = sorted([p for p in ROOT.glob("*.html") if p.name.lower() != "index.html"], key=lambda p:p.name.lower())
    converted = sorted([p for p in OUT.glob("*.html") if p.name.lower() != "index.html"], key=lambda p:p.name.lower())
    resources = []
    for path, kind in [(p,"original") for p in originals] + [(p,"converted") for p in converted]:
        title = path.stem.replace("_"," ").replace("-"," ")
        category, desc, synonyms = classify_resource(path.stem.replace("_"," ").replace("-"," "))
        href = path.name if kind == "original" else "html/" + path.name
        resources.append((title,path.name,href,kind,category,desc,synonyms))
    categories = sorted({r[4] for r in resources})
    counts = {c:sum(r[4] == c for r in resources) for c in categories}
    cards = []
    for title,filename,href,kind,category,desc,synonyms in resources:
        label = "Interactive HTML" if kind == "original" else "Reading edition"
        search = " ".join((title,filename,category,synonyms)).lower()
        cards.append('<a class="card" href="'+escape(href)+'" data-kind="'+kind+'" data-category="'+escape(category)+'" data-search="'+escape(search)+'"><div class="meta"><span>'+escape(category)+'</span><small>'+label+'</small></div><strong>'+escape(title)+'</strong><p>'+escape(desc)+'</p><div class="bottom">'+("Original page" if kind=="original" else "Converted from source document")+' <b>Open ↗</b></div></a>')
    filters = ''.join('<button class="chip" data-category="'+escape(c)+'">'+escape(c)+' <i>'+str(counts[c])+'</i></button>' for c in categories)
    template = """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="A curated, searchable digital library of film, manga, art, books, ideas, learning resources and interactive tools."><title>The Reading Room — Digital Library</title><link rel="preconnect" href="https://fonts.googleapis.com"><link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap" rel="stylesheet"><style>
:root{color-scheme:light;--bg:#f4f1fb;--paper:#fff;--ink:#211d32;--muted:#706b80;--line:#e2dced;--accent:#6652a3;--strong:#4f3c8c;--teal:#347d78}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.6 'DM Sans',sans-serif}.wrap{max-width:1240px;margin:auto;padding:28px 34px 60px}.mast{display:flex;justify-content:space-between;border-bottom:1px solid var(--line);padding-bottom:18px;color:var(--muted);font-size:11px;letter-spacing:.12em;text-transform:uppercase}.mast b{font:800 13px Manrope;color:var(--strong)}.hero{padding:42px 0 26px}.eyebrow{color:var(--teal);font-size:11px;font-weight:700;letter-spacing:.14em;text-transform:uppercase}h1{font:800 clamp(35px,5vw,55px)/1.1 Manrope;letter-spacing:-.05em;margin:10px 0}.hero p{max-width:700px;color:var(--muted);font-size:16px;margin:0}.stats{display:flex;gap:9px;flex-wrap:wrap;margin:22px 0}.stat{background:#ffffffa8;border:1px solid var(--line);border-radius:9px;padding:8px 12px;color:var(--muted);font-size:12px}.stat b{color:var(--ink);margin-right:4px}.discovery{position:sticky;top:0;z-index:5;background:#f4f1fbf2;backdrop-filter:blur(14px);padding:13px 0;border-block:1px solid var(--line)}.searchrow{display:flex;gap:9px}.searchrow input{flex:1;min-width:0;height:46px;border:1px solid #d8d0e7;border-radius:10px;padding:0 14px;background:var(--paper);font:14px 'DM Sans';color:var(--ink)}button,select{cursor:pointer;font:600 12px 'DM Sans'}.reset,select{border:1px solid var(--line);border-radius:9px;padding:0 13px;background:var(--paper);color:var(--ink)}.filters{display:flex;gap:7px;overflow:auto;padding-top:11px}.chip{white-space:nowrap;border:1px solid var(--line);border-radius:30px;background:var(--paper);color:var(--muted);padding:7px 11px}.chip i{font-style:normal;opacity:.7;margin-left:3px}.chip.active{background:var(--strong);color:white;border-color:var(--strong)}.toolbar{display:flex;justify-content:space-between;align-items:center;gap:12px;padding:22px 0 12px}.toolbar h2{font:700 19px Manrope;margin:0}.count{font-size:12px;color:var(--muted)}.grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}.card{display:flex;flex-direction:column;gap:10px;min-height:155px;padding:16px;background:var(--paper);border:1px solid var(--line);border-radius:13px;text-decoration:none;transition:.15s}.card:hover{transform:translateY(-2px);border-color:#b7a9d8;box-shadow:0 8px 24px #30204d10}.meta,.bottom{display:flex;justify-content:space-between;align-items:center;gap:8px}.meta span{font-size:10px;font-weight:700;color:var(--accent)}.meta small{font-size:9px;text-transform:uppercase;letter-spacing:.08em;color:var(--teal);font-weight:700}.card strong{font:700 15px/1.35 Manrope}.card p{font-size:12px;color:var(--muted);margin:0}.bottom{margin-top:auto;border-top:1px solid #f0edf5;padding-top:8px;font-size:10px;color:var(--muted)}.bottom b{color:var(--accent)}.empty{display:none;padding:32px;text-align:center;color:var(--muted);background:var(--paper);border:1px dashed var(--line);border-radius:12px}footer{margin-top:32px;border-top:1px solid var(--line);padding-top:15px;color:var(--muted);font-size:11px}footer a{color:var(--accent)}[hidden]{display:none!important}button:focus-visible,a:focus-visible,input:focus-visible,select:focus-visible{outline:3px solid #6652a355;outline-offset:2px}
@media(max-width:900px){.grid{grid-template-columns:repeat(2,minmax(0,1fr))}}@media(max-width:620px){.wrap{padding:18px 14px 40px}.hero{padding:28px 0 18px}h1{font-size:36px}.hero p{font-size:14px}.discovery{position:static;margin:0 -14px;padding:11px 14px}.grid{grid-template-columns:1fr;gap:9px}.card{min-height:0;padding:14px}.toolbar h2{font-size:16px}.mast span{font-size:9px}}
@media(prefers-color-scheme:dark){:root{color-scheme:dark;--bg:#171522;--paper:#211e2e;--ink:#f0edf7;--muted:#b1aabd;--line:#393348;--accent:#b6a4ed;--strong:#9b85df;--teal:#83c7bd}.discovery{background:#171522f2}.searchrow input,.reset,select,.chip{background:var(--paper);color:var(--ink);border-color:var(--line)}.stat{background:#211e2e}.bottom{border-color:#393348}}
</style><link rel="stylesheet" href="../assets/reading-room.css"></head><body class="rr-page rr--mixed"><nav class="rr-contextbar"><a href="../index.html">← THE READING ROOM</a><span><em>Reference & Discovery</em> · Search and browse all converted reading editions</span></nav><main class="wrap"><header class="mast"><b>THE READING ROOM</b><span>A personal digital library · Open access</span></header><section class="hero"><div class="eyebrow">Curated knowledge · Stories · Creative practice</div><h1>A library for a curious life.</h1><p>Explore a growing collection of cinema, manga, art, books, learning paths, ideas and interactive tools. Search titles and related topics, narrow by subject, and open original pages or clean reading editions.</p></section><div class="stats"><div class="stat"><b>__TOTAL__</b> resources</div><div class="stat"><b>__ORIGINAL__</b> original interactive pages</div><div class="stat"><b>__CONVERTED__</b> converted reading editions</div><div class="stat"><b>__CATS__</b> subject areas</div></div><section class="discovery"><div class="searchrow"><input id="search" type="search" placeholder="Search titles, subjects or related ideas…" aria-label="Search library"><button class="reset" id="reset">Reset</button></div><div class="filters"><button class="chip active" data-category="all">All subjects <i>__TOTAL__</i></button>__FILTERS__</div></section><div class="toolbar"><div><h2 id="heading">Explore the collection</h2><div class="count" id="count">__TOTAL__ resources</div></div><select id="sort" aria-label="Sort resources"><option value="az">A–Z</option><option value="za">Z–A</option><option value="original">Original pages first</option><option value="converted">Reading editions first</option></select></div><div class="grid" id="grid">__CARDS__</div><div class="empty" id="empty">No matching resources. Try a broader search or reset the filters.</div><footer>Original files remain unchanged. Converted editions are text-first reading copies; check source files for complex layouts or scanned material.<br><a href="html/index.html">Converted-document archive ↗</a> · <a href="https://github.com/piyushimself/files">Repository ↗</a></footer></main><script>
const search=document.getElementById('search'),cards=[...document.querySelectorAll('.card')],chips=[...document.querySelectorAll('.chip')],count=document.getElementById('count'),empty=document.getElementById('empty'),sort=document.getElementById('sort');let category='all';function update(){const q=search.value.trim().toLowerCase();let n=0;const list=[...cards].sort((a,b)=>{if(sort.value==='za')return b.querySelector('strong').textContent.localeCompare(a.querySelector('strong').textContent);if(['original','converted'].includes(sort.value))return (a.dataset.kind===sort.value?-1:1)-(b.dataset.kind===sort.value?-1:1);return a.querySelector('strong').textContent.localeCompare(b.querySelector('strong').textContent)});list.forEach(c=>{const ok=(category==='all'||c.dataset.category===category)&&(!q||c.dataset.search.includes(q));c.hidden=!ok;if(ok)n++;document.getElementById('grid').appendChild(c)});count.textContent=n+' of '+cards.length+' resources';empty.style.display=n?'none':'block';document.getElementById('heading').textContent=category==='all'?'Explore the collection':category}chips.forEach(b=>b.addEventListener('click',()=>{category=b.dataset.category;chips.forEach(x=>x.classList.toggle('active',x===b));update()}));search.addEventListener('input',update);sort.addEventListener('change',update);document.getElementById('reset').addEventListener('click',()=>{search.value='';category='all';sort.value='az';chips.forEach(x=>x.classList.toggle('active',x.dataset.category==='all'));update()});update();</script></body></html>"""
    values = {"__TOTAL__":str(len(resources)),"__ORIGINAL__":str(len(originals)),"__CONVERTED__":str(len(converted)),"__CATS__":str(len(categories)),"__FILTERS__":filters,"__CARDS__":"".join(cards)}
    for marker,value in values.items():
        template=template.replace(marker,value)
    (ROOT/"index.html").write_text(template,encoding="utf-8")
    print("Generated categorized portal:",len(resources),"resources across",len(categories),"subjects.")


def build_archive_index():
    files = sorted((p for p in OUT.glob("*.html") if p.name != "index.html"), key=lambda p:p.name.lower())
    source_files = {p.stem.lower(): p for p in [*ROOT.glob("*.pdf"), *ROOT.glob("*.docx")]}
    cards=[]
    for p in files:
        category, desc, synonyms = classify_resource(p.stem.replace("_"," ").replace("-"," "))
        src=source_files.get(p.stem.lower())
        kind=src.suffix.upper().lstrip(".") if src else "DOCUMENT"
        title=p.stem.replace("_"," ").replace("-"," ")
        searchable=" ".join((title,p.name,src.name if src else "",category,synonyms)).lower()
        cards.append(f'<a class="card" href="{escape(p.name)}" data-category="{escape(category)}" data-search="{escape(searchable)}"><div class="meta"><span>{escape(category)}</span><small>{kind} · READING EDITION</small></div><strong>{escape(title)}</strong><p>{escape(desc)}</p><div class="bottom">Converted document <b>Read ↗</b></div></a>')
    cats=sorted({classify_resource(p.stem.replace("_"," ").replace("-"," "))[0] for p in files})
    filters="".join(f'<button class="chip" data-category="{escape(c)}">{escape(c)} <i>{sum(classify_resource(p.stem.replace("_"," ").replace("-"," "))[0]==c for p in files)}</i></button>' for c in cats)
    html="""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Reading Archive — The Reading Room</title><link rel="preconnect" href="https://fonts.googleapis.com"><link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap" rel="stylesheet"><style>
:root{color-scheme:light;--bg:#f4f1fb;--paper:#fff;--ink:#211d32;--muted:#706b80;--line:#e2dced;--accent:#6652a3;--strong:#4f3c8c;--teal:#347d78}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.6 'DM Sans',sans-serif}.wrap{max-width:1240px;margin:auto;padding:28px 34px 60px}.mast{display:flex;justify-content:space-between;border-bottom:1px solid var(--line);padding-bottom:16px;font-size:11px;letter-spacing:.12em;color:var(--muted)}.mast b{font:800 13px Manrope;color:var(--strong)}a{color:var(--accent)}.hero{padding:40px 0 20px}.eyebrow{font-size:11px;font-weight:700;letter-spacing:.14em;color:var(--teal)}h1{font:800 clamp(34px,5vw,50px)/1.1 Manrope;letter-spacing:-.05em;margin:10px 0}.hero p{color:var(--muted);max-width:720px}.stats{display:flex;gap:9px;flex-wrap:wrap;margin:18px 0}.stat{padding:8px 12px;border:1px solid var(--line);border-radius:9px;background:#ffffffa8;color:var(--muted);font-size:12px}.stat b{color:var(--ink)}.discovery{position:sticky;top:0;z-index:3;background:#f4f1fbf2;padding:13px 0;border-block:1px solid var(--line);backdrop-filter:blur(12px)}.searchrow{display:flex;gap:9px}.searchrow input{flex:1;min-width:0;height:46px;border:1px solid #d8d0e7;border-radius:10px;padding:0 14px;font:14px 'DM Sans';background:var(--paper);color:var(--ink)}button,select{font:600 12px 'DM Sans';cursor:pointer}.reset,select,.chip{border:1px solid var(--line);border-radius:9px;background:var(--paper);color:var(--ink);padding:8px 12px}.filters{display:flex;gap:7px;overflow:auto;padding-top:10px}.chip{white-space:nowrap;border-radius:30px;color:var(--muted)}.chip i{font-style:normal;margin-left:4px}.chip.active{background:var(--strong);color:white}.toolbar{display:flex;justify-content:space-between;align-items:center;padding:20px 0 12px}.toolbar h2{font:700 18px Manrope;margin:0}.count{font-size:12px;color:var(--muted)}.grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}.card{display:flex;flex-direction:column;gap:9px;min-height:145px;padding:16px;border:1px solid var(--line);border-radius:13px;background:var(--paper);color:var(--ink);text-decoration:none}.card:hover{border-color:#b7a9d8;transform:translateY(-2px)}.meta,.bottom{display:flex;justify-content:space-between;gap:8px}.meta span{font-size:10px;font-weight:700;color:var(--accent)}.meta small{font-size:9px;color:var(--teal);font-weight:700}.card strong{font:700 15px/1.35 Manrope}.card p{font-size:12px;color:var(--muted);margin:0}.bottom{margin-top:auto;border-top:1px solid var(--line);padding-top:8px;font-size:10px;color:var(--muted)}.empty{display:none;text-align:center;padding:30px;color:var(--muted)}[hidden]{display:none!important}footer{margin-top:30px;border-top:1px solid var(--line);padding-top:14px;font-size:11px;color:var(--muted)}@media(max-width:900px){.grid{grid-template-columns:repeat(2,minmax(0,1fr))}}@media(max-width:620px){.wrap{padding:18px 14px 40px}.hero{padding:26px 0 16px}h1{font-size:35px}.discovery{position:static;margin:0 -14px;padding:11px 14px}.grid{grid-template-columns:1fr;gap:9px}.card{min-height:0;padding:14px}}@media(prefers-color-scheme:dark){:root{color-scheme:dark;--bg:#171522;--paper:#211e2e;--ink:#f0edf7;--muted:#b1aabd;--line:#393348;--accent:#b6a4ed;--strong:#9b85df;--teal:#83c7bd}.discovery{background:#171522f2}.stat{background:#211e2e}.searchrow input,.reset,select,.chip{background:var(--paper);color:var(--ink);border-color:var(--line)}}
</style><link rel="stylesheet" href="../assets/reading-room.css"></head><body class="rr-page rr--mixed"><nav class="rr-contextbar"><a href="../index.html">← THE READING ROOM</a><span><em>Reference & Discovery</em> · Search and browse all converted reading editions</span></nav><main class="wrap"><header class="mast"><b>THE READING ROOM</b><a href="../index.html">← BACK TO COMPLETE LIBRARY</a></header><section class="hero"><div class="eyebrow">THE READING ARCHIVE · __TOTAL__ EDITIONS</div><h1>Read, explore, discover.</h1><p>Converted editions, organised by subject. Search titles and related topics, filter by category, and open a clean reading copy. Original source files remain preserved.</p></section><div class="stats"><div class="stat"><b>__TOTAL__</b> reading editions</div><div class="stat"><b>__CATS__</b> subject areas</div><div class="stat">Search by title, filename or topic</div></div><section class="discovery"><div class="searchrow"><input id="search" type="search" placeholder="Search titles, subjects or related ideas…" aria-label="Search archive"><button class="reset" id="reset">Reset</button></div><div class="filters"><button class="chip active" data-category="all">All subjects <i>__TOTAL__</i></button>__FILTERS__</div></section><div class="toolbar"><div><h2 id="heading">All reading editions</h2><div class="count" id="count">__TOTAL__ editions</div></div><select id="sort"><option value="az">A–Z</option><option value="za">Z–A</option></select></div><div class="grid" id="grid">__CARDS__</div><div class="empty" id="empty">No matching documents. Try another search or reset filters.</div><footer>For complex layouts, images or tables, consult the original PDF or DOCX. <a href="../index.html">Return to all library resources ↗</a></footer></main><script>const q=document.getElementById('search'),cards=[...document.querySelectorAll('.card')],chips=[...document.querySelectorAll('.chip')],count=document.getElementById('count'),empty=document.getElementById('empty'),sort=document.getElementById('sort');let cat='all';function update(){let n=0;[...cards].sort((a,b)=>sort.value==='za'?b.innerText.localeCompare(a.innerText):a.innerText.localeCompare(b.innerText)).forEach(c=>{let ok=(cat==='all'||c.dataset.category===cat)&&(!q.value||c.dataset.search.includes(q.value.toLowerCase()));c.hidden=!ok;if(ok)n++;document.getElementById('grid').appendChild(c)});count.textContent=n+' of '+cards.length+' editions';empty.style.display=n?'none':'block';document.getElementById('heading').textContent=cat==='all'?'All reading editions':cat}chips.forEach(b=>b.onclick=()=>{cat=b.dataset.category;chips.forEach(x=>x.classList.toggle('active',x===b));update()});q.oninput=update;sort.onchange=update;document.getElementById('reset').onclick=()=>{q.value='';cat='all';sort.value='az';chips.forEach(x=>x.classList.toggle('active',x.dataset.category==='all'));update()};update();</script></body></html>"""
    for k,v in {"__TOTAL__":str(len(files)),"__CATS__":str(len(cats)),"__FILTERS__":filters,"__CARDS__":"".join(cards)}.items():
        html=html.replace(k,v)
    (OUT/"index.html").write_text(html,encoding="utf-8")
    print("Generated redesigned archive index:",len(files),"documents.")

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
    build_public_portal()
    build_archive_index()

if __name__ == "__main__":
    main()
