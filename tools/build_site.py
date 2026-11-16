#!/usr/bin/env python3
"""Build the Reading Room homepage, subject pages, page context manifest and shared shell."""
from pathlib import Path
from html import escape
import json
import re

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
COLLECTIONS = ROOT / "collections"
HTML_DIR = ROOT / "html"
ASSETS.mkdir(exist_ok=True)
COLLECTIONS.mkdir(exist_ok=True)

GROUPS = [
{
 "slug":"cinema","file":"cinema.html","name":"Cinema & the moving image",
 "nav":"Cinema","eyebrow":"FILM AS ART, HISTORY AND HUMAN EXPERIENCE",
 "intro":"A way into cinema that goes beyond a ranked watchlist: essential works, animation, world cinema, biographical stories, intimate art films and carefully sequenced viewing paths.",
 "method":"Choose a route rather than trying to finish every catalogue. The shorter essential lists are useful entry points; the larger databases are best used when you already know the kind of film, period, director or country you want to explore.",
 "paths":[
  ("Begin with a shared foundation","A compact route through influential films before moving into more specialised cinema.",["html/100_essential_films.html","html/300_Films_Filmography.html","html/complete_movie_encyclopedia.html"]),
  ("Explore cinema across cultures","Follow filmmakers and stories beyond the familiar Hollywood canon.",["html/asian_cinema_curriculum.html","html/500_Films_500_Music_Global_Guide.html","asian_cinema_curriculum (1).html"]),
  ("Study cinema as an art form","Move from expressive animation to intimacy, experimentation and film language.",["300_animated_films.html","html/50_e_art_films.html","html/masters_of_e_art_cinema.html"])
 ],
 "items":[
 ("300_animated_films.html","300 Essential Animated Films","A broad journey through animation as a serious and varied art form, from accessible classics to distinctive international work."),
 ("asian_cinema_curriculum (1).html","Asian Cinema — Interactive Curriculum","A sequenced viewing path through Asian cinema, organised around emotional, philosophical and human-life themes."),
 ("cinematic-database (1).html","Global Film Database","A searchable film catalogue for exploring titles, filmmakers, regions and genres."),
 ("cinematic_canon (1).html","The Cinematic Canon","A large-scale film reference intended for browsing and comparing critical cinema."),
 ("film_collection_v8.html","The Complete Film Collection","The principal interactive film collection, with search, genre, country, decade, ratings and watched-state controls."),
 ("sen-mood-movies.html","Sensual Mood Cinema","A mood-led film collection covering intimacy, desire, relationships and sensual storytelling; review the content notes before choosing."),
 ("html/100_essential_films.html","100 Essential Films","A deliberately varied starting canon, moving across genres, eras, countries and difficult subjects."),
 ("html/200_Films_Like_Frida.html","200 Films Like Frida","Biographical films about artists, writers and other lives shaped by creative ambition and struggle."),
 ("html/300_Films_Filmography.html","300 Films — A Global Filmography","A curated global film journey for viewers interested in contemplative, humanist and formally distinctive cinema."),
 ("html/500_Films_500_Music_Global_Guide.html","A Life Worth Living — 500 Films & 500 Music","A cross-cultural guide that connects cinema and music with a reflective, lifelong approach to discovery."),
 ("html/50_e_art_films.html","50 Bold, Intimate & Thought-Provoking Art Films","A focused selection of theatrical art cinema exploring the body, intimacy and difficult human questions."),
 ("html/All_Film_Collections_Combined_compressed.html","The Combined Film Collections","A large combined film reference. Use the contents and within-document search to navigate the extensive source."),
 ("html/Bold_Cinema_Collection.html","Bold Cinema Collection","A curated group of sensual, dramatic and formally adventurous films, with clear subject awareness."),
 ("html/Films_That_Open_New_Human_Domains.html","Films That Open New Human Domains","Films and documentaries chosen for the areas of human experience, knowledge and empathy they make visible."),
 ("html/cinema_900 (1).html","Cinema 900","A multi-list cinema collection spanning world cinema, slow cinema, sensual film and other focused paths."),
 ("html/complete_movie_encyclopedia.html","Complete Movie Encyclopedia","A searchable-style reference edition with film details, ratings and availability notes from the source document."),
 ("html/complete_movie_ratings.html","Complete Movie Ratings","A shorter ratings reference bringing together IMDb and Rotten Tomatoes scores for selected films."),
 ("html/complete_movie_ratings_647.html","Complete Movie Ratings — 647 Films","A larger 647-title ratings reference with director, year, IMDb and Rotten Tomatoes information."),
 ("html/masters_of_e_art_cinema.html","Masters of Art Cinema","A filmmaker-centred guide to directors who used desire, the body and intimacy as serious artistic material."),
 ("html/sensitive_cinema.html","Sensitive Cinema","A collection of films selected for empathy, emotional understanding and human sensitivity."),
 ("html/asian_cinema_curriculum.html","Asian Cinema — Reading Edition","The source-document reading edition of the Asian cinema curriculum, arranged as complete thematic journeys.")
 ]
},
{
 "slug":"anime-manga","file":"anime-and-manga.html","name":"Anime, manga & comics","nav":"Manga & comics",
 "eyebrow":"SEQUENTIAL ART, STORY WORLDS AND IDEAS",
 "intro":"From welcoming first reads to complex manga, anime adaptations, political comics and reflective curricula. The collection is arranged so readers can choose by mood, depth, form and subject rather than face one enormous undifferentiated list.",
 "method":"Start with the beginner guide or recommendations if you are new to the medium. Use the larger indexes when you want breadth. The darker and mature collections are separated from the general reading paths and clearly labelled.",
 "paths":[
  ("Find a first manga","Move from welcoming, emotionally engaging stories to longer and more demanding works.",["manga-guide.html","html/manga_recommendations.html","manga-1000.html"]),
  ("Read through ideas and values","Use stories to examine empathy, moral choices, social systems and inner life.",["anime-manga-values-curriculum.html","human-development-curriculum.html","political-comics-list.html"]),
  ("Explore anime and adaptations","Compare essential anime films and series with their manga and film adaptations.",["html/ultimate_anime_guide.html","html/definitive_anime_encyclopedia.html","html/500_Manga_Movies.html"])
 ],
 "items":[
 ("Qwen_html_20260604_f25nf6z8p.html","100 Manga That Will Change How You Think","A focused set of thought-provoking manga exploring philosophy, morality and the human condition."),
 ("anime-manga-values-curriculum.html","Anime & Manga for a Life of Reflection","A 200-work curriculum connecting anime and manga with ethics, sensitivity, integrity and the experience of being human."),
 ("manga-1000.html","1200 Manga — The Complete Reading Atlas","A broad reading atlas across genres, eras, tones and audiences; use the filters to narrow the field."),
 ("manga-comics-master.html","Manga & Comics Master Index","A large index of manga and comics with multiple ways to browse the catalogue."),
 ("manga-guide.html","50 Manga to Read — A Moving Journey","A guided route from approachable, joyful stories to emotionally rich and literary manga."),
 ("manga-index.html","Dark Ink — Transgressive Manga Index","An adult-oriented reference to challenging, transgressive and formally adventurous manga. Mature subject matter; intended for adult readers."),
 ("manhwa300.html","300 Adult Romance Manhwa","A mature romance collection. Adults only; check content and subject notes before reading."),
 ("manhwa_300_filter_app.html","Adult Romance Manhwa — Filter App","An interactive way to narrow the mature manhwa list by preference. Adults only."),
 ("political-comics-list.html","The World in Panels","A political comics and manga curriculum bringing together nonfiction and fiction about power, society and history."),
 ("taboo-comics.html","Forbidden Pages — Transgressive Comics","A reference to comics that challenged social limits or faced suppression. Contains mature themes; intended for adult readers."),
 ("top500_adult_manga.html","Top 500 Adult Manga","A ranked reference to mature, story-led manga and related adaptations. Adults only."),
 ("html/500_Manga_Movies.html","500 Films Based on Manga","A reference to critically recognised films adapted from manga, including anime and live-action work."),
 ("html/definitive_anime_encyclopedia.html","The Definitive Anime Encyclopedia","A guide to essential anime films and series across genres and eras, with paths based on viewing time and interest."),
 ("html/manga_recommendations.html","Manga Recommendations","A practical shortlist organised around romance, mystery, comedy and feel-good reading."),
 ("html/ultimate_anime_guide.html","The Ultimate Anime Guide","A time-aware guide to essential anime movies and series, organised by genre and viewing commitment.")
 ]
},
{
 "slug":"art","file":"art-and-making.html","name":"Art & creative practice","nav":"Art",
 "eyebrow":"LEARN A MEDIUM, STUDY AN ARTIST, MAKE SOMETHING",
 "intro":"Practical learning resources sit alongside artist biographies and small creative exercises. This section is meant to help you move from browsing references to actually practising a medium.",
 "method":"Pick one medium and one manageable exercise. Use the free resource directories for instruction, the artist guides for visual understanding, and the journals or generators for a regular low-pressure practice.",
 "paths":[
  ("Build a drawing and painting foundation","Start with free instruction, then choose a short exercise you can repeat.",["free-art-resources.html","html/Free_Art_Resource_Library.html","watercolour_tasks (1).html"]),
  ("Learn from artists","Study how artists worked, what they made and what shaped their practice.",["html/masters_of_art.html","bob_ross_complete_guide.html"]),
  ("Make an idea concrete","Use a prompt or generator to move from a blank page to a workable brief.",["collage-idea-generator.html","collage-idea-generato - Theme.html"])
 ],
 "items":[
 ("bob_ross_complete_guide.html","Bob Ross — The Joy of Painting","A chronological guide to all 31 seasons and 403 episodes, suitable for following the painting demonstrations in order."),
 ("collage-idea-generato - Theme.html","Collage Idea Generator — Alternate Theme","An alternate visual version of the collage prompt generator, kept as a separate creative interface."),
 ("collage-idea-generator.html","Collage Brief Generator","A practical tool for generating collage briefs and recording recent creative directions."),
 ("free-art-resources.html","Free Creative Art Resources","A curated directory of free or meaningfully free learning resources across drawing, painting, colour and digital art."),
 ("watercolour_tasks (1).html","Watercolour Journal — 30 Painting Tasks","Thirty contemplative painting exercises for building a steady watercolour practice."),
 ("html/Free_Art_Resource_Library.html","Free Art Resource Library — Reading Edition","A structured text edition of free resources for drawing, anatomy, painting, perspective and visual storytelling."),
 ("html/masters_of_art.html","Masters of Art","Artist biographies, notable works, working habits and the qualities that made each artist distinctive.")
 ]
},
{
 "slug":"books","file":"books-and-reading.html","name":"Books & reading journeys","nav":"Books",
 "eyebrow":"LITERATURE, FILM CRAFT AND LIFELONG READING",
 "intro":"Reading lists are more useful when they explain why a work belongs, where it comes from and what kind of journey it supports. This section brings together world fiction, Asian literature, books for filmmakers and large personal reference collections.",
 "method":"Use the curated paths as a sequence, not a compulsory syllabus. Read across traditions and periods; pause to follow authors or themes that interest you. The larger reference collections are for discovery rather than completion.",
 "paths":[
  ("Read across literary traditions","Begin with a broad world-fiction reference, then follow a regional or thematic route.",["html/1000_Greatest_Fictional_Books.html","html/asian_books_curriculum.html","life-fiction-curriculum.html"]),
  ("Understand how stories are made","Pair a filmmaker's reading list with a practical viewing route.",["html/A_Filmmakers_Reading_List.html","html/100_essential_films.html","html/Personal_Reference_Film_Books_Art.html"]),
  ("Build a personal reference shelf","Use the large cross-media indexes when you want to connect books, films, music and art.",["The_Curators_Library.html","html/library-3.html","html/Personal_Reference_Film_Books_Art.html"])
 ],
 "items":[
 ("life-fiction-curriculum.html","The Fiction of Living","A seven-stage literary curriculum mapping stories to the changing questions and challenges of a human life."),
 ("living-curriculum-2026.html","How to Live — A Complete Curriculum","A world-literature reading journey organised around the stages of life and the questions each stage brings."),
 ("The_Curators_Library.html","The Curator's Library","A large personal cross-media catalogue connecting films, books, music, anime, art and other cultural references."),
 ("html/1000_Greatest_Fictional_Books.html","1000 Greatest Fictional Books","A broad world-fiction reference arranged across literary traditions and regional groupings."),
 ("html/A_Filmmakers_Reading_List.html","A Filmmaker's Reading List","Two hundred books across story, screenwriting and cinema craft for readers who want to understand how films are made."),
 ("html/asian_books_curriculum.html","Asian Literature — Sequential Reading Curriculum","Six reading journeys across Asian literary traditions, with thematic arcs and historical range."),
 ("html/Personal_Reference_Film_Books_Art.html","Personal Reference — Film, Books & Art","A compact cross-media reference drawn from a larger personal collection."),
 ("html/library-3.html","Personal Film & Art Library","A very large reference spanning films, anime, books, albums, poems and artists. Use its contents to navigate by medium.")
 ]
},
{
 "slug":"ideas","file":"ideas-and-reflection.html","name":"Ideas & reflection","nav":"Ideas",
 "eyebrow":"THINKING, ATTENTION, EMOTION AND THE SHAPE OF A LIFE",
 "intro":"These collections are designed for slower engagement: reflective prompts, thinkers, films and books that help examine attention, identity, grief, mortality, wonder and the choices that shape a life.",
 "method":"Choose one theme that feels relevant now. Work through a short sequence, write a few notes, and leave room between items. These are invitations to reflect, not clinical advice or a productivity programme.",
 "paths":[
  ("Make space for reflection","Move from writing prompts to thinkers who examine the mind and attention.",["html/200_prompts_mind_detox_v2.html","html/200_thinkers_quiet_mind_v2.html","html/Reading_Course_Emotions_Wonder.html"]),
  ("Follow the questions of a lifetime","Pair the human-development curriculum with literature and cross-media works.",["human-development-curriculum.html","life-fiction-curriculum.html","four-arcs-library.html"]),
  ("Explore loss and mortality thoughtfully","Use the reading and film courses as considered, paced journeys.",["html/memento-mori-course.html","html/meditation_on_death.html","html/200_prompts_emotion_wonder_v2.html"])
 ],
 "items":[
 ("four-arcs-library.html","The Four Arcs — Library of Human Experience","A cross-media journey through films, anime, manga, books, albums and poems, organised around human experience."),
 ("human-development-curriculum.html","The Inner Life — Human Development Curriculum","A five-phase film and manga curriculum about identity, grief, love, purpose and wisdom."),
 ("html/1000_Inspirations.html","1000 Inspirations","A curated collection of things to read, understand, question and explore across several areas of life."),
 ("html/2000_Inspirations (1).html","2000 Inspirations","A broad compendium of ideas for reading, writing, painting, learning skills and exploring life."),
 ("html/200_prompts_emotion_wonder_v2.html","Writing for Emotion & Wonder","A sequenced writing course moving through stillness, connection, suffering, beauty and the wider world."),
 ("html/200_prompts_mind_detox_v2.html","Mind Detox — 200 Writing Prompts","A six-phase writing practice for unloading mental noise, quieting attention and clarifying what matters."),
 ("html/200_thinkers_quiet_mind_v2.html","200 Thinkers for a Quieter Mind","A philosophy curriculum that explores why the mind becomes noisy and how different thinkers approach attention."),
 ("html/A_Life_Worth_Living_500_Suggestions.html","A Life Worth Living — 500 Suggestions","Five hundred entry points into art, literature, music, cinema and thought, arranged as a personal inspiration guide."),
 ("html/Reading_Course_Emotions_Wonder.html","Emotions & Wonder — Reading Course","A sequential course in human experience through fiction from different traditions and countries."),
 ("html/meditation_on_death.html","A Meditation on Death","A cyclic curriculum of books and films approaching mortality through multiple philosophical and cultural traditions."),
 ("html/memento-mori-course.html","Memento Mori — A Curated Study Course","A study course on death, grief and impermanence across literature, film and sound."),
 ("html/1000_Google_Searches_Grand_Curiosity_Atlas.html","The Grand Curiosity Atlas","One thousand specific search trails for exploring overlooked history, unusual science and unfamiliar subjects.")
 ]
},
{
 "slug":"writing","file":"poetry-and-writing.html","name":"Poetry & writing","nav":"Writing",
 "eyebrow":"READ CLOSELY, FIND A VOICE, PUT WORDS ON THE PAGE",
 "intro":"Poetry, writing prompts and small writing surfaces belong together: one helps you read language, another helps you practise it, and the tools give you somewhere to keep the work.",
 "method":"You do not need to begin at the first prompt or finish a whole collection. Choose one page, one poem or one exercise. Keep drafts small and return to them when you have something to add.",
 "paths":[
  ("Find a way into writing","Use a prompt collection to begin, then move into a simple drafting space.",["html/1000_Writing_Prompts.html","typewriter.html","marginalia-diary.html"]),
  ("Read and make poetry","Read the Hindi collection and learn a visual form of found poetry.",["html/Aag_Ki_Kavitayen.html","blackout_poetry_tutorial.html"]),
  ("Keep a reading notebook","Use marginalia to hold observations from books, films and everyday life.",["marginalia-diary.html","html/1000_Writing_Prompts.html","typewriter.html"])
 ],
 "items":[
 ("blackout_poetry_tutorial.html","Blackout Poetry — A Tutorial","A practical introduction to finding poems inside existing text through selection, erasure and attention."),
 ("marginalia-diary.html","Marginalia — A Daily Notebook","A small browser-based notebook for keeping reading notes, observations and personal annotations."),
 ("typewriter.html","Typewriter — Writing Surface","A focused, minimal place to draft text without a large publishing interface."),
 ("html/1000_Writing_Prompts.html","1000 Writing Prompts","A large prompt collection across fiction, nonfiction, poetry, drama, satire and experimental writing."),
 ("html/Aag_Ki_Kavitayen.html","Aag Ki Kavitayen","A Hindi poetry collection organised as a journey through resistance, darkness, hope and change.")
 ]
},
{
 "slug":"family","file":"children-and-family.html","name":"Children & family learning","nav":"Family",
 "eyebrow":"STORIES, CURIOSITY AND LEARNING TOGETHER",
 "intro":"A family learning shelf should make age, stage and purpose clear. These guides gather stories from different regions, reading sequences for young children and wider creative and educational resources.",
 "method":"Use the age band and reading stage as a guide, not a rigid rule. Read aloud, follow the child's attention, and revisit favourites. For large directories, choose one theme or country at a time rather than trying to cover everything.",
 "paths":[
  ("Build a first reading routine","Start with the age-three sequence and use the world stories guide to widen the range.",["html/Three_Year_Old_Reading_Guide (1).html","html/World_Stories_3YearOld_Guide.html","html/Global_Kids_Reading_Guide_FINAL (1).html"]),
  ("Explore stories around the world","Use the global books guide to move between cultures, languages and age bands.",["html/Global_Kids_Books_Complete_Guide.html","html/Global_Kids_Reading_Guide_FINAL (1).html"]),
  ("Follow curiosity beyond books","Use the wider creative and educational directory to find subjects worth exploring together.",["html/1000_Creative_Educational_Cultural_Links.html","html/1000_Google_Searches_Grand_Curiosity_Atlas.html"])
 ],
 "items":[
 ("html/Global_Kids_Books_Complete_Guide.html","Global Kids Books — Complete Guide","A large international children's reading guide spanning ages 0–17, multiple regions and eight age bands."),
 ("html/Global_Kids_Reading_Guide_FINAL (1).html","Global Kids Reading Guide","A companion reading sequence with age bands, regions and practical ways to choose the next story."),
 ("html/Three_Year_Old_Reading_Guide (1).html","Three-Year-Old Reading Guide","A sequenced 40-week, 10-phase reading journey built around story length, rhythm, feelings and early imagination."),
 ("html/World_Stories_3YearOld_Guide.html","World Stories for Three-Year-Olds","A world-story sequence introducing children to stories and cultures through short, age-aware reading."),
 ("html/1000_Creative_Educational_Cultural_Links.html","1000 Creative, Educational & Cultural Links","A global directory of learning portals, artists, science, culture and creative resources for family exploration.")
 ]
},
{
 "slug":"work","file":"work-and-tools.html","name":"Work, security & personal tools","nav":"Work & tools",
 "eyebrow":"EXPLAIN COMPLEX IDEAS, KEEP PRACTICE VISIBLE",
 "intro":"This section connects practical tools with a small set of professional learning resources. It includes film-based ways to explain security concepts to teams, plus lightweight tools for tracking ongoing practice.",
 "method":"Use the storytelling guides as discussion aids, not as substitutes for technical controls or security training. The trackers and writing tools are personal practice aids; keep entries small enough that you will actually return to them.",
 "paths":[
  ("Make security concepts memorable","Use a film analogy to open a conversation, then translate it into the real security control or engineering decision.",["html/Cybersecurity_Stories_For_Your_Teams.html","html/Cybersecurity_Storytelling_Movies.html"]),
  ("Build a sustainable practice","Use the tracker to notice how attention is distributed across ongoing work.",["the-loom-tracker.html","marginalia-diary.html","typewriter.html"])
 ],
 "items":[
 ("html/Cybersecurity_Stories_For_Your_Teams.html","Cybersecurity Stories for Your Teams","Fifty film-based analogies mapped to risk, technical compliance, AppSec, networks, identity and security operations."),
 ("html/Cybersecurity_Storytelling_Movies.html","Movies for Cybersecurity Storytelling","A companion set of film analogies for explaining threat actors, social engineering and security concepts to teams."),
 ("the-loom-tracker.html","The Loom — Four Threads","A personal tracker for keeping active work, daily practice, streaks and balance visible.")
 ]
}
]

