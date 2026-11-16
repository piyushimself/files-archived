#!/usr/bin/env python3
"""Convert repository PDF/DOCX sources into structured, searchable Reading Room editions."""
from pathlib import Path
from html import escape
import base64
import hashlib
import json
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "html"
ASSETS = ROOT / "assets"
OUT.mkdir(exist_ok=True)

URL_RE = re.compile(r"https?://[^\s<>\]\[\"']+", re.I)
BULLET_RE = re.compile(r"^\s*(?:[•▪◦‣●○■□*-]|(?:\d{1,3}|[A-Za-z])[.)])\s+")
NUMBER_RE = re.compile(r"^\s*(\d{1,3})[.)]\s+")
HEADING_RE = re.compile(r"^\s*(?:#{1,4}\s+)?(.+?)\s*$")


def run_command(args):
    return subprocess.run(args, check=True, capture_output=True, text=True)


def extract_pdf(path):
    result = run_command(["pdftotext", "-layout", "-enc", "UTF-8", str(path), "-"])
    text = result.stdout.replace("\x00", "").strip()
    if text:
        return text, "pdftotext"
    # OCR is deliberately a fallback: most files are text PDFs and do not need it.
    pages = []
    with tempfile.TemporaryDirectory() as tmp:
        prefix = str(Path(tmp) / "page")
        run_command(["pdftoppm", "-r", "170", "-png", str(path), prefix])
        for image_path in sorted(Path(tmp).glob("page-*.png")):
            page = run_command(["tesseract", str(image_path), "stdout"])
            pages.append(page.stdout.strip())
    return "\n\f\n".join(pages), "ocr"


def paragraph_html(paragraph):
    """Keep run-level bold and italic from a DOCX paragraph."""
    bits = []
    for run in paragraph.runs:
        value = escape(run.text or "")
        if not value:
            continue
        if run.bold:
            value = "<strong>" + value + "</strong>"
        if run.italic:
            value = "<em>" + value + "</em>"
        bits.append(value)
    return "".join(bits) or escape(paragraph.text or "")


def extract_docx(path):
    """Read paragraphs and tables in their real XML order, not in separate batches."""
    from docx import Document
    from docx.text.paragraph import Paragraph
    from docx.table import Table
    from docx.oxml.ns import qn

    doc = Document(path)
    blocks = []
    body = doc.element.body
    for child in body.iterchildren():
        tag = child.tag.rsplit("}", 1)[-1]
        if tag == "p":
            para = Paragraph(child, doc)
            text_html = paragraph_html(para)
            # Preserve inline pictures at their run positions when possible.
            for run in para.runs:
                drawing_nodes = run._element.xpath(".//a:blip")
                for drawing in drawing_nodes:
                    rel_id = drawing.get(qn("r:embed"))
                    if rel_id and rel_id in doc.part.related_parts:
                        part = doc.part.related_parts[rel_id]
                        mime = getattr(part, "content_type", "image/png")
                        encoded = base64.b64encode(part.blob).decode("ascii")
                        marker = '<img class="docx-inline-image" alt="Image from original document" src="data:' + escape(mime) + ';base64,' + encoded + '">'
                        # A picture-only paragraph still gets a visible image. For mixed
                        # text/picture runs, keep a useful image preview after the text.
                        text_html += marker
            if para.text.strip() or "<img " in text_html:
                style = para.style.name if para.style else "Normal"
                visible_runs = [run for run in para.runs if (run.text or "").strip()]
                is_bold = bool(visible_runs) and all(run.bold for run in visible_runs)
                blocks.append(("paragraph", {"html": text_html, "text": para.text.strip(), "style": style, "bold": is_bold}))
        elif tag == "tbl":
            table = Table(child, doc)
            rows = [[cell.text.strip() for cell in row.cells] for row in table.rows]
            blocks.append(("table", rows))
    return blocks, len(doc.paragraphs), len(doc.tables)


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-") or "section"


def display_title(path):
    name = path.stem.replace("_", " ").replace("-", " ")
    name = re.sub(r"\s+\(1\)$", "", name).strip()
    special = {
        "aag ki kavitayen": "Aag Ki Kavitayen",
        "1000 google searches grand curiosity atlas": "The Grand Curiosity Atlas — 1,000 Search Trails",
        "500 films 500 music global guide": "A Life Worth Living — 500 Films & 500 Music",
        "1000 greatest fictional books": "1000 Greatest Fictional Books",
        "free art resource library": "Free Art Resource Library",
        "global kids books complete guide": "Global Kids Books — Complete Guide",
        "three year old reading guide": "Three-Year-Old Reading Guide",
        "world stories 3yearold guide": "World Stories for Three-Year-Olds",
        "a filmmakers reading list": "A Filmmaker's Reading List",
        "a life worth living 500 suggestions": "A Life Worth Living — 500 Suggestions",
        "complete movie encyclopedia": "Complete Movie Encyclopedia",
        "complete movie ratings": "Complete Movie Ratings",
        "complete movie ratings 647": "Complete Movie Ratings — 647 Films",
        "definitive anime encyclopedia": "The Definitive Anime Encyclopedia",
        "memento mori course": "Memento Mori — A Curated Study Course",
        "meditation on death": "A Meditation on Death",
        "500 manga movies": "500 Films Based on Manga",
        "200 films like frida": "200 Films Like Frida",
        "100 essential films": "100 Essential Films",
        "50 e art films": "50 Bold, Intimate & Thought-Provoking Art Films",
    }
    return special.get(name.lower(), name)


