const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const routes=[];
const context=vm.createContext({document:{addEventListener(){},getElementById(){return null;}},URLSearchParams,
  state:{tasks:{statuses:{active:'In progress',done:'Done',ideas:'Ideas',next:'Next'},streams:{'':'Unsorted',experiments:'Experiments',synthesis:'Research synthesis',tools:'Exploration tools'},entries:[]},editingTask:{id:'task1'}},
  esc,icon:()=>'',option:(v,l,s)=>`<option value="${esc(v)}" ${v===s?'selected':''}>${esc(l)}</option>`,
  $:()=>({close(){}}),go:p=>routes.push(p),musingParagraphs:s=>`<p>${esc(s)}</p>`});
vm.runInContext(fs.readFileSync('behaviorlab/explorer_ui/tasks.js','utf8'),context);
const card={id:'c1',title:'<script>alert(1)</script>',notes:'<img onerror="bad">',finish:'A result',blocker:'A review',completion:'Checked',author:'Local researcher',status:'ideas',stream:'tools',archived:false,position:1,created_at:'2026-09-18',links:[],source:null};
test('board columns follow workflow rather than JSON key sorting',()=>{
 const html=context.taskBoardColumns([]);
 assert.ok(html.indexOf('aria-label="Ideas"')<html.indexOf('aria-label="Next"'));
 assert.ok(html.indexOf('aria-label="Next"')<html.indexOf('aria-label="In progress"'));
 assert.ok(html.indexOf('aria-label="In progress"')<html.indexOf('aria-label="Done"'));
});
test('task text and source quotations cannot inject HTML',()=>{
 const html=context.taskCard(card);
 assert.match(html,/&lt;script&gt;/);assert.match(html,/&lt;img onerror=&quot;bad&quot;&gt;/);
 assert.doesNotMatch(html,/<script>|<img/);
 const source=context.taskSource({source:{kind:'musing',title:'<title>',author:'<author>',revision:1,body:'<body>',source:{original_text:'<original>'}}});
 for(const name of ['title','author','body','original'])assert.ok(source.includes('&lt;'+name+'&gt;'));
});
test('search, stream and archive filters combine without recoding card state',()=>{
 assert.equal(context.taskMatches(card,'RESULT','tools',false),true);
 assert.equal(context.taskMatches(card,'RESULT','experiments',false),false);
 assert.equal(context.taskMatches(card,'','',true),false);
 assert.equal(context.taskMatches({...card,archived:true},'review','tools',true),true);
});
test('priority is stable and current focus excludes archived cards',()=>{
 const cards=[{...card,id:'a',position:8,status:'next',title:'Later'},{...card,id:'b',position:-1,status:'next',title:'First'},{...card,id:'c',position:-2,status:'active',archived:true,title:'Archived item'}];
 context.state.tasks.entries=cards;
 const html=context.taskFocus();
 assert.ok(html.indexOf('First')<html.indexOf('Later'));
 assert.doesNotMatch(html,/Archived item/);
 assert.match(html,/Nothing in progress/);
 assert.equal(cards[0].id,'a');
});
test('passage links preserve exact message, path and return task',()=>{
 context.taskFollowLink({kind:'passage',id:'run1',message:'m2',branch:'right'});
 assert.equal(JSON.stringify(routes.at(-1)),JSON.stringify({run:'run1',message:'m2',branch:'right',fromTask:'task1'}));
 context.taskFollowLink({kind:'musing',id:'original'});
 assert.equal(routes.at(-1).musing,'original');
 const n=routes.length;context.taskFollowLink({kind:'url',url:'javascript:bad'});assert.equal(routes.length,n);
});
