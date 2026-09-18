import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from behaviorlab.common import canonical, fingerprint
from behaviorlab.jev_atlas import MODEL, ENDPOINT, PRICE, read_record, write_record
from behaviorlab.discourse_corpus import prepare, run, replay, payload, RESERVE, paths
from test_jev_atlas import reply


class DiscourseCorpusTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.ws=Path(self.tmp.name);self.dest=self.ws/'execution'
        self.plan={'model':MODEL,'endpoint':ENDPOINT,'budget':{'usd_per_million_input':PRICE},
            'packs':{p:{'questions':{'topic_'+p:{'type':'noul','criteria':'Is this about '+p+'?'}}} for p in ['name_and_definition','name_and_portrait']},
            'targets':[], 'counts':{'new_calls':4,'reuse_requests':0,'logical_requests':4}}
        for n in range(2):
            t={'id':str(n)*24,'speaker':'X','text':'Synthetic topic assessment.','context':[],'requests':{}}
            for v in self.plan['packs']:
                raw=payload(self.plan,t,v)
                t['requests'][v]={'payload_sha256':fingerprint(raw),'bytes':len(canonical(raw).encode())}
            self.plan['targets'].append(t)
        write_record(self.ws/'plan.json',self.plan)
        self.quiet=contextlib.redirect_stdout(io.StringIO());self.quiet.__enter__();self.addCleanup(self.quiet.__exit__,None,None,None)

    def freeze(self,**kwargs):
        return prepare(self.ws,self.ws/'plan.json',self.dest,'Researcher approves finite synthetic test',backoff=(0,0),**kwargs)

    def good(self,p,k):return (*reply(p,k),{})

    def test_resume_complete_and_reuse_never_resends(self):
        before=(self.ws/'plan.json').read_bytes();self.freeze()
        with patch('behaviorlab.discourse_corpus.transport',side_effect=self.good) as send, patch('behaviorlab.discourse_corpus.credential',return_value='secret'):
            out=run(self.ws,self.dest,max_calls=1);self.assertEqual(out['state'],'paused')
            self.assertEqual(out['new_attempts'],1)
            out=run(self.ws,self.dest);self.assertEqual(out['state'],'complete');self.assertEqual(send.call_count,4)
            self.assertAlmostEqual(out['known_cost_usd'],4*900*42/1e9)
            run(self.ws,self.dest);self.assertEqual(send.call_count,4)
        self.assertEqual((self.ws/'plan.json').read_bytes(),before)
        self.assertEqual(len(replay(self.ws,self.dest)[1]),4)

    def test_overload_retry_preserves_original_and_reservation(self):
        self.freeze();calls=[]
        def send(p,k):
            calls.append(p)
            return (529,'overloaded',{}) if len(calls)==1 else self.good(p,k)
        out=run(self.ws,self.dest,send=send)
        self.assertEqual(out['state'],'complete');self.assertEqual(out['new_attempts'],5)
        self.assertEqual(calls[0],calls[1]);self.assertEqual(out['unknown_cost_reserved_usd'],RESERVE/1e9)
        self.assertEqual(len(list((self.dest/'attempts').glob('*/*.response.json'))),5)
        self.assertFalse(replay(self.ws,self.dest)[-1])

    def test_retry_limit_and_aggregate_allocation(self):
        self.freeze(retry_allowance=1)
        out=run(self.ws,self.dest,send=lambda p,k:(429,'limited',{}))
        self.assertEqual(out['new_attempts'],2);self.assertEqual(out['state'],'stopped')
        self.assertEqual(out['committed_usd'],2*RESERVE/1e9)

    def test_budget_reserves_before_dispatch(self):
        self.freeze(ceiling=.001)
        with patch('behaviorlab.discourse_corpus.transport',side_effect=AssertionError('No call')) as send:
            out=run(self.ws,self.dest,send=send)
        self.assertEqual(out['new_attempts'],0);self.assertEqual(out['reason'],'Spending ceiling reached')

    def test_unknown_outcome_blocks_resume(self):
        self.freeze()
        def fail(p,k):raise TimeoutError('secret')
        out=run(self.ws,self.dest,send=fail);self.assertEqual(out['new_attempts'],1)
        out=run(self.ws,self.dest,send=self.good);self.assertEqual(out['new_attempts'],1)
        self.assertEqual(out['state'],'stopped');self.assertEqual(out['unknown_cost_reserved_usd'],RESERVE/1e9)
        self.assertNotIn('secret',next((self.dest/'attempts').glob('*/*.response.json')).read_text())

    def test_invalid_output_and_http_errors_do_not_retry(self):
        self.freeze();out=run(self.ws,self.dest,send=lambda p,k:(200,'{}',{}))
        self.assertEqual(out['state'],'stopped');self.assertEqual(out['new_attempts'],1)
        self.assertEqual(run(self.ws,self.dest,send=self.good)['new_attempts'],1)

    def test_missing_receipt_prevents_duplicate_dispatch(self):
        self.freeze();run(self.ws,self.dest,max_calls=1,send=self.good)
        next((self.dest/'attempts').glob('*/*.response.json')).unlink()
        out=run(self.ws,self.dest,send=self.good)
        self.assertEqual(out['state'],'stopped');self.assertEqual(out['new_attempts'],1)

    def test_changed_software_or_plan_fails_closed(self):
        self.freeze()
        with patch('behaviorlab.discourse_corpus.software',return_value={}):
            with self.assertRaisesRegex(ValueError,'software changed'):run(self.ws,self.dest,send=self.good)
        p=self.ws/'plan.json';record=read_record(p);record.pop('sha256');record['targets'][0]['text']='changed';p.unlink();write_record(p,record)
        with self.assertRaisesRegex(ValueError,'corpus changed'):run(self.ws,self.dest,send=self.good)

    def test_secret_echo_is_removed_and_blocks_retry(self):
        self.freeze();out=run(self.ws,self.dest,send=lambda p,k:(529,'oops KEY-SENSITIVE',{}),key='KEY-SENSITIVE')
        self.assertEqual(out['new_attempts'],1);self.assertEqual(out['state'],'stopped')
        self.assertTrue(all('KEY-SENSITIVE' not in p.read_text() for p in (self.dest/'attempts').glob('*/*.response.json')))

    def test_manual_pause_has_no_network(self):
        self.freeze();(self.dest/'PAUSE').touch()
        out=run(self.ws,self.dest,send=self.good)
        self.assertEqual(out['state'],'paused');self.assertEqual(out['new_attempts'],0)

    def test_concurrent_warmup_drains_and_accounts_every_attempt(self):
        import copy, threading, time
        base=copy.deepcopy(self.plan['targets'][0]);self.plan['targets']=[]
        for n in range(16):
            t=copy.deepcopy(base);t['id']=format(n,'024x');self.plan['targets'].append(t)
        self.plan['counts'].update(new_calls=32,logical_requests=32)
        p=self.ws/'plan.json';p.unlink();write_record(p,self.plan)
        self.freeze(max_workers=4)
        lock=threading.Lock();concurrency=[0,0]
        def send(p,k):
            with lock:concurrency[0]+=1;concurrency[1]=max(concurrency)
            time.sleep(.31)
            with lock:concurrency[0]-=1
            return self.good(p,k)
        out=run(self.ws,self.dest,send=send)
        self.assertEqual(out['state'],'complete');self.assertEqual(out['new_attempts'],32)
        self.assertTrue(2<=concurrency[1]<=4);self.assertEqual(concurrency[0],0)
        self.assertEqual(len(replay(self.ws,self.dest)[1]),32)
        self.assertAlmostEqual(out['known_cost_usd'],32*900*42/1e9)

    def test_exact_reuse_has_no_new_cost_and_changed_payload_is_rejected(self):
        from behaviorlab.jev_atlas import read_record
        from behaviorlab.discourse_corpus import reuse_records
        t=self.plan['targets'][0];v='name_and_definition';raw=payload(self.plan,t,v)
        self.assertEqual(raw['state'],{'target_passage':t['text']})
        write_record(self.ws/'pilot/request.json',{'payload':raw})
        req=read_record(self.ws/'pilot/request.json');code,body=reply(raw,'')
        write_record(self.ws/'pilot/response.json',{'http_status':code,'raw_text':body,'request_sha256':req['sha256']})
        res=read_record(self.ws/'pilot/response.json')
        t['requests'][v]['reuse']={'request':'pilot/request.json','response':'pilot/response.json','request_sha256':req['sha256'],'response_sha256':res['sha256']}
        self.plan['counts'].update(new_calls=3,reuse_requests=1)
        path=self.ws/'plan.json';path.unlink();write_record(path,self.plan);self.freeze()
        calls=[]
        def send(p,k):calls.append(p);return self.good(p,k)
        out=run(self.ws,self.dest,send=send)
        self.assertEqual(len(calls),3);self.assertEqual(out['completed_assessments'],4)
        self.assertEqual(out['reused_assessments'],1)
        self.assertAlmostEqual(out['known_cost_usd'],3*900*42/1e9)
        self.plan['targets'][0]['text']='Changed'
        with self.assertRaisesRegex(ValueError,'Reused request differs'):reuse_records(self.ws,self.plan)

    def test_changed_source_blocks_dispatch(self):
        from behaviorlab.common import sha256
        source=self.ws/'source.txt';source.write_text('original')
        self.plan['source_files']=[{'path':'source.txt','sha256':sha256(source.read_bytes())}]
        path=self.ws/'plan.json';path.unlink();write_record(path,self.plan);self.freeze()
        source.write_text('changed')
        with self.assertRaisesRegex(ValueError,'Source evidence changed'):run(self.ws,self.dest,send=self.good)
