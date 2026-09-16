import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from behaviorlab.common import canonical, fingerprint
from behaviorlab.explorer import Catalog, Notes
from behaviorlab.exploration_collections import ResearchCollections
from behaviorlab.legacy import import_corpus
from behaviorlab.research_bundle import (export_bundle, export_notebook, restore_bundle,
                                         verify_bundle)
from behaviorlab.runner import FakeBackend, create_campaign, execute
from behaviorlab.topic_atlas import TopicAtlas
from test_core import setup_protocol


class ResearchBundleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name); self.workspace = self.base / 'workspace'
        self.workspace.mkdir(); self.bundle = self.base / 'research'
        _, registry, protocol = setup_protocol()
        create_campaign(self.workspace / 'trial', protocol, registry)
        execute(self.workspace / 'trial')
        source = self.base / 'source'; (source / 'data' / 'runs').mkdir(parents=True)
        texts = ['Understanding 🙂 café.', 'I propose emergence.', 'Emergent behavior is interesting.',
                 'Another subject.', 'A separate question.', 'Return to emergence.']
        rows = [dict(kind='header', cond='A', cond_name='closed', pair_model='historical:model',
                     run=1, turns=6, system='Historical prompt.', seed=10)]
        rows += [dict(kind='message', turn=i, speaker='X' if i % 2 else 'Y',
                      content=text, done_reason='stop') for i, text in enumerate(texts, 1)]
        rows[2]['thinking'] = ''
        rows.append(dict(kind='third', after_turn=6, content='An outside intervention.'))
        rows.append(dict(kind='footer', pair_turns=6))
        (source / 'data' / 'runs' / 'A_run01.jsonl').write_bytes(('\r\n'.join(canonical(r) for r in rows)+'\r\n').encode())
        import_corpus(source, self.workspace / 'corpus', 'https://example.test/source', 'fixture')
        self.catalog = Catalog(self.workspace)
        self.run = next(r for r in self.catalog.runs.values() if r['kind'] == 'reference')
        self.notes = Notes(self.workspace / 'explorer' / 'notes.sqlite')
        message = self.run['messages'][0]; start = message['text'].index('🙂')
        note = self.notes.save(dict(run_id=self.run['id'], message_id=message['id'], start=start,
                                   end=start+6, quote='🙂 café', text='Original observation.', tags=['reading']), self.catalog)
        revised = self.notes.save(dict(note, text='Revised observation.'), self.catalog)
        self.notes.delete(dict(id=revised['id'], revision=revised['revision']))
        self.collections = ResearchCollections(self.notes)
        self.collections.save(dict(title='Preserve this reading', author='Codex', edited_by='Codex',
                                   runs=[dict(run_id=self.run['id'])], findings=[]), self.catalog)
        self.atlas = TopicAtlas(self.notes)
        def span(index):
            m = self.run['messages'][index]
            return dict(message_id=m['id'], start=0, end=len(m['text']), quote=m['text'])
        self.atlas.save_review(dict(run_id=self.run['id'], status='selected', author='Codex', edited_by='Codex',
                                   choice=dict(topic_id='emergence', proposal=span(1), uptake=span(2))), self.catalog)
        self.before = export_notebook(self.notes.path)

    def export(self):
        return export_bundle(self.workspace, self.bundle)

    def test_offline_restore_without_originals_preserves_bytes_ids_histories_and_atlas(self):
        originals = {p.relative_to(self.workspace): p.read_bytes() for p in self.workspace.rglob('*')
                     if p.is_file() and 'explorer' not in p.parts
                     and (p.suffix in ('.json', '.jsonl') or 'blobs' in p.parts)}
        before = self.atlas.analyze(self.catalog, self.collections)
        with patch('urllib.request.urlopen', side_effect=AssertionError('No network')), \
             patch.object(FakeBackend, 'generate', side_effect=AssertionError('No inference')):
            self.export()
            self.workspace.rename(self.base / 'inaccessible-original')
            restored = self.base / 'different-location'
            restore_bundle(self.bundle, restored)
            c = Catalog(restored); n = Notes(restored / 'explorer' / 'notes.sqlite')
            after = TopicAtlas(n).analyze(c, ResearchCollections(n))
        self.assertEqual(set(c.runs), set(self.catalog.runs))
        self.assertEqual(export_notebook(n.path), self.before)
        self.assertEqual(n.all(), [])  # A deleted note stays deleted; its three revisions remain.
        self.assertEqual(len(self.before['history']['rows']), 3)
        for relative, raw in originals.items():
            self.assertEqual((restored / relative).read_bytes(), raw)
        for key in ('denominators', 'rows', 'variants', 'reviews', 'occurrences'):
            self.assertEqual(before[key], after[key])
        transcript = json.loads((self.bundle / 'transcripts' / (self.run['id'] + '.json')).read_bytes())
        self.assertEqual(transcript['messages'][0]['thinking'], None)
        self.assertEqual(transcript['messages'][1]['thinking'], '')
        self.assertIn('🙂 café', transcript['messages'][0]['text'])
        self.assertEqual(transcript['messages'][-1]['status'], 'intervention')

    def test_excludes_credentials_caches_and_vendor_code_without_changing_sources(self):
        for name in ('private/access.json', 'source/vendor.json', 'plotting-deps/package.json',
                     'trial/runtime.log', 'trial/.hidden.json', 'explorer/backup.json'):
            path = self.workspace / name; path.parent.mkdir(exist_ok=True, parents=True)
            path.write_text('{"api_key":"sk-test' + 'a'*30 + '"}')
        before = (self.workspace / 'trial' / 'events.jsonl').read_bytes()
        self.export(); manifest = verify_bundle(self.bundle)
        names = {f.get('workspace_path') for f in manifest['files']}
        self.assertNotIn('private/access.json', names); self.assertNotIn('source/vendor.json', names)
        self.assertEqual(before, (self.workspace / 'trial' / 'events.jsonl').read_bytes())
        self.assertEqual(export_notebook(self.notes.path), self.before)

    def test_refuses_credential_in_research_sidecar_without_printing_its_value(self):
        secret = 'sk-or-v1-' + 'b'*40
        (self.workspace / 'reading.json').write_text(json.dumps({'accidental_token': secret}))
        with self.assertRaises(ValueError) as error: self.export()
        self.assertIn('reading.json', str(error.exception)); self.assertNotIn(secret, str(error.exception))
        self.assertFalse(self.bundle.exists())

    def test_recognizes_arbitrary_local_credentials_in_notebook(self):
        private = self.workspace / 'private'; private.mkdir()
        secret = 'test-credential-with-an-unusual-format'
        (private / 'access.json').write_text(json.dumps({'api_key': secret}))
        with self.notes.connect() as db:
            db.execute('UPDATE history SET body=? WHERE revision=1', (json.dumps({'text': secret}),))
        with self.assertRaisesRegex(ValueError, 'Local credential'): self.export()
        self.assertFalse(self.bundle.exists())

    def test_changed_or_unlisted_files_cannot_be_restored(self):
        self.export(); path = next((self.bundle / 'transcripts').iterdir()); raw = path.read_bytes()
        path.write_bytes(raw + b' ')
        target = self.base / 'restored'
        with self.assertRaisesRegex(ValueError, 'Changed bundle file'): restore_bundle(self.bundle, target)
        self.assertFalse(target.exists()); path.write_bytes(raw)
        (self.bundle / 'unexpected.json').write_text('{}')
        with self.assertRaisesRegex(ValueError, 'Unlisted'): restore_bundle(self.bundle, target)
        self.assertFalse(target.exists())

    def test_restore_never_replaces_existing_directory_or_dangling_symlink(self):
        self.export()
        with self.assertRaisesRegex(ValueError, 'already exists'): restore_bundle(self.bundle, self.workspace)
        link = self.base / 'link'; link.symlink_to(self.base / 'missing')
        with self.assertRaisesRegex(ValueError, 'already exists'): restore_bundle(self.bundle, link)
        self.assertTrue(link.is_symlink()); self.assertEqual(export_notebook(self.notes.path), self.before)
        with self.assertRaisesRegex(ValueError, 'new bundle'): export_bundle(self.workspace, link)

    def test_manifest_traversal_and_symlinks_are_rejected(self):
        self.export(); path = self.bundle / 'manifest.json'; original = path.read_bytes()
        manifest = json.loads(original); manifest['notebook_rows']['../../outside'] = 1
        manifest['bundle_sha256'] = fingerprint({k:v for k,v in manifest.items() if k != 'bundle_sha256'})
        path.write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ValueError, 'Invalid notebook'): verify_bundle(self.bundle)
        path.write_bytes(original)
        linked = self.bundle / 'transcripts'; moved = self.base / 'transcripts'; linked.rename(moved); linked.symlink_to(moved)
        with self.assertRaisesRegex(ValueError, 'Symlink'): verify_bundle(self.bundle)

    def test_export_does_not_follow_evidence_symlinks_or_nest_under_workspace(self):
        outside = self.base / 'outside.json'; outside.write_text('{}')
        link = self.workspace / 'sidecar.json'; link.symlink_to(outside)
        with self.assertRaisesRegex(ValueError, 'Symlink'): self.export()
        self.assertFalse(self.bundle.exists()); link.unlink()
        with self.assertRaisesRegex(ValueError, 'outside the workspace'):
            export_bundle(self.workspace, self.workspace / 'research')


if __name__ == '__main__': unittest.main()
