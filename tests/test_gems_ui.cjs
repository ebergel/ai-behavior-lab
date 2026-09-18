const {test}=require('node:test');const assert=require('node:assert/strict');const fs=require('node:fs');const vm=require('node:vm');
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const rubric=JSON.parse(fs.readFileSync('behaviorlab/gem_rubric.json','utf8'));
const ctx=vm.createContext({document:{addEventListener(){}},state:{gems:{rubric,ratings:{gem:'Keep as a gem'},items:[]}},esc,URLSearchParams,option:(v,l,s)=>`<option value="${esc(v)}" ${v===s?'selected':''}>${esc(l)}</option>`});
vm.runInContext(fs.readFileSync('behaviorlab/explorer_ui/gems.js','utf8'),ctx);
const item={id:'one',model:'a',model_label:'Model A',turn:2,speaker:'X',title:'Conversation',text:'A passage',source_current:true,broad_topic:'mind',answers:{surprise:{normalized_score:0},contribution:{normalized_score:84.75}},profile_distance:{value:5,neighbors:[]},readings:[],context:[],sample_role:'pilot',condition:'open',words:2};
test('zero remains observed, absent and stale scores stay unknown',()=>{assert.equal(ctx.gemValue(item,'surprise'),0);assert.equal(ctx.gemValue(item,'complexity'),null);assert.equal(ctx.gemValue({...item,source_current:false},'profile'),null);assert.equal(ctx.gemBin(100),9);assert.equal(ctx.gemBin(null),null);});
test('sorts both distribution tails and keeps missing values last',()=>{const rows=[{...item,id:'unknown',answers:{}},item,{...item,id:'high',answers:{surprise:{normalized_score:90}}}];assert.equal(ctx.gemRows(rows,ctx.gemFilters({sort:'surprise',direction:'asc'})).map(x=>x.id).join(),'one,high,unknown');assert.equal(ctx.gemRows(rows,ctx.gemFilters({sort:'surprise',direction:'desc'})).map(x=>x.id).join(),'high,one,unknown');assert.equal(rows[0].id,'unknown');});
test('hidden mode removes score ordering and bin selection',()=>{const rows=[item,{...item,id:'high',answers:{surprise:{normalized_score:99}}}];const f=ctx.gemFilters({hidden:true,sort:'surprise',bin:'9'});assert.equal(ctx.gemRows(rows,f).map(x=>x.id).join(),'one,high');const html=ctx.gemDetail(item,f);assert.doesNotMatch(html,/84.8|gem-axis-grid|Topic-profile distance:/);assert.match(html,/prior exposure is not controlled/);});
test('researcher and Codex judgments remain separate when filtering',()=>{const rows=[{...item,id:'assistant',readings:[{author:'Codex',rating:'gem',note:'An analysis'}]},{...item,id:'human',readings:[{author:'Local researcher',rating:'gem',note:'Love this'}]}];assert.equal(ctx.gemRows(rows,ctx.gemFilters({reading:'gem'})).map(x=>x.id).join(),'human');assert.equal(ctx.gemRows(rows,ctx.gemFilters({reading:'unread'})).map(x=>x.id).join(),'assistant');});
test('detail safely renders quotations, preceding context and human notes',()=>{const i={...item,text:'<img src=x onerror=bad>',title:'<script>bad</script>',answers:{},context:[{speaker:'<X>',text:'<iframe>'}],readings:[{author:'Local researcher',rating:'gem',note:'</textarea><script>bad</script>',quote:'<img src=x onerror=bad>',axes:{}}]};const html=ctx.gemDetail(i,ctx.gemFilters());assert.doesNotMatch(html,/<img|<script|<iframe/);assert.match(html,/&lt;iframe&gt;/);assert.match(html,/&lt;\/textarea&gt;/);});
test('filters combine text, profile lead, model, own judgment and numeric bin',()=>{const i={...item,readings:[{author:'Local researcher',rating:'gem',note:'The golden idea'}]};const f=ctx.gemFilters({q:'GOLDEN',model:'a',topic:'mind',reading:'gem',bin:'0'});assert.equal(ctx.gemRows([i],f).length,1);assert.equal(ctx.gemRows([i],{...f,bin:'1'}).length,0);assert.equal(ctx.gemRows([i],{...f,model:'other'}).length,0);});
const scored=(id,x,y)=>({...item,id,answers:{surprise:{normalized_score:x},contribution:{normalized_score:y}}});
test('matrix Pearson correlation uses paired observations and preserves zero',()=>{
 const rows=[scored('a',0,100),scored('b',50,50),scored('c',100,0),scored('missing',25,null),{...scored('stale',99,99),source_current:false}];
 const pair=ctx.gemMatrixPair(rows,'surprise','contribution');assert.equal(pair.n,3);assert.equal(pair.r,-1);assert.equal(pair.points[0].x,0);
 assert.equal(ctx.gemMatrixPair(rows.slice(0,2),'surprise','contribution').r,null);
 assert.equal(ctx.gemMatrixPair([scored('a',0,0),scored('b',0,50),scored('c',0,100)],'surprise','contribution').r,null);
 assert.equal(ctx.gemMatrixPair([scored('a',0,0),scored('b',50,100),scored('c',100,0)],'surprise','contribution').r,0);
});
test('matrix ranges remain finite for empty, constant and endpoint samples',()=>{
 for(const [values,expected] of [[[],[0,100]],[[0],[0,10]],[[100],[90,100]],[[50,50],[50,60]],[[.04,18.31],[0,20]]])assert.equal(JSON.stringify(ctx.gemMatrixRange(values,'observed')),JSON.stringify(expected));
 assert.equal(JSON.stringify(ctx.gemMatrixRange([4,12],'full')),JSON.stringify([0,100]));
});
test('full matrix has seven diagonal distributions and all 42 ordered pairs',()=>{
 const rows=[scored('a',0,0),scored('b',50,50),scored('c',100,100)];
 const html=ctx.gemMatrix(rows,ctx.gemFilters({plot:'matrix',item:'a'}));
 assert.equal((html.match(/gem-matrix-cell diagonal/g)||[]).length,7);assert.equal((html.match(/gem-matrix-cell pair/g)||[]).length,42);
 assert.match(html,/r 1.00 · n=3/);assert.match(html,/data-x="profile" data-y="surprise"/);assert.match(html,/gem-matrix-point selected/);
 assert.doesNotMatch(html,/NaN|Infinity/);assert.equal(ctx.gemMatrix(rows,ctx.gemFilters({hidden:true})), '');
 assert.equal(ctx.gemPlots(rows,rows,ctx.gemFilters({hidden:true,plot:'matrix'})), '');
});
test('enlarging a matrix pair preserves the active bin on its original measure',()=>{
 const f=ctx.gemFilters({x:'surprise',bin:'0',model:'a',plot:'matrix',matrix_scale:'observed',item:'a'});
 const next=ctx.gemMatrixFocus(f,'profile','contribution');
 assert.equal(next.plot,'pair');assert.equal(next.x,'profile');assert.equal(next.bin_axis,'surprise');assert.equal(next.bin,'0');assert.equal(next.model,'a');assert.equal(next.item,'a');assert.equal(next.matrix_scale,'observed');
 const rows=[{...scored('low',1,10),profile_distance:{value:99}},{...scored('high',99,10),profile_distance:{value:1}}];
 assert.equal(ctx.gemRows(rows,next).map(i=>i.id).join(),'low');
});
test('matrix plots current filtered rows without unsafe text or unknown-score coercion',()=>{
 const rows=[{...scored('a',0,0),model_label:'<script>bad</script>'},scored('b',10,20),scored('c',20,40)];
 const f=ctx.gemFilters({bin:'0',plot:'matrix'});const filtered=ctx.gemRows(rows,f);
 const html=ctx.gemMatrix(filtered,f);assert.match(html,/1 filtered passages/);assert.match(html,/r — · n=1/);assert.match(html,/&lt;script&gt;/);assert.doesNotMatch(html,/<script>|NaN|Infinity/);
 const empty=ctx.gemMatrix([],ctx.gemFilters({matrix_scale:'observed'}));assert.match(empty,/No paired scores/);assert.match(empty,/No scores/);assert.doesNotMatch(empty,/NaN|Infinity/);
});
