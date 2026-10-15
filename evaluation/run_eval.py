"""LIVE eval. Uses Mesh credits and search network access; do not present results as measured until executed."""
import json
import os
import sys
from pathlib import Path
from app.mesh import get_llm
from app.retrieval import WebRetriever
from app.store import AuditStore
from app.coordinator import Coordinator
from app.vector_store import ChromaEvidenceIndex

def main():
    q_file = Path('evaluation/questions.json')
    if not q_file.exists():
        q_file = Path(__file__).parent / 'questions.json'
    questions = json.loads(q_file.read_text(encoding='utf-8'))

    demo = '--demo' in sys.argv or not bool(os.getenv('MESH_API_KEY'))
    llm = get_llm(demo_mode=demo)
    store = AuditStore()
    chroma_path = os.getenv("CHROMA_PATH", "./data/chroma")
    evidence_index = ChromaEvidenceIndex(chroma_path)
    coordinator = Coordinator(llm, WebRetriever(), store, evidence_index=evidence_index)

    rows = []
    print(f"Running evaluation on {len(questions)} questions (mode={'demo' if demo else 'live Mesh'})...")
    for q in questions:
        print(f"-> Evaluating [{q['id']}]: {q['question']}")
        report = coordinator.run(q['question'])
        row = {
            'id': q['id'], 'run_id': report.run_id,
            'evaluation_mode': 'demo' if demo else 'live_mesh',
            **report.metrics,
        }
        rows.append(row)
        print(f"   Pass rate: {row.get('verification_pass_rate')}, Coverage: {row.get('subquestion_coverage')}")

    out_file = Path('evaluation/results.json')
    out_file.write_text(json.dumps(rows, indent=2), encoding='utf-8')
    print(f"Results written to {out_file}")

if __name__ == '__main__':
    main()

