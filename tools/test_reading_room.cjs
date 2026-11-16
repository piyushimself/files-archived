#!/usr/bin/env node
"use strict";
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const { JSDOM } = require("jsdom");

const ROOT = path.resolve(__dirname, "..");
const sharedJS = fs.readFileSync(path.join(ROOT, "assets/reading-room.js"), "utf8");

async function boot(relativePath) {
  const file = path.join(ROOT, relativePath);
  assert.ok(fs.existsSync(file), "Missing test page: " + relativePath);
  const html = fs.readFileSync(file, "utf8");
  const dom = new JSDOM(html, {
    url: "https://piyushimself.github.io/files/" + relativePath,
    runScripts: "outside-only",
    pretendToBeVisual: true
  });
  dom.window.READING_ROOM_CONTEXT = {};
  dom.window.__rrErrors = [];
  dom.window.addEventListener("error", event => dom.window.__rrErrors.push(String(event.error || event.message)));
  const ready = dom.window.document.readyState === "loading"
    ? new Promise(resolve => dom.window.document.addEventListener("DOMContentLoaded", resolve, { once: true }))
    : Promise.resolve();
  dom.window.eval(sharedJS);
  await ready;
  await new Promise(resolve => setTimeout(resolve, 0));
  return dom;
}
function visibleCount(selector, doc) {
  return [...doc.querySelectorAll(selector)].filter(el => !el.hidden && el.style.display !== "none").length;
}
function setValue(element, value, eventType = "input") {
  element.value = value;
  element.dispatchEvent(new element.ownerDocument.defaultView.Event(eventType, { bubbles: true }));
}
async function testFilmCatalogue() {
  const dom = await boot("html/300_Films_Filmography.html");
  const d = dom.window.document;
  const cards = d.querySelectorAll(".rr-film-card");
  if (!d.querySelector(".rr-film-country")) console.error("FILM DEBUG", { ready: d.readyState, body: d.body.className, data: d.body.dataset, toolbar: !!d.querySelector(".rr-reader-tools"), search: !!d.querySelector("#search"), headings: d.querySelectorAll("#content h2,#content h3").length, errors: dom.window.__rrErrors });
  assert.ok(cards.length >= 30, "300 Films Filmography should render individual film cards; got " + cards.length);
  for (const selector of [".rr-film-country", ".rr-film-director", ".rr-film-year", ".rr-film-category"]) {
    assert.ok(d.querySelector(selector), "Missing film filter " + selector);
  }
  assert.ok([...cards].some(card => card.dataset.country && card.dataset.year), "Film cards should preserve source country/year metadata");
  const search = d.querySelector("#rr-film-search");
  setValue(search, "Ordet");
  assert.ok(visibleCount(".rr-film-card", d) >= 1, "Film search should return Ordet");
  assert.ok(visibleCount(".rr-film-card", d) < cards.length, "Film search should narrow results");
  dom.window.close();
}
async function testOrderedFilmCatalogues() {
  for (const file of ["html/100_essential_films.html", "html/200_Films_Like_Frida.html"]) {
    const dom = await boot(file);
    const d = dom.window.document;
    const count = d.querySelectorAll(".rr-film-card").length;
    assert.ok(count >= 15, file + " should turn numbered list entries into film cards; got " + count);
    assert.ok(d.querySelector(".rr-film-country") && d.querySelector(".rr-film-year"), file + " should expose available country/year filters");
    dom.window.close();
  }
}
async function testGenericReader() {
  const dom = await boot("html/1000_Writing_Prompts.html");
  const d = dom.window.document;
  assert.ok(d.querySelectorAll(".rr-reading-section").length >= 10, "Writing prompts should be grouped into navigable sections");
  assert.ok(d.querySelector(".rr-reader-page-filter") && d.querySelector(".rr-reader-section-filter"), "Generic reader needs page and section filters");
  dom.window.close();
}
async function testMangaGuide() {
  const dom = await boot("manga-guide.html");
  const d = dom.window.document;
  assert.ok(d.querySelector(".rr-manga-guide-tools"), "Manga guide toolbar missing");
  const input = d.querySelector(".rr-manga-guide-tools input");
  setValue(input, "Yotsuba");
  assert.equal(visibleCount(".manga-card", d), 1, "Manga guide search should isolate Yotsuba&!");
  assert.match(d.querySelector(".rr-catalogue-count").textContent, /1 of 50 manga/);
  dom.window.close();
}
async function testPoliticalComics() {
  const dom = await boot("political-comics-list.html");
  const d = dom.window.document;
  assert.ok(d.querySelector(".rr-political-tools"), "Political comics search/filter toolbar missing");
  const input = d.querySelector(".rr-political-tools input");
  setValue(input, "Maus");
  assert.ok(d.querySelector(".rr-catalogue-count").textContent.includes("items in"), "Political comics should show a result count");
  assert.ok(visibleCount(".tab-panel.active .card", d) >= 1, "Political comics search should retain Maus in the active collection");
  dom.window.close();
}
async function testCurricula() {
  for (const [file, term] of [["life-fiction-curriculum.html", "Panchatantra"], ["living-curriculum-2026.html", "Gilgamesh"]]) {
    const dom = await boot(file);
    const d = dom.window.document;
    assert.ok(d.querySelector(".rr-curriculum-tools"), file + " book finder missing");
    assert.ok(d.querySelectorAll(".rr-curriculum-tools select").length >= 2, file + " should filter available origin/period data");
    const input = d.querySelector(".rr-curriculum-tools input");
    setValue(input, term);
    assert.ok(visibleCount(".book-card,.books-list > .book", d) >= 1, file + " search should find available book records");
    dom.window.close();
  }
}
async function testLearningAndArt() {
  {
    const dom = await boot("anime-manga-values-curriculum.html");
    const d = dom.window.document;
    assert.ok(d.querySelector(".rr-curriculum-tools"), "Anime/manga values curriculum search missing");
    setValue(d.querySelector(".rr-curriculum-tools input"), "A Silent Voice");
    assert.ok(visibleCount(".cards-grid .card", d) >= 2, "Curriculum search should find both anime and manga entries");
    dom.window.close();
  }
  {
    const dom = await boot("human-development-curriculum.html");
    const d = dom.window.document;
    assert.ok(d.querySelector(".rr-learning-toolbar"), "Human development curriculum controls missing");
    assert.ok(d.querySelector(".rr-learning-toolbar input"), "Human development search missing");
    dom.window.close();
  }
  {
    const dom = await boot("free-art-resources.html");
    const d = dom.window.document;
    assert.ok(d.querySelector(".rr-art-search input"), "Art resource search missing");
    setValue(d.querySelector(".rr-art-search input"), "watercolor");
    assert.ok(d.querySelector(".rr-art-count").textContent.includes("resources"), "Art resource results count missing");
    dom.window.close();
  }
}


