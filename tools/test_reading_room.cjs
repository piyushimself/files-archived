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
  dom.window.eval(sharedJS);
  dom.window.document.dispatchEvent(new dom.window.Event("DOMContentLoaded", { bubbles: true }));
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
  for (const file of ["life-fiction-curriculum.html", "living-curriculum-2026.html"]) {
    const dom = await boot(file);
    const d = dom.window.document;
    assert.ok(d.querySelector(".rr-curriculum-tools"), file + " book finder missing");
    assert.ok(d.querySelectorAll(".rr-curriculum-tools select").length >= 2, file + " should filter available origin/period data");
    const input = d.querySelector(".rr-curriculum-tools input");
    setValue(input, "Gilgamesh");
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

(async () => {
  await testFilmCatalogue();
  await testOrderedFilmCatalogues();
  await testGenericReader();
  await testMangaGuide();
  await testPoliticalComics();
  await testCurricula();
  await testLearningAndArt();
  console.log("PASS: 8 Reading Room runtime smoke-test groups.");
})().catch(error => {
  console.error(error);
  process.exitCode = 1;
});
