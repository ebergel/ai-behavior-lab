import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from behaviorlab import discourse_job as job, lab_jobs
from behaviorlab.jev_atlas import locked

class DiscourseJobTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.ws=Path(self.tmp.name)
        self.root=self.ws/job.corpus.EXECUTION;self.root.mkdir(parents=True)
        self.plan={'counts':{'logical_requests':4,'reuse_requests':1}}
        patcher=patch.object(job,'check',return_value=(self.root,self.plan,{}));patcher.start();self.addCleanup(patcher.stop)
    def progress(self,state='paused',**values):
        (self.root/'.status.json').write_text(json.dumps(dict(plan_sha256=job.PLAN_SHA,release_sha256=job.RELEASE_SHA,state=state,completed_assessments=2,new_attempts=1,known_cost_usd=.001,unknown_cost_reserved_usd=0,**values)))
    def test_start_deduplicates_and_resets_only_registered_pause(self):
        (self.root/'PAUSE').touch();self.progress();calls=[]
        lab_jobs.start(self.ws,job.JOB_ID,spawn=lambda *a,**kw:calls.append((a,kw)))
        lab_jobs.start(self.ws,job.JOB_ID,spawn=lambda *a,**kw:calls.append((a,kw)))
        self.assertEqual(len(calls),1);self.assertFalse((self.root/'PAUSE').exists())
        self.assertIn(job.JOB_ID,calls[0][0][0]);self.assertTrue(calls[0][1]['start_new_session'])
    def test_live_progress_pause_and_orphan_running_state(self):
        self.progress('running')
        self.assertEqual(job.status(self.ws)['status'],'blocked')
        with locked(self.root/'.runner.lock'):
            s=lab_jobs.pause(self.ws,job.JOB_ID)
            self.assertEqual(s['status'],'running');self.assertTrue(s['pause_requested']);self.assertFalse(s['can_start'])
        self.assertTrue((self.root/'PAUSE').exists())
    def test_worker_records_outcome_without_exposing_errors(self):
        with patch.object(job.corpus,'run',return_value={'state':'complete'}) as run:
            job.worker(self.ws);run.assert_called_once()
        runtime=lab_jobs.directory(self.ws,job.JOB_ID)
        self.assertEqual(lab_jobs.read_state(runtime)['status'],'complete')
        with patch.object(job.corpus,'run',side_effect=ValueError('secret-value')):job.worker(self.ws)
        self.assertNotIn('secret-value',(runtime/'state.json').read_text())
        self.assertEqual(lab_jobs.read_state(runtime)['status'],'blocked')
    def test_progress_cannot_claim_a_different_allocation(self):
        self.progress('complete');p=self.root/'.status.json';d=json.loads(p.read_text());d['plan_sha256']='wrong';p.write_text(json.dumps(d))
        self.assertFalse(job.status(self.ws)['can_start']);self.assertEqual(job.status(self.ws)['status'],'blocked')