def auto_link(text):
    """Escape extracted text first, then make plain URLs safe and clickable."""
    safe = escape(text)
    def link(match):
        url = match.group(0).rstrip(".,;:)")
        tail = match.group(0)[len(url):]
        escaped_url = escape(url, quote=True)
        return '<a href="' + escaped_url + '" target="_blank" rel="noopener noreferrer">' + escape(url) + '</a>' + escape(tail)
    return URL_RE.sub(link, safe)


def looks_like_heading(line):
    value = line.strip()
    if not 3 <= len(value) <= 88:
        return False
    if BULLET_RE.match(value) or value.endswith((".", ",", ";", ":", "?", "!")):
        return False
    if URL_RE.search(value):
        return False
    words = value.split()
    if len(words) > 10:
        return False
    # All-caps section labels and short title-case lines are useful navigational cues.
    alpha = re.sub(r"[^A-Za-z]", "", value)
    if len(alpha) < 3:
        return False
    all_caps = alpha.isupper() and len(words) <= 9
    title_case = value.istitle() and len(words) <= 8
    numbered_section = bool(re.match(r"^(?:PART|PHASE|SECTION|CHAPTER|UNIT|MODULE|LIST)\s+[IVX\d]+", value, re.I))
    return all_caps or title_case or numbered_section


def is_noise_line(line):
    value = line.strip()
    if not value:
        return True
    if re.fullmatch(r"(?:page\s*)?\d{1,4}", value, re.I):
        return True
    if re.fullmatch(r"[-_=•·\s]{3,}", value):
        return True
    return False


def render_pdf_page(raw, page_number, toc, used):
    lines = []
    for line in raw.replace("\r\n", "\n").replace("\r", "\n").splitlines():
        line = re.sub(r"[ \t]+", " ", line).strip()
        if is_noise_line(line):
            continue
        lines.append(line)

    chunks = []
    paragraphs = []
    list_kind = None
    list_items = []

    def flush_paragraph():
        nonlocal paragraphs
        if paragraphs:
            text = " ".join(paragraphs).strip()
            if text:
                chunks.append("<p>" + auto_link(text) + "</p>")
            paragraphs = []

    def flush_list():
        nonlocal list_kind, list_items
        if list_items:
            tag = "ol" if list_kind == "ol" else "ul"
            chunks.append("<" + tag + ">" + "".join("<li>" + auto_link(item) + "</li>" for item in list_items) + "</" + tag + ">")
        list_kind, list_items = None, []

    for line in lines:
        is_bullet = bool(BULLET_RE.match(line))
        if looks_like_heading(line):
            flush_paragraph()
            flush_list()
            heading = re.sub(r"^(?:#{1,4}\s+)", "", line).strip()
            heading = re.sub(r"^[•▪◦‣●○■□]\s*", "", heading)
            anchor_base = slug(heading)
            anchor, suffix = anchor_base, 2
            while anchor in used:
                anchor, suffix = anchor_base + "-" + str(suffix), suffix + 1
            used.add(anchor)
            toc.append((anchor, heading))
            chunks.append('<h2 id="' + anchor + '">' + escape(heading) + "</h2>")
        elif is_bullet:
            flush_paragraph()
            match = BULLET_RE.match(line)
            marker = match.group(0)
            item = line[len(marker):].strip()
            number = NUMBER_RE.match(line)
            kind = "ol" if number else "ul"
            if list_kind and list_kind != kind:
                flush_list()
            list_kind = kind
            if item:
                list_items.append(item)
        else:
            flush_list()
            # Avoid destroying short line breaks such as verse or question prompts.
            if len(line) < 95 and not line.endswith((",", ";")) and paragraphs and len(paragraphs[-1]) > 90:
                flush_paragraph()
            paragraphs.append(line)
    flush_paragraph()
    flush_list()
    if not chunks:
        return ""
    return '<section class="page" id="page-' + str(page_number) + '"><div class="page-label">SOURCE PAGE ' + str(page_number) + '</div>' + "\n".join(chunks) + "</section>"



POEM_MARKER_RE = re.compile(r"^[—–-]+\s*(\d{1,3})\s*[—–-]+$")
POET_BYLINE_RE = re.compile(r"^[—–-]+\s*(.+?)\s*[—–-]+$")

