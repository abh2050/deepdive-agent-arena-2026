# DeepDive — 2-Minute Hackathon Demo

Target length: **1:55–2:00**  
Format: **1080p, 16:9, voice-over with cursor highlights**  
Live app: **https://deepdive-agent-arena-2026.vercel.app/**

## Recording preparation

1. Open the live app in a clean browser window at 100% zoom.
2. Confirm the header says `Mesh API: Active` and Demo Mode is off.
3. Prepare this question:
   `What evidence supports and limits residential heat pump energy savings?`
4. Record the real run, then shorten the waiting period to about three seconds in
   the edit. Add the caption `Real Mesh run — wait condensed` during the cut.
5. Keep API keys, browser bookmarks, notifications, and the Vercel dashboard out
   of frame.

## Timed script and shot list

| Time | Screen action | Narration |
|---|---|---|
| **0:00–0:09** | Start on the DeepDive hero. Slowly move toward the research input. | “AI research can look convincing while hiding weak evidence. DeepDive changes the rule: a claim is published only after it proves where it came from.” |
| **0:09–0:24** | Scroll to the four diagram tabs. Click **Architecture**, then **Verification loop**. | “DeepDive is a self-verifying research analyst built with LangGraph, Mesh API, ChromaDB, and SQLite. Separate agents plan, retrieve, write, and verify—while a bounded retry loop searches again when coverage is thin.” |
| **0:24–0:37** | Click **Evidence lineage** and briefly trace Open Web → Evidence Records → Verified Claims → Report. | “Retrieved pages stay untrusted. Each candidate carries an evidence ID and verbatim quote. The quote must exist in the stored excerpt, and a separate Mesh-routed verifier must confirm full entailment.” |
| **0:37–0:49** | Return to the research input, paste the heat-pump question, ensure Demo Mode is off, and click **Execute DeepDive**. | “Here is a real question running through the live Vercel deployment. Every generative call goes through one mandatory Mesh gateway.” |
| **0:49–0:53** | Condense the wait. Show a small overlay: `Real Mesh run — wait condensed`. | “The coordinator decomposes the question, gathers web evidence, challenges candidate claims, and retries missing coverage.” |
| **0:53–1:12** | Reveal the completed report and metrics. Hover over verified and rejected totals. | “The result does not optimize for a flattering pass rate. Unsupported or ambiguous candidates are rejected; only supported claims reach the deterministic report.” |
| **1:12–1:28** | Click a citation. Open the Evidence Inspector and highlight the source URL, stored excerpt, exact quote, and verdict. | “Every accepted statement is inspectable. Judges can see the source, captured excerpt, exact supporting quote, quality signal, and the verifier’s decision.” |
| **1:28–1:41** | Open **Audit Trail** and scroll through plan, search, evidence, verification, retry, and completion events. | “Every decision leaves an audit event, including searches, rejected claims, retries, and final metrics. The system shows its working instead of asking users to trust a polished answer.” |
| **1:41–1:51** | Ask: `What did the verified evidence establish?` Show the cited follow-up response. | “Follow-up questions remain grounded in the same run evidence and return the evidence IDs they used.” |
| **1:51–2:00** | Finish on the hero or repository README with both URLs visible. | “DeepDive turns citation into an enforceable boundary: no stored quote, no verified claim, no publication. Try the live app and inspect every decision.” |

## On-screen text overlays

Use only four short overlays:

- `No stored quote → no accepted claim`
- `Quote match + independent entailment`
- `Real Mesh run — wait condensed`
- `Every decision is auditable`

## YouTube metadata

**Title**

`DeepDive — Self-Verifying Research Analyst | Agent Arena 2026`

**Description**

```text
DeepDive is a self-verifying multi-agent research analyst built for Agent Arena
2026. Every candidate claim must reference fetched evidence, include a verbatim
source quote, and pass an independent Mesh-routed entailment check before it can
appear in the final report.

Live app: https://deepdive-agent-arena-2026.vercel.app/
Repository: https://github.com/abh2050/deepdive-agent-arena-2026
System atlas: https://abh2050.github.io/deepdive-agent-arena-2026/#architecture

Built with LangGraph, Mesh API, FastAPI, ChromaDB, and SQLite.

#AgentArena2026 #AI #MultiAgentSystems #ResponsibleAI #LangGraph
```

**Thumbnail text**

`CAN THIS AI PROVE EVERY CLAIM?`

Use a screenshot of the Verification Loop with the Dual Verifier highlighted.

## Final upload checklist

- Video is public or unlisted, not private.
- Duration is at most 2:00.
- The Vercel URL is visible and clickable in the description.
- No API keys, tokens, personal tabs, or notifications appear.
- The “wait condensed” caption remains visible during the edit.
- Voice is clear and background music stays below the narration.
- The first frame communicates the problem without requiring audio.
