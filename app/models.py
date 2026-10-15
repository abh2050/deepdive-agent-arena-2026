from typing import Literal
from pydantic import BaseModel, Field

class Question(BaseModel):
    question: str = Field(min_length=12, max_length=2000)
    demo_mode: bool = False
    api_key: str | None = None

class Evidence(BaseModel):
    evidence_id: str
    subquestion: str
    url: str
    title: str
    excerpt: str
    quality: float = 0.5

class Claim(BaseModel):
    claim_id: str
    subquestion: str
    statement: str
    evidence_id: str
    quote: str

class Verdict(BaseModel):
    claim_id: str
    status: Literal['supported', 'rejected', 'unverified']
    reason: str

class Report(BaseModel):
    run_id: str
    question: str
    markdown: str
    verified_claims: list[Claim]
    rejected_claims: list[dict]
    evidence: list[Evidence]
    coverage: dict[str, bool]
    metrics: dict