async function testPoetryReader(){
  const dom=await boot("html/Aag_Ki_Kavitayen.html");
  const d=dom.window.document;
  const poems=d.querySelectorAll(".poem-card");
  assert.ok(d.body.classList.contains("rr--poetry"),"Aag Ki Kavitayen should use a poetry-specific page type");
  assert.ok(poems.length>=80,"Poetry renderer should preserve the poem collection; got "+poems.length);
  assert.ok(d.querySelector(".poetry-line"),"Poem verse should be represented as individual lines");
  assert.ok(d.querySelectorAll(".poetry-stanza").length < d.querySelectorAll(".poetry-line").length / 2,"Blank line spacing must not turn every verse line into a separate stanza");
  assert.ok(d.querySelector(".poet-byline"),"Poet attribution should be retained when present");
  assert.ok(d.querySelector(".rr-poetry-poet-filter")&&d.querySelector(".rr-poetry-volume-filter"),"Poetry filters missing");
  assert.ok(d.body.textContent.includes("Sabse Khatarnak"),"First poem title missing");
  assert.ok(d.body.textContent.includes("Zinda Rehna"),"Second poem title missing");
  assert.ok(!d.body.textContent.includes("\\n"),"Literal backslash-n must not appear in rendered poetry text");
  setValue(d.querySelector("#search"),"Sabse Khatarnak");
  assert.equal(visibleCount(".poem-card",d),1,"Poetry search should isolate the selected poem");
  dom.window.close();
}
async function testVisibleEscapes(){
  const dom=await boot("The_Curators_Library.html");
  const d=dom.window.document;
  const walker=d.createTreeWalker(d.body,dom.window.NodeFilter.SHOW_TEXT);
  const forbidden=[];
  while(walker.nextNode()){
    const parent=walker.currentNode.parentElement;
    if(parent&&parent.closest("script,style,pre,code,textarea"))continue;
    if(/\\[nrt]/.test(walker.currentNode.nodeValue||""))forbidden.push(walker.currentNode.nodeValue);
  }
  assert.deepEqual(forbidden,[],"Visible escaped control sequences remain in The Curator's Library");
  dom.window.close();
}