ALIASES = {
 "Big_library.html":("manga-comics-master.html","This old filename contained no separate library. It now points to the complete manga and comics reference."),
 "grand_library (2).html":("The_Curators_Library.html","This older shortcut did not contain a separate catalogue. The Curator's Library is the maintained cross-media reference."),
 "manga-archive-v4.html":("manga-index.html","This archived filename did not contain a separate collection. The current manga index is the maintained destination."),
 "top500_manga.html":("top500_adult_manga.html","This file was a duplicate shortcut to the adult manga list. The maintained reading page is linked below."),
 "html/All_Film_Collections_Combined_compressed (1).html":("html/All_Film_Collections_Combined_compressed.html","The two source PDFs are byte-identical. This alternate reading URL now opens the single canonical conversion.")
}

def rel_url(href, from_collection=True):
    return "../" + href if from_collection else href

def header(prefix, active):
    links=[]
    for group in GROUPS:
        links.append('<a href="'+prefix+'collections/'+group["file"]+'"'+(' aria-current="page"' if group["slug"]==active else '')+'>'+escape(group["nav"])+'</a>')
    return ('<header class="rr-site-header"><a class="rr-brand" href="'+prefix+'index.html"><span class="rr-brand-mark">R</span>THE READING ROOM</a>'
            '<nav class="rr-navlinks" aria-label="Main collections">'+"".join(links)+'</nav>'
            '<div class="rr-header-actions"><button class="rr-theme-toggle" type="button" aria-label="Switch colour theme" title="Switch colour theme">◐</button>'
            '<button class="rr-menu-toggle" type="button" aria-expanded="false" aria-label="Open navigation">Menu</button></div></header>')

