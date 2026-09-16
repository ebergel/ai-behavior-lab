"""Read-only projections from a completed paid framing journal; no inference.

Preserve the observed prefix cost. Extend each root using its mean reported
completion length and mean prompt-token growth, then average the balanced roots.
Prices come from the saved plan, not a live price or availability claim.
"""
import argparse
from collections import defaultdict
from decimal import Decimal
from pathlib import Path

from behaviorlab.common import require, sha256
from behaviorlab.journal import read_events
from behaviorlab.paid_framing import replay


def estimate(journal):
    raw = journal.read_bytes()
    state = replay(read_events(journal))
    require(state['finished'], 'Use a closed batch for calibration')
    plan = state['plan']
    observed = plan['messages_per_root']
    roots = []
    for root in plan['roots']:
        candidate = plan['candidates'][root['candidate']]
        rows = [state['results'][root['id']+':'+str(t)] for t in range(1, observed+1)]
        require(all(r['status']=='valid' and r.get('cost_usd') is not None for r in rows),
                'Calibration requires complete, uncapped, accounted-for roots')
        inputs = [r['usage']['prompt_tokens'] for r in rows]
        outputs = [r['usage']['completion_tokens'] for r in rows]
        roots.append({'root':root['id'], 'model':candidate['label'],
            'cost_usd':sum(Decimal(r['cost_usd']) for r in rows),
            'input_price':Decimal(candidate['prompt_usd_per_million']),
            'output_price':Decimal(candidate['completion_usd_per_million']),
            'last_input_tokens':inputs[-1],
            'mean_prompt_growth':Decimal(inputs[-1]-inputs[0])/(observed-1),
            'mean_completion_tokens':Decimal(sum(outputs))/observed,
            'observed_cached_input_tokens':sum((r['usage'].get('prompt_tokens_details') or {}).get('cached_tokens',0) for r in rows)})
    totals = defaultdict(Decimal)
    for root in roots:
        totals[root['model']] += root['cost_usd']
    scenarios = []
    for count, horizon in ((8,12),(40,12),(8,30),(40,30),(100,30),(40,60)):
        future = horizon-observed
        require(future >= 0, 'Cannot shorten the calibration prefix')
        costs = defaultdict(Decimal)
        for root in roots:
            # The next prompt includes one further reply; its index starts at 1.
            future_inputs = future*root['last_input_tokens'] + root['mean_prompt_growth']*future*(future+1)/2
            future_outputs = future*root['mean_completion_tokens']
            cost = root['cost_usd'] + (root['input_price']*future_inputs+root['output_price']*future_outputs)/1000000
            costs[root['model']] += cost*Decimal(count)/len(roots)
        scenarios.append({'conversations_total':count,'messages_per_conversation':horizon,
            'calls_total':count*horizon,'model_cost_usd':dict(costs),'total_usd':sum(costs.values()),
            'status':'observed calibration' if count==len(roots) and horizon==observed else 'projection'})
    require(journal.read_bytes()==raw, 'Source changed during calculation')
    return {'schema':'behaviorlab.participant-cost-calibration/1',
        'source':str(journal),'source_sha256':sha256(raw),'rate_snapshot_date':plan['created_at'],
        'observed_calls':len(state['requests']),'observed_cost_usd':sum(totals.values()),
        'observed_cost_by_model_usd':dict(totals),'root_calibration':roots,'scenarios':scenarios,
        'formula':'C(N)=C(H)+[p_in*(k*P_H+g*k*(k+1)/2)+p_out*q*k]/1e6; H=12, k=N-H, g=(P_H-P_1)/(H-1), q=mean completion tokens.',
        'scope':'Balanced models and anonymous/mirror conditions. More roots scale linearly; full-history length increases repeated input cost. Measured prefix retained exactly.',
        'limits':['Point projections, not confidence intervals or spending caps.',
            'Only four observed roots per model; includes the short Haiku closing sequence.',
            'Assumes the same rates, routing, no reasoning/tools, and similar future token lengths and prompt growth.',
            'Observed prefix retains billed cache discounts; additional projected input uses the saved undiscounted rate. Future caching could reduce cost.',
            'Different prompts, output caps, stopping policies, reasoning or models need separate calibration.',
            'No new technical checks, retries, failures or unknown billing included.',
            'No model calls, budget changes or authorization for additional spending.']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('journal',type=Path)
    args = parser.parse_args()
    document = estimate(args.journal)
    import json
    print(json.dumps(document,default=str,ensure_ascii=False,indent=2))