def render_poetry_pdf(extracted):
    """Render Aag Ki Kavitayen as poems, retaining titles, poets, lineation and stanzas."""
    source_pages = extracted.replace("\r\n", "\n").replace("\r", "\n").split("\f")
    front_matter, toc = [], []
    volume_order, volumes = [], {}
    current_volume = "Collection"
    poem_count = 0

    def clean_lines(raw):
        result = []
        for original in raw.splitlines():
            line = re.sub(r"[ \t]+", " ", original).strip()
            if re.fullmatch(r"Aag\s+Ki\s+Kavitayen\s*[·•]\s*\d+", line, re.I):
                continue
            if re.fullmatch(r"(?:page\s*)?\d{1,4}", line, re.I):
                continue
            if re.fullmatch(r"[■□\s]{3,}", line):
                continue
            result.append(line)
        while result and not result[0]:
            result.pop(0)
        while result and not result[-1]:
            result.pop()
        return result

    def front_page(lines, page_number):
        visible = [line for line in lines if line]
        if page_number == 1 and visible and visible[0].strip().lower() == "aag ki kavitayen":
            visible = visible[1:]
        if not visible:
            return ""
        parts = ['<section class="page poetry-frontmatter" id="page-' + str(page_number) + '">',
                 '<div class="page-label">COLLECTION NOTES · SOURCE PAGE ' + str(page_number) + '</div>']
        if page_number == 1:
            parts.append('<div class="poetry-cover-mark">A COLLECTION OF POEMS</div>')
        first_title_used = False
        for line in visible:
            if line.startswith(("◆", "▪", "■")):
                label = re.sub(r"^[◆▪■\s]+", "", line)
                parts.append('<h3 class="poetry-index-heading">' + escape(label) + '</h3>')
            elif not first_title_used and len(line) <= 72 and not re.search(r"[.!?]$", line):
                parts.append('<h2 class="poetry-front-title">' + escape(line) + '</h2>')
                first_title_used = True
            else:
                parts.append('<p class="poetry-front-line">' + auto_link(line) + '</p>')
        parts.append("</section>")
        return "\n".join(parts)

    for page_number, raw in enumerate(source_pages, 1):
        lines = clean_lines(raw)
        if not lines:
            continue
        khand_index = next((i for i, line in enumerate(lines) if re.match(r"^Khand\s+\d+\s*$", line, re.I)), None)
        if khand_index is not None:
            khand = lines[khand_index]
            next_title = next((line for line in lines[khand_index + 1:] if line), "")
            current_volume = (khand + " · " + next_title).strip(" ·")
            volumes.setdefault(current_volume, [])
            if current_volume not in volume_order:
                volume_order.append(current_volume)
            volume_id = "volume-" + slug(current_volume)
            front_matter.append(
                '<section class="page poetry-volume-break" id="' + volume_id + '">'
                '<div class="page-label">PART OF THE COLLECTION</div>'
                '<div class="poetry-volume-kicker">' + escape(khand.upper()) + '</div>'
                '<h2>' + escape(next_title or "Poetry section") + '</h2></section>'
            )
            continue

        marker_index = next((i for i, line in enumerate(lines) if POEM_MARKER_RE.fullmatch(line)), None)
        if marker_index is None:
            front_matter.append(front_page(lines, page_number))
            continue

        marker = POEM_MARKER_RE.fullmatch(lines[marker_index])
        poem_number = int(marker.group(1))
        remaining = lines[marker_index + 1:]
        title_index = next((i for i, line in enumerate(remaining) if line), None)
        if title_index is None:
            front_matter.append(front_page(lines, page_number))
            continue

        poem_title = remaining[title_index]
        byline_index = next((i for i in range(title_index + 1, min(len(remaining), title_index + 4))
                             if remaining[i] and POET_BYLINE_RE.fullmatch(remaining[i])), None)
        poet = ""
        verse_start = title_index + 1
        if byline_index is not None:
            poet_match = POET_BYLINE_RE.fullmatch(remaining[byline_index])
            poet = poet_match.group(1).strip()
            verse_start = byline_index + 1

        # pdftotext may emit one empty line between every baseline in a poem.
        # Treat only a wider blank gap (two or more empty lines) as a stanza break.
        stanzas, current_stanza = [], []
        blank_run = 0
        for line in remaining[verse_start:]:
            if not line:
                blank_run += 1
                continue
            if blank_run >= 2 and current_stanza:
                stanzas.append(current_stanza)
                current_stanza = []
            blank_run = 0
            current_stanza.append(line)
        if current_stanza:
            stanzas.append(current_stanza)

        poem_id = "poem-" + str(poem_number) + "-" + slug(poem_title)
        if any(existing[0] == poem_id for existing in toc):
            poem_id += "-page-" + str(page_number)
        poem_count += 1
        toc.append((poem_id, str(poem_number) + ". " + poem_title))

        search_text = " ".join([poem_title, poet, current_volume] + [line for stanza in stanzas for line in stanza])
        verse_html = "".join(
            '<div class="poetry-stanza">' +
            "".join('<p class="poetry-line">' + auto_link(line) + '</p>' for line in stanza) +
            '</div>' for stanza in stanzas
        )
        if not verse_html:
            verse_html = '<p class="poetry-missing-text">No verse text was extracted from this source page. Open the original PDF to inspect it.</p>'

        card = (
            '<article class="poem-card" id="' + escape(poem_id) + '" data-poet="' + escape(poet) +
            '" data-volume="' + escape(current_volume) + '" data-search="' + escape(search_text.lower(), quote=True) + '">'
            '<div class="poem-card-top"><span>POEM ' + str(poem_number) + '</span><span>SOURCE PAGE ' + str(page_number) + '</span></div>'
            '<h2 class="poem-title">' + escape(poem_title) + '</h2>'
            + ('<p class="poet-byline">' + escape(poet) + '</p>' if poet else '')
            + '<div class="poetry-verses">' + verse_html + '</div></article>'
        )
        volumes.setdefault(current_volume, [])
        if current_volume not in volume_order:
            volume_order.append(current_volume)
        volumes[current_volume].append(card)

    rendered = list(front_matter)
    for volume in volume_order:
        cards = volumes.get(volume, [])
        if not cards:
            continue
        rendered.append(
            '<section class="page poetry-volume-group" id="poetry-' + slug(volume) + '" data-volume="' + escape(volume) + '">'
            '<div class="poetry-volume-heading"><span>COLLECTION SECTION</span><h2>' + escape(volume) + '</h2>'
            '<span class="poetry-volume-count">' + str(len(cards)) + ' poems</span></div>'
            + "\n".join(cards) + '</section>'
        )
    return rendered, toc, poem_count

def render_pdf_blocks(text):
    pages = text.replace("\r\n", "\n").replace("\r", "\n").split("\f")
    rendered, toc, used = [], [], set()
    for number, raw in enumerate(pages, 1):
        section = render_pdf_page(raw, number, toc, used)
        if section:
            rendered.append(section)
    return rendered, toc


