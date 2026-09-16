"""Display each qualification root separately in the existing local WebUI."""
import argparse
from pathlib import Path

from behaviorlab.annotations import save_new
from behaviorlab.common import canonical, read_json, require
from behaviorlab.evidence import completed_campaign
from behaviorlab.webui import export_transcript, import_transcript


def main():
    p = argparse.ArgumentParser(); p.add_argument('directory'); p.add_argument('--import-local', action='store_true')
    p.add_argument('--token-file', default='workspace/private/webui-token'); args = p.parse_args()
    base = Path(args.directory); freeze = read_json((base/'freeze.json').read_text())
    destination = base/'webui'; destination.mkdir(exist_ok=True)
    token = Path(args.token_file).read_text().strip() if args.import_local else None
    for job in freeze['jobs']:
        if job['name'].endswith('-smoke') or not (base/job['name']).exists(): continue
        source = completed_campaign(base/job['name'])
        for root in source.protocol.roots:
            valid = [n for n in source.nodes if n.root == root.name and n.id in source.turns]
            if not valid:
                print(canonical({'job': job['name'], 'root': root.name, 'display': 'no valid messages'})); continue
            file = destination/(job['name']+'-'+root.name+'.json')
            if file.exists():
                document = read_json(file.read_text())
                require(document['chats'][0]['chat']['lab_evidence']['journal_head'] == source.identity['journal_head'],
                        'Existing display belongs to another journal snapshot')
            else:
                document = export_transcript(base/job['name'], valid[-1].id)
                chat = document['chats'][0]['chat']
                invalid = [p.get('reason') for node, (kind, p) in source.state.outcomes.items()
                           if node.startswith(root.name+':') and kind == 'turn_invalid']
                chat['title'] = 'Behavior Lab · '+job['name']+' · '+root.name
                note = '\n\nQualification condition: '+job['name']+'. Valid messages: '+str(len(valid))+' of 30.'
                if invalid:
                    note += ' Stopped after '+str(len(valid))+' valid messages: '+', '.join(invalid)+'. Capped/invalid raw output remains in laboratory evidence; this display contains the valid history only.'
                chat['messages'][0]['content'] += note
                save_new(file, document)
            result = {'job': job['name'], 'root': root.name, 'valid_messages': len(valid), 'file': str(file)}
            if args.import_local:
                result['receipt'] = import_transcript('http://127.0.0.1:8080', token, document,
                                                     destination/(file.stem+'.receipt.json'))
            print(canonical(result), flush=True)


if __name__ == '__main__': main()
