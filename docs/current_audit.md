# Current Project Audit

## Baseline reviewed

The uploaded project contained 25 source/test/data files. Before this upgrade it had a clean deterministic skeleton, a Groq generator, basic engagement/topic checks, lexical voice retrieval, simple quality warnings, and a human review file.

## Concrete gaps found

- The LLM was only mocked in tests; there was no deterministic end-to-end evaluation harness.
- No claims ledger or blocking claims validator existed.
- Feedback stored only candidate/decision/edit/reason and therefore could not be safely scoped by founder or post context.
- Existing feedback contained two duplicate edits and no founder/post context, so it was not safe to reuse as learning evidence.
- Engagement was binary and keyword-based with substring matching (`ai` could match inside unrelated words).
- SKIP stopped the flow with no human override.
- Approval only saved feedback; there was no explicit mocked handoff/outbox.
- Prompt injection was described but not tested.
- There was no README, no deterministic evaluation command, and the time log was empty.
- All current public voice examples had null source URLs; they must be added before submission if the sources can be identified.
- One fixture contained an invalid comment mode (`practical_agreement`). It is now normalized to no mode instead of leaking an invalid enum value.

## Changes made in this phase

- Added `ASK` engagement state and human `Draft Anyway` override.
- Added word-boundary topic matching, sensitive-topic skips, recent-comment flag, uncertainty handling, and promotion heuristics.
- Added founder-aware comment mode selection.
- Improved voice retrieval to prefer similarity between the new post and the historical target post, and to prefer the selected comment mode.
- Added founder voice profiles with evidence IDs.
- Added contextual feedback records with founder, post, mode, AI draft, final text, reason, timestamp, stable ID, and deduplication.
- Added founder-scoped feedback retrieval and rejection-pattern retrieval.
- Added a deterministic stub model so the app/evaluation can run without Groq credentials.
- Added post delimiters and explicit untrusted-content instructions for prompt-injection resistance.
- Added deterministic claims checks for unsupported numeric claims, URLs, and first-person experience/result claims. Claims failures block one-click approval.
- Added a local mock outbox for approved handoffs.
- Added 25-case deterministic evaluation fixtures and `python -m src.eval`.
- Added 5 synthetic demo posts per founder.
- Added a Learned Memory UI with delete support.
- Added README, `.env.example`, and a decision log.
- Moved the old unscoped feedback to `data/legacy_feedback.json`; it is intentionally not used as learning evidence.

## What remains

- Public source URLs are still missing from the imported voice dataset.
- The deterministic eval proves routing/safety behavior, not real LLM voice quality.
- Retrieval is still lightweight lexical retrieval rather than embeddings.
- The live Groq model should be manually re-tested on the new pipeline with the user's key.
- The TIME_LOG must be filled by the candidate with actual active time; it must not be invented by tooling.
