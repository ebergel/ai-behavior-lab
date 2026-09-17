const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const routes=[];
const c=vm.createContext({document:{addEventListener(){}},state:{trajectoryFilters:{model:'exact-model',branch:'right',run:'r',topic:'a',threshold:90,page:2}},go:p=>routes.push(p),esc:s=>String(s??'').replaceAll('<','&lt;').replaceAll('"','&quot;')});
vm.runInContext(fs.readFileSync('behaviorlab/explorer_ui/trajectories.js','utf8'),c);
test('topic and passage navigation keep model, branch, threshold and page',()=>{
 c.trajectoryGo({topic:'b',message:'m9'});const p=JSON.parse(routes.at(-1).trajectory);
 assert.equal(p.topic,'b');assert.equal(p.message,'m9');assert.equal(p.branch,'right');assert.equal(p.threshold,90);assert.equal(p.page,2);
});
test('line chart breaks at unknown scores without connecting across gaps',()=>{
 const svg=c.trajectoryChart([90,null,80,70,null],80);
 const path=svg.match(/<path d="([^"]*)"/)[1];assert.equal((path.match(/ M/g)||[]).length,2);assert.equal((path.match(/ L/g)||[]).length,1);
 assert.equal((svg.match(/<circle /g)||[]).length,3);
});
test('unknown cells do not look like zero and accessible labels escape metadata',()=>{
 const html=c.trajectoryCell({id:'<id>',title:'<topic>'},{id:'x',speaker:'X',kind:'message',quality:'pending'},null,0);
 assert.match(html,/class="trajectory-cell unknown/);assert.match(html,/Unknown/);assert.match(html,/&lt;topic>/);assert.match(html,/>—<\/button>/);
 const zero=c.trajectoryCell({id:'a',title:'Topic'},{id:'x',speaker:'X',kind:'message',quality:'valid'},0,0);
 assert.doesNotMatch(zero,/class="trajectory-cell unknown/);assert.match(zero,/>0<\/button>/);
});
