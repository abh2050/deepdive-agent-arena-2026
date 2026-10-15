"""Single choke point for ALL generative AI. Never instantiate another model client."""
import json
import os
import re
from dataclasses import dataclass
from openai import OpenAI
from app.config import MESH_MODEL

MESH_BASE_URL = 'https://api.meshapi.ai/v1'


@dataclass
class MeshGatewayError(Exception):
    """Stable, safe error contract at the Mesh provider boundary."""

    code: str
    message: str
    status_code: int = 503
    retryable: bool = False

    def __str__(self) -> str:
        return self.message

    def as_detail(self) -> dict:
        return {
            'code': self.code,
            'message': self.message,
            'retryable': self.retryable,
        }


def normalize_mesh_error(exc: Exception) -> MeshGatewayError:
    """Map changing SDK/provider messages onto an application-owned contract."""
    status = getattr(exc, 'status_code', None)
    name = type(exc).__name__.lower()

    if status in (401, 403) or 'authentication' in name or 'permission' in name:
        return MeshGatewayError(
            'mesh_authentication_failed',
            'Mesh rejected the API credentials. Check the configured API key.',
            401,
            False,
        )
    if status == 402:
        return MeshGatewayError(
            'mesh_payment_required',
            'Mesh credits are unavailable. Add credits or use demo mode.',
            402,
            False,
        )
    if status == 429 or 'ratelimit' in name or 'rate_limit' in name:
        return MeshGatewayError(
            'mesh_rate_limited',
            'Mesh is temporarily rate-limiting requests. Please retry shortly.',
            429,
            True,
        )
    if 'timeout' in name:
        return MeshGatewayError(
            'mesh_timeout',
            'Mesh did not respond in time. Please retry.',
            504,
            True,
        )
    if (status is not None and status >= 500) or 'connection' in name:
        return MeshGatewayError(
            'mesh_unavailable',
            'Mesh is temporarily unavailable. Please retry shortly.',
            503,
            True,
        )
    return MeshGatewayError(
        'mesh_request_failed',
        'The model request could not be completed.',
        502,
        False,
    )

def extract_json_object(content: str) -> dict:
    content = content.strip()
    if content.startswith('```'):
        content = content.split('\n', 1)[-1].rsplit('```', 1)[0].strip()
    try:
        res = json.loads(content)
        if isinstance(res, dict):
            return res
    except Exception:
        pass
    start = content.find('{')
    end = content.rfind('}')
    if start != -1 and end != -1 and end > start:
        candidate = content[start:end+1]
        try:
            res = json.loads(candidate)
            if isinstance(res, dict):
                return res
        except Exception:
            pass
    raise ValueError('Expected JSON object')

class MeshLLM:
    def __init__(self, client=None, model: str = MESH_MODEL, api_key: str | None = None):
        if client is None:
            key = api_key or os.environ.get('MESH_API_KEY')
            if not key:
                raise RuntimeError('MESH_API_KEY is required for live research')
            client = OpenAI(base_url=MESH_BASE_URL, api_key=key, timeout=40, max_retries=2)
        self.client = client
        self.model = model

    def json(self, role: str, instruction: str, payload: dict) -> dict:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                temperature=0,
                messages=[
                    {'role': 'system', 'content': role + '\nReturn only a valid JSON object; no Markdown fences.'},
                    {'role': 'user', 'content': instruction + '\nINPUT JSON:\n' + json.dumps(payload, ensure_ascii=False)},
                ],
            )
            content = response.choices[0].message.content or ''
            return extract_json_object(content)
        except MeshGatewayError:
            raise
        except (AttributeError, IndexError, TypeError, ValueError) as exc:
            raise MeshGatewayError(
                'mesh_invalid_response',
                'Mesh returned a response the application could not read.',
                502,
                True,
            ) from exc
        except Exception as exc:
            raise normalize_mesh_error(exc) from exc