def resource_card(item):
    href,title,description=item
    kind="reading edition" if href.startswith("html/") else "interactive page"
    search=" ".join((title,description,kind)).lower()
    return ('<a class="rr-resource-card" href="'+rel_url(href)+'" data-kind="'+("reading" if href.startswith("html/") else "interactive")+'" data-search="'+escape(search,quote=True)+'">'
            '<span class="rr-resource-kind">'+escape(kind)+'</span><strong>'+escape(title)+'</strong><p>'+escape(description)+'</p><span class="rr-open">Open collection ↗</span></a>')

def make_home():
    cards=[]
    for g in GROUPS:
        cards.append('<a class="rr-collection-card" href="collections/'+g["file"]+'"><span class="rr-card-label">'+escape(g["eyebrow"])+'</span><strong>'+escape(g["name"])+'</strong><p>'+escape(g["intro"])+'</p><small>Explore '+str(len(g["items"]))+' collections →</small></a>')
    paths=[
      ("A wider view of cinema","Start with a compact essential list, then move into global filmography and regional curricula.",["html/100_essential_films.html","html/300_Films_Filmography.html","html/asian_cinema_curriculum.html"],"cinema"),
      ("Read manga with intention","Begin with an approachable guide, then follow stories into values, history and social questions.",["manga-guide.html","anime-manga-values-curriculum.html","political-comics-list.html"],"anime-manga"),
      ("Make art part of the week","Use a free learning directory, choose one medium, and keep the exercises small.",["free-art-resources.html","html/Free_Art_Resource_Library.html","watercolour_tasks (1).html"],"art"),
      ("Read and reflect slowly","Choose one human question and follow a short path through writing, thought and literature.",["html/200_prompts_emotion_wonder_v2.html","html/200_thinkers_quiet_mind_v2.html","life-fiction-curriculum.html"],"ideas")
    ]
    paths_html=[]
    for title,desc,steps,slug in paths:
        step_links=[]
        for i,f in enumerate(steps):
            target=next((it[1] for group in GROUPS for it in group["items"] if it[0]==f),f.rsplit("/",1)[-1].replace("_"," ").replace(".html",""))
            step_links.append('<a href="'+f+'">'+escape(target)+'</a>')
        paths_html.append('<article class="rr-route-card"><h3>'+escape(title)+'</h3><p>'+escape(desc)+'</p><div class="rr-route-steps">'+' <span>→</span> '.join(step_links)+'</div></article>')
    total=sum(len(g["items"]) for g in GROUPS)
    return '''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="A personal digital library for cinema, manga, art, books, reflection, writing, family learning and practical tools."><title>The Reading Room — A Library for a Curious Life</title><link rel="stylesheet" href="assets/reading-room.css?v=17"><script src="assets/reading-room-context.js?v=17" defer></script><script src="assets/reading-room.js?v=17" defer></script></head><body class="rr-page rr-home"><div class="rr-home-wrap">'''+header("","") + '''
<main><section class="rr-home-hero"><div class="rr-eyebrow">A PERSONAL DIGITAL LIBRARY · STORIES · KNOWLEDGE · PRACTICE</div><h1>Stories, ideas and practices worth returning to.</h1><p>This is a library to explore at your own pace. Follow a reading path, discover a film, learn an art practice, find stories to read together, or use a small tool to keep your work moving. The collections are organised around context and use, not just file names.</p><div class="rr-hero-actions"><a class="rr-action-link primary" href="collections/cinema.html">Explore the collections ↗</a><a class="rr-action-link" href="html/index.html">Browse source-document editions</a></div></section>
<section><div class="rr-section-head"><div><h2>Choose by curiosity</h2><p>Each area includes an introduction, suggested routes and links to the original interactive pages or the converted reading editions.</p></div></div><div class="rr-collection-grid">'''+''.join(cards)+'''</div></section>
<section><div class="rr-section-head"><div><h2>Suggested ways in</h2><p>Four short routes for when you know the kind of experience you want, but not where to begin.</p></div></div><div class="rr-route-grid">'''+''.join(paths_html)+'''</div></section>
<section class="rr-route-intro"><div><h3>How to use this library</h3><p>Start with the context at the top of a collection page. Use its suggested routes before opening the larger catalogues. In the long lists, search and filters are there to help you narrow down—not to become the main event.</p></div><div><h3>About the reading editions</h3><p>The source PDFs and DOCX files remain preserved. Their HTML reading editions make text searchable and easier to navigate. Use the original document whenever a table, image, layout detail or scanned page matters.</p><p><a href="html/index.html">Open all document reading editions ↗</a></p></div></section></main>
<footer class="rr-home-footer">The Reading Room · A personal collection for learning, reading, making and reflection · <a href="https://github.com/piyushimself/files">Source repository</a></footer></div></body></html>'''

