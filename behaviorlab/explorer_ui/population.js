'use strict';
function populationEscape(value) {return String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
function populationNumber(value) {return typeof value==='number'&&Number.isFinite(value)&&value>=0?value.toLocaleString():'—';}
function populationShare(count,total) {return Number.isFinite(count)&&Number.isFinite(total)&&total>0?(100*count/total).toFixed(1)+'% of this sample':'';}
function populationRecords(rows,key='run_id') {return new Set(rows.map(row=>row[key]).filter(Boolean)).size;}
function populationBanner(scope={},inventory) {
 const p=inventory??(typeof state!=='undefined'?state.boot?.population:null);
 const base=scope.base||{},current=scope.current||{};
 const stage=(label,value,unit,detail,active=false)=>`<div class="population-stage ${active?'population-current':''}"><span class="population-stage-label">${populationEscape(label)}</span><strong class="population-value">${populationNumber(value)} <small>${populationEscape(unit)}</small></strong><span class="population-detail">${populationEscape(detail)}</span></div>`;
 const libraryDetail=`${populationNumber(p?.recorded_messages)} recorded messages · ${populationNumber(p?.synthetic_records)} synthetic fixture records kept separately`;
 const filters=scope.filters||[];
 return `<section class="population-banner" aria-label="Population in view"><div class="population-banner-heading"><h2>Population in view</h2><div class="population-filters" aria-label="Active population restrictions">${(filters.length?filters:['No population filters']).map(label=>`<span class="population-chip">${populationEscape(label)}</span>`).join('')}</div></div><div class="population-stages">${stage('Lab library',p?.records,'conversation records',libraryDetail)}${stage(base.label||'This view’s sample',base.count,base.unit||'target passages',base.detail||'')}${stage('Current subset',current.count,current.unit||base.unit||'target passages',current.detail||populationShare(current.count,base.count),true)}</div>${scope.note?`<p class="population-note">${populationEscape(scope.note)}</p>`:''}</section>`;
}
if(typeof module!=='undefined')module.exports={populationBanner,populationNumber,populationShare,populationRecords};