def render_docx_blocks(blocks):
    parts, toc, used = [], [], set()
    list_kind, list_items = None, []

    def flush_list():
        nonlocal list_kind, list_items
        if list_items:
            tag = "ol" if list_kind == "ol" else "ul"
            parts.append("<" + tag + ">" + "".join("<li>" + item + "</li>" for item in list_items) + "</" + tag + ">")
        list_kind, list_items = None, []

    for kind, value in blocks:
        if kind == "paragraph":
            style = value["style"].lower()
            html = value["html"]
            text = value["text"] or re.sub(r"<[^>]+>", "", html)
            formatted_heading = (
                value.get("bold", False)
                and 3 <= len(text) <= 88
                and len(text.split()) <= 10
                and not text.endswith((".", ",", ";", ":", "?", "!"))
                and not re.match(r"^\s*\d+[.)]\s+", text)
            )
            is_heading = style.startswith("heading") or style in ("title", "subtitle") or formatted_heading
            if is_heading:
                flush_list()
                level_match = re.search(r"(\d+)", style)
                if level_match:
                    level = int(level_match.group(1))
                else:
                    level = 1 if style == "title" else (2 if style.startswith("heading") else 2)
                level = min(max(level, 1), 4)
                heading_text = text
                base = slug(heading_text)
                anchor, suffix = base, 2
                while anchor in used:
                    anchor, suffix = base + "-" + str(suffix), suffix + 1
                used.add(anchor)
                toc.append((anchor, heading_text))
                parts.append('<h' + str(level + 1) + ' id="' + anchor + '">' + html + '</h' + str(level + 1) + '>')
            elif style.startswith("list bullet") or style.startswith("list number") or style.startswith("list continue") or style == "list paragraph":
                next_kind = "ol" if "number" in style else "ul"
                if list_kind and list_kind != next_kind:
                    flush_list()
                list_kind = next_kind
                list_items.append(html)
            else:
                flush_list()
                if html.strip():
                    parts.append("<p>" + html + "</p>")
        elif kind == "table":
            flush_list()
            rows = value
            if rows:
                header = rows[0]
                head = "<thead><tr>" + "".join("<th scope=\"col\">" + escape(cell) + "</th>" for cell in header) + "</tr></thead>"
                body_rows = rows[1:] if len(rows) > 1 else []
                body = "<tbody>" + "".join("<tr>" + "".join("<td>" + escape(cell) + "</td>" for cell in row) + "</tr>" for row in body_rows) + "</tbody>"
                parts.append('<div class="table-wrap"><table>' + head + body + "</table></div>")
    flush_list()
    return ['<section class="page">' + "\n".join(parts) + "</section>"], toc

def category_info(title):
    value = title.lower()
    if any(x in value for x in ("kid", "children", "three year", "world stories")):
        return ("Home Learning & Education", "learning", "This guide is designed to support shared reading and curiosity. Use age bands and stages as flexible guidance, follow the child's attention, and return to favourite stories.")
    if any(x in value for x in ("manga", "anime", "comic")):
        return ("Anime & Manga", "manga", "Use the contents and section headings to find a route through the medium. Larger lists are references for discovery; shorter guides and curricula offer a more deliberate starting point.")
    if any(x in value for x in ("film", "cinema", "movie")):
        return ("Film & Cinema", "cinema", "Use this edition as a viewing reference. Choose a route or theme that interests you, then follow directors, regions, eras or related works rather than trying to complete every title.")
    if any(x in value for x in ("art", "watercolour", "artist")):
        return ("Art & Creative Practice", "art", "Choose one medium or artist to study at a time. Pair a reference section with a small practical exercise, and keep the source document for visual examples.")
    if "aag ki kavitayen" in value:
        return ("Poetry & Writing", "poetry", "Read one poem at a time. Poem titles, poet credits, verse line breaks and stanza spacing are retained; use the poet filter or search to find a particular voice.")
    if any(x in value for x in ("poetry", "kavit", "writing", "prompts")):
        return ("Poetry & Writing", "literary", "Read slowly and use the collection as a prompt for your own practice. You can open at any section; there is no requirement to follow the sequence from the beginning.")
    if any(x in value for x in ("cyber", "security")):
        return ("Technology & Security", "tools", "Use the material as a discussion and learning aid. Translate analogies into concrete technical decisions, threat scenarios and controls before applying them in a real environment.")
    if any(x in value for x in ("thinker", "meditation", "death", "mori", "inspiration", "wonder", "life worth")):
        return ("Ideas & Reflection", "literary", "Choose a theme that is relevant to you and give it time. These are reading and reflection resources, not a programme that needs to be completed at speed.")
    return ("Books & Reference", "mixed", "Use the contents and headings to navigate the source. Follow one theme or section at a time; the original PDF or DOCX remains available for layout-dependent material.")