def make_collection(g):
    path_cards=[]
    for title,desc,steps in g["paths"]:
        links=[]
        for f in steps:
            target=next((it[1] for it in g["items"] if it[0]==f),None)
            if target is None:
                target=next((it[1] for group in GROUPS for it in group["items"] if it[0]==f),f.rsplit("/",1)[-1].replace("_"," ").replace(".html",""))
            links.append('<a href="'+rel_url(f)+'">'+escape(target)+'</a>')
        path_cards.append('<article class="rr-route-card"><h3>'+escape(title)+'</h3><p>'+escape(desc)+'</p><div class="rr-route-steps">'+' <span>→</span> '.join(links)+'</div></article>')
    cards="".join(resource_card(it) for it in g["items"])
    return '''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="'''+escape(g["intro"],quote=True)+'''"><title>'''+escape(g["name"])+''' — The Reading Room</title><link rel="stylesheet" href="../assets/reading-room.css?v=17"><script src="../assets/reading-room-context.js?v=17" defer></script><script src="../assets/reading-room.js?v=17" defer></script></head><body class="rr-page rr-hub"><div class="rr-hub-wrap">'''+header("../",g["slug"])+'''
<main class="rr-collection-page"><section class="rr-hub-hero"><div class="rr-eyebrow">'''+escape(g["eyebrow"])+'''</div><h1>'''+escape(g["name"])+'''</h1><p>'''+escape(g["intro"])+'''</p><div class="rr-collection-note"><strong>A useful way to approach this section</strong><p>'''+escape(g["method"])+'''</p></div></section>
<section><div class="rr-section-head"><div><h2>Suggested routes</h2><p>Follow one of these small paths instead of trying to browse everything at once.</p></div></div><div class="rr-route-grid">'''+''.join(path_cards)+'''</div></section>
<section class="rr-library-section"><div class="rr-section-head"><div><h2>Explore the collection</h2><p>Choose a page by purpose. Interactive pages retain their tools; reading editions open a navigable text copy of the source document.</p></div></div>
<div class="rr-library-toolbar"><input class="rr-hub-search" type="search" placeholder="Search titles or subjects…" aria-label="Search this collection"><select class="rr-hub-kind" aria-label="Filter by page type"><option value="all">All page types</option><option value="interactive">Interactive pages</option><option value="reading">Reading editions</option></select><span class="rr-results-count"></span></div>
<div class="rr-resource-grid">'''+cards+'''</div><div class="rr-no-results">No matching pages. Try a shorter search or select all page types.</div></section></main>
<footer class="rr-hub-footer"><a href="../index.html">← Return to the Reading Room</a> · <a href="../html/index.html">All source-document editions</a></footer></div></body></html>'''

