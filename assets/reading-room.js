(function(){
"use strict";
const NAV=[
  ["cinema","Cinema","collections/cinema.html"],
  ["anime-manga","Manga & comics","collections/anime-and-manga.html"],
  ["art","Art","collections/art-and-making.html"],
  ["books","Books","collections/books-and-reading.html"],
  ["ideas","Ideas","collections/ideas-and-reflection.html"],
  ["writing","Writing","collections/poetry-and-writing.html"],
  ["family","Family","collections/children-and-family.html"],
  ["work","Work & tools","collections/work-and-tools.html"]
];
function siteKey(){
  const path=decodeURIComponent(location.pathname);
  const parts=path.split("/").filter(Boolean);
  const at=parts.indexOf("files");
  return at>=0?parts.slice(at+1).join("/"):(parts.slice(-2).join("/")||"index.html");
}
function basePrefix(key){return key.startsWith("html/")||key.startsWith("collections/")?"../":"";}
function buildNav(key,meta){
  if(document.querySelector(".rr-site-header"))return;
  document.querySelectorAll(".rr-contextbar").forEach(n=>n.remove());
  const prefix=basePrefix(key);
  const header=document.createElement("header");
  header.className="rr-site-header";
  const active=meta&&meta.slug;
  const links=NAV.map(([slug,label,path])=>'<a href="'+prefix+path+'"'+(active===slug?' aria-current="page"':'')+'>'+label+'</a>').join("");
  header.innerHTML='<a class="rr-brand" href="'+prefix+'index.html"><span class="rr-brand-mark">R</span>THE READING ROOM</a><nav class="rr-navlinks" aria-label="Main collections">'+links+'</nav><div class="rr-header-actions"><button type="button" class="rr-theme-toggle" aria-label="Switch colour theme" title="Switch colour theme">◐</button><button type="button" class="rr-menu-toggle" aria-expanded="false" aria-label="Open navigation">Menu</button></div>';
  document.body.insertBefore(header,document.body.firstChild);
  const menu=header.querySelector(".rr-menu-toggle"),nav=header.querySelector(".rr-navlinks");
  menu.addEventListener("click",function(){const open=nav.classList.toggle("is-open");menu.setAttribute("aria-expanded",String(open));menu.textContent=open?"Close":"Menu";});
  const theme=header.querySelector(".rr-theme-toggle");
  theme.addEventListener("click",function(){const next=document.documentElement.dataset.theme==="dark"?"light":"dark";document.documentElement.dataset.theme=next;try{localStorage.setItem("rr-theme",next);}catch(e){};theme.title=next==="dark"?"Switch to light theme":"Switch to dark theme";});
}
function setupTheme(){
  let pref=null;try{pref=localStorage.getItem("rr-theme");}catch(e){}
  if(pref==="light"||pref==="dark")document.documentElement.dataset.theme=pref;
}
function addContext(key,meta){
  if(!meta||document.body.classList.contains("rr-home")||document.body.classList.contains("rr-hub"))return;
  if(document.querySelector(".rr-page-context"))return;
  const box=document.createElement("section");box.className="rr-page-context";
  const category=meta.section||"The Reading Room";
  const desc=meta.description||"A curated page in the Reading Room collection.";
  const guide=meta.guide||"Use the page search and filters to narrow the collection. Start with one section, then follow links that interest you.";
  const link=meta.collectionPath?'<a class="rr-context-link" href="'+basePrefix(key)+meta.collectionPath+'">Explore this collection ↗</a>':"";
  box.innerHTML='<div class="rr-context-kicker">'+category+'</div><p class="rr-context-deck">'+desc+link+'</p><details class="rr-context-guide"><summary>How to use this page</summary><p>'+guide+'</p></details>';
  const header=document.querySelector(".rr-site-header");
  const first=header&&header.nextElementSibling;
  if(first)document.body.insertBefore(box,first);else document.body.appendChild(box);
}
function initHubFilters(){
  document.querySelectorAll(".rr-collection-page").forEach(page=>{
    const input=page.querySelector(".rr-hub-search"),select=page.querySelector(".rr-hub-kind"),cards=[...page.querySelectorAll(".rr-resource-card")],count=page.querySelector(".rr-results-count"),empty=page.querySelector(".rr-no-results");
    if(!input||!select)return;
    function update(){const q=input.value.trim().toLowerCase(),kind=select.value;let n=0;cards.forEach(card=>{const ok=(!q||card.dataset.search.includes(q))&&(kind==="all"||card.dataset.kind===kind);card.hidden=!ok;if(ok)n++;});if(count)count.textContent=n+" of "+cards.length+" resources";if(empty)empty.style.display=n?"none":"block";}
    input.addEventListener("input",update);select.addEventListener("change",update);update();
  });
}
function start(){
  setupTheme();
  const key=siteKey(),manifest=window.READING_ROOM_CONTEXT||{},meta=manifest[key]||null;
  buildNav(key,meta);
  addContext(key,meta);
  initHubFilters();
}
if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",start);else start();
})();