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
function wireHeader(header){
  const menu=header.querySelector(".rr-menu-toggle");
  const nav=header.querySelector(".rr-navlinks");
  if(menu&&nav&&menu.dataset.rrWired!=="1"){
    menu.dataset.rrWired="1";
    menu.addEventListener("click",function(){
      const open=nav.classList.toggle("is-open");
      menu.setAttribute("aria-expanded",String(open));
      menu.textContent=open?"Close":"Menu";
    });
  }
  const theme=header.querySelector(".rr-theme-toggle");
  if(theme&&theme.dataset.rrWired!=="1"){
    theme.dataset.rrWired="1";
    theme.addEventListener("click",function(){
      const next=document.documentElement.dataset.theme==="dark"?"light":"dark";
      document.documentElement.dataset.theme=next;
      try{localStorage.setItem("rr-theme",next);}catch(e){}
      theme.title=next==="dark"?"Switch to light theme":"Switch to dark theme";
    });
  }
}
function buildNav(key,meta){
  const existing=document.querySelector(".rr-site-header");
  if(existing){wireHeader(existing);return;}
  document.querySelectorAll(".rr-contextbar").forEach(n=>n.remove());
  const prefix=basePrefix(key);
  const header=document.createElement("header");
  header.className="rr-site-header";
  const active=meta&&meta.slug;
  const links=NAV.map(([slug,label,path])=>'<a href="'+prefix+path+'"'+(active===slug?' aria-current="page"':'')+'>'+label+'</a>').join("");
  header.innerHTML='<a class="rr-brand" href="'+prefix+'index.html"><span class="rr-brand-mark">R</span>THE READING ROOM</a><nav class="rr-navlinks" aria-label="Main collections">'+links+'</nav><div class="rr-header-actions"><button type="button" class="rr-theme-toggle" aria-label="Switch colour theme" title="Switch colour theme">◐</button><button type="button" class="rr-menu-toggle" aria-expanded="false" aria-label="Open navigation">Menu</button></div>';
  document.body.insertBefore(header,document.body.firstChild);
  wireHeader(header);
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

function addSelect(host, className, label, values){
  const select=document.createElement("select");
  select.className=className;
  select.setAttribute("aria-label",label);
  const all=document.createElement("option");all.value="all";all.textContent="All "+label.toLowerCase();select.appendChild(all);
  [...values].filter(Boolean).sort((a,b)=>a.localeCompare(b)).forEach(value=>{
    const option=document.createElement("option");option.value=value;option.textContent=value;select.appendChild(option);
  });
  host.appendChild(select);return select;
}
function readerToolbar(body){
  const tools=body.querySelector(".rr-reader-tools");
  if(!tools)return null;
  tools.querySelectorAll(".rr-reader-filter,.rr-reader-results,.rr-reader-clear").forEach(node=>node.remove());
  const input=tools.querySelector('input[type="search"],#search');
  if(!input)return null;
  input.placeholder="Search titles, people, places or ideas…";
  const result=document.createElement("span");result.className="rr-reader-results";result.setAttribute("aria-live","polite");
  const clear=document.createElement("button");clear.type="button";clear.className="rr-reader-clear";clear.textContent="Clear";
  clear.addEventListener("click",()=>{input.value="";tools.querySelectorAll("select").forEach(s=>s.value="all");input.dispatchEvent(new Event("input",{bubbles:true}));});
  tools.appendChild(result);tools.appendChild(clear);
  return {tools,input,result,clear};
}
function parseFilmMeta(value){
  const text=(value||"").trim();
  const match=text.match(/^(.+?)\s*[·•]\s*([^·•]+?)\s*[·•]\s*((?:18|19|20)\d{2})(?:\s+(.*))?$/);
  if(!match)return null;
  return {director:match[1].trim(),country:match[2].trim(),year:match[3],tail:(match[4]||"").trim()};
}
function quoteFromText(text){
  const match=(text||"").match(/["“]([^"”]+)["”]/);
  return match?match[1].trim():"";
}
function isFilmCategory(text){
  const value=(text||"").replace(/[■▪◆]+/g,"").trim();
  const alpha=value.replace(/[^A-Za-z]/g,"");
  if(value.length<4||value.length>68||alpha.length<4)return false;
  if(/title|tagline|director|country|year|filmography|300 films/i.test(value))return false;
  return alpha===alpha.toUpperCase() && value.split(/\s+/).length<=9;
}
function splitFilmParagraph(text){
  const value=(text||"").replace(/\s+/g," ").trim();
  if(!value)return [];
  return value.split(/(?<=["”'])\s+(?=\d{1,3}[.)]?\s+[A-ZÀ-ÖØ-Þ])/u).map(v=>v.trim()).filter(Boolean);
}
function buildFilmCatalogue(body,content,toolbar){
  const records=[],intro=[],groups=[];
  let category="Filmography",current=null;
  const startRecord=(number,title,page,id)=>{
    current={number:number||"",title:(title||"").trim(),director:"",country:"",year:"",tagline:"",notes:[],category:category,page:page+1,anchor:id||"",metaAnchors:[]};
    if(!current.title)current.title="Untitled film entry";
    records.push(current);return current;
  };
  const addNote=(value)=>{
    const text=(value||"").replace(/\s+/g," ").trim();
    if(!text)return;
    if(!current){intro.push(text);return;}
    const meta=parseFilmMeta(text);
    if(meta){current.director=meta.director;current.country=meta.country;current.year=meta.year;if(meta.tail){const q=quoteFromText(meta.tail);if(q)current.tagline=current.tagline?current.tagline+" "+q:q;const residue=meta.tail.replace(/["“][\s\S]*?["”]/,"").trim();if(residue)current.notes.push(residue);}return;}
    const quote=quoteFromText(text);
    if(quote){current.tagline= current.tagline ? current.tagline+" "+quote : quote;return;}
    if(text.length>1)current.notes.push(text);
  };
  content.querySelectorAll(":scope > .page").forEach((page,pageIndex)=>{
    [...page.children].forEach(node=>{
      if(node.classList.contains("page-label"))return;
      const text=(node.textContent||"").replace(/\s+/g," ").trim();
      if(!text)return;
      if(/^H[1-3]$/.test(node.tagName)){
        const numbered=text.match(/^(\d{1,3})[.)]?\s+(.+)$/);
        if(numbered){
          startRecord(numbered[1],numbered[2],pageIndex,node.id);
          return;
        }
        const meta=parseFilmMeta(text);
        if(meta){
          if(!current)current=startRecord("", "Film entry",pageIndex,"");
          current.director=meta.director;current.country=meta.country;current.year=meta.year;
          if(node.id)current.metaAnchors.push(node.id);
          return;
        }
        if(isFilmCategory(text)){
          category=text.replace(/[■▪◆]+/g,"").trim();
          groups.push({title:category,anchor:node.id||""});
          return;
        }
        if(/^(?:300 FILMS|A?GLOBAL FILMOGRAPHY|TITLE.*TAGLINE.*DIRECTOR)/i.test(text)){
          if(node.id)intro.push("##ANCHOR##"+node.id);
          return;
        }
        if(current){if(node.id)current.metaAnchors.push(node.id);addNote(text);}else {if(node.id)intro.push("##ANCHOR##"+node.id);intro.push(text);}
        return;
      }
      if(node.tagName==="UL"||node.tagName==="OL"){
        [...node.children].forEach(li=>{
          const label=(li.textContent||"").replace(/\s+/g," ").trim();
          if(isFilmCategory(label)){category=label.replace(/[■▪◆]+/g,"").trim();groups.push({title:category,anchor:li.id||""});}
          else addNote(label);
        });
        return;
      }
      if(node.tagName==="P"||node.tagName==="BLOCKQUOTE"||node.tagName==="LI"){
        const parts=splitFilmParagraph(text);
        parts.forEach(part=>{
          const numbered=part.match(/^(\d{1,3})[.)]?\s+([\s\S]+)$/);
          if(numbered){
            const bodyText=numbered[2].trim();
            const quoteIndex=bodyText.search(/["“]/);
            const visibleTitle=quoteIndex>=0?bodyText.slice(0,quoteIndex).trim():bodyText;
            startRecord(numbered[1],visibleTitle,pageIndex,"");
            const q=quoteFromText(bodyText);if(q)current.tagline=q;
            const meta=parseFilmMeta(bodyText);
            if(meta){current.director=meta.director;current.country=meta.country;current.year=meta.year;if(meta.tail){const q2=quoteFromText(meta.tail);if(q2)current.tagline=q2;}}
            else {const inline=bodyText.match(/^([\\s\\S]+?)\\s*[·•]\\s*([^·•]+?)\\s*[·•]\\s*((?:18|19|20)\\d{2})(?:\\s+(.*))?$/);if(inline){current.country=inline[2].trim();current.year=inline[3];const q2=quoteFromText(inline[4]||"");if(q2)current.tagline=q2;}}
            if(quoteIndex>=0){
              const tail=bodyText.slice(quoteIndex).replace(/["“][\s\S]*?["”]/,"").trim();
              if(tail)addNote(tail);
            }
          }else addNote(part);
        });
        return;
      }
      if(current)addNote(text);else intro.push(text);
    });
  });
  if(records.length<12)return false;
  const groupsByName=new Map();
  records.forEach(record=>{
    const key=record.category||"Filmography";
    if(!groupsByName.has(key))groupsByName.set(key,[]);
    groupsByName.get(key).push(record);
  });
  const countryValues=new Set(records.map(r=>r.country));
  const directorValues=new Set(records.map(r=>r.director));
  const yearValues=new Set(records.map(r=>r.year));
  const categoryValues=new Set(records.map(r=>r.category));
  const filterHost=toolbar.tools;
  const categorySelect=addSelect(filterHost,"rr-reader-filter rr-film-category","category",categoryValues);
  const countrySelect=addSelect(filterHost,"rr-reader-filter rr-film-country","country",countryValues);
  const directorSelect=addSelect(filterHost,"rr-reader-filter rr-film-director","director",directorValues);
  const yearSelect=addSelect(filterHost,"rr-reader-filter rr-film-year","year",yearValues);
  const wrapper=document.createElement("div");wrapper.className="rr-filmography";
  if(intro.length){
    const introBox=document.createElement("section");introBox.className="rr-filmography-intro";
    const introTitle=document.createElement("h2");introTitle.textContent="About this selection";introBox.appendChild(introTitle);
    intro.filter(v=>v.startsWith("##ANCHOR##")).forEach(v=>{const a=document.createElement("span");a.id=v.slice(10);a.className="rr-film-anchor";introBox.appendChild(a);});
    const p=document.createElement("p");p.textContent=intro.filter(v=>!v.startsWith("##ANCHOR##")).join(" ");introBox.appendChild(p);wrapper.appendChild(introBox);
  }
  groupsByName.forEach((items,name)=>{
    const section=document.createElement("section");section.className="rr-film-group";section.dataset.category=name;
    const heading=document.createElement("h2");heading.className="rr-film-group-title";heading.textContent=name;groups.filter(g=>g.title===name&&g.anchor).forEach(g=>{const anchor=document.createElement("span");anchor.id=g.anchor;anchor.className="rr-film-anchor";heading.appendChild(anchor);});section.appendChild(heading);
    const grid=document.createElement("div");grid.className="rr-film-grid";
    items.forEach(record=>{
      const card=document.createElement("article");card.className="rr-film-card";
      card.dataset.category=record.category;card.dataset.country=record.country;card.dataset.director=record.director;card.dataset.year=record.year;
      if(record.anchor)card.id=record.anchor;
      record.metaAnchors.forEach(id=>{const anchor=document.createElement("span");anchor.id=id;anchor.className="rr-film-anchor";card.appendChild(anchor);});
      const top=document.createElement("div");top.className="rr-film-card-top";
      const index=document.createElement("span");index.className="rr-film-index";index.textContent=record.number?"FILM "+record.number:"FILM";top.appendChild(index);
      const source=document.createElement("span");source.className="rr-film-source";source.textContent="Source page "+record.page;top.appendChild(source);card.appendChild(top);
      const title=document.createElement("h3");title.className="rr-film-title";title.textContent=record.title;card.appendChild(title);
      const meta=document.createElement("dl");meta.className="rr-film-meta";
      [["Director",record.director],["Country",record.country],["Year",record.year]].forEach(pair=>{
        if(!pair[1])return;
        const wrap=document.createElement("div"),dt=document.createElement("dt"),dd=document.createElement("dd");
        dt.textContent=pair[0];dd.textContent=pair[1];wrap.appendChild(dt);wrap.appendChild(dd);meta.appendChild(wrap);
      });
      if(meta.children.length)card.appendChild(meta);
      if(record.tagline){const quote=document.createElement("p");quote.className="rr-film-tagline";quote.textContent="“"+record.tagline+"”";card.appendChild(quote);}
      if(record.notes.length){
        const notes=document.createElement("p");notes.className="rr-film-notes";notes.textContent=record.notes.join(" ");card.appendChild(notes);
      }
      card.dataset.search=[record.number,record.title,record.director,record.country,record.year,record.tagline,record.notes.join(" "),record.category].join(" ").toLocaleLowerCase();
      grid.appendChild(card);
    });
    section.appendChild(grid);wrapper.appendChild(section);
  });
  content.replaceChildren(wrapper);
  toolbar.input.id="rr-film-search";
  const count=records.length;
  const update=()=>{
    const query=toolbar.input.value.trim().toLocaleLowerCase();
    let visible=0;
    wrapper.querySelectorAll(".rr-film-card").forEach(card=>{
      const show=(!query||card.dataset.search.includes(query))&&
        (categorySelect.value==="all"||card.dataset.category===categorySelect.value)&&
        (countrySelect.value==="all"||card.dataset.country===countrySelect.value)&&
        (directorSelect.value==="all"||card.dataset.director===directorSelect.value)&&
        (yearSelect.value==="all"||card.dataset.year===yearSelect.value);
      card.hidden=!show;if(show)visible++;
    });
    wrapper.querySelectorAll(".rr-film-group").forEach(section=>{section.hidden=!section.querySelector(".rr-film-card:not([hidden])");});
    toolbar.result.textContent=visible+" of "+count+" film entries";
  };
  [toolbar.input,categorySelect,countrySelect,directorSelect,yearSelect].forEach(control=>control.addEventListener(control===toolbar.input?"input":"change",update));
  update();
  body.classList.add("rr-film-catalogue");
  return true;
}
function buildGenericReader(body,content,toolbar){
  const pages=[...content.querySelectorAll(":scope > .page")],groups=[];
  const pageSelect=addSelect(toolbar.tools,"rr-reader-filter rr-reader-page-filter","source page",pages.map((page,i)=>String(i)));
  [...pageSelect.options].slice(1).forEach((option,i)=>{const label=pages[i].querySelector(".page-label");option.textContent=label?label.textContent.trim():"Source page "+(i+1);});
  const sectionNames=new Set();
  pages.forEach((page,pageIndex)=>{
    const children=[...page.children],label=children.find(n=>n.classList.contains("page-label"));
    let section=null,sectionNo=0;
    const startSection=(title)=>{
      section=document.createElement("section");section.className="rr-reading-section";
      section.dataset.page=String(pageIndex);
      section.dataset.title=title;
      sectionNo++;
      const heading=document.createElement("div");heading.className="rr-reading-section-heading";
      const labelNode=document.createElement("span");labelNode.className="rr-reading-section-kicker";labelNode.textContent="SECTION "+sectionNo;
      heading.appendChild(labelNode);section.appendChild(heading);
      if(title)sectionNames.add(title);
      groups.push(section);page.appendChild(section);
      return section;
    };
    children.forEach(node=>{
      if(node===label)return;
      if(/^H[1-3]$/.test(node.tagName)){
        section=startSection((node.textContent||"").trim());
        section.appendChild(node);
      }else{
        if(!section)section=startSection("Opening notes");
        section.appendChild(node);
      }
    });
    page.dataset.rrPage=String(pageIndex);
  });
  groups.forEach(section=>{
    const heading=section.querySelector("h2,h3,h4");
    const head=section.querySelector(".rr-reading-section-heading");
    if(heading&&head)head.appendChild(heading);
    section.dataset.search=section.textContent.toLocaleLowerCase();
  });
  const sectionSelect=addSelect(toolbar.tools,"rr-reader-filter rr-reader-section-filter","section",sectionNames);
  const empty=document.createElement("div");empty.className="rr-reader-empty";empty.textContent="No matching sections. Try another search or clear the filters.";content.appendChild(empty);
  const update=()=>{
    const query=toolbar.input.value.trim().toLocaleLowerCase();
    let visible=0;
    groups.forEach(section=>{
      const pageMatch=pageSelect.value==="all"||pageSelect.value===section.dataset.page;
      const sectionMatch=sectionSelect.value==="all"||sectionSelect.value===section.dataset.title;
      const searchMatch=!query||section.dataset.search.includes(query);
      const show=pageMatch&&sectionMatch&&searchMatch;section.hidden=!show;if(show)visible++;
    });
    pages.forEach((page,index)=>{page.hidden=!groups.some(section=>section.dataset.page===String(index)&&!section.hidden);});
    empty.hidden=visible>0;
    toolbar.result.textContent=visible+" of "+groups.length+" sections";
  };
  toolbar.input.addEventListener("input",update);pageSelect.addEventListener("change",update);sectionSelect.addEventListener("change",update);update();
}
function parseFilmYearCountry(value){
  const match=(value||"").trim().match(/^((?:18|19|20)\d{2})\s*[·•]\s*(.+?)(?:\s+About:\s*([\s\S]*))?$/);
  return match?{year:match[1],country:match[2].trim(),tail:(match[3]||"").trim()}:null;
}
function parseFilmFullCredit(value){
  const match=(value||"").trim().match(/^(.+?)\s*[·•]\s*([^·•]+?)\s*[·•]\s*([^·•]+?)\s*[·•]\s*((?:18|19|20)\d{2})(?:\s+(.*))?$/);
  return match?{director:match[1].trim(),country:match[2].trim(),location:match[3].trim(),year:match[4],tail:(match[5]||"").trim()}:null;
}
function buildOrderedFilmCatalogue(body,content,toolbar){
  const listCount=content.querySelectorAll(":scope > .page ol li").length;
  if(listCount<12)return false;
  const records=[],intro=[],groupAnchors=[];
  let category="Filmography",current=null,serial=0;
  const newRecord=(title,page,id)=>{
    serial++;
    current={number:String(serial),title:(title||"").trim()||"Untitled film entry",director:"",country:"",location:"",year:"",tagline:"",notes:[],category:category,page:page+1,anchor:id||"",metaAnchors:[]};
    records.push(current);return current;
  };
  const addMeta=(meta)=>{
    if(!current)return false;
    if(meta.director)current.director=meta.director;
    if(meta.country)current.country=meta.country;
    if(meta.location)current.location=meta.location;
    if(meta.year)current.year=meta.year;
    if(meta.tail){const q=quoteFromText(meta.tail);if(q)current.tagline=q;const residue=meta.tail.replace(/["“][\s\S]*?["”]/,"").trim();if(residue)current.notes.push(residue);}
    return true;
  };
  const addText=(value)=>{
    const text=(value||"").replace(/\s+/g," ").trim();if(!text)return;
    if(!current){intro.push(text);return;}
    const full=parseFilmFullCredit(text);
    if(full){addMeta(full);return;}
    const meta=parseFilmMeta(text);
    if(meta){addMeta(meta);return;}
    const yearCountry=parseFilmYearCountry(text);
    if(yearCountry){
      current.year=yearCountry.year;current.country=yearCountry.country;
      if(yearCountry.tail)current.notes.push("About: "+yearCountry.tail);
      return;
    }
    const quote=quoteFromText(text);
    if(quote){current.tagline=current.tagline?current.tagline+" "+quote:quote;return;}
    current.notes.push(text);
  };
  const setCategory=(value,id)=>{
    const label=(value||"").replace(/[■▪◆]+/g,"").trim();
    if(!label)return;
    category=label;
    if(id)groupAnchors.push({title:label,anchor:id});
  };
  content.querySelectorAll(":scope > .page").forEach((page,pageIndex)=>{
    [...page.children].forEach(node=>{
      if(node.classList.contains("page-label"))return;
      const text=(node.textContent||"").replace(/\s+/g," ").trim();if(!text)return;
      if(/^H[1-3]$/.test(node.tagName)){
        if(isFilmCategory(text)){setCategory(text,node.id);return;}
        const full=parseFilmFullCredit(text);
        if(full){addMeta(full);if(node.id&&current)current.metaAnchors.push(node.id);return;}
        const meta=parseFilmMeta(text);
        if(meta){addMeta(meta);if(node.id&&current)current.metaAnchors.push(node.id);return;}
        const yearCountry=parseFilmYearCountry(text);
        if(yearCountry){addMeta(yearCountry);if(node.id&&current)current.metaAnchors.push(node.id);return;}
        if(node.id){if(current)current.metaAnchors.push(node.id);else intro.push("##ANCHOR##"+node.id);}
        if(current)addText(text);else intro.push(text);
        return;
      }
      if(node.tagName==="OL"){
        [...node.children].forEach(li=>{
          const title=(li.textContent||"").replace(/\s+/g," ").trim().replace(/^\d{1,3}[.)]?\s+/,"");
          if(title)newRecord(title,pageIndex,li.id||"");
        });
        return;
      }
      if(node.tagName==="UL"){
        [...node.children].forEach(li=>{
          const label=(li.textContent||"").replace(/\s+/g," ").trim();
          if(label && label.length<70 && !/[.!?]$/.test(label)){setCategory(label,li.id||"");}
          else addText(label);
        });
        return;
      }
      if(node.tagName==="P"||node.tagName==="BLOCKQUOTE"||node.tagName==="LI")addText(text);
      else addText(text);
    });
  });
  if(records.length<12)return false;
  const groupsByName=new Map();
  records.forEach(record=>{
    const key=record.category||"Filmography";
    if(!groupsByName.has(key))groupsByName.set(key,[]);
    groupsByName.get(key).push(record);
  });
  const values=(field)=>new Set(records.map(r=>r[field]).filter(Boolean));
  const categorySelect=addSelect(toolbar.tools,"rr-reader-filter rr-film-category","category",values("category"));
  const countrySelect=addSelect(toolbar.tools,"rr-reader-filter rr-film-country","country",values("country"));
  const directorSelect=values("director").size?addSelect(toolbar.tools,"rr-reader-filter rr-film-director","director",values("director")):null;
  const yearSelect=addSelect(toolbar.tools,"rr-reader-filter rr-film-year","year",values("year"));
  const wrapper=document.createElement("div");wrapper.className="rr-filmography rr-filmography-list";
  if(intro.length){
    const box=document.createElement("section");box.className="rr-filmography-intro";
    const heading=document.createElement("h2");heading.textContent="About this selection";box.appendChild(heading);
    intro.filter(v=>v.startsWith("##ANCHOR##")).forEach(v=>{const a=document.createElement("span");a.id=v.slice(10);a.className="rr-film-anchor";box.appendChild(a);});
    const p=document.createElement("p");p.textContent=intro.filter(v=>!v.startsWith("##ANCHOR##")).join(" ");box.appendChild(p);wrapper.appendChild(box);
  }
  groupsByName.forEach((items,name)=>{
    const section=document.createElement("section");section.className="rr-film-group";section.dataset.category=name;
    const heading=document.createElement("h2");heading.className="rr-film-group-title";heading.textContent=name;
    groupAnchors.filter(g=>g.title===name).forEach(g=>{const a=document.createElement("span");a.id=g.anchor;a.className="rr-film-anchor";heading.appendChild(a);});
    section.appendChild(heading);
    const grid=document.createElement("div");grid.className="rr-film-grid";
    items.forEach(record=>{
      const card=document.createElement("article");card.className="rr-film-card";
      card.dataset.category=record.category;card.dataset.country=record.country;card.dataset.director=record.director;card.dataset.year=record.year;
      if(record.anchor)card.id=record.anchor;
      record.metaAnchors.forEach(id=>{const a=document.createElement("span");a.id=id;a.className="rr-film-anchor";card.appendChild(a);});
      const top=document.createElement("div");top.className="rr-film-card-top";
      const n=document.createElement("span");n.className="rr-film-index";n.textContent="FILM "+record.number;top.appendChild(n);
      const source=document.createElement("span");source.className="rr-film-source";source.textContent="Source page "+record.page;top.appendChild(source);card.appendChild(top);
      const title=document.createElement("h3");title.className="rr-film-title";title.textContent=record.title;card.appendChild(title);
      const meta=document.createElement("dl");meta.className="rr-film-meta";
      [["Director",record.director],["Country",record.country],["Year",record.year],["Setting",record.location]].forEach(pair=>{
        if(!pair[1])return;
        const wrap=document.createElement("div"),dt=document.createElement("dt"),dd=document.createElement("dd");
        dt.textContent=pair[0];dd.textContent=pair[1];wrap.appendChild(dt);wrap.appendChild(dd);meta.appendChild(wrap);
      });
      if(meta.children.length)card.appendChild(meta);
      if(record.tagline){const q=document.createElement("p");q.className="rr-film-tagline";q.textContent="“"+record.tagline+"”";card.appendChild(q);}
      if(record.notes.length){const p=document.createElement("p");p.className="rr-film-notes";p.textContent=record.notes.join(" ");card.appendChild(p);}
      card.dataset.search=[record.title,record.director,record.country,record.year,record.location,record.tagline,record.notes.join(" "),record.category].join(" ").toLocaleLowerCase();
      grid.appendChild(card);
    });
    section.appendChild(grid);wrapper.appendChild(section);
  });
  content.replaceChildren(wrapper);
  const update=()=>{
    const q=toolbar.input.value.trim().toLocaleLowerCase();let visible=0;
    wrapper.querySelectorAll(".rr-film-card").forEach(card=>{
      const show=(!q||card.dataset.search.includes(q))&&
        (categorySelect.value==="all"||card.dataset.category===categorySelect.value)&&
        (countrySelect.value==="all"||card.dataset.country===countrySelect.value)&&
        (!directorSelect||directorSelect.value==="all"||card.dataset.director===directorSelect.value)&&
        (yearSelect.value==="all"||card.dataset.year===yearSelect.value);
      card.hidden=!show;if(show)visible++;
    });
    wrapper.querySelectorAll(".rr-film-group").forEach(section=>{section.hidden=!section.querySelector(".rr-film-card:not([hidden])");});
    toolbar.result.textContent=visible+" of "+records.length+" films";
  };
  [toolbar.input,categorySelect,countrySelect,yearSelect].concat(directorSelect?[directorSelect]:[]).forEach(control=>control.addEventListener(control===toolbar.input?"input":"change",update));
  update();body.classList.add("rr-film-catalogue");return true;
}

function buildPoetryReader(body,content,toolbar){
  const poems=[...content.querySelectorAll(".poem-card")];
  if(poems.length<10){buildGenericReader(body,content,toolbar);return;}
  const poets=new Set(poems.map(card=>card.dataset.poet||"").filter(Boolean));
  const volumes=new Set(poems.map(card=>card.dataset.volume||"").filter(Boolean));
  const poetSelect=addSelect(toolbar.tools,"rr-reader-filter rr-poetry-poet-filter","poet",poets);
  const volumeSelect=addSelect(toolbar.tools,"rr-reader-filter rr-poetry-volume-filter","collection section",volumes);
  const empty=document.createElement("div");empty.className="rr-reader-empty";empty.textContent="No poems match these filters.";content.appendChild(empty);
  const update=()=>{
    const query=toolbar.input.value.trim().toLocaleLowerCase();let visible=0;
    poems.forEach(card=>{
      const show=(!query||(card.dataset.search||card.textContent).toLocaleLowerCase().includes(query))&&
        (poetSelect.value==="all"||(card.dataset.poet||"")===poetSelect.value)&&
        (volumeSelect.value==="all"||(card.dataset.volume||"")===volumeSelect.value);
      card.hidden=!show;if(show)visible++;
    });
    content.querySelectorAll(".poetry-volume-group").forEach(group=>{
      group.hidden=!group.querySelector(".poem-card:not([hidden])");
    });
    empty.hidden=visible>0;
    toolbar.result.textContent=visible+" of "+poems.length+" poems";
  };
  [toolbar.input,poetSelect,volumeSelect].forEach(control=>control.addEventListener(control===toolbar.input?"input":"change",update));
  update();
  body.classList.add("rr-poetry-enhanced");
}


function cinemaText(value){return (value||"").replace(/[■▪◆]+/g," ").replace(/\s+/g," ").trim();}
function cinemaGroupHeading(kind,value){
  const t=cinemaText(value),u=t.toUpperCase();
  if(!t)return false;
  if(kind==="cinema-900"){
    if(/^LIST\s+[123]\s*[—-]/i.test(t))return true;
    if(/^(?:CINEMA CURATED FILMS|TABLE OF CONTENTS|LIST [123]|100 WORLD CINEMA MASTERPIECES|100 SENSUAL & MOOD CINEMA)$/i.test(t))return false;
    return t.length<=42&&u===t&&/^[A-Z0-9 /&'’().—-]+$/.test(t);
  }
  if(kind==="movie-encyclopedia"||kind==="movie-ratings-647"){
    return /^(?:100 ESSENTIAL FILMS|EROTIC ART CINEMA|ANIME MOVIES|MASTERS:\s*.+|SESSION STATISTICS)$/i.test(t);
  }
  if(kind==="movie-ratings"){
    return /^(?:100 ESSENTIAL FILMS|50 EROTIC ART FILMS|100 ANIME MOVIES|RANK FILM TITLE.*|SESSION STATISTICS)$/i.test(t);
  }
  return false;
}
function cinemaSplitCredit(value){
  const words=(value||"").trim().split(/\s+/).filter(Boolean);
  if(words.length<3)return {title:value||"",director:""};
  let n=2;
  const last3=words.slice(-3).join(" ");
  if(/^(?:Alejandro|Carl Theodor|Jean-Luc|Jean-Pierre|Abdellatif|Gillo|Mikhail|Mohsen|Lars von|Costa-Gavras|Fernando Meirelles|Bille August|Satyajit Ray|Sanjay Leela)\b/i.test(last3))n=3;
  if(/^(?:von|del|van|de|di)$/i.test(words[words.length-2]))n=3;
  if(words.length<=n)n=2;
  return {title:words.slice(0,-n).join(" "),director:words.slice(-n).join(" ")};
}
function cinemaParseEntry(segment,kind){
  const m=(segment||"").match(/^(\d{1,3})[.)]?\s+([\s\S]+)$/);
  if(!m)return null;
  const number=m[1],body=m[2].trim();
  const yearMatches=[...body.matchAll(/\b(?:18|19|20)\d{2}\b/g)];
  let ym=null;
  for(const candidate of yearMatches){
    const afterCandidate=body.slice(candidate.index+4);
    const scoreOk=kind==="movie-ratings"?/\d\.\d\/10\s+\d{1,3}%/.test(afterCandidate.slice(0,100)):(kind==="movie-encyclopedia"||kind==="movie-ratings-647")?/\d\.\d\s+\d{1,3}%/.test(afterCandidate.slice(0,100)):/\d\.\d/.test(afterCandidate.slice(0,65));
    if(scoreOk)ym=candidate;
  }
  if(!ym)ym=yearMatches[0];
  if(!ym)return null;
  const before=body.slice(0,ym.index).trim();
  const after=body.slice(ym.index+4).trim();
  if(!before)return null;
  const entry={number:number,title:before,director:"",year:ym[0],imdb:"",rt:"",genre:"",source:"",details:"",raw:body};
  if(kind!=="cinema-900"){
    const credit=cinemaSplitCredit(before);
    if(credit.title){entry.title=credit.title;entry.director=credit.director;}
  }
  if(kind==="cinema-900"){
    const score=after.match(/^(\d\.\d)\s+([\s\S]*)$/);
    let rest=after;
    if(score){entry.imdb=score[1];rest=score[2];}
    const mark=rest.search(/[■▪◆]{1,3}/);
    if(mark>=0){
      entry.director=rest.slice(0,mark).trim();
      rest=rest.slice(mark).replace(/^[■▪◆]+/,"").trim();
    }
    entry.details=rest;
  }else if(kind==="movie-ratings"){
    const score=after.match(/^(.*?)\s+(\d\.\d)\/10\s+(\d{1,3})%\s*([\s\S]*)$/);
    if(score){entry.genre=score[1].trim();entry.imdb=score[2];entry.rt=score[3];entry.details=score[4].trim();}
    else entry.details=after;
  }else{
    const score=after.match(/^(\d\.\d)\s+(\d{1,3})%\s+([\s\S]*)$/);
    if(score){
      entry.imdb=score[1];entry.rt=score[2];entry.details=score[3].trim();
      const source=entry.details.match(/^(Essential|Anime|Erotic|Masters?)(?:\s|$)/i);
      if(source)entry.source=source[0].trim();
    }else entry.details=after;
  }
  return entry;
}
function cinemaSplitNumberedText(value,kind,state){
  const text=(value||"").replace(/\s+/g," ").trim();
  if(!text)return {entries:[],prefix:""};
  const max=kind==="cinema-900"?300:(kind==="movie-ratings"?300:647);
  const pattern=/(?:^|\s)(\d{1,3})[.)]?\s+(?=[A-Z0-9À-ÖØ-Þ])/g;
  const accepted=[];
  let match;
  while((match=pattern.exec(text))!==null){
    const pos=match.index+(match[0].charAt(0)===" "?1:0);
    const number=Number(match[1]);
    if(number<1||number>max)continue;
    const start=pos+match[0].trim().length;
    const tail=text.slice(start);
    if(/^(?:films?|movies?|titles?|unique films?)\b/i.test(tail))continue;
    const yearIndex=tail.search(/\b(?:18|19|20)\d{2}\b/);
    if(yearIndex<0||yearIndex>110)continue;
    const afterYear=tail.slice(yearIndex+4);
    const scoreOk=kind==="movie-ratings"?/\d\.\d\/10/.test(afterYear.slice(0,100)):kind==="movie-encyclopedia"?/\d\.\d\s+\d{1,3}%/.test(afterYear.slice(0,100)):/\d\.\d/.test(afterYear.slice(0,80));
    if(!scoreOk)continue;
    const last=state.lastNumber||0;
    if(last&&number!==1&&number!==last&&number!==last+1&&number!==last+2)continue;
    if(number===1&&last>1)state.lastNumber=0;
    state.lastNumber=number;
    accepted.push({pos:pos,number:number});
  }
  if(!accepted.length)return {entries:[],prefix:text};
  const unique=[];
  accepted.forEach(item=>{if(!unique.length||unique[unique.length-1].pos!==item.pos)unique.push(item);});
  const prefix=text.slice(0,unique[0].pos).trim();
  const entries=unique.map((item,index)=>{
    const end=index+1<unique.length?unique[index+1].pos:text.length;
    return {number:item.number,text:text.slice(item.pos,end).trim()};
  }).filter(item=>item.text);
  return {entries:entries,prefix:prefix};
}
function cinemaAddSelectOption(select,value,label){
  const option=document.createElement("option");option.value=value;option.textContent=label;select.appendChild(option);
}
function cinemaBuildFilmReader(body,content,toolbar,kind){
  const wrapper=document.createElement("div");wrapper.className="rr-cinema-catalogue";
  const groups=[];let current=null;const state={lastNumber:0};
  const ensureGroup=(name,id)=>{
    const group={name:name||"Collection notes",id:id||"",section:document.createElement("section"),grid:document.createElement("div"),notes:document.createElement("div")};
    group.section.className="rr-cinema-group";group.section.dataset.category=group.name;
    if(group.id)group.section.id=group.id;
    const heading=document.createElement("h2");heading.className="rr-cinema-group-title";heading.textContent=group.name;
    group.section.appendChild(heading);
    group.grid.className="rr-cinema-grid";group.section.appendChild(group.grid);
    group.notes.className="rr-cinema-notes";group.section.appendChild(group.notes);
    wrapper.appendChild(group.section);groups.push(group);current=group;state.lastNumber=0;
    return group;
  };
  const addContext=(text)=>{
    const value=cinemaText(text);
    if(!value||/^Page\s+\d+\s*[·|]/i.test(value)||/^(?:The Complete Movie Encyclopedia|Complete Movie Ratings:|Page \d+\s*[·|])/i.test(value))return;
    const group=current||ensureGroup("Collection notes","");
    const p=document.createElement("p");p.className="rr-cinema-context";p.dataset.category=group.name;p.dataset.search=value.toLocaleLowerCase();p.textContent=value;
    group.notes.appendChild(p);
  };
  const addEntry=(entry)=>{
    if(!entry)return;
    const card=document.createElement("article");card.className="rr-cinema-entry";
    card.dataset.category=current.name;card.dataset.year=entry.year||"";card.dataset.imdb=entry.imdb||"";
    const top=document.createElement("div");top.className="rr-cinema-entry-top";
    const number=document.createElement("span");number.className="rr-cinema-entry-number";number.textContent="ENTRY "+entry.number;top.appendChild(number);
    const year=document.createElement("span");year.className="rr-cinema-entry-year";year.textContent=entry.year;top.appendChild(year);
    card.appendChild(top);
    const title=document.createElement("h3");title.className="rr-cinema-entry-title";title.textContent=entry.title;card.appendChild(title);
    if(entry.director){const credit=document.createElement("p");credit.className="rr-cinema-credit";credit.textContent="Director · "+entry.director;card.appendChild(credit);}
    const badges=document.createElement("div");badges.className="rr-cinema-entry-badges";
    if(entry.imdb){const b=document.createElement("span");b.className="rr-cinema-score";b.textContent="IMDb "+entry.imdb;badges.appendChild(b);}
    if(entry.rt){const b=document.createElement("span");b.className="rr-cinema-score rr-cinema-score-rt";b.textContent="Rotten Tomatoes "+entry.rt+"%";badges.appendChild(b);}
    if(entry.genre){const b=document.createElement("span");b.className="rr-cinema-chip";b.textContent=entry.genre;badges.appendChild(b);}
    if(entry.source){const b=document.createElement("span");b.className="rr-cinema-chip";b.textContent=entry.source;badges.appendChild(b);}
    if(badges.children.length)card.appendChild(badges);
    if(entry.details){const detail=document.createElement("p");detail.className="rr-cinema-entry-detail";detail.textContent=entry.details;card.appendChild(detail);}
    card.dataset.search=[entry.number,entry.title,entry.director,entry.year,entry.imdb,entry.rt,entry.genre,entry.source,entry.details,entry.raw,current.name].join(" ").toLocaleLowerCase();
    current.grid.appendChild(card);
  };
  const skipHeading=/^(?:CINEMA CURATED FILMS|TABLE OF CONTENTS|LIST [123]$|THE COMPLETE MOVIE|ENCYCLOPEDIA|DESCRIPTION|ABOUT THIS ENCYCLOPEDIA|COMPLETE MOVIE RATINGS|IMDB COLOR SCALE RT COLOR SCALE|FILM (?:TITLE )?DIRECTOR YEAR.*|SENSITIVE CINEMA|A CURATED GUIDE TO FILMS THAT MOVE YOU)$/i;
  content.querySelectorAll(":scope > .page").forEach((page)=>{
    [...page.children].forEach(node=>{
      if(node.classList.contains("page-label"))return;
      const rawText=node.textContent||"";
      const text=cinemaText(rawText);if(!text)return;
      if(/^H[1-3]$/.test(node.tagName)){
        if(skipHeading.test(text)){return;}
        if(cinemaGroupHeading(kind,text)){
          ensureGroup(text,node.id||"");return;
        }
        if(kind==="cinema-900"&&/^(?:100 World Cinema Masterpieces|100 Sensual & Mood Cinema|World Cinema Masterpieces|Sensual & Mood Cinema|Explicit Erotic Art Cinema)$/i.test(text)){
          if(!current)ensureGroup("Cinema collections","");
          const sub=document.createElement("h3");sub.className="rr-cinema-subheading";sub.textContent=text;current.section.insertBefore(sub,current.grid);return;
        }
        if(current){
          const sub=document.createElement("h3");sub.className="rr-cinema-subheading";sub.textContent=text;
          if(node.id)sub.id=node.id;current.section.insertBefore(sub,current.grid);
        }else{
          ensureGroup("About this edition","");addContext(text);
        }
        return;
      }
      if(node.tagName==="P"){
        const split=cinemaSplitNumberedText(text,kind,state);
        if(split.prefix&&!/^(?:#\s*)?(?:FILM|TITLE|RANK|100 films|Page \d+)/i.test(split.prefix))addContext(split.prefix);
        if(split.entries.length){
          split.entries.forEach(item=>addEntry(cinemaParseEntry(item.text,kind)));
        }else addContext(text);
        return;
      }
      if(node.tagName==="UL"||node.tagName==="OL"){
        [...node.children].forEach(li=>addContext(li.textContent||""));return;
      }
      addContext(text);
    });
  });
  if(!groups.length)ensureGroup("Film collection","");
  const categories=[...new Set(groups.map(g=>g.name))];
  const years=[...new Set([...wrapper.querySelectorAll(".rr-cinema-entry")].map(c=>c.dataset.year).filter(Boolean))].sort();
  const categorySelect=addSelect(toolbar.tools,"rr-reader-filter rr-cinema-category","collection",categories);
  const yearSelect=addSelect(toolbar.tools,"rr-reader-filter rr-cinema-year","year",years);
  const scoreSelect=document.createElement("select");scoreSelect.className="rr-reader-filter rr-cinema-score-filter";scoreSelect.setAttribute("aria-label","Minimum IMDb rating");
  [["all","Any IMDb rating"],["8","IMDb 8.0+"],["7","IMDb 7.0+"],["6","IMDb 6.0+"]].forEach(v=>cinemaAddSelectOption(scoreSelect,v[0],v[1]));
  toolbar.tools.appendChild(scoreSelect);
  const sortSelect=document.createElement("select");sortSelect.className="rr-reader-filter rr-cinema-sort";sortSelect.setAttribute("aria-label","Sort film entries");
  [["original","Original order"],["title","Title A–Z"],["year","Newest year"],["rating","Highest IMDb"]].forEach(v=>cinemaAddSelectOption(sortSelect,v[0],v[1]));
  toolbar.tools.appendChild(sortSelect);
  const allCards=[...wrapper.querySelectorAll(".rr-cinema-entry")];
  const empty=document.createElement("div");empty.className="rr-cinema-empty";empty.textContent="No film entries match these filters. Clear a filter or try another search.";wrapper.appendChild(empty);
  const validIds=new Set(groups.map(g=>g.id).filter(Boolean));
  document.querySelectorAll(".toc a[href^='#']").forEach(a=>{const id=a.getAttribute("href").slice(1);if(!validIds.has(id))a.remove();});
  const summary=document.querySelector(".toc summary");if(summary)summary.textContent="EXPLORE "+validIds.size+" COLLECTIONS";
  const originalOrder=new Map(allCards.map((card,i)=>[card,i]));
  const update=()=>{
    const q=toolbar.input.value.trim().toLocaleLowerCase(),category=categorySelect.value,year=yearSelect.value,minimum=Number(scoreSelect.value)||0;
    let visible=0,visibleNotes=0;
    allCards.forEach(card=>{
      const score=Number(card.dataset.imdb)||0;
      const show=(!q||card.dataset.search.includes(q))&&(category==="all"||card.dataset.category===category)&&(year==="all"||card.dataset.year===year)&&(!minimum||score>=minimum);
      card.hidden=!show;if(show)visible++;
    });
    wrapper.querySelectorAll(".rr-cinema-context").forEach(note=>{
      const show=(!q||note.dataset.search.includes(q))&&(category==="all"||note.dataset.category===category);
      note.hidden=!show;if(show)visibleNotes++;
    });
    groups.forEach(group=>{
      group.section.hidden=!group.section.querySelector(".rr-cinema-entry:not([hidden])")&&!group.notes.querySelector(".rr-cinema-context:not([hidden])");
      const cards=[...group.grid.children];
      if(sortSelect.value!=="original"){
        cards.sort((a,b)=>{
          if(sortSelect.value==="title")return a.querySelector(".rr-cinema-entry-title").textContent.localeCompare(b.querySelector(".rr-cinema-entry-title").textContent);
          if(sortSelect.value==="year")return (Number(b.dataset.year)||0)-(Number(a.dataset.year)||0);
          if(sortSelect.value==="rating")return (Number(b.dataset.imdb)||0)-(Number(a.dataset.imdb)||0);
          return originalOrder.get(a)-originalOrder.get(b);
        }).forEach(card=>group.grid.appendChild(card));
      }
    });
    empty.hidden=visible>0||visibleNotes>0;
    toolbar.result.textContent=visible.toLocaleString()+" film listings";
  };
  [toolbar.input,categorySelect,yearSelect,scoreSelect,sortSelect].forEach(control=>control.addEventListener(control===toolbar.input?"input":"change",update));
  content.replaceChildren(wrapper);body.classList.add("rr-cinema-structured");update();
  return true;
}
function buildSensitiveCinemaReader(body,content,toolbar){
  body.dataset.sensitiveSourceColumns=String(content.querySelectorAll(".rr-source-column").length);
  const wrapper=document.createElement("div");wrapper.className="rr-sensitive-catalogue";
  const groups=[];let current=null,currentFilm=null,lessonMode=false,pendingTitle="";
  const ensure=(name,id)=>{
    const group={name:name,id:id||"",section:document.createElement("section"),entries:[]};
    group.section.className="rr-sensitive-group";group.section.dataset.category=name;
    if(group.id)group.section.id=group.id;
    const h=document.createElement("h2");h.className="rr-sensitive-group-title";h.textContent=name;group.section.appendChild(h);
    wrapper.appendChild(group.section);groups.push(group);current=group;lessonMode=false;return group;
  };
  const addSubheading=(text,id)=>{
    if(!current)ensure("Film notes","");
    const h=document.createElement("h3");h.className="rr-sensitive-subheading";h.textContent=text;if(id)h.id=id;current.section.appendChild(h);
  };
  const flushFilm=()=>{
    if(!currentFilm)return;
    const film=currentFilm;currentFilm=null;
    if(!current)ensure("Film notes","");
    const card=document.createElement("article");card.className="rr-sensitive-entry";
    card.dataset.category=current.name;
    const search=[film.title,film.kind,film.meta,...film.description,...film.lesson,...film.ratings].join(" ").toLocaleLowerCase();
    card.dataset.search=search;
    const title=document.createElement("h3");title.className="rr-sensitive-entry-title";title.textContent=film.title||"Untitled film";card.appendChild(title);
    if(film.kind){const kind=document.createElement("span");kind.className="rr-sensitive-kind";kind.textContent=film.kind;card.appendChild(kind);}
    if(film.meta){const meta=document.createElement("p");meta.className="rr-sensitive-meta";meta.textContent=film.meta;card.appendChild(meta);}
    if(film.ratings.length){
      const ratings=document.createElement("div");ratings.className="rr-sensitive-ratings";
      film.ratings.forEach(value=>{const badge=document.createElement("span");badge.textContent="IMDb "+value;ratings.appendChild(badge);});
      card.appendChild(ratings);
    }
    film.description.filter(Boolean).forEach(value=>{const p=document.createElement("p");p.className="rr-sensitive-entry-copy";p.textContent=value;card.appendChild(p);});
    if(film.lesson.length){
      const label=document.createElement("div");label.className="rr-sensitive-lesson-label";label.textContent="What it teaches";card.appendChild(label);
      film.lesson.filter(Boolean).forEach(value=>{const p=document.createElement("p");p.className="rr-sensitive-lesson-copy";p.textContent=value;card.appendChild(p);});
    }
    current.section.appendChild(card);current.entries.push(card);
  };
  const startFilm=(title,kind)=>{
    flushFilm();
    currentFilm={title:cinemaText(title),kind:cinemaText(kind),meta:"",description:[],lesson:[],ratings:[]};
    pendingTitle="";lessonMode=false;
  };
  const addFilmText=(value)=>{
    const text=cinemaText(value);
    if(!text)return;
    const ratings=[...text.matchAll(/★\s*(\d(?:\.\d)?)/g)].map(m=>m[1]);
    const clean=text.replace(/\s*★\s*\d(?:\.\d)?/g,"").trim();
    if(currentFilm){
      currentFilm.ratings.push(...ratings);
      if(clean&&currentFilm.meta){
        const boundaries=[...clean.matchAll(/[.!?]\s+(?=[A-Z“])/g)];
        if(boundaries.length){
          const boundary=boundaries[boundaries.length-1];
          const splitAt=boundary.index+boundary[0].length;
          const candidate=clean.slice(splitAt).trim();
          const words=candidate.split(/\s+/);
          const smallWords=new Set(["a","an","and","as","at","by","de","del","for","in","la","of","on","the","to","van","von","with"]);
          const titleCase=words.length>=2&&words.length<=9&&words.every((word,index)=>smallWords.has(word.toLowerCase())||/^[A-Z0-9]/.test(word));
          if(titleCase&&!/[.!?]$/.test(candidate)){
            const prior=clean.slice(0,splitAt).trim();
            if(prior){if(lessonMode)currentFilm.lesson.push(prior);else currentFilm.description.push(prior);}
            pendingTitle=candidate;
            return;
          }
        }
      }
      if(clean){
        if(lessonMode)currentFilm.lesson.push(clean);
        else currentFilm.description.push(clean);
      }
    }else if(clean){
      const words=clean.split(/\s+/);
      if(words.length>=2&&words.length<=9&&words.every((word,index)=>["a","an","and","as","at","by","de","del","for","in","la","of","on","the","to","van","von","with"].includes(word.toLowerCase())||/^[A-Z0-9]/.test(word)))pendingTitle=clean;
      else addContext(clean);
    }
  };
  const splitFilmMarkers=(raw)=>{
    const text=String(raw||"").replace(/\s+/g," ").trim();
    const markers=[...text.matchAll(/■\s*([A-Z]{2,})\b/g)];
    if(!markers.length){addFilmText(text);return;}
    let cursor=0;
    markers.forEach(marker=>{
      const before=text.slice(cursor,marker.index).trim();
      const withoutRatings=before.replace(/\s*★\s*\d(?:\.\d)?/g,"").trim();
      let titleStart=-1;
      const boundaries=[...withoutRatings.matchAll(/[.!?]\s+(?=[A-Z“])/g)];
      if(boundaries.length)titleStart=boundaries[boundaries.length-1].index+boundaries[boundaries.length-1][0].length;
      else if(currentFilm){
        const words=withoutRatings.split(/\s+/);
        if(words.length>8)titleStart=words.slice(0,-8).join(" ").length+1;
      }
      const prior=titleStart>=0?withoutRatings.slice(0,titleStart).trim():(!currentFilm?"": "");
      const title=titleStart>=0?withoutRatings.slice(titleStart).trim():withoutRatings;
      if(prior)addFilmText(prior);
      if(title)startFilm(title,marker[1]);
      cursor=marker.index+marker[0].length;
    });
    const tail=text.slice(cursor).trim();
    if(tail)addFilmText(tail);
  };
  const addContext=(value)=>{
    const text=cinemaText(value);
    if(!text||!current)return;
    const p=document.createElement("p");p.className="rr-sensitive-context";p.textContent=text;current.section.appendChild(p);
  };
  content.querySelectorAll(":scope > .page").forEach(page=>{
    const pageNodes=[...page.children].flatMap(node=>
      node.classList.contains("rr-source-column")?[...node.children]:[node]
    );
    pageNodes.forEach(node=>{
      if(node.classList.contains("page-label"))return;
      const rawText=node.textContent||"";
      const text=cinemaText(rawText);
      if(!text)return;
      if(/^H[1-3]$/.test(node.tagName)){
        if(/WHAT IT TEACHES/i.test(text)){
          lessonMode=true;return;
        }
        const meta=text.match(/^(.+?)\s+·\s+((?:18|19|20)\d{2})\s+·\s+([\s\S]+)$/);
        if(meta){
          if(currentFilm&&currentFilm.meta){
            flushFilm();
            currentFilm={title:pendingTitle||"Untitled film",kind:"",meta:"",description:[],lesson:[],ratings:[]};
            pendingTitle="";lessonMode=false;
          }else if(!currentFilm){
            currentFilm={title:pendingTitle||"Untitled film",kind:"",meta:"",description:[],lesson:[],ratings:[]};
            pendingTitle="";lessonMode=false;
          }
          if(currentFilm)currentFilm.meta=text;
          return;
        }
        if(/^(?:SENSITIVE CINEMA|A CURATED GUIDE TO FILMS THAT MOVE YOU)$/i.test(text))return;
        if(text===text.toUpperCase()&&text.length<70){
          flushFilm();ensure(text,node.id||"");return;
        }
        if(currentFilm){
          if(lessonMode)currentFilm.lesson.push(text);
          else currentFilm.description.push(text);
        }else if(current)addSubheading(text,node.id||"");
        return;
      }
      if(node.tagName==="P"){
        splitFilmMarkers(rawText);
        return;
      }
      if(node.tagName==="UL"||node.tagName==="OL"){
        [...node.children].forEach(li=>addContext(li.textContent||""));return;
      }
      if(currentFilm){
        if(lessonMode)currentFilm.lesson.push(text);
        else currentFilm.description.push(text);
      }else addContext(text);
    });
  });
  flushFilm();
  if(!groups.length)ensure("Sensitive cinema","");
  const categories=[...new Set(groups.map(g=>g.name))];
  const categorySelect=addSelect(toolbar.tools,"rr-reader-filter rr-sensitive-category","category",categories);
  const allCards=[...wrapper.querySelectorAll(".rr-sensitive-entry")];
  const empty=document.createElement("div");empty.className="rr-cinema-empty";empty.textContent="No reading notes match. Clear the filters or try another search.";wrapper.appendChild(empty);
  const validIds=new Set(groups.map(g=>g.id).filter(Boolean));
  document.querySelectorAll(".toc a[href^='#']").forEach(a=>{const id=a.getAttribute("href").slice(1);if(!validIds.has(id))a.remove();});
  const summary=document.querySelector(".toc summary");if(summary)summary.textContent="EXPLORE "+validIds.size+" THEMES";
  const update=()=>{
    const q=toolbar.input.value.trim().toLocaleLowerCase(),cat=categorySelect.value;let visible=0;
    allCards.forEach(card=>{const show=(!q||card.dataset.search.includes(q))&&(cat==="all"||card.dataset.category===cat);card.hidden=!show;if(show)visible++;});
    groups.forEach(group=>{group.section.hidden=!group.section.querySelector(".rr-sensitive-entry:not([hidden])");});
    empty.hidden=visible>0;toolbar.result.textContent=visible.toLocaleString()+" films";
  };
  [toolbar.input,categorySelect].forEach(control=>control.addEventListener(control===toolbar.input?"input":"change",update));
  content.replaceChildren(wrapper);body.classList.add("rr-sensitive-structured");update();
  return true;
}
function initReaderControls(){
  document.querySelectorAll("body.rr-reader").forEach(body=>{
    if(body.dataset.rrReaderEnhanced==="1")return;
    const content=body.querySelector("#content"),toolbar=readerToolbar(body);
    if(!content||!toolbar)return;
    body.dataset.rrReaderEnhanced="1";
    const kind=body.dataset.readerKind||"";
    if(kind==="sensitive-cinema"){buildSensitiveCinemaReader(body,content,toolbar);return;}
    if(kind==="cinema-900"||kind==="movie-encyclopedia"||kind==="movie-ratings"||kind==="movie-ratings-647"){
      cinemaBuildFilmReader(body,content,toolbar,kind);return;
    }
    const title=(body.querySelector(".hero h1")||body.querySelector("h1")||{}).textContent||"";
    if(body.classList.contains("rr--poetry")){buildPoetryReader(body,content,toolbar);return;}
    const headings=[...content.querySelectorAll("h2,h3")];
    const filmMetaCount=headings.filter(h=>parseFilmMeta(h.textContent)).length;
    const numberedCount=headings.filter(h=>/^\s*\d{1,3}[.)]?\s+/.test(h.textContent)).length;
    const textNumberCount=((content.innerText||"").match(/(?:^|\s)\d{1,3}[.)]?\s+[A-ZÀ-ÖØ-Þ]/g)||[]).length;
    const filmLike=/film|cinema|movie/i.test(title);
    const isFilmCatalogue=filmLike&&(filmMetaCount>=8||numberedCount>=18||(/filmography/i.test(title)&&textNumberCount>=12));
    const orderedFilmCount=content.querySelectorAll(":scope > .page ol li").length;
    if(filmLike&&orderedFilmCount>=12&&buildOrderedFilmCatalogue(body,content,toolbar))return;
    if(isFilmCatalogue&&buildFilmCatalogue(body,content,toolbar))return;
    buildGenericReader(body,content,toolbar);
  });
}
function initLearningCurriculum(){
  const body=document.querySelector("body.rr--learning");
  if(!body||body.dataset.rrLearningEnhanced==="1")return;
  const entries=[...body.querySelectorAll(".entry")];
  if(entries.length<20)return;
  body.dataset.rrLearningEnhanced="1";
  const toolbar=document.createElement("section");toolbar.className="rr-learning-toolbar";
  const search=document.createElement("input");search.type="search";search.placeholder="Search works, creators, themes or lessons…";search.setAttribute("aria-label","Search curriculum entries");
  const mediumValues=new Set(),phaseValues=new Set(),tagValues=new Set();
  const metaFor=(entry)=>entry.querySelector(".entry-meta")?.textContent.trim()||"";
  const titleFor=(entry)=>entry.querySelector(".entry-title")?.textContent.trim()||"";
  const lessonFor=(entry)=>entry.querySelector(".entry-lesson")?.textContent.trim()||"";
  const phaseFor=(entry)=>{
    const phase=entry.closest(".phase");const h=phase?.querySelector(".phase-title h2");
    return h?h.textContent.trim():"Curriculum";
  };
  const mediumFor=(entry)=>{
    const column=entry.closest(".entry")?.parentElement;
    return column?.querySelector(".col-title")?.textContent.trim()||"";
  };
  entries.forEach(entry=>{
    const medium=mediumFor(entry),phase=phaseFor(entry);
    if(medium)mediumValues.add(medium);if(phase)phaseValues.add(phase);
    entry.querySelectorAll(".tag").forEach(t=>{if(t.textContent.trim())tagValues.add(t.textContent.trim());});
  });
  const mediumSelect=addSelect(toolbar,"rr-learning-filter","medium",mediumValues);
  const phaseSelect=addSelect(toolbar,"rr-learning-filter","phase",phaseValues);
  const topicSelect=addSelect(toolbar,"rr-learning-filter","theme",tagValues);
  const count=document.createElement("span");count.className="rr-learning-count";count.setAttribute("aria-live","polite");
  const clear=document.createElement("button");clear.type="button";clear.className="rr-learning-clear";clear.textContent="Clear";
  toolbar.appendChild(search);toolbar.appendChild(mediumSelect);toolbar.appendChild(phaseSelect);toolbar.appendChild(topicSelect);toolbar.appendChild(count);toolbar.appendChild(clear);
  const nav=body.querySelector(".phase-nav");
  if(nav)nav.insertAdjacentElement("afterend",toolbar);
  else {const first=body.querySelector(".phase");if(first)first.insertAdjacentElement("beforebegin",toolbar);else body.insertBefore(toolbar,body.firstChild);}
  const empty=document.createElement("p");empty.className="rr-learning-empty";empty.textContent="No curriculum entries match these filters.";
  toolbar.insertAdjacentElement("afterend",empty);
  const update=()=>{
    const q=search.value.trim().toLocaleLowerCase();let visible=0;
    entries.forEach(entry=>{
      const medium=mediumFor(entry),phase=phaseFor(entry);
      const tags=[...entry.querySelectorAll(".tag")].map(t=>t.textContent.trim());
      const text=[titleFor(entry),metaFor(entry),lessonFor(entry),tags.join(" "),phase,medium].join(" ").toLocaleLowerCase();
      const show=(!q||text.includes(q))&&(mediumSelect.value==="all"||mediumSelect.value===medium)&&
        (phaseSelect.value==="all"||phaseSelect.value===phase)&&(topicSelect.value==="all"||tags.includes(topicSelect.value));
      entry.hidden=!show;if(show)visible++;
    });
    body.querySelectorAll(".phase").forEach(phase=>{
      const phaseEntries=[...phase.querySelectorAll(".entry")];
      phase.hidden=phaseEntries.length>0&&!phaseEntries.some(entry=>!entry.hidden);
    });
    count.textContent=visible+" of "+entries.length+" works";empty.hidden=visible>0;
  };
  [search,mediumSelect,phaseSelect,topicSelect].forEach(control=>control.addEventListener(control===search?"input":"change",update));
  clear.addEventListener("click",()=>{search.value="";[mediumSelect,phaseSelect,topicSelect].forEach(s=>s.value="all");update();});
  update();body.classList.add("rr-learning-enhanced");
}
function initArtResourceSearch(){
  const body=document.querySelector("body.rr--art");
  if(!body||body.dataset.rrArtSearch==="1")return;
  const sections=[...body.querySelectorAll(".section[data-section]")];
  const cards=[...body.querySelectorAll(".section[data-section] .card")];
  const tabs=[...body.querySelectorAll(".ftab")];
  if(!cards.length||!tabs.length)return;
  body.dataset.rrArtSearch="1";
  const host=tabs[0].parentElement;
  const toolbar=document.createElement("div");toolbar.className="rr-art-search";
  const input=document.createElement("input");input.type="search";input.placeholder="Search tools, artists, mediums or skills…";input.setAttribute("aria-label","Search art resources");
  const count=document.createElement("span");count.className="rr-art-count";count.setAttribute("aria-live","polite");
  toolbar.appendChild(input);toolbar.appendChild(count);
  host.parentNode.insertBefore(toolbar,host);
  const update=()=>{
    const q=input.value.trim().toLocaleLowerCase();
    const active=body.querySelector(".ftab.active");
    const filter=active?active.dataset.filter:"all";let visible=0;
    cards.forEach(card=>{
      const tags=(card.dataset.tags||"").split(/\s+/);
      const category=filter==="all"||tags.includes(filter);
      const match=!q||(card.textContent||"").toLocaleLowerCase().includes(q);
      const show=category&&match;card.style.display=show?"":"none";if(show)visible++;
    });
    sections.forEach(section=>{section.classList.toggle("hidden",!section.querySelector(".card:not([style*='display: none'])"));});
    count.textContent=visible+" of "+cards.length+" resources";
  };
  tabs.forEach(tab=>tab.addEventListener("click",()=>requestAnimationFrame(update)));
  input.addEventListener("input",update);update();
}


function initMangaGuideCatalogue(){
  const body=document.querySelector("body.rr--manga"),cards=[...document.querySelectorAll(".manga-card")];
  if(!body||cards.length<15||body.dataset.rrMangaGuide==="1")return;
  body.dataset.rrMangaGuide="1";
  const host=document.createElement("section");host.className="rr-manga-guide-tools";
  const input=document.createElement("input");input.type="search";input.placeholder="Search titles, Japanese names, genres or descriptions…";input.setAttribute("aria-label","Search manga guide");
  const genre=new Set(),feel=new Set(),length=new Set();
  cards.forEach(card=>{
    const add=(selector,set)=>{const value=card.querySelector(selector)?.textContent.trim();if(value)set.add(value);};
    add(".tag-genre",genre);add(".tag-feel",feel);add(".tag-length",length);
  });
  const genreSelect=addSelect(host,"rr-reader-filter","genre",genre);
  const feelSelect=addSelect(host,"rr-reader-filter","reading mood",feel);
  const lengthSelect=addSelect(host,"rr-reader-filter","publication status",length);
  const count=document.createElement("span");count.className="rr-catalogue-count";count.setAttribute("aria-live","polite");
  const clear=document.createElement("button");clear.type="button";clear.className="rr-reader-clear";clear.textContent="Clear";
  host.prepend(input);host.appendChild(count);host.appendChild(clear);
  const header=body.querySelector("header");
  if(header)header.insertAdjacentElement("afterend",host);else cards[0].closest(".tier-block")?.insertAdjacentElement("beforebegin",host);
  const update=()=>{
    const q=input.value.trim().toLocaleLowerCase();let visible=0;
    cards.forEach(card=>{
      const g=card.querySelector(".tag-genre")?.textContent.trim()||"";
      const f=card.querySelector(".tag-feel")?.textContent.trim()||"";
      const l=card.querySelector(".tag-length")?.textContent.trim()||"";
      const show=(!q||(card.textContent||"").toLocaleLowerCase().includes(q))&&
        (genreSelect.value==="all"||genreSelect.value===g)&&
        (feelSelect.value==="all"||feelSelect.value===f)&&
        (lengthSelect.value==="all"||lengthSelect.value===l);
      card.hidden=!show;if(show)visible++;
    });
    document.querySelectorAll(".tier-block").forEach(tier=>{tier.hidden=!tier.querySelector(".manga-card:not([hidden])");});
    count.textContent=visible+" of "+cards.length+" manga";
  };
  [input,genreSelect,feelSelect,lengthSelect].forEach(el=>el.addEventListener(el===input?"input":"change",update));
  clear.addEventListener("click",()=>{input.value="";[genreSelect,feelSelect,lengthSelect].forEach(s=>s.value="all");update();});
  update();
}
function initPoliticalComicsFinder(){
  const body=document.querySelector("body.rr--comics,body"),panels=[...document.querySelectorAll(".tab-panel")];
  if(!panels.length||!document.querySelector(".filter-btn[onclick*='filterCards']")||body.dataset.rrPoliticalFinder==="1")return;
  body.dataset.rrPoliticalFinder="1";
  const allCards=[...panels.flatMap(panel=>[...panel.querySelectorAll(".card")])];
  if(allCards.length<20)return;
  const host=document.createElement("section");host.className="rr-political-tools";
  const input=document.createElement("input");input.type="search";input.placeholder="Search titles, creators, countries and themes…";input.setAttribute("aria-label","Search political comics and manga");
  const formats=new Set(allCards.map(card=>card.dataset.format||"").filter(Boolean));
  const regions=new Set(allCards.map(card=>card.dataset.region||"").filter(Boolean));
  const formatSelect=addSelect(host,"rr-reader-filter","format",formats);
  const regionSelect=addSelect(host,"rr-reader-filter","region",regions);
  const count=document.createElement("span");count.className="rr-catalogue-count";count.setAttribute("aria-live","polite");
  const clear=document.createElement("button");clear.type="button";clear.className="rr-reader-clear";clear.textContent="Clear search";
  host.prepend(input);host.appendChild(count);host.appendChild(clear);
  const tabs=document.querySelector(".tab-btn")?.parentElement;
  if(tabs)tabs.insertAdjacentElement("afterend",host);else panels[0].insertAdjacentElement("beforebegin",host);
  const update=()=>{
    const active=document.querySelector(".tab-panel.active")||panels[0];
    const query=input.value.trim().toLocaleLowerCase();let visible=0,total=0;
    panels.forEach(panel=>{
      const isActive=panel===active;
      [...panel.querySelectorAll(".card")].forEach(card=>{
        if(!isActive){card.style.removeProperty("display");return;}
        total++;
        const format=card.dataset.format||"",region=card.dataset.region||"";
        const show=!card.classList.contains("hidden")&&
          (!query||(card.textContent||"").toLocaleLowerCase().includes(query))&&
          (formatSelect.value==="all"||format===formatSelect.value)&&
          (regionSelect.value==="all"||region===regionSelect.value);
        card.style.display=show?"":"none";if(show)visible++;
      });
      panel.querySelectorAll(".card-grid").forEach(grid=>{
        const shown=[...grid.querySelectorAll(".card")].some(card=>card.style.display!=="none"&&!card.classList.contains("hidden"));
        const header=grid.previousElementSibling?.classList.contains("section-header")?grid.previousElementSibling:null;
        grid.hidden=isActive&&!shown;if(header)header.hidden=isActive&&!shown;
      });
    });
    count.textContent=visible+" of "+total+" items in "+(active.id==="tab-fiction"?"fiction":"nonfiction");
  };
  [input,formatSelect,regionSelect].forEach(el=>el.addEventListener(el===input?"input":"change",update));
  clear.addEventListener("click",()=>{input.value="";formatSelect.value="all";regionSelect.value="all";update();});
  document.querySelectorAll(".filter-btn,.tab-btn").forEach(button=>button.addEventListener("click",()=>setTimeout(update,0)));
  update();
}
function initCurriculumBookFinder(){
  const body=document.body;
  const bookCards=[...body.querySelectorAll(".book-card")];
  const books=[...body.querySelectorAll(".books-list > .book")];
  const entries=bookCards.length?bookCards:books;
  if(entries.length<12||body.dataset.rrBookFinder==="1")return;
  body.dataset.rrBookFinder="1";
  const host=document.createElement("section");host.className="rr-curriculum-tools";
  const input=document.createElement("input");input.type="search";input.placeholder="Search titles, authors, traditions or reading notes…";input.setAttribute("aria-label","Search curriculum books");
  const originSet=new Set(),descriptorSet=new Set(),stageSet=new Set();
  const metaFor=entry=>entry.querySelector(".book-origin,.book-origin-tag")?.textContent.replace(/\s+/g," ").trim()||"";
  const descriptorFor=entry=>entry.querySelector(".book-type-tag")?.textContent.trim()||(()=>{
    const meta=metaFor(entry);return meta.includes("·")?meta.split("·").slice(1).join("·").trim():"";
  })();
  const stageFor=entry=>{
    const stage=entry.closest(".stage,.stage-block");
    return stage?.querySelector(".stage-title")?.textContent.replace(/\s+/g," ").trim()||"";
  };
  entries.forEach(entry=>{
    const meta=metaFor(entry),origin=meta.includes("·")?meta.split("·")[0].replace(/[^\p{L}\p{N}\s&/-]/gu,"").trim():meta;
    if(origin)originSet.add(origin);
    const descriptor=descriptorFor(entry);if(descriptor)descriptorSet.add(descriptor);
    const stage=stageFor(entry);if(stage)stageSet.add(stage);
  });
  const originSelect=addSelect(host,"rr-reader-filter","tradition / origin",originSet);
  const descriptorSelect=addSelect(host,"rr-reader-filter","form / period",descriptorSet);
  const stageSelect=stageSet.size?addSelect(host,"rr-reader-filter","stage",stageSet):null;
  const count=document.createElement("span");count.className="rr-catalogue-count";count.setAttribute("aria-live","polite");
  const clear=document.createElement("button");clear.type="button";clear.className="rr-reader-clear";clear.textContent="Clear";
  host.prepend(input);host.appendChild(count);host.appendChild(clear);
  const anchor=body.querySelector(".hero");
  if(anchor)anchor.insertAdjacentElement("afterend",host);else entries[0].parentElement.insertAdjacentElement("beforebegin",host);
  const update=()=>{
    const q=input.value.trim().toLocaleLowerCase();let visible=0;
    entries.forEach(entry=>{
      const meta=metaFor(entry),origin=meta.includes("·")?meta.split("·")[0].replace(/[^\p{L}\p{N}\s&/-]/gu,"").trim():meta;
      const descriptor=descriptorFor(entry),stage=stageFor(entry);
      const show=(!q||(entry.textContent||"").toLocaleLowerCase().includes(q))&&
        (originSelect.value==="all"||origin===originSelect.value)&&
        (descriptorSelect.value==="all"||descriptor===descriptorSelect.value)&&
        (!stageSelect||stageSelect.value==="all"||stage===stageSelect.value);
      entry.hidden=!show;if(show)visible++;
    });
    body.querySelectorAll(".stage,.stage-block").forEach(stage=>{
      const direct=[...stage.querySelectorAll(".book-card,.book")];
      if(direct.length)stage.hidden=!direct.some(item=>!item.hidden);
    });
    count.textContent=visible+" of "+entries.length+" reading selections";
  };
  [input,originSelect,descriptorSelect].concat(stageSelect?[stageSelect]:[]).forEach(el=>el.addEventListener(el===input?"input":"change",update));
  clear.addEventListener("click",()=>{input.value="";[originSelect,descriptorSelect].forEach(s=>s.value="all");if(stageSelect)stageSelect.value="all";update();});
  update();
}
function initValuesCurriculumFinder(){
  const body=document.querySelector("body.rr--learning");
  const cards=[...document.querySelectorAll(".cards-grid .card")];
  if(!body||cards.length<40||body.dataset.rrValuesFinder==="1")return;
  body.dataset.rrValuesFinder="1";
  const host=document.createElement("section");host.className="rr-curriculum-tools";
  const input=document.createElement("input");input.type="search";input.placeholder="Search titles, creators, themes or reflections…";input.setAttribute("aria-label","Search anime and manga curriculum");
  const themes=new Set();
  cards.forEach(card=>{
    const raw=card.querySelector(".card-theme-tag")?.textContent||"";
    raw.replace(/^[▸►·\s]+/,"").split(/[·•,;]/).map(v=>v.trim()).filter(Boolean).forEach(v=>themes.add(v));
  });
  const themeSelect=addSelect(host,"rr-reader-filter","theme",themes);
  const count=document.createElement("span");count.className="rr-catalogue-count";count.setAttribute("aria-live","polite");
  const clear=document.createElement("button");clear.type="button";clear.className="rr-reader-clear";clear.textContent="Clear";
  host.prepend(input);host.appendChild(themeSelect);host.appendChild(count);host.appendChild(clear);
  const filterBar=body.querySelector(".filter-bar");
  if(filterBar)filterBar.insertAdjacentElement("afterend",host);else cards[0].closest("section")?.insertAdjacentElement("beforebegin",host);
  const update=()=>{
    const q=input.value.trim().toLocaleLowerCase();let visible=0;
    cards.forEach(card=>{
      const theme=(card.querySelector(".card-theme-tag")?.textContent||"").replace(/^[▸►·\s]+/,"").trim();
      const show=!card.classList.contains("hidden")&&
        (!q||(card.textContent||"").toLocaleLowerCase().includes(q))&&
        (themeSelect.value==="all"||theme.split(/[·•,;]/).map(v=>v.trim()).includes(themeSelect.value));
      card.style.display=show?"":"none";if(show)visible++;
    });
    body.querySelectorAll(".section").forEach(section=>{
      const own=[...section.querySelectorAll(".cards-grid .card")];
      if(own.length)section.hidden=!own.some(card=>card.style.display!=="none"&&!card.classList.contains("hidden"));
    });
    count.textContent=visible+" of "+cards.length+" works";
  };
  [input,themeSelect].forEach(el=>el.addEventListener(el===input?"input":"change",update));
  clear.addEventListener("click",()=>{input.value="";themeSelect.value="all";update();});
  body.querySelectorAll(".filter-btn,.nav-tab").forEach(btn=>btn.addEventListener("click",()=>setTimeout(update,0)));
  update();
}

function start(){
  setupTheme();
  const key=siteKey(),manifest=window.READING_ROOM_CONTEXT||{},meta=manifest[key]||null;
  buildNav(key,meta);
  addContext(key,meta);
  initHubFilters();
  initReaderControls();
  initLearningCurriculum();
  initArtResourceSearch();
  initMangaGuideCatalogue();
  initPoliticalComicsFinder();
  initCurriculumBookFinder();
  initValuesCurriculumFinder();
}
if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",start);else start();
})();