SUMMARY_OVERRIDES = {
    "films that open new human domains": "A guided film and documentary collection organised around domains of human experience — childhood, care, illness, family, solitude, war, creativity and more. Each selection pairs a film with the human perspective it can help a viewer understand, making this a route for reflective watching rather than a ranked watchlist.",
    "aag ki kavitayen": "A 100-poem Hindi collection in a revolutionary and humanist tradition, with poems on resistance, dignity, labour, hope, identity and love. Each poem is presented as its own piece, with the source title, poet attribution, verse lineation and stanza breaks preserved.",
    "aag ki kavitayen": "A 100-poem Hindi collection in a revolutionary and humanist tradition, with poems on resistance, dignity, labour, hope, identity and love. Each poem is presented as its own piece, with the source title, poet attribution, verse lineation and stanza breaks preserved.",
    "the definitive anime encyclopedia": "A broad anime viewing reference covering 100 essential films and 100 essential series across genres and eras. Use it to plan a first watchlist or trace how styles, studios and creators changed from early television to contemporary work.",
    "manga recommendations": "A compact manga shortlist for readers drawn to romance, mystery and feel-good storytelling, with a simple rating key to help compare recommendations. Treat it as a welcoming starting shelf rather than a comprehensive canon.",
    "ultimate anime guide": "A time-aware guide to essential anime films and series, organised around genre and viewing commitment. It helps readers choose a manageable route through a large medium rather than browse an undifferentiated catalogue.",
    "library 3": "A large cross-media reference spanning films, anime, books, albums, poems and artists. Use its contents to move between media and themed sections; the HTML edition is searchable, while the original PDF preserves its visual layout.",
    "three-year-old reading guide": "A global early-reading guide organised by region and developmental stage, moving from sounds and rhythms toward imagination and bigger ideas. Use it as a flexible shared-reading resource, following the child's attention rather than treating it as a strict curriculum.",
    "100 essential films": "A 100-film starting canon spanning genres, eras, directors and countries. It is designed to introduce a broad range of cinematic language and human experience, not to prescribe one definitive ranking.",
    "complete movie encyclopedia": "A reference encyclopedia of 647 unique films, bringing together IMDb and Rotten Tomatoes ratings, viewing availability in India and short descriptions. It also draws together essential cinema, art films, anime and director filmographies.",
    "complete movie ratings": "A compact film-rating reference covering 218 unique titles, bringing together IMDb and Rotten Tomatoes scores with a simple colour key for comparing ratings.",
    "complete movie ratings — 647 films": "An expanded ratings reference for 647 films, combining IMDb and Rotten Tomatoes scores with director filmographies and broad genre coverage.",
    "sensitive cinema": "A film collection centred on emotional sensitivity, empathy and difficult human experiences. Brief context alongside the titles helps viewers choose works for reflection rather than simply follow a ranking.",
    "cinema 900": "A large mood-led film reference spanning sensual cinema, slow cinema and work from Japan, Korea, China, Iran, the Arab world, Southeast Asia and India. Browse by emotional tone and cinematic approach.",
    "global kids books — complete guide": "A global children's reading guide bringing together folklore, mythology, fiction, biography, fantasy, graphic novels and poetry from Asia, Africa, Europe, the Americas, the Middle East and Oceania.",
    "global kids reading guide final": "A cross-cultural guide to children's reading, bringing together folklore, mythology, fiction, biography, fantasy, graphic novels and poetry from multiple world regions. Use it to broaden a child's reading beyond familiar traditions.",
    "1000 inspirations": "A curiosity atlas of things to read, know, question and explore. Its purpose is to widen the reader's field of interest across different subjects; browse one theme at a time and follow the ideas that invite deeper learning.",
    "2000 inspirations": "A 2,000-item creative and intellectual compendium organised into ten categories, including reading, writing, painting, sketching, urban art, life skills and broader reflection. Browse one category at a time and choose an idea to try.",
    "1000 writing prompts": "A practical collection of 835 prompts across fiction, science fiction, fantasy, horror, romance, historical fiction, memoir, journalism, poetry, drama, satire and experimental writing. Use it for timed warm-ups, first drafts, workshops or longer projects; prompts are starting points, not rigid assignments.",
    "a life worth living — 500 suggestions": "Five hundred suggestions spanning art, literature, music, cinema and thought, curated as possible doorways into a richer and more examined life. Use the sections as invitations to explore, not as tasks to finish.",
    "masters of art": "A reference to 25 artists from the Renaissance to contemporary practice, bringing together their lives, famous works, working habits and the qualities that made each artist distinctive.",
    "the grand curiosity atlas — 1,000 search trails": "A curated set of 1,000 exact Google search queries designed to open research trails across knowledge, culture and creative interests. Copy a query, follow the results and use it as a starting point for independent discovery.",
    "all film collections combined compressed": "A combined film archive that brings multiple uploaded film-related collections into one large reference. Use the contents and within-document search to navigate it; the original PDF remains available for its page layout.",
    "cybersecurity stories for your teams": "A workplace storytelling guide using films and familiar narratives to explain security risks, technical controls, compliance, remediation and operational decisions. It is designed to support team discussion and make abstract security ideas easier to remember.",
    "masters of e art cinema": "A filmmaker-centred guide to directors who used desire, the body and intimacy as serious artistic material. It introduces 15 filmmakers and gives readers a route into their distinctive approaches to cinema."
}


def document_summary(title, extracted, fallback):
    """Create a short, source-led description rather than a filename-only catalogue label."""
    override = SUMMARY_OVERRIDES.get(title.strip().lower())
    if override:
        return override
    raw = (extracted or "").replace("\x00", " ").replace("\f", "\n")
    raw = re.sub(r"(?m)^\s*(?:page\s+)?\d{1,4}\s*$", "", raw, flags=re.I)
    raw = re.sub(r"(?m)^\s*[-–—|·•]+\s*$", "", raw)
    blocks = [re.sub(r"\s+", " ", part).strip() for part in re.split(r"\n\s*\n+", raw)]
    title_key = re.sub(r"[^a-z0-9]+", "", title.lower())
    candidates = []
    for block in blocks:
        if len(block) < 55:
            continue
        key = re.sub(r"[^a-z0-9]+", "", block.lower())
        if title_key and (key.startswith(title_key) or title_key in key[:len(title_key)+24]):
            block = re.sub(re.escape(title), "", block, flags=re.I).strip(" :-–—|")
        if len(block) < 55 or (block.isupper() and len(block.split()) < 12):
            continue
        if re.match(r"^(contents|table of contents|index|copyright|all rights reserved|how to use this book)\b", block, re.I):
            continue
        candidates.append(block)
        if len(candidates) == 2:
            break
    if not candidates:
        for line in raw.splitlines():
            line = re.sub(r"\s+", " ", line).strip()
            if len(line) >= 70 and not line.isupper() and not re.match(r"^(contents|table of contents|page \d+)\b", line, re.I):
                candidates.append(line)
                if len(candidates) == 2:
                    break
    summary = " ".join(candidates) or fallback
    summary = re.sub(r"\s+", " ", summary).strip()
    if len(summary) > 290:
        summary = summary[:287].rsplit(" ", 1)[0].rstrip(" ,;:-") + "…"
    return summary



