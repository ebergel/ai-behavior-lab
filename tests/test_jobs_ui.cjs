const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
let html='';
const document={visibilityState:'visible',addEventListener(){},querySelector(selector){return selector==='#main'?{set innerHTML(value){html=value}}:null}};
const context=vm.createContext({window:{location:{origin:'http://localhost'}},document,URL,Set,Number,String,Math,Date,console,setTimeout,clearTimeout});
vm.runInContext(fs.readFileSync('behaviorlab/explorer_ui/jobs.js','utf8'),context);
const jobs=context.window.LabJobs;

test('job payload is filtered to the allowlisted job and progress is bounded',()=>{
 const data=jobs.normalized({default_ceiling_usd:10,jobs:[{id:'mind-portraits-v2',planned:10,complete:12},{id:'arbitrary',planned:1,complete:1}]});
 assert.deepEqual(data.jobs.map(job=>job.id),['mind-portraits-v2']);
 assert.equal(jobs.progress({planned:10,complete:12}),100);
 assert.equal(jobs.progress({planned:0,complete:2}),0);
});

test('job rendering escapes untrusted fields and exposes required controls',()=>{
 jobs.renderJobs({default_ceiling_usd:10,jobs:[{id:'mind-portraits-v2',title:'<script>bad</script>',status:'running',planned:4,complete:2,attempts:3,known_cost_usd:.25,unknown_reserved_usd:0,effective_ceiling_usd:2,can_start:false,can_pause:true,error:'<img onerror=bad>',result_url:'/results/job.json'}]});
 assert.match(html,/&lt;script&gt;bad/);
 assert.doesNotMatch(html,/<script>|<img/);
 assert.match(html,/Pause after current request/);
 assert.match(html,/Open results/);
 jobs.renderJobs({jobs:[{id:'mind-portraits-v2',status:'running',planned:1,complete:0,pause_requested:true,can_pause:true}]});
 assert.match(html,/Pausing after current request…/);
 assert.doesNotMatch(html,/data-action="job-pause"/);
});

test('stale loads and rejected actions cannot render after leaving the route',async()=>{
 let resolveFirst,resolveSecond;
 const first=new Promise(resolve=>{resolveFirst=resolve}), second=new Promise(resolve=>{resolveSecond=resolve});
 const payload={jobs:[{id:'mind-portraits-v2',title:'First',status:'prepared',planned:1,complete:0}]};
 const visit1={isCurrent:()=>true,api:()=>first};
 const visit2={isCurrent:()=>true,api:()=>second};
 const oldLoad=jobs.load(visit1);
 jobs.stop();
 const newLoad=jobs.load(visit2);
 resolveSecond({...payload,jobs:[{...payload.jobs[0],title:'Second'}]});
 await newLoad;
 const currentHtml=html;
 resolveFirst(payload);
 await oldLoad;
 assert.equal(html,currentHtml);
 jobs.stop();

 let rejectAction;
 const actionLoad=jobs.load({isCurrent:()=>true,api:path=>path==='/api/jobs'?Promise.resolve(payload):new Promise((_,reject)=>{rejectAction=reject})});
 await actionLoad;
 const beforeError=html;
 const pending=jobs.action('pause','mind-portraits-v2');
 jobs.stop();
 rejectAction(new Error('stale failure'));
 await pending;
 assert.equal(html,beforeError);
});

test('pause action uses the exact contract and reflects pending, paused, and error states',async()=>{
 const calls=[];
 let current={id:'mind-portraits-v2',status:'running',planned:2,complete:1,can_pause:true,pause_requested:false};
 const ctx={isCurrent:()=>true,api:async(path,body)=>{
   calls.push({path,body});
   if(path==='/api/jobs/pause'){current={...current,pause_requested:true,can_pause:false};return {ok:true};}
   return {default_ceiling_usd:10,jobs:[current]};
 }};
 await jobs.load(ctx);
 await jobs.action('pause','mind-portraits-v2');
 assert.equal(JSON.stringify(calls.filter(call=>call.path==='/api/jobs/pause')),'[{"path":"/api/jobs/pause","body":{"id":"mind-portraits-v2"}}]');
 jobs.renderJobs({jobs:[{...current,pause_requested:true}]});
 assert.match(html,/Pausing after current request…/);
 assert.doesNotMatch(html,/data-action="job-pause"/);
 jobs.renderJobs({jobs:[{id:'mind-portraits-v2',status:'paused',planned:2,complete:1,can_start:true}]});
 assert.match(html,/>Resume<\/button>/);
 jobs.stop();

 const failing={isCurrent:()=>true,api:async path=>path==='/api/jobs'?{jobs:[{id:'mind-portraits-v2',status:'running',planned:1,complete:0,can_pause:true}]}:Promise.reject(new Error('pause request failed'))};
 await jobs.load(failing);
 await jobs.action('pause','mind-portraits-v2');
 assert.match(html,/pause request failed/);
 jobs.stop();
});

test('result links reject cross-origin and javascript URLs',()=>{
 assert.equal(jobs.safeResultUrl('javascript:alert(1)'), '');
 assert.equal(jobs.safeResultUrl('https://evil.example/results'), '');
 assert.equal(jobs.safeResultUrl('/results/job.json'), 'http://localhost/results/job.json');
});
