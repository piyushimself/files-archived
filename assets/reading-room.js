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

function initReaderControls(){
  document.querySelectorAll("body.rr-reader").forEach(body=>{
    const content=body.querySelector("#content"),toolbar=readerToolbar(body);
    if(!content||!toolbar||body.dataset.rrReaderEnhanced==="1")return;
    body.dataset.rrReaderEnhanced="1";
    const title=(body.querySelector(".hero h1")||body.querySelector("h1")||{}).textContent||"";
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

function start(){
  setupTheme();
  const key=siteKey(),manifest=window.READING_ROOM_CONTEXT||{},meta=manifest[key]||null;
  buildNav(key,meta);
  addContext(key,meta);
  initHubFilters();
  initReaderControls();
  initLearningCurriculum();
  initArtResourceSearch();
}
if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",start);else start();
})();