"""Real LangGraph orchestration with explicit conditional research retry."""
import uuid
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from app.agents import Planner, Researcher, ClaimWriter, Verifier, Synthesizer, ContradictionDetector
from app.config import MAX_RESEARCH_ROUNDS
from app.models import Report

class ResearchState(TypedDict):
    run_id: str
    question: str
    subquestions: list[str]
    evidence: dict
    accepted: dict
    rejected: list
    evaluated: set
    round_id: int
    report: object

class Coordinator:
    def __init__(self, llm, retriever, store, max_rounds=MAX_RESEARCH_ROUNDS, evidence_index=None):
        self.planner = Planner(llm)
        self.researcher = Researcher(llm, retriever)
        self.writer = ClaimWriter(llm)
        self.verifier = Verifier(llm)
        self.synthesizer = Synthesizer()
        self.contradiction_detector = ContradictionDetector(llm)
        self.store = store
        self.max_rounds = max_rounds
        self.evidence_index = evidence_index
        graph = StateGraph(ResearchState)
        graph.add_node("plan", self._plan)
        graph.add_node("research_and_verify", self._research_and_verify)
        graph.add_node("synthesize", self._synthesize)
        graph.add_edge(START, "plan")
        graph.add_edge("plan", "research_and_verify")
        graph.add_conditional_edges("research_and_verify", self._next_step,
                                    {"retry":"research_and_verify", "finish":"synthesize"})
        graph.add_edge("synthesize", END)
        self.graph = graph.compile()

    def _plan(self, state: ResearchState):
        subs = self.planner.plan(state["question"])
        if not subs:
            raise ValueError("Planner returned no subquestions")
        self.store.log(state["run_id"], "plan", subquestions=subs)
        return {"subquestions":subs}

    def _research_and_verify(self, state: ResearchState):
        run_id = state["run_id"]
        round_id = state["round_id"]
        evidence = dict(state["evidence"])
        accepted = dict(state["accepted"])
        rejected = list(state["rejected"])
        evaluated = set(state["evaluated"])
        pending = [s for s in state["subquestions"]
                   if not any(c.subquestion == s for c in accepted.values())]
        self.store.log(run_id,"round_start",round=round_id+1,pending=pending)
        for subq in pending:
            query, items = self.researcher.collect(subq,round_id)
            self.store.log(run_id,"search",subquestion=subq,query=query,returned=len(items))
            if self.evidence_index is not None:
                self.evidence_index.add(run_id,items)
            for e in items:
                evidence[e.evidence_id] = e
                self.store.log(run_id,"evidence",**e.model_dump())
            for claim in self.writer.extract(subq,items):
                if claim.claim_id in evaluated:
                    continue
                evaluated.add(claim.claim_id)
                verdict = self.verifier.verify(claim,evidence[claim.evidence_id])
                self.store.log(run_id,"verification",claim=claim.model_dump(),verdict=verdict.model_dump())
                if verdict.status == "supported":
                    accepted[claim.claim_id] = claim
                else:
                    rejected.append({"claim":claim.model_dump(),"verdict":verdict.model_dump()})
        return {"evidence":evidence,"accepted":accepted,"rejected":rejected,
                "evaluated":evaluated,"round_id":round_id+1}

    def _next_step(self,state: ResearchState):
        pending = [s for s in state["subquestions"]
                   if not any(c.subquestion == s for c in state["accepted"].values())]
        if pending and state["round_id"] < self.max_rounds:
            self.store.log(state["run_id"],"research_retry",missing=pending,
                           next_round=state["round_id"]+1)
            return "retry"
        return "finish"

    def _synthesize(self,state: ResearchState):
        accepted = list(state["accepted"].values())
        rejected = state["rejected"]
        discrepancies = []
        try:
            accepted_by_id = {claim.claim_id: claim for claim in accepted}
            for subq in state["subquestions"]:
                sub_claims = [c for c in accepted if c.subquestion == subq]
                raw_discrepancies = self.contradiction_detector.detect(
                    subq, sub_claims, state["evidence"])
                for item in raw_discrepancies:
                    claim_ids = list(dict.fromkeys(item.get("claim_ids", [])))
                    claims = [accepted_by_id[cid] for cid in claim_ids if cid in accepted_by_id]
                    # Keep only cross-source comparisons between already verified
                    # claims. Detector prose is intentionally not propagated.
                    if len(claims) < 2 or len({c.evidence_id for c in claims}) < 2:
                        continue
                    discrepancies.append({
                        "claim_ids": [c.claim_id for c in claims],
                        "statements": [c.statement for c in claims],
                        "evidence_ids": [c.evidence_id for c in claims],
                    })
            if discrepancies:
                self.store.log(state["run_id"], "contradictions_detected", discrepancies=discrepancies)
        except Exception:
            pass
        markdown, coverage = self.synthesizer.compose(
            state["question"], state["subquestions"], accepted, state["evidence"],
            discrepancies=discrepancies if discrepancies else None
        )
        attempts = len(accepted) + len(rejected)
        metrics = {"attempted_claims":attempts,"verified_claims":len(accepted),
                   "rejected_or_unverified_claims":len(rejected),
                   "verification_pass_rate":round(len(accepted)/attempts,4) if attempts else 0,
                   "subquestion_coverage":round(sum(coverage.values())/len(coverage),4) if coverage else 0}
        report = Report(run_id=state["run_id"],question=state["question"],markdown=markdown,
                        verified_claims=accepted,rejected_claims=rejected,
                        evidence=list(state["evidence"].values()),coverage=coverage,metrics=metrics)
        self.store.save(state["run_id"],report)
        self.store.log(state["run_id"],"completed",metrics=metrics)
        return {"report":report}

    def run(self,question: str) -> Report:
        run_id = str(uuid.uuid4())
        self.store.log(run_id,"started",question=question)
        final = self.graph.invoke({"run_id":run_id,"question":question,"subquestions":[],
          "evidence":{},"accepted":{},"rejected":[],"evaluated":set(),"round_id":0,
          "report":None},config={"recursion_limit":max(25,self.max_rounds*5+5)})
        return final["report"]
