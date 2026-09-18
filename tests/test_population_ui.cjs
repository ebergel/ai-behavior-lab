const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const {populationBanner,populationNumber,populationShare,populationRecords}=require('../behaviorlab/explorer_ui/population.js');

test('population counts distinguish true zero from unknown and share uses the sample denominator',()=>{
 assert.equal(populationNumber(0),'0');
 for(const value of [undefined,null,NaN,Infinity,'0',-1])assert.equal(populationNumber(value),'—');
 assert.equal(populationShare(3,48),'6.3% of this sample');
 assert.equal(populationShare(0,48),'0.0% of this sample');
 assert.equal(populationShare(0,0),'');
 assert.equal(populationRecords([{run_id:'a'},{run_id:'a'},{run_id:'b'},{}]),2);
});

test('population labels escape text and preserve distinct target and fixture units',()=>{
 const html=populationBanner({base:{count:48,detail:'<script>sample</script>'},current:{count:0},filters:['Search: <img onerror=x>']},{records:472,recorded_messages:11245,synthetic_records:60});
 assert.match(html,/472 <small>conversation records/);
 assert.match(html,/48 <small>target passages/);
 assert.match(html,/0 <small>target passages/);
 assert.match(html,/60 synthetic fixture records kept separately/);
 assert.match(html,/&lt;script&gt;/);
 assert.doesNotMatch(html,/<script|<img/);
 assert.match(populationBanner({base:{count:0},current:{count:0}},{}),/— <small>conversation records/);
});

const ctx=vm.createContext({state:{boot:{population:{records:472,recorded_messages:11245,synthetic_records:60}}},document:{addEventListener(){}},short:s=>s});
vm.runInContext(fs.readFileSync('behaviorlab/explorer_ui/population.js','utf8'),ctx);
vm.runInContext(fs.readFileSync('behaviorlab/explorer_ui/discourse.js','utf8'),ctx);

test('Mind banner counts the full evidence sample and combined filtered targets before rendering',()=>{
 const samples=[{id:'a',kind:'transcript',run_id:'r1',words:100,model:'m',text:'text',probabilities:{},topic_scores:{consciousness:90}},
 {id:'b',kind:'transcript',run_id:'r1',words:20,model:'m',text:'text',probabilities:{},topic_scores:{consciousness:80}},
 {id:'c',kind:'transcript',run_id:'r2',words:100,model:'m',text:'text',probabilities:{},topic_scores:{consciousness:70}},
 {id:'control',kind:'synthetic',words:100,model:'',text:'text',probabilities:{}}];
 const data={samples,topic_filter:{available:true,topics:[{id:'consciousness',title:'Consciousness'}]}};
 const filters=ctx.lensFilters({topic:'consciousness',topic_threshold:'80',min:'50',variant:'name_and_portrait'});
 const rows=ctx.lensRows(data,filters);
 assert.equal(rows.length,1);
 const html=ctx.discoursePopulation(data,filters,rows);
 assert.match(html,/3 <small>target passages/);
 assert.match(html,/1 <small>target passages/);
 assert.match(html,/2 source records · 1 synthetic controls/);
 assert.match(html,/33.3% of this sample · 1 source records/);
 assert.match(html,/Topic: Consciousness ≥ 80%/);
 assert.match(html,/Words ≥ 50/);
 assert.match(html,/Assessment wording: Names \+ portraits/);
 const controls=ctx.lensFilters({kind:'synthetic',topic:'unavailable',variant:'definition_only'});
 const controlHtml=ctx.discoursePopulation(data,controls,ctx.lensRows(data,controls));
 assert.match(controlHtml,/1 <small>synthetic control texts/);
 assert.doesNotMatch(controlHtml,/Topic: unavailable/);
 assert.match(controlHtml,/No population filters/);
});

vm.runInContext(fs.readFileSync('behaviorlab/explorer_ui/gems.js','utf8'),ctx);
vm.runInContext(fs.readFileSync('behaviorlab/explorer_ui/jev-atlas.js','utf8'),ctx);

test('Gem banner follows sample items, score-bin intersection and hidden-mode bypass',()=>{
 const data={items:[0,85,90].map((score,i)=>({id:String(i),run_id:i===2?'r2':'r1',words:20,model:'m',model_label:'Readable model',text:'answer',readings:[],answers:{surprise:{normalized_score:score}}})),batches:[{id:'pilot',title:'Original pilot'}],topics:[],ratings:{},rubric:{axes:[{id:'surprise',title:'Surprise'}]}};
 ctx.state.gems=data;
 const f=ctx.gemFilters({batch:'pilot',model:'m',bin:'8',bin_axis:'surprise'});
 let rows=ctx.gemRows(data.items,f),html=ctx.gemPopulationBanner(data,f,rows);
 assert.match(html,/Original pilot · 2 source records/);
 assert.match(html,/3 <small>target passages/);
 assert.match(html,/1 <small>target passages/);
 assert.match(html,/Model: Readable model/);
 assert.match(html,/Surprise: 80–90 \(upper bound excluded\)/);
 const hidden={...f,hidden:true};rows=ctx.gemRows(data.items,hidden);html=ctx.gemPopulationBanner(data,hidden,rows);
 assert.equal(rows.length,3);assert.doesNotMatch(html,/Surprise: 80/);
 const empty={...f,q:'no matching words'};html=ctx.gemPopulationBanner(data,empty,ctx.gemRows(data.items,empty));
 assert.match(html,/0 <small>target passages/);
});

test('JEV banner counts the whole queue, not the page or number of questions',()=>{
 const rows=Array.from({length:30},(_,i)=>({id:String(i),run_id:'r'+Math.floor(i/3),models:['m'],text:'answer',run_title:'run',status:'complete',answers:{topic_mind:{noul:i<20?.85:.2}},literal:{mind:[]}}));
 const data={rows,reviews:[],plan:{dictionary:[{id:'mind',title:'Mind'}],thresholds:{candidate:.8,unlikely:.2}}};
 ctx.state.jev=data;ctx.state.jevIndex={batches:[{id:'batch',title:'Thirty targets'}]};
 const f={batch:'batch',topic:'mind',mode:'candidate',q:'',sort:'order',bin:'',page:1};ctx.state.jevFilters=f;
 let selected=ctx.jevSelection(),html=ctx.jevPopulationBanner(data,f,selected);
 assert.equal(selected.length,20);assert.match(html,/30 <small>target passages/);assert.match(html,/20 <small>target passages/);
 assert.match(html,/Thirty targets · 10 source records/);assert.match(html,/Topic: Mind/);
 const all={...f,mode:'all'};html=ctx.jevPopulationBanner(data,all,rows);
 assert.match(html,/No population filters/);assert.doesNotMatch(html,/Topic: Mind/);
 const bin={...all,bin:'8'};ctx.state.jevFilters=bin;html=ctx.jevPopulationBanner(data,bin,ctx.jevSelection());
 assert.match(html,/Topic: Mind/);assert.match(html,/Probability: 80–&lt;90%/);
 assert.match(html,/before pagination/);assert.match(html,/distributions describe the full batch/);
});