async function testCompleteFilmCollection(){
  const file=path.join(ROOT,"film_collection_v8.html");
  const raw=fs.readFileSync(file,"utf8");
  const dom=new JSDOM(raw,{
    url:"https://piyushimself.github.io/files/film_collection_v8.html",
    runScripts:"dangerously",
    pretendToBeVisual:true,
    beforeParse(window){
      window.scrollTo=()=>{};
      window.HTMLElement.prototype.scrollIntoView=function(){};
      window.IntersectionObserver=class{constructor(callback){this.callback=callback;}observe(){}unobserve(){}disconnect(){}takeRecords(){return[];}};
    }
  });
  await new Promise(resolve=>setTimeout(resolve,0));
  const d=dom.window.document;
  assert.ok(d.body.classList.contains("rr-cinema-app"),"Film collection must use its isolated design scope");
  assert.ok(raw.includes("reading-room.css?v=16"),"Film collection must request the current shared stylesheet");
  assert.ok(d.querySelectorAll(".mc").length>=20,"Film catalogue should render its records");
  assert.ok(d.querySelector("#searchInput")&&d.querySelector("#countrySel")&&d.querySelector("#genreSel"),"Core catalogue filters must remain available");
  assert.ok(d.querySelector("#progressWrap")&&d.querySelector("#wfWatched")&&d.querySelector("#importFile"),"Watch tracking controls must remain available");
  const grid=d.querySelector("#grid");
  assert.ok(grid.querySelector(".tier-sep"),"Rating tier separators should be present");
  const original=d.querySelectorAll(".mc").length;
  const search=d.querySelector("#searchInput");
  setValue(search,"The Godfather");
  const matching=[...d.querySelectorAll(".mc")].filter(card=>!card.hidden);
  assert.ok(matching.length>=1&&matching.length<original,"Instant film search should narrow the visible results");
  assert.ok(matching.some(card=>card.textContent.includes("The Godfather")),"Search should keep the expected title visible");
  setValue(d.querySelector("#countrySel"),"USA","change");
  assert.ok([...d.querySelectorAll(".mc")].filter(card=>!card.hidden).length>=1,"Country filtering should continue to work");
  dom.window.close();

  const css=fs.readFileSync(path.join(ROOT,"assets/reading-room.css"),"utf8");
  assert.match(css,/body\.rr-page\s*\{[^}]*--text:var\(--rr-ink\)/s,"Theme compatibility variables must resolve on the page body");
  assert.match(css,/body\.rr-page\.rr-cinema-app \.tier-sep\s*\{[^}]*grid-column:1\s*\/\s*-1/s,"Tier headings must span the whole film grid");
  assert.match(css,/body\.rr-page\.rr-cinema-app \.mc-title\s*\{[^}]*color:var\(--rr-ink\)!important/s,"Film title contrast must follow the selected theme");
}

(async () => {
  await testFilmCatalogue();
  await testOrderedFilmCatalogues();
  await testGenericReader();
  await testMangaGuide();
  await testPoliticalComics();
  await testCurricula();
  await testLearningAndArt();
  await testCompleteFilmCollection();
  await testVisibleEscapes();
  await testPoetryReader();
  console.log("PASS: 8 Reading Room runtime smoke-test groups.");
})().catch(error => {
  console.error(error);
  process.exitCode = 1;
});
