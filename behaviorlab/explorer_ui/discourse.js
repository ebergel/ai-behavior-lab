'use strict';
const lensVariants=[['definition_only','Definitions only'],['name_only','Names only'],['name_and_definition','Names + definitions']];
function lensFilters(raw={}) {
 const valid=(key,values,fallback)=>values.includes(raw[key])?raw[key]:fallback;
 const number=key=>raw[key]!==''&&raw[key]!==undefined&&Number.isFinite(Number(raw[key]))&&Number(raw[key])>=0?String(Number(raw[key])):'';
 return {family:valid('family',['all','thinkers','discourse'],'all'),kind:valid('kind',['transcript','synthetic'],'transcript'),
  variant:valid('variant',lensVariants.map(v=>v[0]),'definition_only'),panel:valid('panel',['codebook','passages','matrix'],'codebook'),
  feature:String(raw.feature||'f11'),item:String(raw.item||''),model:String(raw.model||''),q:String(raw.q||''),
  sort:valid('sort',['probability','probability_asc','delta','words','sample'],'probability'),min:number('min'),max:number('max')};
}
function lensGo(change={}) {go({view:'discourse',lens:JSON.stringify(lensFilters({...state.lensFilters,...change}))});}
function lensRows(data,f) {
 const rows=data.samples.filter(s=>s.kind===f.kind&&(!f.model||s.model===f.model)&&(f.min===''||s.words>=Number(f.min))&&(f.max===''||s.words<=Number(f.max))&&(!f.q||[s.text,s.title,s.model_label].join(' ').toLowerCase().includes(f.q.toLowerCase())));
 const score=s=>s.probabilities[f.variant]?.[f.feature]??null;
 const delta=s=>{const a=s.probabilities.name_and_definition?.[f.feature],b=s.probabilities.definition_only?.[f.feature];return Number.isFinite(a)&&Number.isFinite(b)?a-b:null;};
 const metric=s=>f.sort==='words'?s.words:f.sort==='delta'?(delta(s)===null?null:Math.abs(delta(s))):score(s);
 if(f.sort!=='sample')rows.sort((a,b)=>{const x=metric(a),y=metric(b);return x===null?(y===null?0:1):y===null?-1:(f.sort==='probability_asc'?x-y:y-x);});
 return rows;
}
function lensSummary(rows,key,variant) {
 const vals=rows.map(s=>s.probabilities[variant]?.[key]).filter(Number.isFinite);
 const diffs=rows.filter(s=>Number.isFinite(s.probabilities.name_and_definition?.[key])&&Number.isFinite(s.probabilities.definition_only?.[key])).map(s=>s.probabilities.name_and_definition[key]-s.probabilities.definition_only[key]);
 return {n:vals.length,mean:vals.length?vals.reduce((a,b)=>a+b,0)/vals.length:null,candidates:vals.filter(v=>v>=.8).length,paired:diffs.length,delta:diffs.length?diffs.reduce((a,b)=>a+Math.abs(b),0)/diffs.length:null};
}
function lensProbability(p) {return Number.isFinite(p)?(100*p).toFixed(1)+'%':'—';}
function lensDelta(a,b) {return Number.isFinite(a)&&Number.isFinite(b)?((a-b)*100>=0?'+':'')+((a-b)*100).toFixed(1)+' pp':'—';}
async function loadLenses(raw={}) {
 const previousItem=state.lensFilters?.item;const version=++routeVersion;state.run=null;state.view='discourse';state.lensFilters=lensFilters(raw);
 const data=await api('/api/discourse');if(version!==routeVersion)return;state.lenses=data;
 renderSidebar();renderCompareTray();renderLenses();if(raw.item&&raw.item!==previousItem)$('#lens-selected')?.scrollIntoView({block:'start'});
}
function lensDetail(s,feature) {
 if(!s)return '<p class="source-note">Select a passage to read it and compare the three wordings.</p>';
 return `<article class="lens-detail"><div class="eyebrow">${s.kind==='synthetic'?'CODEX SYNTHETIC CONTROL':'FROZEN TRANSCRIPT PASSAGE'} · ${s.words} WORDS</div><h3>${esc(s.title)}</h3>${s.kind==='transcript'?`<p>${modelBadge(s.model)} ${s.source_current===false?'<strong>Source has changed; text below is the frozen version.</strong>':''}</p>`:`<p class="source-note">${esc(s.purpose)}</p>`}<p class="lens-text">${esc(s.text)}</p><div class="lens-scores">${lensVariants.map(([v,title])=>`<div><small>${title}</small><strong>${lensProbability(s.probabilities[v]?.[feature.id])}</strong><span>${esc(feature.label)}</span></div>`).join('')}</div>${s.kind==='transcript'?`<button class="button" data-lens-source="${esc(s.id)}">Open full conversation →</button>`:''}</article>`;
}
function renderLenses() {
 const d=state.lenses,f=state.lensFilters;
 if(d.status==='not_prepared'){$('#main').innerHTML=`<div class="content">${pageTop('Mind & discourse','Descriptive patterns across thinking, writing and discourse.')}<p>The assessment plan has not been prepared in this workspace.</p></div>`;return;}
 const features=d.spec.features.filter(x=>f.family==='all'||x.family===f.family);
 const feature=features.find(x=>x.id===f.feature)||features[0];f.feature=feature.id;
 const rows=lensRows(d,f),selected=rows.find(s=>s.id===f.item);const ex=d.execution;
 const models=[...new Set(d.samples.filter(s=>s.kind==='transcript').map(s=>s.model))];
 const th=t=>`<th scope="col">${t}</th>`;
 const choose=(key,label)=>`<button class="text-button" data-lens-feature="${esc(key)}">${esc(label)}</button>`;
 $('#main').innerHTML=`<div class="content lens-page">${pageTop('Mind & discourse','A descriptive profile of how a passage thinks, writes and speaks.')}
 <div class="lens-intro"><div><span class="eyebrow">${d.status==='prepared'?'PREPARED · AWAITING DISPATCH CONFIRMATION':d.status==='complete'?'EXPLORATORY CLASSIFIER · COMPLETED':'EXPLORATORY CLASSIFIER · '+esc(d.status.toUpperCase())}</span><p><strong>16 thinkers and writers. 11 discourse practices.</strong> Compare familiar labels with explicit definitions. Several patterns can apply, or none. Your review evaluates the classifier’s coherence and usefulness.</p><p class="source-note">These are provisional operational lenses. A probability is JEV’s yes-confidence for a question, not a degree of similarity, authorship or quality score. Missing assessments stay unknown.</p></div><a class="button" href="/api/discourse/export" download>Export plan & results</a></div>
 <div class="lens-metrics"><div><strong>48 + 12</strong><span>transcript passages + synthetic controls</span></div><div><strong>${num(ex.complete)} / ${num(ex.planned)}</strong><span>completed requests · 3 wordings per text</span></div><div><strong>27</strong><span>independent features per request</span></div><div><strong>$${Number(ex.known_cost_usd).toFixed(5)}</strong><span>reported cost · $2 total ceiling</span></div></div>
 ${ex.unknown_reserved_usd?`<p class="source-note">Additional unknown-cost reserve: $${ex.unknown_reserved_usd.toFixed(6)}.</p>`:''}
 <form id="lens-filters" class="lens-filters"><label>Feature family<select name="family">${[['all','All 27 features'],['thinkers','Thinkers & writers'],['discourse','Discourse practices']].map(([v,t])=>option(v,t,f.family)).join('')}</select></label><label>Feature<select name="feature">${features.map(x=>option(x.id,x.label,f.feature)).join('')}</select></label><label>Assessment wording<select name="variant">${lensVariants.map(([v,t])=>option(v,t,f.variant)).join('')}</select></label><label>Evidence<select name="kind">${option('transcript','Transcript passages',f.kind)}${option('synthetic','Codex synthetic controls',f.kind)}</select></label><label>Source model<select name="model" ${f.kind==='synthetic'?'disabled':''}>${option('','All sampled models',f.model)}${models.map(m=>option(m,short(m),f.model)).join('')}</select></label><label>Minimum words<input name="min" type="number" min="0" value="${f.min}"></label><label>Maximum words<input name="max" type="number" min="0" value="${f.max}"></label><label>Find in passages<input name="q" type="search" value="${esc(f.q)}"></label><button class="button" type="submit">Apply</button><button class="quiet" type="button" data-lens-reset>Reset</button></form>
 <div class="lens-tabs">${[['codebook','Codebook & overview'],['passages','Passage comparison'],['matrix','Profile matrix']].map(([v,t])=>`<button class="button ${f.panel===v?'primary':''}" data-lens-panel="${v}" aria-pressed="${f.panel===v}">${t}</button>`).join('')}<span class="source-note">${rows.length} ${f.kind==='transcript'?'transcript passages':'synthetic controls'} in view</span></div>
 <section class="lens-definition"><div class="eyebrow">${feature.family==='thinkers'?'THINKER / WRITER LENS':'DISCOURSE PRACTICE'}</div><h2>${esc(feature.label)}</h2><p>${esc(feature.definition)}</p><details><summary>Exact assessment question · ${esc(lensVariants.find(v=>v[0]===f.variant)[1])}</summary><p class="lens-question">${esc(d.conditions[f.variant][feature.id].instructions)}</p></details></section>
 ${f.panel==='codebook'?`<div class="lens-table-wrap"><table class="lens-table"><caption>Overview for the ${rows.length} filtered ${f.kind==='transcript'?'transcript passages':'synthetic controls'}. ≥80% is a browsing threshold. Paired differences compare names + definitions with definitions only.</caption><thead><tr>${['Feature','Observed','Mean yes probability','≥80%','Mean |label difference|','Paired n'].map(th).join('')}</tr></thead><tbody>${features.map(x=>{const v=lensSummary(rows,x.id,f.variant);return `<tr class="${x.id===f.feature?'selected':''}"><td>${choose(x.id,x.label)}</td><td>${v.n} / ${rows.length}</td><td>${lensProbability(v.mean)}</td><td>${v.n?v.candidates:'—'}</td><td>${v.delta===null?'—':(v.delta*100).toFixed(1)+' pp'}</td><td>${v.paired}</td></tr>`;}).join('')}</tbody></table></div>`:''}
 ${f.panel==='passages'?`<label class="lens-sort">Sort passages<select id="lens-sort">${[['probability','Highest probability'],['probability_asc','Lowest probability'],['delta','Largest label difference'],['words','Most words'],['sample','Frozen sample order']].map(([v,t])=>option(v,t,f.sort)).join('')}</select></label><div class="lens-table-wrap"><table class="lens-table"><caption>${esc(feature.label)} · all three wordings side by side. Label difference = names + definitions minus definitions only.</caption><thead><tr>${['Passage','Words','Names only','Definitions only','Names + definitions','Label difference'].map(th).join('')}</tr></thead><tbody>${rows.map(s=>`<tr class="${s.id===f.item?'selected':''}"><td><button class="text-button" data-lens-item="${esc(s.id)}">${esc(s.kind==='transcript'?s.model_label:s.title)}<small>${esc(s.text.slice(0,115))}…</small></button></td><td>${s.words}</td>${['name_only','definition_only','name_and_definition'].map(v=>`<td>${lensProbability(s.probabilities[v]?.[f.feature])}</td>`).join('')}<td>${lensDelta(s.probabilities.name_and_definition?.[f.feature],s.probabilities.definition_only?.[f.feature])}</td></tr>`).join('')}</tbody></table></div>`:''}
 ${f.panel==='matrix'?`<div class="lens-table-wrap"><table class="lens-table lens-matrix"><caption>${esc(lensVariants.find(v=>v[0]===f.variant)[1])} · yes-probability 0 → 100%. Select any cell to read the exact passage and definition. — = unassessed.</caption><thead><tr>${th('Passage')}${features.map(x=>th(choose(x.id,x.label))).join('')}</tr></thead><tbody>${rows.map((s,i)=>`<tr><th scope="row"><button class="text-button" data-lens-item="${esc(s.id)}">${i+1}. ${esc(s.kind==='transcript'?s.model_label:s.title)}<small>${s.words} words</small></button></th>${features.map(x=>{const p=s.probabilities[f.variant]?.[x.id];return `<td><button data-lens-cell="${esc(s.id)}" data-feature="${esc(x.id)}" aria-label="${esc(x.label)}, passage ${i+1}, ${lensProbability(p)}" style="${Number.isFinite(p)?`background:rgba(116,85,153,${p*.75});color:${p>.65?'white':'#2d2735'}`:''}">${Number.isFinite(p)?Math.round(p*100):'—'}</button></td>`;}).join('')}</tr>`).join('')}</tbody></table></div>`:''}
 <div id="lens-selected">${lensDetail(selected,feature)}</div>
 <details class="lens-method"><summary>Scope, selection and interpretation</summary><p>${esc(d.selection.method)}</p><p>Word bands: ${Object.entries(d.word_band_counts).map(([b,n])=>esc(b)+': '+n).join(' · ')}.</p><p>${esc(d.interpretation)}</p><p>${esc(d.review_guide)}</p><p>Plan SHA-256: <code>${esc(d.plan_sha256)}</code></p></details></div>`;
}
document.addEventListener('submit',e=>{if(e.target.id!=='lens-filters')return;e.preventDefault();const f=Object.fromEntries(new FormData(e.target));lensGo({...f,item:''});});
document.addEventListener('change',e=>{if(e.target.id==='lens-sort')lensGo({sort:e.target.value});else if(e.target.closest('#lens-filters')&&e.target.tagName==='SELECT'){const f=Object.fromEntries(new FormData($('#lens-filters')));lensGo({...f,model:f.kind==='synthetic'?'':f.model,item:''});}});
document.addEventListener('click',e=>{
 const el=e.target.closest('[data-lens-feature],[data-lens-item],[data-lens-cell],[data-lens-panel],[data-lens-source],[data-lens-reset]');if(!el)return;
 if(el.hasAttribute('data-lens-feature'))lensGo({feature:el.dataset.lensFeature});
 else if(el.hasAttribute('data-lens-item'))lensGo({item:el.dataset.lensItem});
 else if(el.hasAttribute('data-lens-cell'))lensGo({item:el.dataset.lensCell,feature:el.dataset.feature});
 else if(el.hasAttribute('data-lens-panel'))lensGo({panel:el.dataset.lensPanel});
 else if(el.hasAttribute('data-lens-reset'))go({view:'discourse'});
 else {const s=state.lenses.samples.find(x=>x.id===el.dataset.lensSource);go({run:s.run_id,message:s.message_id});}
});
if(typeof module!=='undefined')module.exports={lensFilters,lensRows,lensSummary,lensProbability,lensDelta};
