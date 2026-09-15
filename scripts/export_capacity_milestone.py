"""Create separate, labeled WebUI views of the capacity engineering trajectories."""
import argparse
from pathlib import Path

from behaviorlab.annotations import save_new
from behaviorlab.common import canonical, read_json, require
from behaviorlab.evidence import completed_campaign
from behaviorlab.webui import export_transcript, import_transcript


if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('directory'); p.add_argument('--import-local',action='store_true')
    p.add_argument('--token-file',default='workspace/private/webui-token'); args=p.parse_args()
    base=Path(args.directory); destination=base/'webui'; destination.mkdir(exist_ok=True)
    token=Path(args.token_file).read_text().strip() if args.import_local else None
    for job in read_json((base/'freeze.json').read_text())['jobs']:
        if not job['name'].startswith('long-') or not (base/job['name']).exists(): continue
        source=completed_campaign(base/job['name']); valid=[n for n in source.nodes if n.id in source.turns]
        if not valid: continue
        file=destination/(job['name']+'.json')
        if file.exists():
            document=read_json(file.read_text())
            require(document['chats'][0]['chat']['lab_evidence']['journal_head']==source.identity['journal_head'],'Display source differs')
        else:
            document=export_transcript(base/job['name'],valid[-1].id); chat=document['chats'][0]['chat']
            chat['title']='Behavior Lab · Capacity 2048 · '+job['name']
            invalid=[p for k,p in source.state.outcomes.values() if k=='turn_invalid']
            note='\n\nCapacity engineering trial, not a semantic qualification screen or factorial result. Output allowance: 2,048 tokens; soft word instruction: 150. Valid messages: '+str(len(valid))+' of 50.'
            if invalid:
                note+=' Preserved failure: '+', '.join('message '+str(p['global_turn'])+' '+p['reason'] for p in invalid)+'. This view contains valid ancestry only; the raw capped reply remains in the laboratory journal.'
            chat['messages'][0]['content']+=note; save_new(file,document)
        output={'job':job['name'],'valid_messages':len(valid)}
        if args.import_local:
            output['receipt']=import_transcript('http://127.0.0.1:8080',token,document,destination/(job['name']+'.receipt.json'))
        print(canonical(output),flush=True)
