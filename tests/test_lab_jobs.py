import unittest
from unittest.mock import patch
from behaviorlab import lab_jobs
from behaviorlab.jev_atlas import write_record
from tests import test_discourse_portraits as fixtures

class LabJobTests(unittest.TestCase):
    def setUp(self):
        self.fx=fixtures.PortraitTests();self.fx.setUp();self.fx.authorize();self.workspace=self.fx.workspace
        self.pin=patch.object(lab_jobs,'PLAN_SHA',self.fx.plan['sha256']);self.pin.start()
    def tearDown(self):self.pin.stop();self.fx.tearDown()
    def test_registry_and_budget_gate(self):
        self.assertEqual(lab_jobs.status(self.workspace)['effective_ceiling_usd'],2)
        self.assertEqual(lab_jobs.listing(self.workspace)['default_ceiling_usd'],10)
        with self.assertRaisesRegex(ValueError,'Unknown'):lab_jobs.start(self.workspace,'../../shell')
        with patch.object(lab_jobs,'DEFAULT_CEILING',1):self.assertFalse(lab_jobs.status(self.workspace)['can_start'])
    def test_start_is_detached_allowlisted_and_repeated_click_is_idempotent(self):
        calls=[]
        def spawn(*args,**kwargs):calls.append((args,kwargs))
        a=lab_jobs.start(self.workspace,lab_jobs.JOB_ID,spawn=spawn)
        self.assertEqual(a['status'],'running');self.assertEqual(len(calls),1)
        lab_jobs.start(self.workspace,lab_jobs.JOB_ID,spawn=spawn)
        self.assertEqual(len(calls),1);self.assertTrue(calls[0][1]['start_new_session'])
        self.assertNotIn('shell',calls[0][1]);self.assertIn('behaviorlab.lab_jobs',calls[0][0][0])
        self.assertTrue(lab_jobs.pause(self.workspace,lab_jobs.JOB_ID)['pause_requested'])
    def test_pauses_only_between_requests_and_resumes(self):
        root=lab_jobs.directory(self.workspace,lab_jobs.JOB_ID);calls=[]
        def execute(workspace,max_calls):
            calls.append(max_calls);(root/'pause').touch()
            return {'complete':1,'planned':240,'stopped':[]}
        lab_jobs.worker(self.workspace,lab_jobs.JOB_ID,execute=execute,sleep=lambda _:None)
        self.assertEqual(calls,[1]);self.assertEqual(lab_jobs.read_state(root)['status'],'paused')
        lab_jobs.start(self.workspace,lab_jobs.JOB_ID,spawn=lambda *a,**k:None)
        self.assertFalse((root/'pause').exists())
    def test_worker_returns_on_completion_or_invalid_result(self):
        calls=[]
        def execute(*args,**kw):calls.append(1);return {'complete':240,'planned':240,'stopped':[]}
        lab_jobs.worker(self.workspace,lab_jobs.JOB_ID,execute=execute,sleep=lambda _:None)
        self.assertEqual(calls,[1]);self.assertEqual(lab_jobs.read_state(lab_jobs.directory(self.workspace,lab_jobs.JOB_ID))['status'],'complete')
        lab_jobs.worker(self.workspace,lab_jobs.JOB_ID,execute=lambda *a,**k:{'complete':4,'planned':240,'stopped':['invalid']},sleep=lambda _:None)
        self.assertEqual(lab_jobs.status(self.workspace)['status'],'blocked')
    def test_exception_content_is_never_exposed_or_retried(self):
        def broken(*a,**k):raise ValueError('sensitive-secret')
        lab_jobs.worker(self.workspace,lab_jobs.JOB_ID,execute=broken)
        s=lab_jobs.status(self.workspace);self.assertEqual(s['status'],'blocked');self.assertNotIn('sensitive-secret',str(s))
    def test_interrupted_request_cannot_restart(self):
        from behaviorlab.discourse_portrait_probe import ROOT,payload
        item=self.fx.plan['items'][0]
        write_record(self.workspace/ROOT/'attempts'/item['id']/'01.request.json',{'plan_sha256':self.fx.plan['sha256'],'item_id':item['id'],'attempt':1,'payload':payload(self.fx.plan,item)})
        s=lab_jobs.status(self.workspace);self.assertEqual(s['status'],'blocked');self.assertFalse(s['can_start']);self.assertGreater(s['unknown_reserved_usd'],0)
        with self.assertRaises(ValueError):lab_jobs.start(self.workspace,lab_jobs.JOB_ID,spawn=lambda *a,**kw:self.fail('Dispatched'))

    def test_inflight_request_is_running_while_worker_lock_is_held(self):
        from behaviorlab.discourse_portrait_probe import ROOT,payload
        from behaviorlab.jev_atlas import locked
        item=self.fx.plan['items'][0]
        write_record(self.workspace/ROOT/'attempts'/item['id']/'01.request.json',{'plan_sha256':self.fx.plan['sha256'],'item_id':item['id'],'attempt':1,'payload':payload(self.fx.plan,item)})
        with locked(lab_jobs.directory(self.workspace,lab_jobs.JOB_ID)/'worker.lock'), locked(self.workspace/ROOT/'.runner.lock'):
            from behaviorlab.discourse_view import build
            self.assertEqual(build(self.workspace)['status'],'in_progress')
            self.assertEqual(lab_jobs.status(self.workspace)['status'],'running')
            self.assertTrue(lab_jobs.status(self.workspace)['can_pause'])
        self.assertEqual(lab_jobs.status(self.workspace)['status'],'blocked')
