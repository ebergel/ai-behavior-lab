const {test}=require('node:test');const assert=require('node:assert/strict');const fs=require('node:fs');const vm=require('node:vm');
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const catalog=JSON.parse(fs.readFileSync('behaviorlab/lab_dictionary.json','utf8'));
const rubric=JSON.parse(fs.readFileSync('behaviorlab/gem_rubric.json','utf8'));
catalog.rubric={...rubric,file_sha256:'test-hash'};
for(const a of rubric.axes)catalog.entries.find(e=>e.id===a.id).rubric=a;
function context(){const main={innerHTML:''};let lastUrl;
 const c=vm.createContext({document:{addEventListener(){}},state:{dictionary:catalog,view:'dictionary',dictionaryFilters:{}},esc,URLSearchParams,history:{replaceState(a,b,url){lastUrl=url;}},$:()=>main,pageTop:(t)=>`<h1>${esc(t)}</h1>`,option:(v,l,s)=>`<option value="${esc(v)}" ${v===s?'selected':''}>${esc(l)}</option>`});
 vm.runInContext(fs.readFileSync('behaviorlab/explorer_ui/dictionary.js','utf8'),c);return {c,main,url:()=>lastUrl};}
test('Gem definition links retain complete matrix, passage and filter state through related terms',()=>{
 const {c}=context();const f={plot:'matrix',matrix_scale:'observed',model:'a',item:'selected',x:'profile',bin:'1',bin_axis:'surprise',hidden:true,q:'words & <text>'};
 c.state.view='gems';c.state.gemFilters=f;
 const p=new URLSearchParams(c.dictionaryUrl('profile').slice(1));assert.equal(p.get('view'),'dictionary');assert.equal(p.get('term'),'profile');assert.deepEqual(JSON.parse(p.get('fromGem')),f);
 c.state.view='dictionary';c.state.dictionaryFilters=c.dictionaryParams(Object.fromEntries(p));
 const related=new URLSearchParams(c.dictionaryUrl('surprise',{q:'',category:''}).slice(1));assert.deepEqual(JSON.parse(related.get('fromGem')),f);
});
test('search uses synonyms, technical detail and category with AND across words',()=>{
 const {c}=context();const match=(q,category='')=>c.dictionaryMatches(catalog.entries,{q,category}).map(e=>e.id);
 assert.ok(match('outlier').includes('profile'));assert.ok(match('CALIBRATION').includes('confidence'));
 assert.deepEqual(Array.from(match('outlier RMS','measures')),['profile']);assert.equal(match('outlier','evidence').length,0);
 assert.equal(match('no_such_definition').length,0);
});
test('entry rendering labels illustrative examples, escapes prose and includes exact rubric criteria',()=>{
 const {c}=context();const e={...catalog.entries[0],definition:'<script>unsafe</script>',example:'<img src=x>',sources:['<iframe>']};
 const html=c.dictionaryEntry(e,catalog);assert.doesNotMatch(html,/<script>|<img|<iframe>/);assert.match(html,/&lt;script&gt;/);
 assert.match(html,/NOT SCORED CORPUS EVIDENCE/);for(const criterion of e.rubric.criteria)assert.ok(html.includes(esc(criterion)));
 assert.match(html,/25 ON DISPLAY SCALE/);assert.match(html,/gem-development-v1/);
});
test('invalid return state cannot become an external return URL',()=>{
 const {c}=context();for(const bad of ['javascript:alert(1)','[]','null','"https://elsewhere"','{broken'])assert.equal(c.dictionaryParams({fromGem:bad}).fromGem,'');
 c.state.dictionaryFilters=c.dictionaryParams({fromGem:JSON.stringify({q:'"<script>'})});
 c.renderDictionary();assert.doesNotMatch(c.$().innerHTML,/<script>/);assert.match(c.$().innerHTML,/Return to your Gem view/);
});
test('unknown term/category resolves to a visible canonical entry; empty searches have no stale detail',()=>{
 const {c,main,url}=context();c.state.dictionaryFilters=c.dictionaryParams({term:'unknown',category:'invalid'});c.renderDictionary();
 assert.equal(c.state.dictionaryFilters.category,'');assert.equal(c.state.dictionaryFilters.term,'surprise');assert.match(main.innerHTML,/aria-current="true"/);assert.match(url(),/term=surprise/);
 c.state.dictionaryFilters=c.dictionaryParams({term:'surprise',q:'no_such_definition'});c.renderDictionary();assert.match(main.innerHTML,/No terms match/);assert.doesNotMatch(main.innerHTML,/id="dictionary-title"/);assert.equal(c.state.dictionaryFilters.term,'');
});
