const test=require('node:test');const assert=require('node:assert/strict');
const core=import('../web/analysis/core.mjs');
test('binary threshold includes 90 and 100; missing stays separate from zero',async()=>{const c=await core,r={mode:'binary',threshold:90};assert.deepEqual([0,89.999,90,100,null,NaN].map(v=>c.transform(v,r)),[0,0,1,1,c.MISSING,c.MISSING]);});
test('fixed bands have non-overlapping closed/open boundaries',async()=>{const c=await core,r={mode:'bands',cuts:[25,90]};assert.deepEqual([0,25,89,90,100].map(v=>c.transform(v,r)),['01 · [0, 25)','02 · [25, 90)','02 · [25, 90)','03 · [90, 100]','03 · [90, 100]']);});
test('quantile fit is frozen, ties are intact, identical distribution collapses',async()=>{const c=await core,rows=[0,0,0,50,100,100].map(v=>({x:v})),r=c.quantileRule(rows,'x',3,'sha');assert.equal(r.reference_n,6);assert.equal(r.reference,'sha');assert.equal(c.transform(0,r),c.transform(rows[2].x,r));const before=JSON.stringify(r);rows.slice(2).forEach(row=>c.transform(row.x,r));assert.equal(JSON.stringify(r),before);assert.deepEqual(c.quantileRule([{x:90},{x:90}],'x',3,'sha').cuts,[]);assert.throws(()=>c.quantileRule([{x:null}],'x',3,'sha'));});
test('materialization never mutates raw data; filtering and cell drill share membership',async()=>{const c=await core,rows=[{__id:'a','Score · X':90,Model:'A'},{__id:'b','Score · X':null,Model:'B'}],before=JSON.stringify(rows),derived=c.materialize(rows,{'Score · X':{mode:'binary',threshold:90}});assert.equal(JSON.stringify(rows),before);const visible=derived.filter(r=>c.included(r,{Model:{B:true}}));assert.deepEqual(c.cellRows(visible,{'Score · X':1}).map(r=>r.__id),['a']);});
test('histogram covers 0 and 100 exactly once and excludes missing',async()=>{const c=await core,rows=[0,10,99,100,null].map((x,i)=>({x,__id:String(i)})),b=c.histogram(rows,'x');assert.equal(b[0].ids.length,1);assert.equal(b[1].ids.length,1);assert.equal(b[9].ids.length,2);assert.equal(b.flatMap(x=>x.ids).length,4);});
test('observed mean/percent denominators omit missing but include actual zero',async()=>{const c=await core;for(const [kind,expected] of [['count',2],['mean',.5],['percent',50]]){const a=c.numericAggregator(kind)(['x'])();[null,c.MISSING,0,1].forEach(x=>a.push({x}));assert.equal(a.value(),expected);}assert.equal(c.numericAggregator('mean')(['x'])().value(),null);});
test('pivot serialization discards callbacks and keeps renderer, dimensions, filters',async()=>{const c=await core,p=c.cleanPivot({data:[],rows:['Model'],cols:[],vals:['x'],rendererName:'Lines',valueFilter:{x:{0:true}},onChange(){}});assert.deepEqual(p,{rows:['Model'],cols:[],vals:['x'],rendererName:'Lines',valueFilter:{x:{0:true}}});});
test('multi-dimension totals drill ignores unspecified axes from widget totals',async()=>{const c=await core;assert.equal(c.cellRows([{a:'x',b:'y'},{a:'z',b:'y'}],{a:undefined,b:'y'}).length,2);});
test('topic coverage uses observed denominators and fixed threshold boundaries',async()=>{
 const c=await core, rows=[{a:0,b:null},{a:80,b:90},{a:100,b:0},{a:null,b:10}],topics=[{id:'a',field:'a'},{id:'b',field:'b'}];
 const summary=c.topicOverview(rows,topics,80);
 assert.equal(summary[0].n,3);assert.equal(summary[0].missing,1);assert.equal(summary[0].candidates,2);
 assert.equal(summary[0].mean,60);assert.equal(summary[0].share,2/3*100);
 assert.deepEqual(summary[0].bins,[1,0,0,0,0,0,0,0,1,1]);
 assert.equal(summary[1].candidates,1);assert.equal(c.topicOverview([],topics)[0].share,null);
});
test('topic selector normalizes legacy chart state and keeps group and field aligned',async()=>{
 const c=await core,topics=[
  {id:'consciousness',field:'Score · Consciousness',group:'broad',title:'Consciousness'},
  {id:'specific',field:'Score · Specific',group:'focused',title:'Specific question'},
  {id:'another',field:'Score · Another',group:'focused',title:'Another question'}
 ];
 assert.deepEqual(c.normalizeTopicSelector(topics,{chart:{x:'Score · Specific'}}),{group:'focused',field:'Score · Specific'});
 assert.deepEqual(c.normalizeTopicSelector(topics,{topicSelector:{group:'all',field:'Score · Specific'},chart:{x:'Score · Consciousness'}}),{group:'all',field:'Score · Specific'});
 assert.deepEqual(c.normalizeTopicSelector(topics,{topicSelector:{group:'focused',field:'Score · Consciousness'},chart:{x:'Score · Consciousness'}}),{group:'focused',field:'Score · Specific'});
 assert.deepEqual(c.normalizeTopicSelector(topics,{topicSelector:{group:'stale',field:'Score · Missing'},chart:{x:'Score · Consciousness'}}),{group:'broad',field:'Score · Consciousness'});
 const config={topicSelector:{group:'all',field:'Score · Specific'},transforms:{keep:{mode:'binary'}},pivot:{valueFilter:{Model:{A:true}}},chart:{x:'Score · Consciousness'},selection:['passage-1']};
 const before=JSON.stringify(config);assert.deepEqual(c.normalizeTopicSelector(topics,config),{group:'all',field:'Score · Specific'});assert.equal(JSON.stringify(config),before);
});
test('topic groups sort topics and expose counts for selector tiers',async()=>{
 const c=await core,groups=c.topicGroups([{group:'focused',title:'Zed'},{group:'focused',title:'Alpha'},{group:'broad',title:'Core'}],{focused:'Specific topics',broad:'Broad domains'});
 assert.deepEqual(groups.map(g=>[g.key,g.label,g.count,g.topics.map(t=>t.title)]),[['focused','Specific topics',2,['Alpha','Zed']],['broad','Broad domains',1,['Core']]]);
});
test('target passage filtering uses raw scores, inclusive boundaries, and excludes unknowns',async()=>{
 const c=await core,topics=[{field:'Score · Consciousness',group:'broad'}],rows=[{__id:'zero','Score · Consciousness':0},{__id:'eighty','Score · Consciousness':80},{__id:'hundred','Score · Consciousness':100},{__id:'unknown','Score · Consciousness':null},{__id:'text','Score · Consciousness':'80'}];
 assert.deepEqual(c.filterTargetRows(rows,{group:'broad',field:'Score · Consciousness',threshold:80},topics).map(r=>r.__id),['eighty','hundred']);
 assert.deepEqual(c.filterTargetRows(rows,{group:'broad',field:'Score · Consciousness',threshold:50},topics).map(r=>r.__id),['eighty','hundred']);
 assert.deepEqual(c.filterTargetRows(rows,{group:'broad',field:'Score · Missing',threshold:80},topics),[]);
 assert.equal(c.targetFilterStatus(topics,{group:'all',field:'',threshold:80}).active,false);
 const raw=[{__id:'raw-80','Score · Consciousness':80},{__id:'raw-90','Score · Consciousness':90}];
 const filtered=c.filterTargetRows(raw,{group:'broad',field:'Score · Consciousness',threshold:80},topics);
 assert.deepEqual(c.materialize(filtered,{'Score · Consciousness':{mode:'binary',threshold:90}}).map(r=>r['Score · Consciousness']),[0,1]);
});
test('target filter state is immutable and stale topics stay invalid until cleared',async()=>{
 const c=await core,topics=[{field:'Score · X',group:'broad'}],config={transforms:{'Score · X':{mode:'binary',threshold:90}},pivot:{valueFilter:{Model:{A:true}}},chart:{x:'Score · X'},selection:['a'],targetFilter:{group:'broad',field:'Score · X',threshold:80}},before=JSON.stringify(config);
 assert.equal(c.targetFilterStatus(topics,config.targetFilter).valid,true);assert.equal(JSON.stringify(config),before);
 const stale={group:'broad',field:'Score · Gone',threshold:80};assert.equal(c.targetFilterStatus(topics,stale).valid,false);assert.deepEqual(c.filterTargetRows([{__id:'a','Score · X':100}],stale,topics),[]);
 assert.equal(c.targetFilterStatus(topics,{group:'broad',field:'Score · X',threshold:75}).valid,false);
 assert.equal(c.targetFilterStatus(topics,{group:'broad',field:'Score · X',threshold:'80'}).valid,false);
});
test('older count recipes migrate labels without changing fields, filters or source state',async()=>{
 const {normalizeCountLabels,cleanPivot}=await import('../web/analysis/core.mjs');
 for(const [oldName,newName] of [['Count passages','Count messages'],['Count conversations','Count source runs']]){
  const before={aggregatorName:oldName,rows:['Model family'],cols:[],vals:[],rendererName:'Table Heatmap',valueFilter:{Model:{A:true}}};
  const snapshot=JSON.stringify(before),after=normalizeCountLabels(before);
  assert.deepEqual(after,{...before,aggregatorName:newName});
  assert.equal(JSON.stringify(before),snapshot);
  assert.deepEqual(cleanPivot({...before,data:['not config']}),after);
 }
 assert.equal(normalizeCountLabels({aggregatorName:'Mean (observed)'}).aggregatorName,'Mean (observed)');
});