class SimulationMeshLLM:
    """High-fidelity deterministic simulation for offline testing, demos, and evaluation without a Mesh key."""
    def __init__(self, model: str = 'simulation/deterministic-v1'):
        self.model = model

    def json(self, role: str, instruction: str, payload: dict) -> dict:
        # 1. Planner
        if 'subquestions' in instruction:
            q = payload.get('question', '')
            words = [w for w in re.findall(r'\b[A-Za-z]{3,}\b', q) if w.lower() not in {'what', 'when', 'where', 'which', 'who', 'whom', 'this', 'that', 'with', 'from', 'have', 'main'}]
            core = ' '.join(words[:4]) or 'the subject'
            return {
                'subquestions': [
                    f'What are the core technical and operational factors influencing {core}?',
                    f'What are the primary economic, supply-chain, or regulatory risks affecting {core}?',
                    f'What verifiable mitigations, outcomes, or performance standards are documented for {core}?'
                ]
            }

        # 2. Researcher
        if 'query' in instruction:
            subq = payload.get('subquestion', '')
            retry = payload.get('retry', 0)
            cleaned = re.sub(r'[^\w\s]', '', subq)
            words = [w for w in cleaned.split() if w.lower() not in {'what', 'are', 'the', 'main', 'for', 'and', 'how', 'does', 'factors'}]
            base_q = ' '.join(words[:5])
            if retry > 0:
                base_q += ' primary evidence analysis'
            return {'query': base_q or 'research evidence'}

        # 3. ClaimWriter
        if 'atomic factual' in instruction:
            subq = payload.get('subquestion', '')
            evidence_list = payload.get('evidence', [])
            claims = []
            for e in evidence_list[:3]:
                eid = e.get('evidence_id', '')
                excerpt = e.get('excerpt', '')
                sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', excerpt) if 30 <= len(s.strip()) <= 180]
                if sentences:
                    quote1 = sentences[0]
                    claims.append({
                        'statement': f'According to {e.get("title", "source")}, {quote1.rstrip(".")}.',
                        'evidence_id': eid,
                        'quote': quote1
                    })
                    if len(sentences) > 2:
                        quote2 = sentences[1]
                        claims.append({
                            'statement': f'The documented record notes: {quote2.rstrip(".")}.',
                            'evidence_id': eid,
                            'quote': quote2
                        })
            return {'claims': claims[:5]}

        # 4. Verifier
        if 'DIRECTLY supports' in instruction:
            statement = payload.get('statement', '')
            quote = payload.get('quote', '')
            source_excerpt = payload.get('source_excerpt', '')
            if quote not in source_excerpt:
                return {'status': 'rejected', 'reason': 'Quote is absent from the stored source excerpt'}
            if len(statement) > 0 and len(quote) > 0:
                return {
                    'status': 'supported',
                    'reason': f'The source quote directly asserts the core proposition: "{quote[:100]}..."'
                }
            return {'status': 'unverified', 'reason': 'Ambiguous or insufficient supporting detail in excerpt'}

        # 5. Contradiction / Discrepancy detector
        if 'discrepancies' in instruction:
            claims = payload.get('claims', [])
            if len(claims) >= 2:
                # Return simulated potential nuance if multiple sources
                c1, c2 = claims[0], claims[1]
                return {
                    'discrepancies': [{
                        'claim_ids': [c1.get('claim_id'), c2.get('claim_id')],
                        'description': f"Divergent focal aspects between '{c1.get('statement')[:60]}...' and alternate source perspective.",
                        'sources': [c1.get('evidence_id'), c2.get('evidence_id')]
                    }]
                }
            return {'discrepancies': []}

        # 6. Follow-up conversational agent
        if 'follow-up' in instruction.lower():
            fq = payload.get('followup_question', '')
            excerpts = payload.get('evidence_excerpts', [])
            cited = []
            for exc in excerpts[:2]:
                if exc.startswith('['):
                    eid = exc[1:].split(']')[0]
                    cited.append(eid)
            cite_str = ' '.join(f'[{e}]' for e in cited)
            return {
                'answer': f'Based on the verified evidence gathered for this research run, {fq.rstrip("?")} relates directly to established findings {cite_str}. All assertions trace to the cited primary records.',
                'cited_evidence': cited
            }

        raise ValueError(f'Unhandled simulation instruction: {instruction[:100]}')


def get_llm(api_key: str | None = None, demo_mode: bool = False):
    key = api_key or os.environ.get('MESH_API_KEY')
    if key and not demo_mode:
        return MeshLLM(api_key=key)
    return SimulationMeshLLM()

