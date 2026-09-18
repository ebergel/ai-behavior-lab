"""Read-only measurement guide. Rubric wording comes from the scoring source."""
import hashlib
import json
from pathlib import Path


def dictionary_catalog():
    root = Path(__file__).parent
    catalog = json.loads((root / 'lab_dictionary.json').read_text())
    raw = (root / 'gem_rubric.json').read_bytes()
    rubric = json.loads(raw)
    axes = {axis['id']: axis for axis in rubric['axes']}
    for entry in catalog['entries']:
        if entry['id'] in axes:
            entry['rubric'] = axes[entry['id']]
            entry['scale'] = '0–100 · scaled expected rubric level'
            entry['formula'] = 'Displayed score = 100 × returned Score / 4 = 25 × returned Score'
            entry['method'] = [
                'TypeSafe JEV (pilot model: jev-1.13.0) assesses one selected message with up to two preceding evidence events on its actual path. These may be participant messages or external interventions; no later replies are supplied.',
                'The Score response contains five levels (0–4), their probabilities, an expected level and confidence. The lab scales the returned expected level to 0–100; it does not turn it into a probability of quality.',
                'Level spacing is an analysis convention. A score of 80 is not twice as good as 40. Rounded returned probabilities can differ slightly from the returned expected level; the lab preserves the original response.',
            ]
            entry['scope'] = rubric['scope']
            entry['sources'] = ['behaviorlab/gem_rubric.json', 'behaviorlab/gem_plan.py: payload', 'behaviorlab/gem_runner.py: validate']
    catalog['rubric'] = {k: rubric[k] for k in ('version', 'status', 'author')}
    catalog['rubric']['file_sha256'] = hashlib.sha256(raw).hexdigest()
    return catalog
