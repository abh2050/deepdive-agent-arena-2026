import json
import sqlite3
from datetime import datetime, timezone
from app.config import DATABASE_PATH

class AuditStore:
    def __init__(self,path=DATABASE_PATH):
        self.path=path
        with self.connect() as c:
            c.execute('CREATE TABLE IF NOT EXISTS audit (id INTEGER PRIMARY KEY AUTOINCREMENT, run_id TEXT NOT NULL, timestamp TEXT NOT NULL, event TEXT NOT NULL, payload TEXT NOT NULL)')
            c.execute('CREATE TABLE IF NOT EXISTS reports (run_id TEXT PRIMARY KEY, json TEXT NOT NULL)')
    def connect(self): return sqlite3.connect(self.path)
    def log(self,run_id,event,**payload):
        with self.connect() as c:
            c.execute('INSERT INTO audit(run_id,timestamp,event,payload) VALUES (?,?,?,?)',
              (run_id,datetime.now(timezone.utc).isoformat(),event,json.dumps(payload,default=str)))
    def save(self,run_id,report):
        with self.connect() as c:
            c.execute('INSERT OR REPLACE INTO reports(run_id,json) VALUES (?,?)',(run_id,report.model_dump_json()))
    def get(self,run_id):
        with self.connect() as c:
            result=c.execute('SELECT json FROM reports WHERE run_id=?',(run_id,)).fetchone()
            return json.loads(result[0]) if result else None
    def events(self,run_id):
        with self.connect() as c:
            rows=c.execute('SELECT timestamp,event,payload FROM audit WHERE run_id=? ORDER BY id',(run_id,)).fetchall()
        return [{'timestamp':t,'event':e,'payload':json.loads(p)} for t,e,p in rows]
    def list_runs(self, limit: int = 20) -> list[dict]:
        with self.connect() as c:
            rows = c.execute('SELECT run_id, json FROM reports ORDER BY rowid DESC LIMIT ?', (limit,)).fetchall()
        summaries = []
        for run_id, raw_json in rows:
            try:
                data = json.loads(raw_json)
                summaries.append({
                    'run_id': run_id,
                    'question': data.get('question', ''),
                    'metrics': data.get('metrics', {}),
                    'verified_count': len(data.get('verified_claims', [])),
                    'rejected_count': len(data.get('rejected_claims', [])),
                })
            except Exception:
                summaries.append({'run_id': run_id, 'question': 'Unknown', 'metrics': {}})
        return summaries

