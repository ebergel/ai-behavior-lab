'use strict';
let assessmentData=null, assessmentFilter='all';
const assessmentCheckNames={system:'System instruction',user:'User instruction',history:'History recall',json:'JSON format'};
function assessmentMark(check){
 if(check.match===true)return ['match','Matched'];
 if(check.match===false)return ['mismatch','Did not match'];
 return check.status==='invalid'?['error','API / format error']:check.status==='cap'?['error','Capped']:['pending','Not tested'];
}
function assessmentStatus(p){
 if(p.availability!=='eligible')return 'Route unavailable';
 if(p.errors.length)return 'Connection issue';
 if(!p.responses)return 'Not dispatched';
 return p.valid_messages===8?'Sample complete':'Partial sample';
}
function assessmentCard(p){
 const self=p.runs.find(r=>r.kind==='selfplay');
 return `<article class="assessment-card"><div class="card-top"><span class="eyebrow">${esc(p.model.split('/')[0])}</span><span class="pill ${p.errors.length?'amber':''}">${esc(assessmentStatus(p))}</span></div>
 <h2>${esc(p.name.replace(' (free)',''))}</h2><div class="assessment-model-id">${esc(p.model)}</div>
 <p class="assessment-description">${esc(p.description)}</p>
 <dl class="assessment-facts"><div><dt>Route at freeze</dt><dd>${esc(p.route?.provider_name||'No eligible route')}</dd></div><div><dt>Context advertised</dt><dd>${p.route?num(p.route.context_length)+' tokens':'Unavailable'}</dd></div><div><dt>API replies / valid messages</dt><dd>${p.responses} / ${p.valid_messages}</dd></div><div><dt>Median request time</dt><dd>${p.median_seconds===null?'Not measured':p.median_seconds.toFixed(2)+' s'+(p.errors.length?' · errors included':'')}</dd></div></dl>
 ${p.errors.map(e=>`<div class="assessment-error"><strong>HTTP ${esc(e.code)}</strong> ${esc(e.message)}${e.limit_source?'<small>'+esc(e.limit_source.replaceAll('_',' '))+'</small>':''}<button class="text-button" data-action="assessment-open" data-id="${e.run_id}">Inspect saved request & response ${icon('arrow',12)}</button></div>`).join('')}
 <div class="assessment-checks">${Object.keys(assessmentCheckNames).map(k=>{const c=p.checks[k];const [style,label]=assessmentMark(c);return `<button class="assessment-check ${style}" data-action="assessment-open" data-id="${c.run_id}"><span>${assessmentCheckNames[k]}</span><strong>${label}</strong></button>`;}).join('')}</div>
 <div class="assessment-sample"><span class="eyebrow">OPEN CONVERSATION · ${self.messages} / 4 REPLIES</span><p>${esc(self.preview||'No self-play text recorded. This is missing behavioral evidence.')}</p><button class="button" data-action="assessment-open" data-id="${self.id}">${self.messages?'Read & annotate':'View planned conversation'} ${icon('arrow',12)}</button></div></article>`;
}
function renderAssessments(){
 const data=assessmentData;
 $('#main').innerHTML=`<div class="content assessment-page">${pageTop('Model assessment','Meet the participants before choosing an experiment.')}
 <div class="assessment-intro"><div><span class="eyebrow">A FIELD GUIDE, ONE SAVED SAMPLE AT A TIME</span><p>Explore what each model says, how it follows the setting, and whether its service works reliably. Every check opens in the transcript reader, with the exact inputs and response beside it.</p></div><span class="assessment-intro-mark">Aa<span>→</span>Aa</span></div>
 ${data.assessments.length?[...data.assessments].reverse().map(a=>{
 const profiles=a.profiles.filter(p=>assessmentFilter==='all'||(assessmentFilter==='issues'?p.errors.length||p.availability!=='eligible':p.valid_messages>0));
 return `<section class="assessment-batch"><div class="assessment-batch-heading"><div><span class="eyebrow">FREE OPENROUTER SCREEN · ${esc(stamp(a.date))}</span><h2>${a.profiles.length} candidates. One shared protocol.</h2></div><button class="button" data-action="assessment-protocol" data-id="${a.id}">${icon('document',14)} Protocol & source</button></div>
 <div class="assessment-metrics">${[[a.profiles.length,'Candidates'],[a.calls,'Requests sent'],[a.profiles.reduce((n,p)=>n+p.valid_messages,0),'Valid visible replies'],['$0','Allowed price']].map(([n,l])=>`<div><strong>${esc(n)}</strong><span>${l}</span></div>`).join('')}</div>
 <p class="source-note">${a.finished?'Batch closed':'Batch in progress'} · ${a.missing_cost?`${a.missing_cost} API responses have no cost accounting; the $0 figure is the request ceiling.`:'Provider-reported cost: $'+Number(a.cost_usd).toFixed(6)+'.'} Model descriptions below come from the frozen OpenRouter catalog.</p>
 ${a.reading?`<div class="assessment-reading"><div class="eyebrow">SAVED FINDINGS · ${esc(a.reading.author)}</div><p>${esc(a.reading.summary)}</p>${a.reading.findings.map(f=>`<details><summary>${esc(f.title)}</summary><p>${esc(f.text)}</p>${(f.evidence||[]).map(q=>`<blockquote>${esc(q.quote)}</blockquote><button class="text-button" data-action="assessment-open" data-id="${q.run_id}" data-message="${q.message_id}">Read source passage ${icon('arrow',12)}</button>`).join('')}</details>`).join('')}<small>${esc(a.reading.method)}</small></div>`:''}
 <div class="assessment-toolbar"><span class="eyebrow">BROWSE CANDIDATES</span><div role="group" aria-label="Filter assessed models">${[['all','All candidates'],['issues','Connection issues'],['replies','With valid replies']].map(([k,l])=>`<button class="button ${assessmentFilter===k?'primary':''}" data-action="assessment-filter" data-filter="${k}">${l}</button>`).join('')}</div></div>
 ${profiles.length?`<div class="assessment-grid">${profiles.map(assessmentCard).join('')}</div>`:'<div class="empty"><h2>No candidates in this view.</h2><p>Unavailable or undispatched replies remain unknown.</p></div>'}
 <details class="assessment-method"><summary>What does this screen tell us?</summary><p>${esc(a.plan.scope)}</p><p>${esc(a.plan.selection)}</p><p>“Matched” means an exact expected response under a declared rule. One success or failure is not a general capability score. Four replies cannot establish an attractor or its absence. Open a sample to add personal notes, tags, or passages to a research collection.</p></details></section>`;
 }).join(''):'<div class="empty"><h2>No model screens recorded yet.</h2></div>'}
 ${data.prior_checks.length?`<section class="assessment-prior"><div class="eyebrow">EARLIER CLOUD CONNECTION CHECKS</div><h2>GPT-4o mini & Claude Haiku 4.5</h2><p>Seven technical calls preceded this free-model screen. The larger paid comparison is held; full GPT-4o is deferred. These checks are not self-play samples.</p><div>${data.prior_checks.map(r=>`<button class="report-link" data-action="assessment-open" data-id="${r.id}">${icon('message',15)}<span>${esc(r.title)}<small>${esc(r.models.map(short).join(' / '))}</small></span>${icon('arrow',12)}</button>`).join('')}</div></section>`:''}
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
 dialog('Frozen assessment protocol',`<p>${esc(a.plan.question)}</p><p>${esc(a.plan.scope)}</p><h3>Conversation prompt</h3><p class="prompt-text">${esc(a.plan.prompt)}</p><h3>Execution rules</h3><p>${esc(a.plan.failure_policy)}</p><p>${esc(a.plan.seed_policy)}</p><details><summary>Complete plan & source fingerprints</summary><pre class="assessment-json">${esc(JSON.stringify({plan:a.plan,source:a.source},null,2))}</pre></details>`,'',true);
 }
 }catch(e){toast(e.message);}
});
