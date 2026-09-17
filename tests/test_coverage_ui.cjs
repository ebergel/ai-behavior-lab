const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const routes=[];
const c=vm.createContext({document:{addEventListener(){}},state:{request:0,coverageFilters:{scope:'atlas',axis:'identity',group:'model',task:'Open-ended'}},go:x=>routes.push(x),num:n=>String(n),esc:s=>String(s??'').replaceAll('<','&lt;').replaceAll('"','&quot;')});
vm.runInContext(fs.readFileSync('behaviorlab/explorer_ui/coverage.js','utf8'),c);
test('cell navigation retains scope and task and resets pagination',()=>{
 c.coverageCell('exact/model:id','Anonymous-AI');
 const p=JSON.parse(routes.at(-1).coverage);
 assert.equal(p.row,'exact/model:id');assert.equal(p.column,'Anonymous-AI');assert.equal(p.scope,'atlas');assert.equal(p.task,'Open-ended');assert.equal(p.page,0);
 assert.equal(c.state.request,1);
});
test('return route retains zero-cell selection and page',()=>{
 const f={scope:'inventory',axis:'participants',group:'family',row:'Google',column:'3',page:2};
 const p=c.coverageParams(f);assert.equal(p.view,'coverage');
 assert.deepEqual(JSON.parse(p.coverage),{...JSON.parse(JSON.stringify(c.coverageFilters())),...f});
});
test('zero cells remain navigable and labels escape external metadata',()=>{
 const html=c.coverageCellHtml({key:'<model>',label:'<model>'},{value:'3',records:0,flagged:0,branched:0});
 assert.match(html,/coverage-cell empty/);assert.match(html,/data-action="coverage-cell"/);
 assert.match(html,/&lt;model>/);assert.doesNotMatch(html,/disabled/);
});
