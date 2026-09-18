const {test}=require('node:test');const assert=require('node:assert/strict');
global.document={addEventListener(){}};
const {lensPage,lensFilters,lensRows,lensSummary}=require('../behaviorlab/explorer_ui/discourse.js');
test('corpus pagination clamps stale pages while summaries keep the full subset',()=>{
 const rows=Array.from({length:205},(_,i)=>({id:i,probabilities:{name_and_portrait:{f01:i<200?.8:.2}}}));
 assert.equal(lensPage(rows,0).rows.length,100);assert.equal(lensPage(rows,999).page,2);assert.equal(lensPage(rows,2).rows.length,5);
 assert.equal(lensSummary(rows,'f01','name_and_portrait').n,205);assert.equal(lensSummary(rows,'f01','name_and_portrait').candidates,200);
 assert.equal(lensPage([],4).page,0);
});
test('corpus scope separates technical runs and follows recorded turn order',()=>{
 const sample=(id,run,turn,category)=>({id,run_id:run,turn,inventory_category:category,kind:'transcript',words:20,text:'text',title:run,model_label:'test',probabilities:{}});
 const data={samples:[sample('late','r',8,'conversation'),sample('check','tech',1,'technical_or_short'),sample('early','r',2,'conversation')]};
 const f=lensFilters({batch:'corpus',run:'r',sort:'turn'});assert.equal(f.category,'conversation');assert.equal(f.batch,'corpus');
 assert.deepEqual(lensRows(data,f).map(s=>s.id),['early','late']);
 assert.deepEqual(lensRows(data,lensFilters({batch:'corpus',category:'technical_or_short'})).map(s=>s.id),['check']);
 assert.equal(lensFilters({}).batch,'pilot');
});
