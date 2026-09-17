const test=require('node:test');
const assert=require('node:assert/strict');
const {jevMatch,jevDecision,jevProbability,jevFilters}=require('../behaviorlab/explorer_ui/jev-atlas.js');
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
 const f=jevFilters(new URLSearchParams({batch:'abc',topic:'emergence',mode:'semantic_only',page:'2',item:'x',blind:'1'}));
 assert.equal(f.batch,'abc');assert.equal(f.mode,'semantic_only');assert.equal(f.page,2);assert.equal(f.item,'x');assert.equal(f.blind,true);
 assert.equal(jevFilters(new URLSearchParams('mode=invalid&page=-4')).mode,'all');
 assert.equal(jevFilters(new URLSearchParams('page=-4')).page,0);
});
