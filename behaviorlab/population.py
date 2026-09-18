"""Read-only inventory counts for the Explorer's population context."""


def catalog_population(runs, indexed_at=None):
    runs = list(runs)
    started = [run for run in runs if not run.get('unstarted_assessment')]
    evidence = [run for run in started if run['kind'] != 'synthetic']
    synthetic = [run for run in started if run['kind'] == 'synthetic']

    def counts(selected):
        messages = [run.get('message_count') for run in selected]
        return {'records': len(selected),
                'recorded_messages': sum(messages) if all(type(n) is int and n >= 0 for n in messages) else None}

    return dict(counts(evidence),
                synthetic_records=len(synthetic),
                synthetic_messages=counts(synthetic)['recorded_messages'],
                unstarted_records=len(runs) - len(started),
                by_kind={kind: counts([run for run in started if run['kind'] == kind])
                         for kind in ('reference', 'lab', 'synthetic')},
                indexed_at=indexed_at)