def alias_page(path,target,note):
    prefix="../" if path.startswith("html/") else ""
    href=prefix+target
    title=Path(path).stem.replace("_"," ").replace("-"," ")
    html='''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Archived shortcut — '''+escape(title)+'''</title><link rel="stylesheet" href="'''+prefix+'''assets/reading-room.css?v=17"><script src="'''+prefix+'''assets/reading-room.js?v=17" defer></script></head><body class="rr-page rr--mixed"><main style="max-width:860px;margin:38px auto;padding:20px"><div class="rr-eyebrow">ARCHIVE NOTE</div><h1>'''+escape(title)+'''</h1><p>'''+escape(note)+'''</p><p><a class="rr-action-link primary" href="'''+escape(href)+'''">Open the maintained collection ↗</a></p><p><a href="'''+prefix+'''index.html">Return to the Reading Room</a></p></main></body></html>'''
    ROOT.joinpath(path).write_text(html,encoding="utf-8")

def inject_shared_assets(path):
    text=path.read_text(encoding="utf-8")
    prefix="../" if path.parent.name=="html" else ""
    # Some imported app files are body fragments rather than full documents.
    if not re.search(r"<html\b", text, re.I):
        styles=re.findall(r"<style\b[^>]*>[\s\S]*?</style>", text, re.I)
        text=re.sub(r"<style\b[^>]*>[\s\S]*?</style>", "", text, flags=re.I)
        tags=('<link rel="stylesheet" href="'+prefix+'assets/reading-room.css?v=17">'
              '<script src="'+prefix+'assets/reading-room-context.js?v=17" defer></script>'
              '<script src="'+prefix+'assets/reading-room.js?v=17" defer></script>')
        text='<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'+''.join(styles)+tags+'</head><body class="rr-page rr--mixed">'+text+'</body></html>'
        path.write_text(text,encoding="utf-8")
        return
    text=re.sub(r'<link\b[^>]*reading-room\.css[^>]*>',"",text,flags=re.I)
    text=re.sub(r'<script\b[^>]*reading-room(?:-[a-z-]+)?\.js[^>]*>\s*</script>\s*',"",text,flags=re.I)
    tags=('<link rel="stylesheet" href="'+prefix+'assets/reading-room.css?v=17">'
          '<script src="'+prefix+'assets/reading-room-context.js?v=17" defer></script>'
          '<script src="'+prefix+'assets/reading-room.js?v=17" defer></script>')
    if re.search(r'</head>',text,re.I):
        text=re.sub(r'</head>',tags+'</head>',text,count=1,flags=re.I)
    elif re.search(r'<head\b[^>]*>',text,re.I):
        text=re.sub(r'<head\b[^>]*>',lambda m:m.group(0)+tags,text,count=1,flags=re.I)
    else:
        text=re.sub(r'<html\b[^>]*>',lambda m:m.group(0)+'<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'+tags+'</head>',text,count=1,flags=re.I)
    def body_repl(m):
        attrs=m.group(1)
        cm=re.search(r'''class=["']([^"']*)["']''',attrs,re.I)
        if cm:
            cls=cm.group(1)
            if "rr-page" not in cls: cls += " rr-page"
            if "rr--" not in cls: cls += " rr--mixed"
            attrs=attrs[:cm.start(1)]+cls+attrs[cm.end(1):]
        else:
            attrs+=' class="rr-page rr--mixed"'
        return '<body'+attrs+'>'
    if re.search(r'<body\b',text,re.I):
        text=re.sub(r'<body([^>]*)>',body_repl,text,count=1,flags=re.I)
    else:
        text=re.sub(r'</head>', '</head><body class="rr-page rr--mixed">', text, count=1, flags=re.I)
        text=text.replace('</html>','</body></html>')
    path.write_text(text,encoding="utf-8")

