const {test}=require('node:test');const assert=require('node:assert/strict');const fs=require('node:fs');const vm=require('node:vm');
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const rubric=JSON.parse(fs.readFileSync('behaviorlab/gem_rubric.json','utf8'));
const ctx=vm.createContext({document:{addEventListener(){}},state:{gems:{rubric,ratings:{gem:'Keep as a gem'},items:[]}},esc,URLSearchParams,option:(v,l,s)=>`<option value="${esc(v)}" ${v===s?'selected':''}>${esc(l)}</option>`});
vm.runInContext(fs.readFileSync('behaviorlab/explorer_ui/dictionary.js','utf8'),ctx);
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
test('full matrix has eight diagonal distributions and all 56 ordered pairs',()=>{
 const rows=[scored('a',0,0),scored('b',50,50),scored('c',100,100)];
 const html=ctx.gemMatrix(rows,ctx.gemFilters({plot:'matrix',item:'a'}));
 assert.equal((html.match(/gem-matrix-cell diagonal/g)||[]).length,8);assert.equal((html.match(/gem-matrix-cell pair/g)||[]).length,56);
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
 const html=ctx.gemMatrix(filtered,f);assert.match(html,/1 filtered messages/);assert.match(html,/r — · n=1/);assert.match(html,/&lt;script&gt;/);assert.doesNotMatch(html,/<script>|NaN|Infinity/);
 const empty=ctx.gemMatrix([],ctx.gemFilters({matrix_scale:'observed'}));assert.match(empty,/No paired scores/);assert.match(empty,/No scores/);assert.doesNotMatch(empty,/NaN|Infinity/);
});
test('word count stays in actual units, handles zero and excludes invalid or stale counts',()=>{
 assert.equal(ctx.gemValue({...item,words:599},'words'),599);assert.equal(ctx.gemValue({...item,words:0},'words'),0);
 for(const words of [undefined,null,-1,2.5,'599',Infinity])assert.equal(ctx.gemValue({...item,words},'words'),null);
 assert.equal(ctx.gemValue({...item,source_current:false,words:599},'words'),null);
 const rows=[{...item,id:'missing',words:null},{...item,id:'long',words:599},{...item,id:'short',words:13}];
 assert.equal(ctx.gemRows(rows,ctx.gemFilters({sort:'words',direction:'asc'})).map(i=>i.id).join(),'short,long,missing');
 assert.equal(ctx.gemRows(rows,ctx.gemFilters({sort:'words',direction:'desc'})).map(i=>i.id).join(),'long,short,missing');
});
test('word ranges cover values over 100 on both matrix modes and constant or empty samples',()=>{
 for(const [values,mode,expected] of [[[13,599],'full',[0,600]],[[213,599],'observed',[210,600]],[[0],'observed',[0,1]],[[599],'observed',[590,600]],[[],'full',[0,10]]])assert.equal(JSON.stringify(ctx.gemMatrixRange(values,mode,'words')),JSON.stringify(expected));
 const rows=[{...scored('a',0,0),words:1},{...scored('b',50,50),words:300},{...scored('c',100,100),words:599}];
 const pair=ctx.gemMatrixPair(rows,'words','contribution');assert.equal(pair.r,1);assert.equal(pair.n,3);
 for(const f of [ctx.gemFilters({x:'words',y:'contribution'}),ctx.gemFilters({x:'contribution',y:'words'})]){
  const html=ctx.gemScatter(rows,f);assert.doesNotMatch(html,/NaN|Infinity/);assert.match(html,/599/);assert.match(html,/Pearson r 1.00 · n=3/);
  for(const m of html.matchAll(/<circle cx="([^"]+)" cy="([^"]+)"/g)){assert.ok(Number(m[1])>=48&&Number(m[1])<=568);assert.ok(Number(m[2])>=42&&Number(m[2])<=242);}
 }
});
test('word histogram bins retain explicit boundaries when filters or plotted pairs change',()=>{
 const rows=[0,59,60,599,600,601].map((words,n)=>({...item,id:String(n),words}));
 assert.equal(ctx.gemBinWidth(rows.slice(0,4),'words'),60);assert.equal(ctx.gemBin(599,'words',60),9);assert.equal(ctx.gemBin(600,'words',60),9);assert.equal(ctx.gemBin(601,'words',60),null);
 const f=ctx.gemFilters({x:'words',bin:'9',bin_axis:'words',bin_width:60});
 assert.equal(ctx.gemRows(rows,f).map(i=>i.words).join(),'599,600');
 const next=ctx.gemMatrixFocus(f,'surprise','contribution');assert.equal(next.bin_axis,'words');assert.equal(next.bin_width,60);assert.equal(ctx.gemRows(rows,next).map(i=>i.words).join(),'599,600');
 const html=ctx.gemHistogram(rows,f);assert.match(html,/data-width="60"/);assert.match(html,/540 to 600 inclusive words: 2 messages/);assert.match(html,/1 values outside this fixed bin range/);
 assert.equal(ctx.gemBinCaption(next),'540–600 words inclusive');
});
test('inclusive word limits combine with existing filters and work while scores are hidden',()=>{
 const rows=[0,13,50,100,599].map((words,n)=>({...item,id:String(n),words}));
 const f=ctx.gemFilters({min_words:'13',max_words:'100',hidden:true});
 assert.equal(ctx.gemRows(rows,f).map(i=>i.words).join(),'13,50,100');
 assert.equal(ctx.gemRows(rows,{...f,model:'missing'}).length,0);
 assert.equal(ctx.gemRows(rows,{...f,min_words:0,max_words:0}).length,1);
 assert.equal(ctx.gemRows([{...item,words:null},{...item,source_current:false}],f).length,0);
 for(const value of ['',null,undefined,'bad',-1,1.5,Infinity])assert.equal(ctx.gemLengthBound(value),null);
 assert.equal(ctx.gemLengthBound('0'),0);
});
test('sample loading caches each cohort separately and retains other filters',async()=>{
 const local=vm.createContext({document:{addEventListener(){}},state:{},routeVersion:0,URLSearchParams,esc});
 vm.runInContext(fs.readFileSync('behaviorlab/explorer_ui/gems.js','utf8'),local);
 const requests=[];local.api=async u=>{requests.push(u);return {items:[]};};
 local.renderSidebar=()=>{};local.renderCompareTray=()=>{};local.renderGems=()=>{};
 await local.loadGems({batch:'pilot',max_words:'50',plot:'matrix'});
 await local.loadGems({batch:'pilot',max_words:'25',plot:'pair'});
 await local.loadGems({batch:'expansion-20260918-v1',max_words:'25',plot:'matrix'});
 assert.deepEqual(requests,['/api/gems?batch=pilot','/api/gems?batch=expansion-20260918-v1']);
 assert.equal(local.state.gemFilters.max_words,'25');assert.equal(local.state.gemFilters.plot,'matrix');
});
test('historical empty replies are labeled and cannot create an unsupported passage reading',()=>{
 const html=ctx.gemDetail({...item,text:'\n',words:0,answers:{}},ctx.gemFilters());
 assert.match(html,/Empty visible reply/);assert.match(html,/minimum words to 1/);
 assert.match(html,/disabled>Save my reading/);
});
