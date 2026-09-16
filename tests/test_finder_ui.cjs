const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const context=vm.createContext({document:{addEventListener(){}},state:{boot:{model_catalog:{'exact/id':{id:'exact/id',label:'Clear alias',color:'gemma',developer:'Google',weights:'Open weights'}}},view:'finder',finderFilters:{models:['first'],identity:['Anonymous-AI'],cohort:'study'},activeStudy:null},esc:s=>String(s??'').replaceAll('<','&lt;').replaceAll('"','&quot;')});
vm.runInContext(fs.readFileSync('behaviorlab/explorer_ui/finder.js','utf8'),context);
const plain=x=>JSON.parse(JSON.stringify(x));
test('multi-selection toggles one value and preserves other conditions',()=>{
 const f={models:['one'],identity:['Mirror'],role:'interventions'};
 assert.deepEqual(plain(context.finderToggle(f,'models','two')),{...f,models:['one','two']});
 assert.deepEqual(plain(context.finderToggle(f,'models','one')),{...f,models:[]});
 assert.deepEqual(f.models,['one']);
});
test('finder route round trips exact IDs and selected page',()=>{
 const f={models:['hf.co/a:b','a & b'],model_match:'all',q:'x < y'};
 const p=new URLSearchParams(context.finderParams(f,40));
 assert.deepEqual(JSON.parse(p.get('finder')),f);assert.equal(p.get('offset'),'40');
});
test('model badges preserve exact identity, color and noninteractive form',()=>{
 const html=context.modelBadge('exact/id');assert.match(html,/Clear alias/);assert.match(html,/model-gemma/);assert.match(html,/data-model="exact\/id"/);
 assert.match(context.modelBadge('exact/id',false),/^<span/);
 assert.doesNotMatch(context.modelBadge('<script>',false),/<script>/);
});
test('clicking a badge in finder retains other selected conditions',()=>{
 assert.deepEqual(plain(context.finderModelFilter('second','interventions')),{models:['second'],identity:['Anonymous-AI'],cohort:'study',role:'interventions'});
});
test('rapid tag and match-rule changes use the pending selection and invalidate old results',()=>{
 const routes=[];context.go=p=>routes.push(plain(p));context.state.request=10;
 context.finderNavigate({models:['Gemma','Haiku']});context.finderGo({model_match:'all'});
 assert.deepEqual(JSON.parse(routes[1].finder),{models:['Gemma','Haiku'],model_match:'all'});
 assert.equal(context.state.request,12);
});