def main():
    expected={it[0] for g in GROUPS for it in g["items"]}|set(ALIASES)
    actual={p.name for p in ROOT.glob("*.html") if p.name!="index.html"}|{"html/"+p.name for p in HTML_DIR.glob("*.html") if p.name!="index.html"}
    missing=sorted(actual-expected); absent=sorted(expected-actual)
    if missing or absent:
        raise SystemExit("Page coverage mismatch. Unmapped: "+", ".join(missing)+"; missing targets: "+", ".join(absent))
    context={}
    for g in GROUPS:
        for file,title,desc in g["items"]:
            context[file]={"section":g["name"],"slug":g["slug"],"description":desc,"guide":g["method"],"collectionPath":"collections/"+g["file"]}
    for path,(target,note) in ALIASES.items():
        group=next((g for g in GROUPS if any(it[0]==target for it in g["items"])),None)
        context[path]={"section":"Archive shortcut","slug":group["slug"] if group else "books","description":note,"guide":"This is a legacy filename kept so saved links continue to work. Use the maintained destination linked on this page.","collectionPath":"collections/"+group["file"] if group else "collections/books-and-reading.html"}
    context["html/index.html"]={"section":"Source-document reading archive","slug":"books","description":"Browse the searchable HTML reading editions created from the repository's PDF and DOCX source documents. Each edition links back to its original file.","guide":"Search by title or category, open a reading edition, and use its contents or within-document search. The original PDF or DOCX remains available from the source link."}
    (ASSETS/"reading-room-context.js").write_text("window.READING_ROOM_CONTEXT = "+json.dumps(context,ensure_ascii=False)+";\n",encoding="utf-8")
    (ROOT/"index.html").write_text(make_home(),encoding="utf-8")
    for g in GROUPS:
        (COLLECTIONS/g["file"]).write_text(make_collection(g),encoding="utf-8")
    for path,(target,note) in ALIASES.items():
        alias_page(path,target,note)
    for path in [*ROOT.glob("*.html"),*HTML_DIR.glob("*.html")]:
        if path.name=="index.html" and path.parent==ROOT:
            continue
        inject_shared_assets(path)
    print("Built Reading Room:",len(GROUPS),"subject pages,",sum(len(g["items"]) for g in GROUPS),"curated resources,",len(ALIASES),"archive shortcuts.")
    print("Validated coverage of",len(actual),"existing HTML resource pages.")

if __name__=="__main__":
    main()
