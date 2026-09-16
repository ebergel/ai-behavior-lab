'use strict';
let assessmentData=null, assessmentFilter='all', assessmentBatchId=null;
const assessmentCheckNames={system:'System instruction',user:'User instruction',history:'History recall',json:'JSON format'};
function assessmentReading(a){
 return a.reading?`<div class="assessment-reading"><div class="eyebrow">SAVED FINDINGS · ${esc(a.reading.author)}</div><p>${esc(a.reading.summary)}</p>${a.reading.findings.map(f=>`<details><summary>${esc(f.title)}</summary><p>${esc(f.text)}</p>${(f.evidence||[]).map(q=>`<blockquote>${esc(q.quote)}</blockquote><button class="text-button" data-action="assessment-open" data-id="${q.run_id}" data-message="${q.message_id}">Read source passage ${icon('arrow',12)}</button>`).join('')}</details>`).join('')}<small>${esc(a.reading.method)}</small></div>`:'';
}
function framingScreen(a){
 const review=a.reading?.root_reviews||{};
 const cells=Object.values(a.roots.reduce((counts,r)=>{const key=(r.candidate??0)+'/'+r.condition;counts[key]=(counts[key]||0)+1;return counts;},{}));
 const perCell=cells.length&&cells.every(n=>n===cells[0])?(cells[0]===1?'One fresh root':'Two fresh roots')+' per condition per model':a.roots.length+' fresh roots';
 return `<section class="assessment-batch"><div class="assessment-batch-heading"><div><span class="eyebrow">FRAMING COMPARISON · ${esc(stamp(a.date))}</span><h2>${a.plan.candidates.length===1?'One model. Two conversation settings.':'Two models. The same conversation settings.'}</h2></div><button class="button" data-action="assessment-protocol" data-id="${a.id}">${icon('document',14)} Protocol & source</button></div>
 <div class="assessment-metrics">${[[a.roots.length,'Fresh conversations'],[a.calls+' / '+a.plan.max_calls,'Requests sent'],[a.roots.reduce((n,r)=>n+r.valid,0),'Valid visible replies'],['$'+Number(a.plan.budget_usd).toFixed(2),'Batch budget ceiling']].map(([n,l])=>`<div><strong>${esc(n)}</strong><span>${l}</span></div>`).join('')}</div>
 <p class="source-note">${a.finished?'Batch closed':'Batch in progress'} · ${a.missing_cost||a.unresolved?'Some dispatched calls lack cost accounting.':'Provider-reported cost: $'+Number(a.cost_usd).toFixed(6)+'.'} ${perCell}, up to ${a.plan.messages_per_root} messages each. Codex readings are exploratory.</p>
 <div class="framing-contrast"><div><span class="eyebrow">SHARED PROMPT</span><p>${esc(a.plan.prompts.anonymous)}</p></div><div><span class="eyebrow">ADDED IN MIRROR</span><p>${esc(a.plan.prompts.mirror.slice(a.plan.prompts.anonymous.length).trim())}</p><small>These two cues are tested together.</small></div></div>
 ${assessmentReading(a)}
 ${a.reading?.collection_id?`<button class="button" data-action="study-open" data-id="${esc(a.reading.collection_id)}">${icon('folder',14)} Open the research collection ${icon('arrow',12)}</button>`:''}
 <div class="assessment-toolbar"><span class="eyebrow">ALL ${a.roots.length} CONVERSATIONS · CLICK A MESSAGE TO READ</span></div>
 <div class="assessment-grid">${[...a.roots].sort((r,s)=>(r.candidate??0)-(s.candidate??0)||r.condition.localeCompare(s.condition)||r.replicate-s.replicate).map(r=>`<article class="assessment-card"><div class="card-top"><span class="eyebrow">${esc(r.condition.toUpperCase())} · REPLICATE ${r.replicate}</span><button class="compare-add ${state.compare.includes(r.run_id)?'selected':''}" data-action="compare-add" data-id="${r.run_id}" data-title="${esc(r.title)}" aria-label="Compare ${esc(r.title)}">${icon('compare',15)}</button></div><h2>${esc(r.title)}</h2><div class="assessment-model-id">${esc(r.model)}</div>
 <p class="framing-root-summary">${esc(review[r.id]?.trajectory||r.preview||'No visible reply recorded.')}</p>
 ${review[r.id]?`<dl class="assessment-facts">${[['Current-exchange discussion',review[r.id].metaconversation],['AI experience question',review[r.id].experience_question],['Explicit nonseparation',review[r.id].nonseparation]].map(([l,v])=>`<div><dt>${l}</dt><dd>${esc(v)}</dd></div>`).join('')}</dl>`:''}
 <div class="framing-turns">${r.messages.map(m=>`<button class="${esc(m.status)}" data-action="assessment-open" data-id="${r.run_id}" data-message="${m.id}" title="Message ${m.turn} · ${esc(m.status)}${m.words===null?'':' · '+m.words+' words'}" aria-label="${esc(r.title)}, message ${m.turn}">${m.turn}</button>`).join('')}</div>
 <p class="source-note">${r.visible} / 12 visible · ${r.caps} capped · ${r.word_overruns} over 150 words · ${r.cost_usd===null?'cost incomplete':'$'+Number(r.cost_usd).toFixed(5)}${r.median_seconds===null?'':' · '+r.median_seconds.toFixed(2)+' s median request'}</p><button class="button" data-action="assessment-open" data-id="${r.run_id}">Read & annotate ${icon('arrow',12)}</button></article>`).join('')}</div>
 <details class="assessment-method"><summary>What can this comparison tell us?</summary><p>${esc(a.plan.scope)}</p><p>${esc(a.plan.contrast)}</p><p>${esc(a.plan.order)}</p><p>${esc(a.plan.seed_policy)}</p></details></section>`;
}
function assessmentMark(check){
 if(check.match===true)return ['match','Matched'];
 if(check.match===false)return ['mismatch','Did not match'];
 return check.status==='invalid'?['error','API / format error']:check.status==='cap'?['error','Capped']:['pending','Not tested'];
}
function assessmentStatus(p){
 if(p.availability!=='eligible')return 'Route unavailable';
 if(p.errors.length)return 'Connection issue';
 if(!p.responses)return 'Not dispatched';
 return p.valid_messages===(p.planned_calls??8)?'Sample complete':'Partial sample';
}
function assessmentCard(p){
 const self=p.runs.find(r=>r.kind==='selfplay');
 return `<article class="assessment-card"><div class="card-top"><span class="eyebrow">${esc(p.model.split('/')[0])}</span><span class="pill ${p.errors.length?'amber':''}">${esc(assessmentStatus(p))}</span></div>
 <h2>${esc(p.name.replace(' (free)',''))}</h2><div class="assessment-model-id">${esc(p.model)}</div>
 <p class="assessment-description">${esc(p.description)}</p>
 <dl class="assessment-facts"><div><dt>Route at freeze</dt><dd>${esc(p.route?.provider_name||'No eligible route')}</dd></div><div><dt>Context advertised</dt><dd>${p.route?num(p.route.context_length)+' tokens':'Unavailable'}</dd></div><div><dt>API replies / valid messages</dt><dd>${p.responses} / ${p.valid_messages}</dd></div><div><dt>Median request time</dt><dd>${p.median_seconds===null?'Not measured':p.median_seconds.toFixed(2)+' s'+(p.errors.length?' · errors included':'')}</dd></div></dl>
 ${p.errors.map(e=>`<div class="assessment-error"><strong>HTTP ${esc(e.code)}</strong> ${esc(e.message)}${e.limit_source?'<small>'+esc(e.limit_source.replaceAll('_',' '))+'</small>':''}<button class="text-button" data-action="assessment-open" data-id="${e.run_id}">Inspect saved request & response ${icon('arrow',12)}</button></div>`).join('')}
 <div class="assessment-checks">${Object.keys(assessmentCheckNames).map(k=>{const c=p.checks[k];const [style,label]=assessmentMark(c);return `<button class="assessment-check ${style}" data-action="assessment-open" data-id="${c.run_id}"><span>${assessmentCheckNames[k]}${c.source==='prior'?' · earlier batch':''}</span><strong>${label}</strong></button>`;}).join('')}</div>
 <div class="assessment-sample"><span class="eyebrow">OPEN CONVERSATION · ${self.messages} / 4 REPLIES</span>${p.selfplay_word_overruns?`<p class="source-note">${p.selfplay_word_overruns} replies exceeded the 150-word instruction. Full text preserved.</p>`:''}<p>${esc(self.preview||'No self-play text recorded. This is missing behavioral evidence.')}</p><button class="button" data-action="assessment-open" data-id="${self.id}">${self.messages?'Read & annotate':'View planned conversation'} ${icon('arrow',12)}</button></div></article>`;
}
function renderAssessments(){
 const data=assessmentData;
 const screens=[...data.assessments].sort((a,b)=>b.date.localeCompare(a.date));
 const selected=screens.find(a=>a.id===assessmentBatchId)||screens[0];
 if(selected)assessmentBatchId=selected.id;
 $('#main').innerHTML=`<div class="content assessment-page">${pageTop('Model assessment','Meet the participants before choosing an experiment.')}
 <div class="assessment-intro"><div><span class="eyebrow">A FIELD GUIDE, ONE SAVED SAMPLE AT A TIME</span><p>Explore what each model says, how it follows the setting, and whether its service works reliably. Every check opens in the transcript reader, with the exact inputs and response beside it.</p></div><span class="assessment-intro-mark">Aa<span>→</span>Aa</span></div>
 ${screens.length?`<div class="assessment-toolbar"><label class="eyebrow" for="assessment-batch">SAVED SCREENS · ${screens.length}</label><select id="assessment-batch" aria-label="Choose assessment batch">${screens.map((a,i)=>`<option value="${esc(a.id)}" ${a.id===assessmentBatchId?'selected':''}>${i===0?'Latest · ':''}${esc(a.plan.title||'Assessment '+a.plan.schema.split('/').pop())} · ${esc(a.date.replace('T',' ').slice(0,19))} UTC</option>`).join('')}</select></div>`:''}
 ${selected?[selected].map(a=>{
 if(a.screen_type==='framing')return framingScreen(a);
 const profiles=a.profiles.filter(p=>assessmentFilter==='all'||(assessmentFilter==='issues'?p.errors.length||p.availability!=='eligible':p.valid_messages>0));
 return `<section class="assessment-batch"><div class="assessment-batch-heading"><div><span class="eyebrow">FREE OPENROUTER SCREEN · ${esc(stamp(a.date))}</span><h2>${a.profiles.length} candidates. One shared protocol.</h2></div><button class="button" data-action="assessment-protocol" data-id="${a.id}">${icon('document',14)} Protocol & source</button></div>
 <div class="assessment-metrics">${[[a.profiles.length,'Candidates'],[a.calls,'Requests sent'],[a.profiles.reduce((n,p)=>n+p.valid_messages,0),'Valid visible replies'],['$0','Allowed price']].map(([n,l])=>`<div><strong>${esc(n)}</strong><span>${l}</span></div>`).join('')}</div>
 <p class="source-note">${a.finished?'Batch closed':'Batch in progress'} · ${a.missing_cost?`${a.missing_cost} API response${a.missing_cost===1?' has':'s have'} no cost accounting; the $0 figure is the request ceiling.`:'Provider-reported cost: $'+Number(a.cost_usd).toFixed(6)+'.'} Model descriptions below come from the frozen OpenRouter catalog.</p>
 ${a.reading?`<div class="assessment-reading"><div class="eyebrow">SAVED FINDINGS · ${esc(a.reading.author)}</div><p>${esc(a.reading.summary)}</p>${a.reading.findings.map(f=>`<details><summary>${esc(f.title)}</summary><p>${esc(f.text)}</p>${(f.evidence||[]).map(q=>`<blockquote>${esc(q.quote)}</blockquote><button class="text-button" data-action="assessment-open" data-id="${q.run_id}" data-message="${q.message_id}">Read source passage ${icon('arrow',12)}</button>`).join('')}</details>`).join('')}<small>${esc(a.reading.method)}</small></div>`:''}
 <div class="assessment-toolbar"><span class="eyebrow">BROWSE CANDIDATES</span><div role="group" aria-label="Filter assessed models">${[['all','All candidates'],['issues','Connection issues'],['replies','With valid replies']].map(([k,l])=>`<button class="button ${assessmentFilter===k?'primary':''}" data-action="assessment-filter" data-filter="${k}">${l}</button>`).join('')}</div></div>
 ${profiles.length?`<div class="assessment-grid">${profiles.map(assessmentCard).join('')}</div>`:'<div class="empty"><h2>No candidates in this view.</h2><p>Unavailable or undispatched replies remain unknown.</p></div>'}
 <details class="assessment-method"><summary>What does this screen tell us?</summary><p>${esc(a.plan.scope)}</p><p>${esc(a.plan.selection)}</p><p>“Matched” means an exact expected response under a declared rule. One success or failure is not a general capability score. Four replies cannot establish an attractor or its absence. Open a sample to add personal notes, tags, or passages to a research collection.</p></details></section>`;
 }).join(''):'<div class="empty"><h2>No model screens recorded yet.</h2></div>'}
 ${data.prior_checks.length?`<section class="assessment-prior"><div class="eyebrow">EARLIER CLOUD CONNECTION CHECKS</div><h2>GPT-4o mini & Claude Haiku 4.5</h2><p>Seven earlier technical calls checked these two models. They are separate from the later participant conversations. The original thirty-message comparison remains held. Later participant screens appear in the selector above.</p><div>${data.prior_checks.map(r=>`<button class="report-link" data-action="assessment-open" data-id="${r.id}">${icon('message',15)}<span>${esc(r.title)}<small>${esc(r.models.map(short).join(' / '))}</small></span>${icon('arrow',12)}</button>`).join('')}</div></section>`:''}
 </div>`;
 renderSidebar();renderCompareTray();
}
async function loadAssessments(){
 const version=++state.request;state.run=null;state.view='assessment';state.activeStudy=null;
 const data=await api('/api/assessments');if(version!==state.request)return;
 assessmentData=data;renderAssessments();
}
document.addEventListener('click',async event=>{
 const el=event.target.closest('[data-action^="assessment-"]');if(!el)return;
 try{
 if(el.dataset.action==='assessment-filter'){assessmentFilter=el.dataset.filter;renderAssessments();}
 else if(el.dataset.action==='assessment-open'){state.view='assessment';go({run:el.dataset.id,fromAssessment:'1',...(el.dataset.message?{message:el.dataset.message}:{})});}
 else if(el.dataset.action==='assessment-protocol'){
 const a=assessmentData.assessments.find(a=>a.id===el.dataset.id);
 dialog('Frozen assessment protocol',`<p>${esc(a.plan.question)}</p><p>${esc(a.plan.scope)}</p>${Object.entries(a.plan.prompts||{'Conversation':a.plan.prompt}).map(([k,p])=>`<h3>${esc(k)} prompt</h3><p class="prompt-text">${esc(p)}</p>`).join('')}<h3>Execution rules</h3><p>${esc(a.plan.failure_policy)}</p><p>${esc(a.plan.seed_policy)}</p><details><summary>Complete plan & source fingerprints</summary><pre class="assessment-json">${esc(JSON.stringify({plan:a.plan,source:a.source},null,2))}</pre></details>`,'',true);
 }
 }catch(e){toast(e.message);}
});
document.addEventListener('change',event=>{
 if(event.target.id==='assessment-batch'){assessmentBatchId=event.target.value;assessmentFilter='all';renderAssessments();}
});
