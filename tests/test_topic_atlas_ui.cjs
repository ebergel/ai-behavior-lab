// The browser list must preserve the scientific meaning of each table count.
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const path=require('node:path');
const context=vm.createContext({document:{addEventListener(){}},URLSearchParams});
vm.runInContext(fs.readFileSync(path.join(__dirname,'../behaviorlab/explorer_ui/topic-atlas.js'),'utf8'),context);
const {atlasConversationRows:rows,atlasSorted:sort,atlasParams,atlasRouteFilters}=context;
const plain=value=>JSON.parse(JSON.stringify(value));
const opening=id=>({run_id:id,title:id,models:['local','cloud'],condition:'mirror'});
const hit=(id,turn)=>({run_id:id,message_id:id+':'+turn,turn,speaker:'X',excerpt:'emergence',matches:[{quote:'emergence'}]});
const review=(id,current=true)=>({run_id:id,status:'selected',source_current:current,dictionary_current:true,choice:{topic_id:'emergence',proposal:{message_id:id+':2',turn:2,quote:'collective properties'}}});
const a={topic:'emergence',openings:['early','late','paraphrase','stale','untagged'].map(opening),occurrences:[hit('early',2),hit('early',2),hit('early',8),hit('late',9)],reviews:[review('paraphrase'),review('stale',false)]};

test('each conversation counts once; repeated requires distinct messages',()=>{
 assert.deepEqual(plain(rows(a).map(r=>r.id)),['early','late']);
 assert.deepEqual(plain(rows(a,'early').map(r=>[r.id,r.count,r.first.turn])),[['early',1,2]]);
 assert.deepEqual(plain(rows(a,'repeated').map(r=>[r.id,r.count])),[['early',2]]);
});
test('reviewed initial choices include paraphrases without literal hits and exclude stale reviews',()=>{
 assert.deepEqual(plain(rows(a,'initial').map(r=>[r.id,r.count,r.first.message_id])),[['paraphrase',0,'paraphrase:2']]);
});
test('search keeps the whole conversation and combines with the selected evidence subset',()=>{
 assert.equal(rows(a,'any','cloud').length,2);
 assert.equal(rows(a,'early','emergence').length,1);
 assert.equal(rows(a,'any','no such term').length,0);
 assert.equal(rows(a,'initial','collective').length,1);
});
test('sorting is numeric, reversible and deterministic without mutating source rows',()=>{
 const data=[{id:'a',title:'Alpha',n:2},{id:'b',title:'Beta',n:10},{id:'z',title:'Zulu',n:2}];
 assert.deepEqual(plain(sort(data,'n','desc').map(r=>r.id)),['b','a','z']);
 assert.deepEqual(plain(sort(data,'title','desc').map(r=>r.id)),['z','b','a']);
 assert.equal(data[0].id,'a');
});
test('a transcript return URL retains topic, cohort, mode, sorting, search and page',()=>{
 const f={cohort:'pilot',subject:'emergence',model:'local',panel:'conversations',match:'repeated',sort:'run_hits',direction:'asc',variantSort:'messages',variantDirection:'desc',chatSort:'matches',q:'a & b',page:3};
 assert.deepEqual(plain(atlasRouteFilters(new URLSearchParams(atlasParams(f)))),f);
});
