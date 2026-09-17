const test=require('node:test');
const assert=require('node:assert/strict');
const {jevMatch,jevDecision,jevProbability,jevFilters,jevBin,jevDistribution,jevSortRows}=require('../behaviorlab/explorer_ui/jev-atlas.js');
const thresholds={candidate:.8,unlikely:.2};
function row(p,hits=false,status='complete'){return {status,literal:{consciousness:hits?[{}]:[]},answers:p===null?null:{topic_consciousness:{noul:p},outside_dictionary:{noul:.9}}};}
test('unassessed and failed messages never become semantic negatives',()=>{
 for(const status of ['pending','error','unresolved']){
  const r=row(null,true,status);assert.equal(jevProbability(r,'consciousness'),null);
  for(const mode of ['candidate','semantic_only','literal_only','uncertain','disagreement','outside'])assert.equal(jevMatch(r,'consciousness',mode,{label:'present'},thresholds),false);
  assert.equal(jevMatch(r,'consciousness','pending',null,thresholds),true);
 }
});
test('comparison queues distinguish semantic candidates and incidental phrase matches',()=>{
 assert(jevMatch(row(.91),'consciousness','semantic_only',null,thresholds));
 assert(!jevMatch(row(.91,true),'consciousness','semantic_only',null,thresholds));
 assert(jevMatch(row(.1,true),'consciousness','literal_only',null,thresholds));
 assert(jevMatch(row(.5),'consciousness','uncertain',null,thresholds));
 assert.equal(jevDecision(.8,thresholds),'Candidate');assert.equal(jevDecision(.2,thresholds),'Unlikely');
});
test('human uncertainty is not counted as disagreement and reviewers remain separate',()=>{
 assert(jevMatch(row(.91),'consciousness','disagreement',{label:'absent'},thresholds));
 assert(jevMatch(row(.1),'consciousness','disagreement',{label:'present'},thresholds));
 assert(!jevMatch(row(.91),'consciousness','disagreement',{label:'uncertain'},thresholds));
 assert(jevMatch(row(.91),'consciousness','unreviewed',null,thresholds));
});
test('bookmark filters retain batch, topic, queue and selected passage',()=>{
 const f=jevFilters(new URLSearchParams({batch:'abc',topic:'emergence',mode:'semantic_only',page:'2',item:'x',sort:'probability_asc',bin:'0'}));
 assert.equal(f.batch,'abc');assert.equal(f.mode,'semantic_only');assert.equal(f.page,2);assert.equal(f.item,'x');assert.equal(f.blind,false);
 assert.equal(f.sort,'probability_asc');assert.equal(f.bin,'0');
 assert.equal(jevFilters(new URLSearchParams('mode=invalid&page=-4')).mode,'all');
 assert.equal(jevFilters(new URLSearchParams('page=-4')).page,0);
});
test('probability sort includes exact zero and one, keeps missing last in both directions, and preserves evidence order',()=>{
 const rows=[row(.7),row(null),row(0),row(1),row(.7),row(null,false,'error')];
 const asc=jevSortRows(rows,'consciousness','probability_asc'),desc=jevSortRows(rows,'consciousness','probability');
 assert.deepEqual(asc.map(r=>jevProbability(r,'consciousness')),[0,.7,.7,1,null,null]);
 assert.deepEqual(desc.map(r=>jevProbability(r,'consciousness')),[1,.7,.7,0,null,null]);
 assert.equal(asc[1],rows[0]);assert.equal(asc[2],rows[4]);assert.equal(rows[0].answers.topic_consciousness.noul,.7);
});
test('distribution accounts for each boundary once and excludes unassessed rather than assigning zero',()=>{
 const rows=[0,.099,.1,.2,.3,.4,.5,.6,.7,.8,.9,1].map(p=>row(p));
 rows.push(row(null),row(.4,false,'error'),row(.4,false,'unresolved'));
 const d=jevDistribution(rows,'consciousness');
 assert.deepEqual(d.bins,[2,1,1,1,1,1,1,1,1,2]);assert.equal(d.assessed,12);assert.equal(d.excluded,3);
 assert.equal(d.median,.45);assert(Math.abs(d.mean-5.599/12)<1e-12);
 assert.equal(jevBin(1),9);for(const p of [null,undefined,NaN,Infinity,-.01,1.01,'0'])assert.equal(jevBin(p),-1);
 const empty=jevDistribution([row(null)],'consciousness');assert.equal(empty.mean,null);assert.equal(empty.median,null);assert.equal(empty.assessed,0);
});
test('blind bookmarks cannot reveal probabilities through range selection or sorting',()=>{
 const f=jevFilters(new URLSearchParams('blind=1&bin=8&sort=probability_asc&mode=candidate'));
 assert.equal(f.bin,'');assert.equal(f.sort,'order');assert.equal(f.mode,'all');
 for(const bin of ['-1','10','.1','foo'])assert.equal(jevFilters(new URLSearchParams({bin})).bin,'');
 assert.equal(jevFilters(new URLSearchParams('sort=unknown')).sort,'order');
});
