"""Read-only audit of the settled Mind & discourse corpus, retaining missingness."""
import argparse
from collections import Counter
from pathlib import Path
from statistics import mean
import json
from behaviorlab import discourse_corpus as corpus
from behaviorlab.common import require, fingerprint
from behaviorlab.jev_atlas import read_record, write_record, locked, now
from behaviorlab.research_bundle import export_notebook


def audit(workspace):
    workspace=Path(workspace).resolve();root=workspace/corpus.EXECUTION
    with locked(root/'.runner.lock',blocking=False):
        release=read_record(root/'release.json')
        require(release['software_sha256']==corpus.software(),'Original execution software changed')
        plan,results,attempts,ledger,fatal=corpus.replay(workspace,root,release)
        groups={}
        for category in ('conversation','technical_or_short','synthetic'):
            targets=[t for t in plan['targets'] if ('synthetic' if t['kind']=='synthetic' else t['inventory_category'])==category]
            packs={}
            for pack in plan['packs']:
                values=[results[(t['id'],pack)]['answers'] for t in targets if (t['id'],pack) in results]
                rows=[]
                for f in plan['spec']['features']:
                    scores=[r[f['id']]['noul'] for r in values]
                    rows.append({'id':f['id'],'label':f['label'],'family':f['family'],'observed':len(scores),
                                 'mean_probability':mean(scores) if scores else None,'at_least_80':sum(x>=.8 for x in scores)})
                packs[pack]=sorted(rows,key=lambda r:-(r['mean_probability'] or 0))
            groups[category]={'messages':len(targets),'both_wordings':sum(all((t['id'],v) in results for v in plan['packs']) for t in targets),'features':packs}
        missing=[{'target':t['id'],'variant':v,'kind':t['kind'],'category':t.get('inventory_category'),'run_id':t.get('run_id'),'message_id':t.get('message_id'),'attempts':attempts[(t['id'],v)]} for t in plan['targets'] for v in plan['packs'] if (t['id'],v) not in results]
        return {'schema':'behaviorlab.discourse-corpus-audit/1','at':now(),'author':'Codex',
          'status':'complete' if not missing else 'settled_with_missing_assessments','plan_sha256':plan['sha256'],'release_sha256':release['sha256'],
          'source_and_original_software_verified':True,'completed_assessments':len(results),'planned_assessments':plan['counts']['logical_requests'],
          'probabilities':sum(len(x['answers']) for x in results.values()),'new_attempts':len(ledger),'reused':sum(x['origin']=='reuse' for x in results.values()),
          'known_new_cost_usd':sum(x['known_nanodollars'] or 0 for x in ledger)/1e9,
          'unknown_reserved_usd':sum(x['charge_nanodollars'] for x in ledger if x['known_nanodollars'] is None)/1e9,
          'missing':missing,'fatal_receipts':fatal,'groups':groups,
          'notebook_sha256':fingerprint(export_notebook(workspace/'explorer'/'notes.sqlite')),
          'interpretation':'Message-weighted exploratory descriptions of classifier answers, not author similarity, model quality, causal effects or independent human validation. Wordings operationalize different constructs. Missing scores excluded from means; controls and technical messages separate.'}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--workspace',default='workspace');p.add_argument('--output',required=True);a=p.parse_args()
    report=audit(a.workspace);write_record(Path(a.output),report)
    print(json.dumps({k:v for k,v in report.items() if k not in ('groups','missing','fatal_receipts')},indent=2))
