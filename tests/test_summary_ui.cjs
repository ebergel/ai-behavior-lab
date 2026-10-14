const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const listeners={},state={view:'purpose',musingSection:'summary'},panel={innerHTML:''};
const c=vm.createContext({state,document:{addEventListener:(k,fn)=>(listeners[k]??=[]).push(fn)},$:selector=>selector==='#lab-summary'?panel:null,num:n=>String(n),esc:s=>String(s??'').replace(/[&<>"']/g,x=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[x])),icon:()=>'',option:(v,t)=>`<option>${t}</option>`,musingTime:s=>s,modelBadges:()=>'',api:async()=>({})});
vm.runInContext(fs.readFileSync('behaviorlab/explorer_ui/summary.js','utf8'),c);
const plain=x=>JSON.parse(JSON.stringify(x));

test('atlas cohort changes show scan and review units without changing assessment coverage',()=>{
 const cohort=(id,title,runs,messages,reviews)=>({id,title,runs,scan_messages:messages,opening_reviews_resolved:reviews,opening_reviews_pending:runs-reviews,opening_reviews_stale:0,opening_reviews_unavailable:0,href:'#view=topic-atlas&cohort='+id});
 const atlas={title:'Topic atlas · dictionary matching & opening reviews',status:'Reading instrument',eligible_runs:438,topic_definitions:23,cohorts:[cohort('all','All atlas-eligible runs',438,11204,12),cohort('study','Opening & partner',12,168,12)]};
 state.boot={studies:[{id:'study'}]};state.atlasFilters=undefined;state.summaryAtlasCohort=undefined;
 const union={covered_messages:11054,denominator:11245,coverage:98.301467};
 state.labSummary={topic_atlas:atlas,assessment_union:union};state.view='library';
 let html=c.summaryAtlasRow(atlas);
 assert.match(html,/168/);assert.match(html,/12 \/ 12/);assert.match(html,/23 topic definitions/);
 assert.match(html,/messages in scan scope/);assert.match(html,/Not comparable/);assert.match(html,/Excluded from assessment coverage/);
 assert.match(html,/#view=topic-atlas&amp;cohort=study/);assert.doesNotMatch(html,/168 source-current messages|168 \/ 168/);
 listeners.change.forEach(fn=>fn({target:{id:'summary-atlas-cohort',value:'all'}}));
 html=c.summaryAtlasRow(atlas);assert.match(html,/11204/);assert.match(html,/12 \/ 438/);assert.match(html,/426 unreviewed/);
 assert.deepEqual(union,{covered_messages:11054,denominator:11245,coverage:98.301467});
 listeners.change.forEach(fn=>fn({target:{id:'summary-atlas-cohort',value:'unknown'}}));assert.equal(state.summaryAtlasCohort,'all');
 state.summaryAtlasCohort='removed';assert.equal(c.summaryAtlasCohort(atlas).id,'all');
 state.summaryAtlasCohort=undefined;state.boot=undefined;state.view='purpose';
});
test('unavailable atlas stays visible with escaped error and unknown metrics',()=>{
 const html=c.summaryAtlasRow({title:'Topic atlas',status:'Unavailable',error:'<missing>'});
 assert.match(html,/Unavailable/);assert.match(html,/&lt;missing&gt;/);assert.doesNotMatch(html,/<missing>|0 \/ 0/);
});

test('generation filtering and sorting preserve source rows and percentage denominators',()=>{
 const rows=[{id:'a',title:'Alpha',kind:'real',messages:10,share_all:25,share_kind:100,models:['M'],conditions:['open'],source:'a'}, {id:'b',title:'Beta',kind:'synthetic',messages:30,share_all:75,share_kind:100,models:[],conditions:[],source:'b'}];
 assert.deepEqual(plain(c.summaryRows(rows,{kind:'all',q:'',sort:'messages',direction:'desc'})).map(r=>r.id),['b','a']);
 const filtered=c.summaryRows(rows,{kind:'real',q:'open',sort:'title',direction:'asc'});
 assert.equal(filtered.length,1);assert.equal(filtered[0].share_all,25);assert.equal(filtered[0].share_kind,100);
 assert.equal(rows[0].id,'a');assert.equal(c.summaryPercent(null),'—');assert.equal(c.summaryPercent(0),'0.0%');
});
test('assessment sorting keeps unavailable coverage last in either direction and preserves zero',()=>{
 const rows=[{title:'Missing'},{title:'Zero',covered_messages:0},{title:'Known',covered_messages:10}];
 assert.deepEqual(plain(c.summaryAssessmentRows(rows)).map(r=>r.title),['Known','Zero','Missing']);
 assert.deepEqual(plain(c.summaryAssessmentRows(rows,'covered_messages','asc')).map(r=>r.title),['Zero','Known','Missing']);
});
test('summary copy separates sample controls and corpus coverage, escaping source labels',()=>{
 state.labSummary={indexed_at:'today',generated_at:'now',inventory:{messages:4,real_messages:3,synthetic_messages:1,real_share:75,synthetic_share:25,empty_messages:{},whitespace_messages:{},categories:{inventory:1,synthetic:1},unstarted:0,experiments:[]},assessment_union:{covered_messages:1,coverage:100/3},assessments:[{title:'<unsafe>',status:'Complete',real_sample:1,real_complete:1,controls:1,controls_complete:1,source_runs:1,coverage:100/3,covered_messages:1,questions:2,wordings:3,source:'source'}],issues:[],catalog_notices:[],probe_batches:[],counting_rules:['Rule']};
 const html=c.labSummaryHtml();assert.match(html,/&lt;unsafe&gt;/);assert.doesNotMatch(html,/<unsafe>/);
 assert.match(html,/50.0% of sample texts/);assert.match(html,/33.3%/);assert.match(html,/of 3 messages/);
 assert.match(html,/3 wordings/);assert.match(html,/Synthetic controls/);assert.match(html,/percentages overlap/i);
});
test('a slow summary load cannot repaint another workspace tab',async()=>{
 state.labSummary=null;let release;c.api=()=>new Promise(resolve=>{release=resolve;});
 const request=c.loadLabSummary();state.musingSection='journal';panel.innerHTML='journal';release({inventory:{}});await request;
 assert.equal(panel.innerHTML,'journal');assert.equal(state.labSummaryLoading,false);
});

test('source links preserve a route back to the summary',()=>{
 assert.deepEqual(plain(c.summarySourceRoute('exact-run')), {run:'exact-run',fromSummary:'1'});
 assert.equal(c.summaryPercent(100/11245),'0.009%');
});
