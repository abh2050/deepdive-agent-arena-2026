import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def client():
    return TestClient(app)

def test_health(client):
    res = client.get('/health')
    assert res.status_code == 200
    assert res.json() == {'status': 'ok'}

def test_config(client):
    res = client.get('/config')
    assert res.status_code == 200
    data = res.json()
    assert 'model' in data
    assert 'max_rounds' in data
    assert 'has_api_key' in data

def test_evaluation_questions(client):
    res = client.get('/evaluation/questions')
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) >= 3

def test_research_demo_mode(client):
    payload = {
        'question': 'What are the main risks of investing in EV batteries in 2026?',
        'demo_mode': True
    }
    res = client.post('/research', json=payload)
    assert res.status_code == 200
    data = res.json()
    assert 'run_id' in data
    assert 'markdown' in data
    assert 'metrics' in data
    assert data['metrics']['attempted_claims'] >= 0

    run_id = data['run_id']
    # Test get run
    run_res = client.get(f'/runs/{run_id}')
    assert run_res.status_code == 200
    assert run_res.json()['run_id'] == run_id

    # Test audit
    audit_res = client.get(f'/runs/{run_id}/audit')
    assert audit_res.status_code == 200
    events = audit_res.json()
    assert isinstance(events, list)
    assert any(e['event'] == 'started' for e in events)

    # Test markdown report
    md_res = client.get(f'/runs/{run_id}/report.md')
    assert md_res.status_code == 200
    assert 'DeepDive Research Report' in md_res.text

    # Test list runs
    runs_res = client.get('/runs')
    assert runs_res.status_code == 200
    assert any(r['run_id'] == run_id for r in runs_res.json())

    # Test conversational follow-up
    followup_res = client.post(f'/runs/{run_id}/followup', json={
        'question': 'Can you summarize key mitigations?',
        'demo_mode': True
    })
    assert followup_res.status_code == 200
    f_data = followup_res.json()
    assert 'answer' in f_data
    assert 'cited_evidence' in f_data
    assert f_data['run_id'] == run_id

