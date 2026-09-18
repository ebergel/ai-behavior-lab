"""Attach existing corpus topic scores to exact, current transcript targets.

This is a read-only evidence join. It never infers a topic from a conversation,
model, neighbouring passage, or classifier feature label.
"""
from collections import defaultdict
import math


def attach_target_topics(samples, dataset=None, message=None):
    index = defaultdict(list)
    topics = dataset.get('topics', []) if dataset else []
    if dataset:
        for row in dataset['rows']:
            passage = dataset['passages'].get(row['__id'])
            if passage:
                index[(passage['run_id'], passage['message_id'])].append((row, passage))
    joined = []
    for sample in samples:
        scores = {}
        status = 'unavailable'
        if sample['kind'] != 'transcript':
            status = 'synthetic'
        elif dataset:
            candidates = index.get((sample['run_id'], sample['message_id']), [])
            exact = [(r, p) for r, p in candidates
                     if p.get('source_sha256') and p['source_sha256'] == sample.get('source_sha256')
                     and p.get('text') == sample['text']]
            if sample.get('source_current') is not True:
                status = 'source_changed'
            elif len(exact) > 1:
                status = 'ambiguous'
            elif not exact:
                status = 'source_changed' if candidates else 'no_score'
            else:
                row, passage = exact[0]
                if row.get('Reading split') == 'reference_reserved':
                    status = 'reserved'
                elif passage.get('source_current') is not True:
                    status = 'source_changed'
                else:
                    for topic in topics:
                        value = row.get(topic['field'])
                        if type(value) in (int, float) and math.isfinite(value) and 0 <= value <= 100:
                            scores[topic['id']] = value
                    status = 'matched' if scores else 'no_score'
        joined.append(dict(sample, topic_scores=scores, topic_status=status))
    return joined, {
        'available': dataset is not None,
        'topics': topics,
        'dataset_fingerprint': dataset.get('fingerprint') if dataset else None,
        'message': message or ('Existing JEV corpus scores for the exact target passage. '
                              'Thresholds select model-scored candidates; unknown scores do not match.'
                              if dataset else 'Corpus topic scores are unavailable in this workspace.'),
    }