CINEMA_READER_OVERRIDES = {
    "cinema 900": {
        "kind": "cinema-900",
        "title": "Cinema 900",
        "meta": "900 curated films · 3 distinct viewing routes",
        "summary": "A three-part cinema atlas: 300 world-cinema masterpieces, 300 sensual and mood-led films, and 300 explicit erotic-art selections. The first route spans regions and traditions; the second follows longing, intimacy and atmosphere; the third is an adult-only route.",
        "guidance": "Start with World Cinema for a broad route through countries and traditions. Choose Sensual & Mood Cinema for atmosphere and relationships. The Explicit Erotic Art list is separate and intended for adults; review its content advisory before browsing."
    },
    "complete movie encyclopedia": {
        "kind": "movie-encyclopedia",
        "title": "Complete Movie Encyclopedia",
        "meta": "647 unique films · IMDb · Rotten Tomatoes · India streaming notes",
        "summary": "A reference work bringing together essential cinema, erotic art films, anime and director-led genre collections. Entries combine IMDb and Rotten Tomatoes scores, editorial descriptions and source-era notes on where to watch in India.",
        "guidance": "Use the collection sections to explore by theme or filmmaker. IMDb is an audience score; Rotten Tomatoes is the share of positive critic reviews. Streaming notes in this source are dated 2025 and should be treated as historical pointers, not live availability."
    },
    "complete movie ratings": {
        "kind": "movie-ratings",
        "title": "Complete Movie Ratings",
        "meta": "218 unique titles · IMDb audience scores · Rotten Tomatoes critic scores",
        "summary": "A comparison reference for the films collected in this session, organised across essential cinema, erotic art films and anime. A title may appear in more than one source section; the stated total refers to unique titles, not the sum of section counts.",
        "guidance": "IMDb is an audience rating out of 10. Rotten Tomatoes is the percentage of critics who reviewed a film positively, not an average score. A 100% Tomatometer does not mean a perfect film, and scores for older or less-reviewed titles may rely on small samples."
    },
    "sensitive cinema": {
        "kind": "sensitive-cinema",
        "title": "Sensitive Cinema",
        "meta": "253 films · 15 thematic categories · Reflection-led viewing",
        "summary": "A guided collection across animation, world cinema, documentary and quiet drama. It pairs film notes with reflective prompts about empathy, grief, identity, family, memory and social conditions.",
        "guidance": "This is a reflective guide, not a ranking or a set of objective lessons. It includes difficult themes such as war, trauma, illness, political violence, sexuality and loss. Check the film notes and choose according to your comfort."
    }
}


