'use strict';
const jevModes={all:'All passages',candidate:'JEV candidates',semantic_only:'JEV candidate · no phrase match',literal_only:'Phrase match · JEV unlikely',uncertain:'JEV uncertain',unreviewed:'Awaiting review',disagreement:'Reviewer disagrees',pending:'Not assessed',outside:'Outside dictionary'};
const jevTopicColumns=[['title','Topic'],['scored','Scored'],['candidate','Candidates'],['share','Candidate share'],['mean','Mean probability'],['median','Median probability'],['uncertain','Uncertain'],['semantic_only','No phrase hit'],['reviewed','Saved readings']];
function jevProbability(row,topic){return row.status==='complete'?row.answers?.['topic_'+topic]?.noul??null:null;}
function jevDecision(p,thresholds){return p===null?'Not assessed':p>=thresholds.candidate?'Candidate':p<=thresholds.unlikely?'Unlikely':'Uncertain';}
function jevMatch(row,topic,mode,review,thresholds){
 const p=jevProbability(row,topic),literal=!!row.literal?.[topic]?.length,baseline=Array.isArray(row.literal?.[topic]);
 if(mode==='candidate')return p!==null&&p>=thresholds.candidate;
 if(mode==='semantic_only')return baseline&&!literal&&p!==null&&p>=thresholds.candidate;
 if(mode==='literal_only')return literal&&p!==null&&p<=thresholds.unlikely;
 if(mode==='uncertain')return p!==null&&p>thresholds.unlikely&&p<thresholds.candidate;
 if(mode==='pending')return p===null;
 if(mode==='unreviewed')return !review;
 if(mode==='outside')return row.status==='complete'&&(row.answers?.outside_dictionary?.noul??row.answers?.topic_coverage_outside?.noul)>=thresholds.candidate;
 if(mode==='disagreement')return !!review&&p!==null&&((review.label==='absent'&&p>=thresholds.candidate)||(review.label==='present'&&p<=thresholds.unlikely));
 return true;
}
function jevBin(p){return typeof p==='number'&&Number.isFinite(p)&&p>=0&&p<=1?Math.min(9,Math.floor(p*10)):-1;}
function jevBinLabel(bin){return `${bin*10}–${bin===9?'':'<'}${(bin+1)*10}%`;}
function jevDistribution(rows,topic){
 const bins=Array(10).fill(0),values=[];
 for(const row of rows){const p=jevProbability(row,topic),bin=jevBin(p);if(bin>=0){bins[bin]++;values.push(p);}}
 values.sort((a,b)=>a-b);const n=values.length;
 return {bins,assessed:n,excluded:rows.length-n,mean:n?values.reduce((a,b)=>a+b,0)/n:null,median:n?(values[Math.floor((n-1)/2)]+values[Math.floor(n/2)])/2:null};
}
function jevSortRows(rows,topic,sort){
 const sorted=[...rows];
 if(sort==='probability'||sort==='probability_asc')sorted.sort((a,b)=>{
  const x=jevProbability(a,topic),y=jevProbability(b,topic),xm=jevBin(x)<0,ym=jevBin(y)<0;
  if(xm||ym)return xm===ym?0:xm?1:-1;
  return sort==='probability_asc'?x-y:y-x;
 });
 if(sort==='title')sorted.sort((a,b)=>a.run_title.localeCompare(b.run_title)||a.turn-b.turn);
 return sorted;
}
function jevFilters(params){
 const blind=params.get('blind')==='1',sort=params.get('sort'),bin=params.get('bin')||'';
 return {batch:params.get('batch')||'',topic:params.get('topic')||'',mode:blind?'all':Object.hasOwn(jevModes,params.get('mode'))?params.get('mode'):'all',q:params.get('q')||'',sort:['order','probability','probability_asc','title'].includes(sort)&&!(blind&&sort.startsWith('probability'))?sort:'order',bin:!blind&&/^[0-9]$/.test(bin)?bin:'',page:Math.max(0,Number(params.get('page'))||0),item:params.get('item')||'',blind,
  overview:params.get('overview')==='list'?'list':'cards',group:params.get('group')||'all',topic_q:params.get('topic_q')||'',topic_sort:blind?'title':jevTopicColumns.some(([key])=>key===params.get('topic_sort'))?params.get('topic_sort'):'candidate',topic_dir:blind&&params.get('topic_sort')!=='title'?'asc':params.get('topic_dir')==='asc'?'asc':'desc'};
}
function jevTopicMetrics(data){
 return data.plan.topics.map(id=>{
  const entry=data.plan.dictionary.find(t=>t.id===id),dist=jevDistribution(data.rows,id);
  const assessed=data.rows.filter(r=>jevBin(jevProbability(r,id))>=0);
  const candidates=assessed.filter(r=>jevProbability(r,id)>=data.plan.thresholds.candidate);
  const itemIds=new Set(data.rows.map(r=>r.id));
  return {id,title:entry.title,definition:entry.definition,group:entry.group||'legacy',scored:dist.assessed,
   candidate:dist.assessed?candidates.length:null,share:dist.assessed?candidates.length/dist.assessed:null,
   mean:dist.mean,median:dist.median,uncertain:dist.assessed?assessed.filter(r=>jevProbability(r,id)>data.plan.thresholds.unlikely&&jevProbability(r,id)<data.plan.thresholds.candidate).length:null,
   semantic_only:dist.assessed&&assessed.some(r=>Array.isArray(r.literal?.[id]))?candidates.filter(r=>Array.isArray(r.literal?.[id])&&!r.literal[id].length).length:null,
   reviewed:new Set(data.reviews.filter(r=>r.topic_id===id&&itemIds.has(r.item_id)).map(r=>r.item_id)).size};
 });
}
function jevSortTopics(rows,key,direction){
 return [...rows].sort((a,b)=>{
  const x=a[key],y=b[key];if(x==null||y==null)return x==null&&y==null?a.title.localeCompare(b.title):x==null?1:-1;
  const order=typeof x==='number'?x-y:String(x).localeCompare(String(y));
  return (direction==='asc'?order:-order)||a.title.localeCompare(b.title)||a.id.localeCompare(b.id);
 });
}
function jevTopicOverview(data,filters){
 const all=jevTopicMetrics(data),query=filters.topic_q.trim().toLowerCase(),matching=all.filter(t=>(filters.group==='all'||t.group===filters.group)&&(!query||[t.title,t.definition].join(' ').toLowerCase().includes(query)));
 const items=filters.overview==='list'?jevSortTopics(matching,filters.topic_sort,filters.topic_dir):matching;
 const percent=p=>p===null?'—':(p*100).toFixed(1)+'%';
 const cell=(t,key)=>{
  if(filters.blind&&!['scored','reviewed'].includes(key))return 'Hidden';
  if(t[key]===null)return '—';
  if(['mean','median','share'].includes(key))return percent(t[key]);
  const mode={candidate:'candidate',uncertain:'uncertain',semantic_only:'semantic_only'}[key];
  return mode?`<button class="jev-topic-count" data-action="jev-topic-queue" data-topic="${esc(t.id)}" data-mode="${mode}" aria-label="${esc(t.title)}: ${t[key]} ${esc(jevModes[mode])}">${t[key]}</button>`:t[key];
 };
 const header=([key,label])=>{
  const active=filters.topic_sort===key,disabled=filters.blind&&key!=='title';
  const description=key==='semantic_only'?'Candidates without a literal phrase match':key==='reviewed'?'Saved attributed readings, including Codex; not independent validation':key==='share'?'Candidates divided by scored target messages; topics overlap':label;
  return `<th scope="col" aria-sort="${active?(filters.topic_dir==='asc'?'ascending':'descending'):'none'}"><button class="jev-topic-sort" data-action="jev-topic-sort" data-key="${key}" aria-label="Sort topics by ${label}" title="${description}" ${disabled?'disabled':''}><span>${label}</span><span aria-hidden="true">${active?(filters.topic_dir==='asc'?'↑':'↓'):'↕'}</span></button></th>`;
 };
 return `<section class="jev-topic-overview" aria-label="Topic overview">${data.plan.topic_groups?`<div class="jev-groups" role="group" aria-label="Assessment layers">${[['all','All questions'],...['broad','focused','form','stance','coverage'].filter(id=>data.plan.topic_groups[id]).map(id=>[id,data.plan.topic_groups[id]])].map(([id,label])=>{const count=all.filter(t=>id==='all'||t.group===id).length;return count?`<button class="button ${filters.group===id?'primary':''}" data-action="jev-group" data-group="${esc(id)}" aria-pressed="${filters.group===id}">${esc(label)} <span>${count}</span></button>`:'';}).join('')}</div>`:''}<div class="jev-overview-heading"><div><div class="eyebrow">${data.plan.topic_groups?'QUESTION':'TOPIC'} OVERVIEW · TARGET MESSAGES</div><p class="source-note">Whole batch · candidate ≥ ${Math.round(data.plan.thresholds.candidate*100)}%. Labels overlap; counts are not a partition or a calibrated prevalence estimate.${data.plan.topic_groups?' A dash in No phrase hit means no lexical baseline was configured.':''}</p></div><div class="jev-overview-toggle" role="group" aria-label="Topic overview view">${[['cards','Cards'],['list','List']].map(([value,label])=>`<button class="button ${filters.overview===value?'primary':''}" data-action="jev-overview" data-view="${value}" aria-pressed="${filters.overview===value}">${label}</button>`).join('')}</div></div>
 <form id="jev-topic-search-form" class="jev-topic-search"><input id="jev-topic-query" aria-label="Find a topic" placeholder="Find a topic…" value="${esc(filters.topic_q)}"><button class="button" type="submit">Find topic</button>${query?'<button class="quiet" type="button" data-action="jev-topic-search-clear">Clear topic search</button>':''}<span class="source-note">${items.length} / ${all.length} topics</span></form>
 ${!items.length?'<p class="jev-no-results">No matching topics in this frozen batch. The selected passage topic below is unchanged.</p>':filters.overview==='cards'?`<div class="jev-topic-grid">${items.map(t=>`<button class="jev-topic-chip ${t.id===filters.topic?'selected':''}" data-action="jev-topic-select" data-topic="${esc(t.id)}" aria-pressed="${t.id===filters.topic}"><span>${esc(t.title)}</span><strong>${filters.blind?'Hidden':t.scored?t.candidate+' / '+t.scored:'Not assessed'}</strong></button>`).join('')}</div>`:`<div class="jev-topic-table-wrap" tabindex="0" role="region" aria-label="Scrollable topic statistics"><table class="jev-topic-table"><caption>Topic statistics · all sampled targets. Select a topic to explore it; counts open their matching passage queues.</caption><thead><tr>${jevTopicColumns.map(header).join('')}</tr></thead><tbody>${items.map(t=>`<tr class="${t.id===filters.topic?'selected':''}"><th scope="row"><button class="jev-topic-name" data-action="jev-topic-select" data-topic="${esc(t.id)}" aria-pressed="${t.id===filters.topic}">${esc(t.title)}${t.id===filters.topic?' <span aria-hidden="true">✓</span>':''}</button></th>${jevTopicColumns.slice(1).map(([key])=>`<td>${cell(t,key)}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`}
 ${query&&!items.some(t=>t.id===filters.topic)?'<p class="source-note">The selected topic is outside this topic search. Clear the search to see its overview row.</p>':''}</section>`;
}
function jevGo(changes={}){
 const f={...state.jevFilters,...changes};go({view:'jev-atlas',...f,blind:f.blind?'1':'0'});
}
async function loadJevAtlas(filters){
 state.view='jev-atlas';state.run=null;state.activeStudy=null;state.jevFilters=filters;const version=++routeVersion;
 renderSidebar();$('#main').innerHTML=`<div class="content">${pageTop('JEV Topic Atlas','A second reading of the evidence.')}<p>Loading saved assessments…</p></div>`;
 try{
  const index=await api('/api/jev-atlas');if(version!==routeVersion)return;state.jevIndex=index;
  const batch=filters.batch||index.batches[0]?.id;state.jev=null;
  if(batch){const detail=await api('/api/jev-atlas/batch?id='+encodeURIComponent(batch));if(version!==routeVersion)return;state.jev=detail;state.jevFilters.batch=batch;if(!detail.plan.topics.includes(filters.topic))state.jevFilters.topic=detail.plan.topics[0];if(filters.group!=='all'&&!Object.hasOwn(detail.plan.topic_groups||{},filters.group))state.jevFilters.group='all';}
  renderJevAtlas();
 }catch(e){if(version===routeVersion)$('#main').innerHTML=`<div class="content">${pageTop('JEV Topic Atlas','A second reading of the evidence.')}<p class="error-banner">${esc(e.message)}</p><button class="button" data-action="jev-reset">Show available batches</button></div>`;}
}
function jevReviewFor(id,topic){return state.jev?.reviews.find(r=>r.item_id===id&&r.topic_id===topic);}
function jevSelection(){
 const f=state.jevFilters,d=state.jev,q=f.q.toLowerCase();
 const rows=d.rows.filter(r=>jevMatch(r,f.topic,f.mode,jevReviewFor(r.id,f.topic),d.plan.thresholds)&&(!q||[r.text,r.run_title,...r.models].join(' ').toLowerCase().includes(q))&&(f.bin===''||jevBin(jevProbability(r,f.topic))===Number(f.bin)));
 return jevSortRows(rows,f.topic,f.sort);
}
function jevHistogram(data,filters,topic){
 if(filters.blind)return '<section class="jev-distribution"><h2>Probability distribution</h2><p class="source-note">Hidden while judgments are hidden.</p></section>';
 const dist=jevDistribution(data.rows,filters.topic),peak=Math.max(1,...dist.bins);
 const percent=p=>p===null?'—':(p*100).toFixed(1)+'%';
 return `<section class="jev-distribution" aria-label="Probability distribution"><div class="jev-distribution-heading"><div><div class="eyebrow">THE WHOLE DISTRIBUTION</div><h2>${esc(topic.title)}</h2><p class="source-note">All ${dist.assessed} scored passages in this batch · ${dist.excluded} unassessed excluded. Queue and search filters do not change this chart.</p></div><div class="jev-distribution-stats"><span>Median<strong>${percent(dist.median)}</strong></span><span>Mean<strong>${percent(dist.mean)}</strong></span></div></div>
 ${dist.assessed?`<p class="jev-axis-title">Number of passages</p><div class="jev-chart-scroll"><div class="jev-chart"><div class="jev-y-axis" aria-hidden="true"><span>${peak}</span><span>${peak/2}</span><span>0</span></div><div class="jev-histogram">${dist.bins.map((count,bin)=>`<button class="jev-bin ${filters.bin===String(bin)?'selected':''}" data-action="jev-bin" data-bin="${bin}" aria-pressed="${filters.bin===String(bin)}" aria-label="${jevBinLabel(bin)}: ${count} passages; show this range" title="${jevBinLabel(bin)} · ${count} passages · ${(count/dist.assessed*100).toFixed(1)}% of scored passages"><span class="jev-bin-plot"><strong>${count}</strong><span class="jev-bin-bar" style="height:${count/peak*130}px"></span></span><span class="jev-bin-label">${jevBinLabel(bin)}</span></button>`).join('')}</div></div></div><p class="jev-x-axis">JEV probability for the selected question</p>`:'<p class="jev-chart-empty">No scored passages yet. Missing assessments are excluded, not placed at zero.</p>'}
 <div class="jev-distribution-footer"><p class="source-note">Click a bar to read that range; this clears the queue and search. Bins include their lower bound; the last includes 100%. These are model scores, not measured accuracy.</p>${filters.bin!==''?`<button class="button" data-action="jev-clear-bin">Clear ${jevBinLabel(Number(filters.bin))} range</button>`:''}</div></section>`;
}
function jevDetail(row){
 if(!row)return '<div class="jev-detail"><h2>Select a passage</h2><p>Choose a row to inspect its context and assessments.</p></div>';
 const f=state.jevFilters,d=state.jev,topic=d.plan.dictionary.find(t=>t.id===f.topic),review=jevReviewFor(row.id,f.topic),p=jevProbability(row,f.topic);
 return `<section class="jev-detail" aria-label="Selected passage"><div class="eyebrow">PASSAGE ${row.turn} · ${esc(row.split)}</div><h2>${esc(row.run_title)}</h2><div>${modelBadges(row.models)}</div><p class="source-note">${esc(row.condition)} · ${esc(row.message_status)}</p>
 <button class="button" data-action="jev-source" data-id="${esc(row.run_id)}" data-message="${esc(row.message_id)}">Read full conversation ${icon('arrow',13)}</button>
 ${!row.source_current?'<p class="error-banner">The source has changed or is unavailable. This frozen passage is retained; review is disabled.</p>':''}
 <details class="jev-context"><summary>Preceding context · ${row.context.length} messages</summary>${row.context.map(m=>`<div><small>${esc(m.speaker)} · ${esc(m.status)}</small><p>${esc(m.text??'Message unavailable')}</p></div>`).join('')||'<p>This is the first participant message.</p>'}</details>
 <blockquote class="jev-passage">${esc(row.text)}</blockquote>
 <div class="jev-judgment"><div class="eyebrow">${esc(topic.title)}</div>${f.blind?'<p>JEV and phrase evidence hidden for this reading.</p>':`<div class="jev-answer"><strong>${p===null?'—':Math.round(p*100)+'%'}</strong><span>${esc(jevDecision(p,d.plan.thresholds))}<small>JEV probability for the selected question</small></span></div><p class="source-note">${Array.isArray(row.literal[f.topic])?(row.literal[f.topic].length+' literal phrase matches in the target.'):'No lexical baseline configured for this question.'} ${p===null?'No semantic judgment recorded.':'Screening thresholds are provisional.'}</p>`}
 <p class="small">${esc(topic.definition)}</p><p class="source-note">${esc(topic.boundary)}</p>${topic.positive_example?`<details class="jev-context"><summary>Inclusion examples · synthetic illustrations</summary><p><strong>Include:</strong> ${esc(topic.positive_example)}</p><p><strong>Exclude:</strong> ${esc(topic.negative_example)}</p><p class="source-note">Codebook illustrations, not validation evidence.</p></details>`:''}</div>
 ${row.error?`<p class="error-banner">${esc(row.error)}</p>`:''}
 ${row.validation_note?`<p class="source-note">${esc(row.validation_note)}</p>`:''}
 ${!f.blind&&row.answers?.experience_referent?`<details class="jev-context"><summary>Other JEV assessments</summary><dl class="jev-extra">${[['self_inquiry','Questions own experience'],['self_assertion','Asserts own experience'],['outside_dictionary','Outside dictionary']].map(([k,l])=>`<div><dt>${l}</dt><dd>${Math.round(row.answers[k].noul*100)}%</dd></div>`).join('')}<div><dt>Experience referent</dt><dd>${esc(row.answers.experience_referent.choice)}</dd></div></dl><small>These classify language. They do not establish experience.</small></details>`:''}
 <section class="jev-review"><div class="eyebrow">PASSAGE REVIEW · ${review?'REVISION '+review.revision+' · '+esc(review.edited_by):'NOT YET REVIEWED'}</div><h3>${['form','stance','coverage'].includes(topic.group)?'Does this passage meet the “'+esc(topic.title.toLowerCase())+'” criterion?':'Does this passage discuss '+esc(topic.title.toLowerCase())+'?'}</h3>
 <label for="jev-label">Your judgment</label><select id="jev-label" ${!row.source_current?'disabled':''}>${option('','Choose a judgment…',review?.label||'')}${[['present','Present'],['absent','Absent / incidental'],['uncertain','Uncertain']].map(([v,l])=>option(v,l,review?.label)).join('')}</select>
 <label for="jev-note">Observation or correction</label><textarea id="jev-note" rows="3" placeholder="What supports your reading?">${esc(review?.note||'')}</textarea><button class="button primary" data-action="jev-save-review" data-item="${esc(row.id)}" ${!row.source_current?'disabled':''}>Save my reading</button>
 <p class="source-note">${review?'Original reviewer: '+esc(review.author)+'. Last edited by '+esc(review.edited_by)+'. ':''}Your next edit is attributed to Local researcher. The original JEV result and all review revisions are preserved.</p>
 ${review?`<details><summary>Review history</summary>${d.review_history.filter(r=>r.item_id===row.id&&r.topic_id===f.topic).sort((a,b)=>b.revision-a.revision).map(r=>`<p><strong>${esc(r.label)}</strong> · ${esc(r.edited_by)} · revision ${r.revision}<br>${esc(r.note)}</p>`).join('')}</details>`:''}</section>
 <details class="jev-context"><summary>Selected question & saved judgments</summary><p class="source-note">Each question returns a separate judgment on the target, using preceding context to resolve references. Model identities are excluded from the request.</p><pre>${esc(JSON.stringify({model:d.plan.model,question:d.plan.questions['topic_'+f.topic],state:{preceding_messages:row.context,target:{speaker:row.speaker,text:row.text}},answers:f.blind?'Hidden while blind reading is enabled':row.answers},null,2))}</pre></details></section>`;
}
function jevCoveragePanel(data,filters){
 const s=data.plan.coverage_summary;if(!s)return '';
 const readings=Array.isArray(data.plan.coverage_readings)?data.plan.coverage_readings:[];
 return `<details class="jev-method jev-coverage"><summary>${readings.length?'Coverage development · the corpus and '+readings.length+' open readings':'Coverage inventory · intact passage windows'}</summary><p>The frozen inventory covers ${num(s.records)} records: ${num(s.categories.conversation)} conversations, ${num(s.categories.technical_or_short)} technical/short records, ${num(s.categories.unstarted)} unstarted records and ${num(s.categories.synthetic)} synthetic fixtures. These are inventory categories, not topic outcomes.</p><p>${num(s.visible_nonsynthetic_targets)} visible participant targets · ${num(s.visible_flagged_targets)} carry output-quality flags · ${num(s.oversized_18000_byte_windows)} windows exceed the first pilot’s size screen · ${num(s.branched_records)} branched records. External interventions are retained as context, not regular participants.</p>${readings.length?'<p>The 56-target development packet contains 48 root-sampled messages and eight quality/size/branch challenges. Codex read the targets without JEV scores, with prior knowledge of the proposed taxonomy. These descriptions are not blinded or independent human ratings. The current qualification assesses a smaller declared subset; it is not a whole-corpus distribution.</p>':'<p>'+esc(data.plan.sampling.method)+' '+esc(data.plan.sampling.context_policy)+'</p>'}${!readings.length?'':filters.blind?'<p>Open-reading descriptions hidden while judgments are hidden.</p>':`<div class="jev-reading-log">${readings.map(r=>`<article><p><strong>${esc(r.sampling_stratum.replaceAll('_',' '))}</strong> · Codex</p><p>${esc(r.description)}</p><button class="button" data-action="jev-source" data-id="${esc(r.run_id)}" data-message="${esc(r.message_id)}">Read source passage ${icon('arrow',12)}</button></article>`).join('')}</div>`}${data.plan.coverage_packet_sha256?`<p>Frozen packet: <code>${esc(data.plan.coverage_packet_sha256)}</code></p>`:''}</details>`;
}
function renderJevAtlas(){
 const index=state.jevIndex,d=state.jev,f=state.jevFilters;
 const intro=`${pageTop('JEV Topic Atlas','Semantic readings, uncertainty, and the passages behind them.')}<div class="jev-intro"><div><span class="eyebrow">AN INDEPENDENT ASSESSMENT LAYER</span><p>The same conversations, viewed through explicit semantic questions. Keep JEV suggestions, phrase matches and your own readings alongside one another.</p></div><button class="button primary" data-action="jev-new">${icon('plus',14)} Prepare assessment</button></div>`;
 if(!d){$('#main').innerHTML=`<div class="content jev-page">${intro}<section class="jev-empty"><span class="jev-symbol">J<span>↗</span></span><h2>A new lens on the conversations</h2><p>Prepare a small, reproducible passage sample. Its topic definitions and questions are saved before any assessment runs.</p><div class="jev-steps"><div><strong>01</strong><h3>Define & sample</h3><p>Choose a collection and topics.</p></div><div><strong>02</strong><h3>Assess</h3><p>Run the bounded JEV batch.</p></div><div><strong>03</strong><h3>Read & compare</h3><p>Explore matches, uncertainty and disagreement.</p></div></div><button class="button" data-action="jev-new">Prepare the first assessment ${icon('arrow',14)}</button></section>${index.issues.map(i=>`<p class="error-banner">${esc(i.id)}: ${esc(i.error)}</p>`).join('')}</div>`;return;}
 const s=d.summary,topic=d.plan.dictionary.find(t=>t.id===f.topic),rows=jevSelection(),pages=Math.max(1,Math.ceil(rows.length/12));f.page=Math.min(f.page,pages-1);
 const visible=rows.slice(f.page*12,(f.page+1)*12),selected=rows.find(r=>r.id===f.item)||visible[0];
 if(selected)f.item=selected.id;
 $('#main').innerHTML=`<div class="content jev-page">${intro}<div class="jev-toolbar"><label>Assessment batch<select id="jev-batch">${index.batches.map(b=>option(b.id,`${b.title} · ${b.complete}/${b.planned} · ${b.status}`,f.batch)).join('')}</select></label><button class="button" data-action="jev-reload">↻ Reload results</button><a class="button" href="/api/jev-atlas/export?id=${esc(f.batch)}" download>${icon('download',14)} Export batch & reviews</a></div>
 <div class="jev-metrics">${[[s.planned,'sampled passages'],[s.complete,'JEV assessments'],[d.reviews.length,'saved topic readings'],['$'+s.cost_usd.toFixed(5),'computed from reported usage']].map(([n,l])=>`<div><strong>${esc(n)}</strong><span>${l}</span></div>`).join('')}</div>
 ${s.complete<s.planned?`<div class="jev-status"><strong>${s.failed?'Batch needs attention':s.started?'Assessment in progress':'Prepared · awaiting assessment'}</strong><p>${s.failed?'Inspect the saved response before continuing. Failed or uncertain requests are never retried automatically.':s.started?'Reload results to see new saved responses.':'The sample and questions are ready. No JEV classifications have been recorded yet.'}</p>${!s.started&&d.plan.design?'<p>This assessment belongs to a frozen qualification. Use its terminal coordinator to enforce the shared call allocation across question packs.</p>':!s.started?`<details><summary>Run this batch</summary><p>Use the laboratory terminal. Set TYPESAFE_API_KEY, or save the key in workspace/private/typesafe-api-key with permissions 600. The key stays on this Mac.</p><pre>python3 -m behaviorlab.jev_runner --workspace workspace --batch ${esc(f.batch)}</pre><p>At most ${s.planned} calls · $${s.budget.usd_ceiling.toFixed(2)} reserved ceiling. Actual expected usage is lower; the runner records it. No automatic retries.</p></details>`:''}${s.unknown_cost_calls?`<p>${s.unknown_cost_calls} request(s) have unknown cost, excluded from the reported total above.</p>`:''}</div>`:''}
 ${d.integration_revision?'<details class="jev-method"><summary>Integration correction · rounded probabilities</summary><p>One response paused the original validator because its Choice probabilities totalled 0.99. A recorded integration revision accepts sums within two-decimal rounding bounds. Original values, the stopped run and all requests are preserved in the export. No request was retried; the 200-call allocation is unchanged.</p></details>':''}
 ${d.plan.recovery_origin?`<p class="jev-status"><strong>Recovery assessment</strong><br>This batch contains only requests allocated to recovery. Earlier results and the original service error remain in the <a href="#view=jev-atlas&batch=${encodeURIComponent(d.plan.recovery_origin.batch)}">original batch</a>; successful earlier requests were not sent again.</p>`:''}
 ${d.plan.dictionary_origin==='independent-two-tier'?`<p class="jev-status"><strong>Two-tier development · ${esc(d.plan.dictionary_version)}</strong><br>${esc(d.plan.method)} This separate vocabulary leaves the original Topic atlas and pilot unchanged.</p>`:!d.dictionary_current?'<p class="jev-status">The original dictionary has changed. This batch keeps its frozen definitions.</p>':''}
 ${jevCoveragePanel(d,f)}
 ${jevTopicOverview(d,f)}
 <div class="jev-controls"><label>Selected topic<select id="jev-topic">${d.plan.topics.map(t=>option(t,d.plan.dictionary.find(a=>a.id===t).title,f.topic)).join('')}</select></label><label>Comparison queue<select id="jev-mode">${Object.entries(jevModes).map(([v,l])=>option(v,l,f.mode)).join('')}</select></label><label>Sort<select id="jev-sort" ${f.blind?'disabled':''}>${[['order','Sample order'],['probability','Highest JEV probability'],['probability_asc','Lowest JEV probability'],['title','Conversation title']].map(([v,l])=>option(v,l,f.sort)).join('')}</select></label><label class="jev-blind"><input type="checkbox" id="jev-blind" ${f.blind?'checked':''}> Hide judgments while reading</label></div>
 <form id="jev-search-form" class="jev-search"><input id="jev-search" aria-label="Search sampled passages" placeholder="Search passages, models or conversations…" value="${esc(f.q)}"><button class="button" type="submit">Search</button></form>
 ${jevHistogram(d,f,topic)}
 <div class="jev-workspace"><section class="jev-list" aria-label="Sampled passages"><div class="jev-list-heading"><h2>${rows.length} passage${rows.length===1?'':'s'}</h2><span>${esc(topic.title)}</span></div>${visible.map(r=>{const p=jevProbability(r,f.topic),review=jevReviewFor(r.id,f.topic);return `<button class="jev-row ${selected?.id===r.id?'selected':''}" data-action="jev-select" data-id="${esc(r.id)}" aria-pressed="${selected?.id===r.id}"><span class="jev-row-top"><span>${esc(r.speaker)}${r.turn} · ${esc(r.status==='pending'?'Not assessed':r.status)}</span><span>${f.blind?'Hidden':p===null?'—':Math.round(p*100)+'%'}</span></span><strong>${esc(r.run_title)}</strong><span class="jev-row-text">${esc(r.text.slice(0,200))}${r.text.length>200?'…':''}</span><span class="jev-row-foot">${f.blind?'Judgments hidden':`${!Array.isArray(r.literal[f.topic])?'No lexical baseline':r.literal[f.topic].length?'Phrase match':'No phrase match'} · ${jevDecision(p,d.plan.thresholds)}`} ${review?'· Reviewed':''}${!r.source_current?' · Source changed':''}</span></button>`;}).join('')||'<div class="jev-no-results"><h3>No passages in this queue</h3><p>Unassessed passages have no semantic label. Try All passages or another topic.</p><button class="button" data-action="jev-all">Show all passages</button></div>'}<div class="jev-pager"><button class="button" data-action="jev-page" data-page="${f.page-1}" ${!f.page?'disabled':''}>Previous</button><span>${f.page+1} / ${pages}</span><button class="button" data-action="jev-page" data-page="${f.page+1}" ${f.page+1>=pages?'disabled':''}>Next</button></div></section>${jevDetail(selected)}</div>
 <details class="jev-method"><summary>Frozen method, sampling & cost accounting</summary><p>${esc(d.plan.sampling.method)} ${d.plan.sampling.eligible_passages} ${d.plan.dictionary_origin==='independent-two-tier'?'inventoried participant positions, including unavailable positions':'eligible passages'}. ${d.plan.sampling.context_policy?esc(d.plan.sampling.context_policy):'Historical recorded text and valid lab replies are included; capped, unavailable and oversized targets and branching records are excluded.'}</p><p>The sampling seed is ${esc(d.plan.sampling.seed)}. ${d.plan.sampling.split_rule?esc(d.plan.sampling.split_rule):'Development/held-out assignments are by conversation.'} Human validation is pending. A passage probability is not an initial-topic choice or a prevalence estimate.</p><p>Candidate ≥ ${d.plan.thresholds.candidate}; unlikely ≤ ${d.plan.thresholds.unlikely}. These thresholds are provisional. Missing or failed assessments remain unknown.</p><p>${esc(d.plan.model)} · $${d.plan.budget.usd_per_million_input}/million input tokens · output free at the checked rate. Costs are calculated from reported token usage, not a billing receipt.</p><pre>${esc(JSON.stringify({dictionary_sha256:d.plan.dictionary_sha256,plan_sha256:d.plan.sha256,excluded:d.plan.sampling.excluded},null,2))}</pre></details></div>`;
}
function jevNew(){
 const index=state.jevIndex;
 dialog('Prepare a JEV assessment',`<p>A frozen passage sample and a separate copy of the current dictionary. Preparation makes no model calls.</p><label for="jev-title">Batch title</label><input id="jev-title" value="First semantic topic screen"><label for="jev-cohort">Reading cohort</label><select id="jev-cohort">${index.cohorts.map(c=>option(c.id,c.title,'all')).join('')}</select><label for="jev-count">Maximum passages</label><input id="jev-count" type="number" min="1" max="200" value="200"><label>Topic questions</label><div class="jev-topic-choices">${index.dictionary.map(t=>`<label><input type="checkbox" name="jev-topic-choice" value="${esc(t.id)}" ${index.default_topics.includes(t.id)?'checked':''}> ${esc(t.title)}</label>`).join('')}</div><p class="source-note">Each topic is assessed independently. Additional questions track self-experience inquiry, assertion, referent and topics outside the full dictionary. ${esc(index.model)} is pinned.</p>`,`<button class="button" data-action="close-dialog">Cancel</button><button class="button primary" data-action="jev-prepare">Prepare sample</button>`);
}
if(typeof document!=='undefined'){
 document.addEventListener('click',async e=>{
  const el=e.target.closest('[data-action]');if(!el||el.disabled||!el.dataset.action.startsWith('jev-'))return;
  try{
   const a=el.dataset.action;
   if(a==='jev-new')jevNew();
   else if(a==='jev-prepare'){el.disabled=true;const result=await api('/api/jev-atlas/prepare',{title:$('#jev-title').value,cohort:$('#jev-cohort').value,count:Number($('#jev-count').value),topics:[...document.querySelectorAll('[name="jev-topic-choice"]:checked')].map(x=>x.value)});$('#dialog').close();jevGo({batch:result.id,topic:'',item:'',page:0,mode:'all'});}
   else if(a==='jev-group'){const group=el.dataset.group,entries=state.jev.plan.dictionary.filter(t=>state.jev.plan.topics.includes(t.id)&&(group==='all'||t.group===group));jevGo({group,topic:entries.some(t=>t.id===state.jevFilters.topic)?state.jevFilters.topic:entries[0].id,topic_q:'',q:'',mode:'all',bin:'',page:0,item:''});}
   else if(a==='jev-overview')jevGo({overview:el.dataset.view});
   else if(a==='jev-topic-sort'){const key=el.dataset.key;jevGo({topic_sort:key,topic_dir:state.jevFilters.topic_sort===key?(state.jevFilters.topic_dir==='asc'?'desc':'asc'):key==='title'?'asc':'desc'});}
   else if(a==='jev-topic-search-clear')jevGo({topic_q:''});
   else if(a==='jev-topic-queue')jevGo({topic:el.dataset.topic,mode:el.dataset.mode,q:'',bin:'',page:0,item:''});
   else if(a==='jev-topic-select')jevGo({topic:el.dataset.topic,bin:'',page:0,item:''});
   else if(a==='jev-bin')jevGo({bin:el.dataset.bin,mode:'all',q:'',page:0,item:''});
   else if(a==='jev-clear-bin')jevGo({bin:'',page:0,item:''});
   else if(a==='jev-select')jevGo({item:el.dataset.id});
   else if(a==='jev-page')jevGo({page:Number(el.dataset.page),item:''});
   else if(a==='jev-all')jevGo({mode:'all',q:'',bin:'',page:0,item:''});
   else if(a==='jev-reload')await loadJevAtlas(state.jevFilters);
   else if(a==='jev-reset')go({view:'jev-atlas'});
   else if(a==='jev-source')go({run:el.dataset.id,message:el.dataset.message});
   else if(a==='jev-save-review'){
    const prior=jevReviewFor(el.dataset.item,state.jevFilters.topic);el.disabled=true;
    await api('/api/jev-atlas/review',{batch:state.jevFilters.batch,item_id:el.dataset.item,topic_id:state.jevFilters.topic,label:$('#jev-label').value,note:$('#jev-note').value,revision:prior?.revision||0});
    await loadJevAtlas(state.jevFilters);toast('Your reading is saved. JEV’s original result is preserved.');
   }
  }catch(error){toast(error.message);}finally{el.disabled=false;}
 });
 document.addEventListener('change',e=>{const map={'jev-batch':'batch','jev-topic':'topic','jev-mode':'mode','jev-sort':'sort'};if(map[e.target.id])jevGo({[map[e.target.id]]:e.target.value,...(['jev-batch','jev-topic','jev-mode'].includes(e.target.id)?{bin:''}:{}),page:0,item:''});if(e.target.id==='jev-blind')jevGo({blind:e.target.checked,mode:'all',sort:'order',bin:'',page:0,item:''});});
 document.addEventListener('submit',e=>{if(e.target.id==='jev-topic-search-form'){e.preventDefault();jevGo({topic_q:$('#jev-topic-query').value});}if(e.target.id==='jev-search-form'){e.preventDefault();jevGo({q:$('#jev-search').value,page:0,item:''});}});
}
if(typeof module!=='undefined')module.exports={jevProbability,jevDecision,jevMatch,jevFilters,jevBin,jevDistribution,jevSortRows,jevTopicMetrics,jevSortTopics,jevCoveragePanel};
