from app.coordinator import Coordinator
from app.models import Evidence
from app.store import AuditStore
from app.retrieval import safe_url

SRC = Evidence(evidence_id='e1',subquestion='What is established?',url='https://example.org/evidence',
 title='Reference',excerpt='The program began in 2020 and served 120 households.',quality=0.7)

class FakeMesh:
    def json(self,role,instruction,payload):
        if 'subquestions' in instruction:return {'subquestions':['What is established?']}
        if 'query' in instruction:return {'query':'program outcomes'}
        if 'atomic factual' in instruction:
            return {'claims':[
                {'statement':'The program began in 2020.','evidence_id':'e1','quote':'The program began in 2020'},
                {'statement':'The program served 2 million households.','evidence_id':'e1','quote':'served 120 households.'},
                {'statement':'The program ended in 2025.','evidence_id':'e1','quote':'No such text appears'}]}
        if 'DIRECTLY supports' in instruction:
            return {'status':'supported' if 'began in 2020' in payload['statement'] else 'rejected',
                    'reason':'Directly stated' if 'began in 2020' in payload['statement'] else 'Numerical mismatch'}
        raise AssertionError(instruction)

class FakeSearch:
    def search(self,query,subquestion):return [SRC]

def test_rejects_unsupported_and_missing_quote(tmp_path):
    store=AuditStore(str(tmp_path/'audit.sqlite3'))
    r=Coordinator(FakeMesh(),FakeSearch(),store,max_rounds=2).run('What did the program achieve?')
    assert len(r.verified_claims)==1
    assert len(r.rejected_claims)==2
    assert r.metrics['verification_pass_rate']==round(1/3,4)
    assert '2 million' not in r.markdown
    assert 'began in 2020' in r.markdown
    events=store.events(r.run_id)
    assert sum(e['event']=='research_retry' for e in events)==0
    assert sum(e['event']=='verification' for e in events)==3
    assert store.get(r.run_id)['metrics']==r.metrics

class EmptySearch:
    def search(self,query,subquestion): return []

def test_insufficient_evidence_triggers_bounded_retry(tmp_path):
    store=AuditStore(str(tmp_path/'retry.sqlite3'))
    r=Coordinator(FakeMesh(),EmptySearch(),store,max_rounds=2).run('What did the program achieve?')
    assert r.metrics['subquestion_coverage']==0
    assert 'Insufficient verified evidence' in r.markdown
    events=store.events(r.run_id)
    assert sum(e['event']=='search' for e in events)==2
    assert sum(e['event']=='research_retry' for e in events)==1

def test_safe_url_blocks_non_public_network_targets():
    blocked = [
        'http://localhost/admin',
        'http://service.local/metadata',
        'http://127.0.0.1/',
        'http://10.20.30.40/',
        'http://172.20.0.1/',
        'http://192.168.1.1/',
        'http://169.254.169.254/latest/meta-data/',
        'http://2130706433/',
        'http://0x7f000001/',
        'http://[::1]/',
        'http://[fc00::1]/',
        'http://[fe80::1]/',
        'https://user:password@example.com/',
        'file:///etc/passwd',
    ]
    assert all(not safe_url(url) for url in blocked)
    assert safe_url('https://example.org/research')