def make_reader(source, title, kind, sections, toc, extraction_method, source_hash, summary):
    override = CINEMA_READER_OVERRIDES.get(title.strip().lower())
    category, theme, guidance = category_info(title)
    reader_kind = ""
    intro_kicker = "About this collection"
    search_label = "FIND IN THIS DOCUMENT"
    display_title = title
    if override:
        reader_kind = override["kind"]
        display_title = override["title"]
        summary = override["summary"]
        guidance = override["guidance"]
        category = "Film & Cinema"
        theme = "cinema"
        edition_meta = override["meta"]
        intro_kicker = "Reader’s guide"
        search_label = "SEARCH THIS COLLECTION"
    else:
        edition_meta = (str(len(toc)) + " poems · Original sequence preserved · Search by poet or section") if theme == "poetry" else (str(len(sections)) + " reading sections · Original file preserved · Search within this edition")
    safe_title = escape(display_title)
    source_rel = "../" + source.relative_to(ROOT).as_posix()
    if len(toc) > 12:
        toc_block = '<nav class="toc"><details><summary>ON THIS PAGE · ' + str(len(toc)) + ' sections</summary>' + "".join('<a href="#' + escape(anchor) + '">' + escape(label) + "</a>" for anchor, label in toc) + "</details></nav>"
    elif toc:
        toc_block = '<nav class="toc"><div class="toc-title">ON THIS PAGE</div>' + "".join('<a href="#' + escape(anchor) + '">' + escape(label) + "</a>" for anchor, label in toc) + "</nav>"
    else:
        toc_block = ""
    layout_class = "layout" if toc else "layout rr-no-toc"
    body = "\n".join(sections)
    if len(body) < 100:
        body = '<section class="page"><p>No readable text could be extracted. Please open the original source document for the complete material.</p></section>'
    body_attributes = ' class="rr-page rr-reader rr--' + theme + '"'
    if reader_kind:
        body_attributes += ' data-reader-kind="' + escape(reader_kind, quote=True) + '"'
    return """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="Reading edition of """ + safe_title + """. Original source preserved.">
<title>""" + safe_title + """ — The Reading Room</title>
<link rel="stylesheet" href="../assets/reading-room.css?v=16">
<script src="../assets/reading-room-context.js?v=16" defer></script>
<script src="../assets/reading-room.js?v=16" defer></script>
<style>
.rr-reader-intro{margin:12px 0 14px;padding:13px 15px;border:1px solid var(--rr-line);border-left:3px solid var(--rr-accent);border-radius:9px;background:var(--rr-panel)}
.rr-reader-intro .kicker{font-size:10px;letter-spacing:.1em;text-transform:uppercase;color:var(--rr-accent-strong);font-weight:750}
.rr-reader-intro p{margin:5px 0 0!important;color:var(--rr-muted);font-size:12px!important;line-height:1.6!important}
.rr-reader-tools{display:flex;align-items:center;gap:9px;flex-wrap:wrap;margin:10px 0 13px;padding:9px 11px;border:1px solid var(--rr-line);border-radius:8px;background:var(--rr-panel)}
.rr-reader-tools label{font-size:11px;font-weight:700;color:var(--rr-muted)}
.rr-reader-tools input{flex:1 1 240px;max-width:440px;min-height:34px!important;font-size:12px!important}
body.rr-reader .layout.rr-no-toc{display:block!important;max-width:900px!important}
body.rr-reader .layout.rr-no-toc article{max-width:860px;margin:0 auto}
body.rr-reader .page{min-height:0}
body.rr-reader .page h2,body.rr-reader .page h3{scroll-margin-top:78px}
body.rr-reader .page li{margin:3px 0}
body.rr-reader .page img.docx-inline-image{display:block;max-width:100%;height:auto;margin:12px auto;border-radius:6px}
body.rr-reader .page table{min-width:520px}
body.rr-reader .page th{background:var(--rr-accent-soft);font-weight:700}
body.rr-reader .page blockquote{margin:12px 0;padding:8px 14px;border-left:3px solid var(--rr-accent);background:var(--rr-panel);color:var(--rr-muted)}
body.rr-reader .page a{overflow-wrap:anywhere}
body.rr-reader .page-label{margin-bottom:8px}
body.rr-reader .toc details summary{cursor:pointer;font-size:11px;font-weight:700;color:var(--rr-ink)}
body.rr-reader .toc details a:first-of-type{margin-top:8px}
</style></head><body""" + body_attributes + """>
""" + toc_block + """
<main class=\"""" + layout_class + """\"><article>
<section class="hero"><div class="kicker">SOURCE DOCUMENT · """ + kind + """ · """ + escape(category) + """</div><h1>""" + safe_title + """</h1><div class="meta">""" + edition_meta + """</div></section>
<section class="rr-reader-intro"><div class="kicker">""" + intro_kicker + """</div><p class="rr-reader-summary">""" + escape(summary) + """</p><p class="rr-reader-guidance"><strong>How to use this edition:</strong> """ + escape(guidance) + """</p><p><a href=\"""" + '"' + escape(source_rel) + '"' + """ target="_blank" rel="noopener">Open original """ + kind + """ ↗</a></p></section>
<div class="rr-reader-tools"><label for="search">""" + search_label + """</label><input id="search" type="search" placeholder="Search titles, directors, years, themes or ratings…" aria-label="Search this collection"></div>
<div id="content">""" + body + """</div>
<footer class="footer">Converted from <a href=\"""" + '"' + escape(source_rel) + '"' + """">""" + escape(source.name) + """</a>. Extraction method: """ + escape(extraction_method) + """. The original file is retained for images, complex layouts and visual details.</footer>
</article></main></body></html>"""




def canonical_duplicate_alias(path, canonical):
    rel = "../" + canonical.relative_to(ROOT).as_posix()
    title = display_title(path)
    return """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Duplicate source edition — """ + escape(title) + """</title><link rel="stylesheet" href="../assets/reading-room.css?v=16"><script src="../assets/reading-room-context.js?v=16" defer></script><script src="../assets/reading-room.js?v=16" defer></script></head><body class="rr-page rr-reader rr--cinema"><main class="layout"><article><section class="hero"><div class="kicker">DUPLICATE SOURCE DOCUMENT</div><h1>""" + escape(title) + """</h1><p>This source document is byte-identical to another file in the archive. To avoid two competing copies of the same reading experience, this link opens the single maintained edition.</p><p><a class="link" href=""" + '"' + escape(rel) + '"' + """>Open the canonical reading edition ↗</a></p></section></article></main></body></html>"""


def build_archive_index(catalogue):
    categories = {}
    for row in catalogue:
        categories.setdefault(row["category"], []).append(row)
    cards = []
    for category, entries in sorted(categories.items()):
        for row in entries:
            description = row.get("description") or "Open the reading edition to explore the source document, its sections and its original file."
            search_text = " ".join((row["title"], row["source"], row["category"], description)).lower()
            cards.append(
                '<a class="rr-resource-card" href="' + escape(row["reader"]) + '" data-category="' + escape(category, quote=True) +
                '" data-search="' + escape(search_text, quote=True) + '">' +
                '<span class="rr-resource-kind">' + escape(category) + '</span>' +
                '<strong>' + escape(row["title"]) + '</strong>' +
                '<p>' + escape(description) + '</p>' +
                '<span class="rr-resource-meta">' + escape(row["kind"]) + ' · ' + str(row["sections"]) + ' sections · ' + escape(row["source"]) + '</span>' +
                '<span class="rr-open">Read this edition ↗</span></a>'
            )
    options = '<option value="all">All subjects</option>' + "".join(
        '<option value="' + escape(category, quote=True) + '">' + escape(category) + ' (' + str(len(entries)) + ')</option>'
        for category, entries in sorted(categories.items())
    )
    html = """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="Source-led reading editions for the Reading Room's books, films, art, writing, learning and reflection collections."><title>Document library — The Reading Room</title><link rel="stylesheet" href="../assets/reading-room.css?v=16"><script src="../assets/reading-room-context.js?v=16" defer></script><script src="../assets/reading-room.js?v=16" defer></script></head><body class="rr-page rr--mixed"><main class="rr-archive">
<section class="rr-archive-hero"><div class="rr-eyebrow">THE READING ROOM · DOCUMENT LIBRARY</div><h1>Read beyond the title.</h1>
<p>These editions are built from the original PDFs and Word documents in this library. Each page keeps the source text searchable, gives you a navigable reading view and links back to the untouched original. The descriptions below are drawn from the document itself wherever an opening passage provides useful context.</p>
<p class="rr-archive-context">Browse by subject when you want a particular kind of material, or search for a person, theme, title or phrase. Open a reading edition to see its contents and work through one section at a time.</p></section>
<div class="rr-archive-tools"><input id="archive-search" type="search" placeholder="Search titles, themes, people or source text…" aria-label="Search document library">
<select id="archive-category" class="rr-archive-filter-select" aria-label="Filter by subject">""" + options + """</select>
<span class="rr-archive-count" id="archive-count"></span></div>
<div class="rr-archive-grid" id="archive-grid">""" + "".join(cards) + """</div>
<p id="archive-empty" hidden>No matching editions. Try a broader phrase or choose all subjects.</p>
<div class="rr-archive-note">A note on fidelity: extracted text is easier to search and read, but it may not reproduce the original page design, illustrations, columns or complex tables. The original PDF or DOCX remains the authoritative visual copy.</div>
<footer class="rr-site-footer"><a href="../index.html">← Return to the Reading Room</a></footer></main>
<script>(function(){const q=document.getElementById('archive-search'),select=document.getElementById('archive-category'),cards=[...document.querySelectorAll('.rr-resource-card')],count=document.getElementById('archive-count'),empty=document.getElementById('archive-empty');function update(){const term=q.value.trim().toLowerCase(),cat=select.value;let n=0;cards.forEach(c=>{const ok=(cat==='all'||c.dataset.category===cat)&&(!term||c.dataset.search.includes(term));c.hidden=!ok;if(ok)n++;});count.textContent=n+' of '+cards.length+' editions';empty.hidden=n>0;}q.addEventListener('input',update);select.addEventListener('change',update);update();})();</script></body></html>"""
    (OUT / "index.html").write_text(html, encoding="utf-8")



