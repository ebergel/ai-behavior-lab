'use strict';
function dictionaryParams(raw={}) {
 const out={term:String(raw.term||''),q:String(raw.q||''),category:String(raw.category||''),fromGem:''};
 if(out.term==='passage'){out.term='message';out.category='entities';}
 if(out.category==='evidence'&&out.term==='lineage')out.category='entities';
 if(raw.fromGem){try{const value=JSON.parse(raw.fromGem);if(value&&typeof value==='object'&&!Array.isArray(value))out.fromGem=JSON.stringify(value);}catch{}}
 return out;
}
function dictionaryUrl(term='',change={}) {
 const current=state.view==='dictionary'?(state.dictionaryFilters||{}):{};
 const params=dictionaryParams({...current,...change,term});
 if(state.view==='gems')params.fromGem=JSON.stringify(state.gemFilters||{});
 return '#'+new URLSearchParams({view:'dictionary',...Object.fromEntries(Object.entries(params).filter(([,v])=>v!==''))});
}
function dictionaryLink(term,label='Definition & interpretation') {
 return `<a class="dictionary-link" href="${esc(dictionaryUrl(term,{q:'',category:''}))}">${esc(label)} ↗</a>`;
}
function dictionaryMatches(entries,f) {
 const words=f.q.toLocaleLowerCase().trim().split(/\s+/).filter(Boolean);
 return entries.filter(e=>(!f.category||e.category===f.category)&&words.every(w=>JSON.stringify(e).toLocaleLowerCase().includes(w)));
}
async function loadDictionary(raw={}) {
 const previousView=state.view,previousTerm=state.dictionaryFilters?.term;
 const version=++routeVersion;state.run=null;state.view='dictionary';state.dictionaryFilters=dictionaryParams(raw);
 if(!state.dictionary){const data=await api('/api/dictionary');if(version!==routeVersion)return;state.dictionary=data;}
 renderSidebar();renderCompareTray();renderDictionary();
 if(previousView!=='dictionary')window.scrollTo({top:0});
 else if(raw.term&&raw.term!==previousTerm)$('#dictionary-detail').scrollIntoView({block:'start'});
}
function dictionaryEntry(e,catalog) {
 const list=items=>`<ul>${items.map(t=>`<li>${esc(t)}</li>`).join('')}</ul>`;
 return `<article class="dictionary-entry" aria-labelledby="dictionary-title"><header><div class="eyebrow">${esc(e.kind)}</div><h2 id="dictionary-title">${esc(e.title)}</h2><p class="dictionary-definition">${esc(e.definition)}</p>${e.scale?`<span class="dictionary-scale">${esc(e.scale)}</span>`:''}</header>
 <section class="dictionary-practical"><h3>What it means in practice</h3><p>${esc(e.practical)}</p>${e.low?`<div class="dictionary-range"><div><span>LOWER VALUES</span><p>${esc(e.low)}</p></div><div><span>HIGHER VALUES</span><p>${esc(e.high)}</p></div></div>`:''}</section>
 ${e.example?`<section class="dictionary-example"><div class="eyebrow">ILLUSTRATIVE EXAMPLE · NOT SCORED CORPUS EVIDENCE</div><p>${esc(e.example)}</p></section>`:''}
 <section><h3>Technical specification</h3>${e.formula?`<pre class="dictionary-formula">${esc(e.formula)}</pre>`:''}${list(e.method||[])}${e.rubric?`<div class="dictionary-rubric"><h4>Exact assessment question · original wording</h4><p class="source-note">This recorded instrument uses “passage” for the selected message. Its original wording is preserved for reproducibility.</p><p>${esc(e.rubric.question)}</p><h4>The five rubric levels</h4><ol start="0">${e.rubric.criteria.map((c,k)=>`<li><span>LEVEL ${k} · ${k*25} ON DISPLAY SCALE</span><p>${esc(c)}</p></li>`).join('')}</ol><details><summary>Shared assessment instructions</summary><p>${esc(e.scope)}</p></details></div>`:''}</section>
 <section class="dictionary-limits"><h3>What this does not establish</h3>${list(e.limits||[])}</section>
 <section><h3>Related terms</h3><div class="dictionary-related">${e.related.map(id=>dictionaryLink(id,catalog.entries.find(x=>x.id===id)?.title||id)).join('')}</div></section>
 <details class="dictionary-provenance"><summary>Definition version & implementation sources</summary><p>Guide: ${esc(catalog.version)} · ${esc(catalog.author)}</p>${e.rubric?`<p>Exact rubric: ${esc(catalog.rubric.version)} · ${esc(catalog.rubric.status)}</p><p class="dictionary-hash">Rubric file SHA-256: ${esc(catalog.rubric.file_sha256)}</p>`:''}${list(e.sources||[])}<p>The guide is explanatory documentation. Opening it does not reassess messages or change saved readings.</p></details>
 </article>`;
}
function dictionaryEntityMap() {
 const term=(id,label)=>`<a href="${esc(dictionaryUrl(id,{q:'',category:'entities'}))}">${esc(label)}</a>`;
 return `<section class="dictionary-entity-map" aria-label="Research entity relationships"><div><span class="eyebrow">EVIDENCE HIERARCHY</span><p>${term('conversation','Conversation')} <span aria-hidden="true">→</span> ${term('message','Message')} <span aria-hidden="true">→</span> ${term('excerpt','Optional excerpt')}</p></div><div><span class="eyebrow">ASSESSMENT RELATIONSHIP</span><p>${term('target','Selected object')} <span aria-hidden="true">→</span> ${term('assessment','Assessment')} <span aria-hidden="true">→</span> ${term('score','Feature scores')}</p></div><p class="dictionary-map-note">Target describes an object's role in an analysis. Context supplies supporting evidence. Repeated assessments do not add messages to the sample. ${term('unit-of-analysis','Read the counting rules →')}</p></section>`;
}
function renderDictionary() {
 const d=state.dictionary,f=state.dictionaryFilters;
 if(f.category&&!d.categories.some(c=>c.id===f.category))f.category='';
 const rows=dictionaryMatches(d.entries,f);
 const selected=rows.find(e=>e.id===f.term)||rows[0];
 f.term=selected?.id||'';
 history.replaceState(null,'',dictionaryUrl(f.term));
 $('#main').innerHTML=`<div class="content dictionary-page">${pageTop('Lab dictionary','Definitions, methods and practical meaning. A shared language for exploring the laboratory.')}
 <div class="dictionary-intro"><div><span class="eyebrow">THE LABORATORY'S SHARED VOCABULARY</span><p><strong>Know what you are counting and measuring.</strong> Explore the research entities, their relationships and units of analysis, alongside the eight Gem Finder measures and guidance for interpreting scores. Each entry links definitions, practical meaning and counting or measurement rules.</p></div><div class="actions"><a class="button" href="${esc(dictionaryUrl('conversation',{q:'',category:'entities'}))}">Research entities & units →</a>${f.fromGem?`<a class="button" href="#${esc(new URLSearchParams({view:'gems',gem:f.fromGem}).toString())}">← Return to your Gem view</a>`:`<a class="button" href="#view=gems">Open Gem Finder →</a>`}<a class="button" href="/api/dictionary" download="lab-dictionary.json">Export dictionary</a></div></div>
 ${(f.category==='entities'||selected?.category==='entities')?dictionaryEntityMap():''}
 <form id="dictionary-search" class="dictionary-search"><label>Find a term<input id="dictionary-query" type="search" placeholder="Message, target, assessment, confidence…" value="${esc(f.q)}" autocomplete="off"></label><label>Section<select id="dictionary-category">${option('','All terms',f.category)}${d.categories.map(c=>option(c.id,c.title,f.category)).join('')}</select></label><button class="button" type="submit">Search</button>${f.q||f.category?`<a class="quiet" href="${esc(dictionaryUrl('',{q:'',category:''}))}">Clear filters</a>`:''}<span class="source-note" role="status">${rows.length} / ${d.entries.length} terms</span></form>
 <div class="dictionary-layout"><nav class="dictionary-nav" aria-label="Dictionary terms">${d.categories.map(c=>{const entries=rows.filter(e=>e.category===c.id);return entries.length?`<section><h3>${esc(c.title)} <span>${entries.length}</span></h3>${entries.map(e=>`<a href="${esc(dictionaryUrl(e.id))}" class="${selected?.id===e.id?'selected':''}" ${selected?.id===e.id?'aria-current="true"':''}><span>${esc(e.title)}</span><small>${esc(e.kind)}</small></a>`).join('')}</section>`:'';}).join('')}</nav><div id="dictionary-detail">${selected?dictionaryEntry(selected,d):'<div class="empty"><h2>No terms match this search.</h2><p>Try another phrase or clear the filters.</p></div>'}</div></div></div>`;
}
document.addEventListener('submit',e=>{if(e.target.id!=='dictionary-search')return;e.preventDefault();location.hash=dictionaryUrl('',{q:$('#dictionary-query').value,category:$('#dictionary-category').value});});
document.addEventListener('change',e=>{if(e.target.id==='dictionary-category')location.hash=dictionaryUrl('',{category:e.target.value,q:$('#dictionary-query').value});});
