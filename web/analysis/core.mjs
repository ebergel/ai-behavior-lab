// Probability transformations are derived fields. Source scores stay immutable.
export const MISSING = 'Missing / unknown';
export const numeric = v => typeof v === 'number' && Number.isFinite(v);
export const labelNumber = n => String(Number(n.toPrecision(7)));
export function quantileRule(rows, field, count, reference) {
  if (!Number.isInteger(count) || count < 2 || count > 20) throw Error('Choose 2–20 quantile groups.');
  const values = rows.map(r => r[field]).filter(numeric).sort((a,b) => a-b);
  if (!values.length) throw Error('There are no observed scores to fit.');
  const cuts = [...new Set(Array.from({length:count-1}, (_,i) => {
    const pos = (values.length-1)*(i+1)/count, lo = Math.floor(pos), hi = Math.ceil(pos);
    return values[lo] + (values[hi]-values[lo])*(pos-lo);
  }))].filter(v => v > values[0]);
  return {mode:'quantile', cuts, requested:count, reference, reference_n:values.length, method:'linear interpolation (type 7); ties stay together'};
}
export function transform(v, rule={mode:'continuous'}) {
  if (!numeric(v)) return MISSING;
  if (rule.mode === 'continuous') return v;
  if (rule.mode === 'binary') return v >= rule.threshold ? 1 : 0;
  const cuts = rule.cuts || [], idx = cuts.filter(c => v >= c).length;
  const low = idx ? cuts[idx-1] : 0, high = cuts[idx] ?? 100;
  return `${String(idx+1).padStart(2,'0')} · [${labelNumber(low)}, ${labelNumber(high)}${idx===cuts.length ? ']' : ')'}`;
}
export function materialize(rows, rules) {
  return rows.map(row => Object.fromEntries(Object.entries(row).map(([field,value]) => [field,
    field.startsWith('Score · ') ? transform(value,rules[field]) : value])));
}
export function included(row, filters={}) {
  return Object.entries(filters).every(([key,excluded]) => !excluded?.[String(row[key] ?? 'null')]);
}
export function cellRows(rows, filters={}) {
  return rows.filter(row => Object.entries(filters).every(([key,value]) => value===undefined || String(row[key])===String(value)));
}
export function histogram(rows, field) {
  const bins = Array.from({length:10},(_,i)=>({low:i*10, high:(i+1)*10, ids:[]}));
  for (const row of rows) if (numeric(row[field])) bins[Math.min(9,Math.floor(row[field]/10))].ids.push(row.__id);
  return bins;
}
export function observedSummary(rows, field) {
  const values = rows.map(r=>r[field]).filter(numeric);
  return {n:values.length, missing:rows.length-values.length, mean:values.length ? values.reduce((a,b)=>a+b,0)/values.length : null};
}
const KEYS=['rows','cols','vals','aggregatorName','rendererName','valueFilter','rowOrder','colOrder'];
export function cleanPivot(state) { return Object.fromEntries(KEYS.filter(k=>state[k]!==undefined).map(k=>[k,state[k]])); }
export function numericAggregator(kind) {
  return ([field]) => () => {
    let n=0, sum=0, ones=0;
    return {numInputs:1, push(row){if(numeric(row[field])) {n++;sum+=row[field];if(row[field]===1)ones++;}},
      value(){return !n ? null : kind==='count' ? n : kind==='percent' ? ones/n*100 : sum/n;},
      format(v){return v==null?'—':kind==='count'?String(v):v.toLocaleString(undefined,{maximumFractionDigits:2})+(kind==='percent'?'%':'');}};
  };
}
export function topicOverview(rows, topics, threshold=80) {
  return topics.map(topic=>{
    const values=rows.map(r=>r[topic.field]).filter(numeric),n=values.length;
    const bins=Array(10).fill(0);for(const v of values)bins[Math.min(9,Math.floor(v/10))]++;
    const candidates=values.filter(v=>v>=threshold).length;
    return {...topic,n,missing:rows.length-n,candidates,share:n?candidates/n*100:null,
      mean:n?values.reduce((a,b)=>a+b,0)/n:null,bins};
  });
}

// Topic selection is presentation state. Keep it separate from transforms,
// pivot filters, chart choices, and passage selections so browsing the topic
// list cannot change the analysis itself.
export function normalizeTopicSelector(topics=[], config={}) {
  const list=Array.isArray(topics)?topics:[], valid=new Set(list.map(t=>t.field));
  const requested=config.topicSelector?.field;
  const chartField=config.chart?.x;
  const consciousness=list.find(t=>t.id==='consciousness')?.field;
  const groupKeys=new Set(list.map(t=>t.group));
  const requestedGroup=config.topicSelector?.group;
  const candidate=[requested,chartField,consciousness,list[0]?.field].find(f=>f&&valid.has(f))||'';
  const candidateTopic=list.find(t=>t.field===candidate);
  const group=requestedGroup==='all'||(requestedGroup&&groupKeys.has(requestedGroup))?requestedGroup:(candidateTopic?.group||list[0]?.group||'all');
  const topic=group==='all'||candidateTopic?.group===group?candidateTopic:list.find(t=>t.group===group);
  const field=topic?.field||candidate;
  return {group,field};
}

export function topicGroups(topics=[], labels={}) {
  const groups=new Map();
  for(const topic of (Array.isArray(topics)?topics:[])) {
    const key=topic.group||'other';
    if(!groups.has(key)) groups.set(key,{key,label:labels[key]||key,count:0,topics:[]});
    const group=groups.get(key);group.count++;group.topics.push(topic);
  }
  return [...groups.values()].map(group=>({...group,topics:group.topics.slice().sort((a,b)=>String(a.title||a.field).localeCompare(String(b.title||b.field)))}));
}

export function targetFilterStatus(topics=[], targetFilter=null) {
  if(!targetFilter||!targetFilter.field) return {active:false,valid:true,topic:null,reason:''};
  const topic=(Array.isArray(topics)?topics:[]).find(t=>t.field===targetFilter.field);
  const groupValid=targetFilter.group==='all'||!targetFilter.group||topic?.group===targetFilter.group;
  const threshold=targetFilter.threshold;
  if(!topic) return {active:true,valid:false,topic:null,reason:'The saved target topic is unavailable in this dataset.'};
  if(!groupValid) return {active:true,valid:false,topic,reason:'The saved target topic tier no longer contains this topic.'};
  if(typeof threshold!=='number'||![50,80,90].includes(threshold)) return {active:true,valid:false,topic,reason:'The saved target threshold is invalid.'};
  return {active:true,valid:true,topic,threshold,reason:''};
}

export function filterTargetRows(rows=[], targetFilter=null, topics=[]) {
  const status=targetFilterStatus(topics,targetFilter);
  if(!status.active) return rows;
  if(!status.valid) return [];
  return rows.filter(row=>numeric(row[status.topic.field])&&row[status.topic.field]>=status.threshold);
}
