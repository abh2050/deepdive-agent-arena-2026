import json
import os
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from app.config import MESH_MODEL, MAX_RESEARCH_ROUNDS
from app.coordinator import Coordinator
from app.mesh import get_llm, MeshGatewayError
from app.models import Question
from app.retrieval import WebRetriever
from app.store import AuditStore
from app.vector_store import ChromaEvidenceIndex

app = FastAPI(title='DeepDive | Self-Verifying Research Analyst', version='0.1.0')
store = AuditStore()


def is_serverless() -> bool:
    return bool(os.getenv('VERCEL'))


def build_evidence_index():
    """Use durable Chroma locally; Vercel requests carry their evidence inline."""
    if is_serverless():
        return None
    chroma_path = os.getenv('CHROMA_PATH', './data/chroma')
    return ChromaEvidenceIndex(chroma_path)


@app.exception_handler(MeshGatewayError)
async def mesh_gateway_error_handler(_request, exc: MeshGatewayError):
    return JSONResponse(status_code=exc.status_code, content={'detail': exc.as_detail()})

# Static assets directory
static_dir = Path(__file__).parent / 'static'
if static_dir.exists():
    app.mount('/static', StaticFiles(directory=str(static_dir)), name='static')

@app.get('/', response_class=HTMLResponse)
def index():
    html_file = static_dir / 'index.html'
    if html_file.exists():
        return html_file.read_text(encoding='utf-8')
    return '<h1>DeepDive Research Analyst</h1><p>Static UI not found.</p>'

@app.get('/health')
def health():
    return {'status': 'ok'}

@app.get('/config')
def get_config():
    return {
        'model': MESH_MODEL,
        'max_rounds': MAX_RESEARCH_ROUNDS,
        'has_api_key': bool(os.getenv('MESH_API_KEY')),
        'version': '0.1.0',
        'runtime': 'vercel' if is_serverless() else 'local',
    }

@app.post('/research')
def research(request: Question):
    try:
        llm = get_llm(api_key=request.api_key, demo_mode=request.demo_mode)
        evidence_index = build_evidence_index()
        coordinator = Coordinator(llm, WebRetriever(), store, evidence_index=evidence_index)
        report = coordinator.run(request.question)
        # Returning the audit with the report makes the primary experience
        # reliable even when the next request reaches another Vercel instance.
        result = report.model_dump()
        result['audit_events'] = store.events(report.run_id)
        return result
    except MeshGatewayError:
        raise
    except Exception as exc:
        # Keep internal exception text out of the public API response.
        raise HTTPException(
            status_code=500,
            detail={
                'code': 'research_internal_error',
                'message': 'Research could not be completed due to an internal error.',
                'retryable': False,
            },
        ) from exc

@app.get('/runs')
def list_runs():
    return store.list_runs(limit=30)

@app.get('/runs/{run_id}')
def get_run(run_id: str):
    result = store.get(run_id)
    if not result:
        raise HTTPException(404, 'Unknown run')
    return result

@app.get('/runs/{run_id}/audit')
def get_audit(run_id: str):
    if not store.get(run_id):
        raise HTTPException(404, 'Unknown run')
    return store.events(run_id)

@app.get('/runs/{run_id}/report.md', response_class=PlainTextResponse)
def download_markdown(run_id: str):
    report = store.get(run_id)
    if not report:
        raise HTTPException(404, 'Unknown run')
    return report['markdown']

@app.post('/runs/{run_id}/followup')
def followup_query(run_id: str, payload: dict):
    report = store.get(run_id) or payload.get('report')
    if not report:
        raise HTTPException(404, 'Unknown run')
    question = payload.get('question', '').strip()
    if not question:
        raise HTTPException(400, 'Question is required')
    demo_mode = payload.get('demo_mode', not bool(os.getenv('MESH_API_KEY')))
    llm = get_llm(api_key=payload.get('api_key'), demo_mode=demo_mode)
    evidence_index = build_evidence_index()
    from app.agents import FollowUpAgent
    agent = FollowUpAgent(llm, evidence_index=evidence_index)
    res = agent.answer(run_id, question, report)
    try:
        store.log(run_id, 'followup_query', question=question, answer=res.get('answer'), cited=res.get('cited_evidence'))
    except Exception:
        # A response must not fail merely because an ephemeral serverless
        # instance could not retain a nonessential audit write.
        pass
    return res


@app.get('/evaluation/questions')
def get_eval_questions():
    p = Path('evaluation/questions.json')
    if not p.exists():
        p = Path(__file__).parent.parent / 'evaluation' / 'questions.json'
    if p.exists():
        return json.loads(p.read_text(encoding='utf-8'))
    return []

@app.get('/evaluation/results')
def get_eval_results():
    for candidate in [Path('evaluation/results.json'), Path('evaluation/results.example.json')]:
        if candidate.exists():
            try:
                return json.loads(candidate.read_text(encoding='utf-8'))
            except Exception:
                pass
    return []

@app.post('/evaluation/run')
def run_evaluation():
    p = Path('evaluation/questions.json')
    if not p.exists():
        p = Path(__file__).parent.parent / 'evaluation' / 'questions.json'
    if not p.exists():
        raise HTTPException(404, 'evaluation/questions.json not found')
    
    questions = json.loads(p.read_text(encoding='utf-8'))
    demo = not bool(os.getenv('MESH_API_KEY'))
    llm = get_llm(demo_mode=demo)
    evidence_index = build_evidence_index()
    coordinator = Coordinator(llm, WebRetriever(), store, evidence_index=evidence_index)
    
    rows = []
    for q in questions:
        report = coordinator.run(q['question'])
        row = {
            'id': q['id'], 'run_id': report.run_id,
            'evaluation_mode': 'demo' if demo else 'live_mesh',
            **report.metrics,
        }
        rows.append(row)
        
    out_path = Path('/tmp/evaluation-results.json' if is_serverless() else 'evaluation/results.json')
    out_path.write_text(json.dumps(rows, indent=2), encoding='utf-8')
    return rows