def main():
    sources = sorted([*ROOT.glob("*.pdf"), *ROOT.glob("*.docx")], key=lambda p: ("(1)" in p.stem.lower(), p.name.lower()))
    catalogue = []
    hashes = {}
    report = []
    for source in sources:
        title = display_title(source)
        kind = source.suffix[1:].upper()
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        output = OUT / (source.stem + ".html")
        if digest in hashes:
            canonical_source, canonical_reader = hashes[digest]
            output.write_text(canonical_duplicate_alias(source, canonical_reader), encoding="utf-8")
            category, _, _ = category_info(title)
            catalogue.append({"title": title, "source": source.name, "reader": output.name, "kind": kind, "sections": 0, "category": category, "description": "This source is a duplicate of " + canonical_source + ". Open the maintained edition to read the complete collection."})
            report.append({"source": source.name, "output": "html/" + output.name, "sha256": digest, "status": "duplicate-alias", "canonical_source": canonical_source, "extracted_chars": 0})
            print("Duplicate:", source.name, "->", canonical_source)
            continue
        hashes[digest] = (source.name, output)
        try:
            if source.suffix.lower() == ".pdf":
                extracted, extraction_method = extract_pdf(source)
                if title.strip().lower() == "aag ki kavitayen":
                    sections, toc, poem_count = render_poetry_pdf(extracted)
                else:
                    sections, toc = render_pdf_blocks(extracted)
                    poem_count = 0
                paragraph_count = 0
                table_count = 0
            else:
                blocks, paragraph_count, table_count = extract_docx(source)
                sections, toc = render_docx_blocks(blocks)
                extraction_method = "python-docx"
                extracted = "\n\n".join((b[1].get("text", "") if b[0] == "paragraph" else " ".join(" ".join(row) for row in b[1])) for b in blocks)
            if not sections:
                sections = ['<section class="page"><p>No readable text was extracted. Please open the original source document.</p></section>']
            category, _, guidance = category_info(title)
            summary = document_summary(title, extracted, guidance)
            html = make_reader(source, title, kind, sections, toc, extraction_method, digest, summary)
            output.write_text(html, encoding="utf-8")
            category, _, _ = category_info(title)
            catalogue.append({"title": title, "source": source.name, "reader": output.name, "kind": kind, "sections": len(sections), "category": category, "description": summary})
            report.append({"source": source.name, "output": "html/" + output.name, "sha256": digest, "status": "converted" if len(extracted.strip()) > 150 else "low-text-review", "extracted_chars": len(extracted), "sections": len(sections), "toc_entries": len(toc), "poem_count": poem_count if source.suffix.lower() == ".pdf" else 0, "extraction": extraction_method, "docx_paragraphs": paragraph_count, "docx_tables": table_count, "docx_styles": {name: sum(1 for b in blocks if b[0] == "paragraph" and b[1]["style"] == name) for name in sorted({b[1]["style"] for b in blocks if b[0] == "paragraph"})} if source.suffix.lower() == ".docx" else {}, "output_bytes": output.stat().st_size})
            print("Converted:", source.name, "->", output.name, "(" + str(len(sections)) + " sections)")
        except Exception as exc:
            report.append({"source": source.name, "output": "html/" + output.name, "sha256": digest, "status": "error", "error": str(exc)})
            raise
    expected = len(sources)
    if len(catalogue) != expected:
        raise SystemExit("Conversion count mismatch: expected " + str(expected) + ", built " + str(len(catalogue)))
    build_archive_index(catalogue)
    report_path = OUT / "conversion-report.json"
    report_path.write_text(json.dumps({"source_count": expected, "reader_count": len(catalogue), "sources": report}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    statuses = {x["status"]: sum(1 for y in report if y["status"] == x["status"]) for x in report}
    print("Conversion complete:", expected, "source documents;", statuses, "report:", report_path)
    

if __name__ == "__main__":
    main()
