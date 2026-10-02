# Decision Log

## Architecture and Product Decisions

### 1. Canonical Founder-Evidence Model & Hierarchy
- **Decision:** Unified `src/context.py` and `src/founder_context.py` into a single canonical evidence pack. 
- **Rationale:** Previously, UI calibration came from one store while LLM generation consulted another. Now, observed comments (target-matched vs style-only), founder context overrides, reviewed feedback, and candidate calibration are strictly distinguished in a shared object with explicit authority ranking.
- **Alternatives Considered:** Keeping separate retrieval stores for UI and model. Rejected due to drift and display ambiguity.

### 2. Inspectable Founder-Fit Scoring Over Static Keyword Allow-Lists
- **Decision:** Replaced the static keyword list in `src/engagement.py` with an inspectable founder-fit score (0.0 to 1.0) and explicit positive/negative factors.
- **Rationale:** Different founders have different topical authority (e.g. Fathin on agent evaluations and recovery boundaries vs Rico on early-stage hackathon velocity and shipping). The system surfaces positive factors (+), warning/caution factors (-), and allows human override via "Draft Anyway".

### 3. Contribution Planning Before Word Selection
- **Decision:** Added `src/planner.py` to identify the post's core hook, context type, plausible founder contribution, and response shape before generating words.
- **Rationale:** LLMs tend to generate fluent, generic praise if not constrained by the specific tension or milestone in the source post. Defining the contribution first grounds the generation and prevents artificial variety.

### 4. Dual Candidate Generation Only When Justified
- **Decision:** The system returns 2 distinct candidates (e.g. observation + mechanism question) only when the post's depth justifies two angles; otherwise it returns 1 grounded candidate or abstains (`CANNOT_GENERATE`).
- **Rationale:** Forcing multiple drafts on simple posts produces generic filler. The founder is presented with distinct response shapes rather than cosmetic paraphrases.

### 5. Vocabulary Stuffing Guardrails
- **Decision:** Added deterministic vocabulary stuffing checks in `src/quality.py`.
- **Rationale:** Terms associated with founders (e.g., Rico's *"young goats"* or *"canon event"*) must never be used unless the post context independently warrants them (student hackathons or early startup struggles). Vocabulary refines style, but never supplies the topic.

### 6. Strengthened Claims Ledger & Adversarial Injection Defense
- **Decision:** Expanded `src/claims.py` to check multiplier metrics (`10x`, `2x`), customer/client claims, and external person attributions. In `src/engagement.py`, prompt injections embedded in high-topic posts trigger a hard, safe `SKIP`.
- **Rationale:** Preserving the human's reputation is paramount. Fabricated client results or external attributions destroy trust.

### 7. Reversible Scoped Feedback & Edit Magnitude
- **Decision:** Feedback records now track `edit_magnitude` (light vs substantial via string similarity) and support individual deletion via `delete_review`.
- **Rationale:** Erroneous or regretted feedback must be reversible without corrupting the founder's long-term retrieval memory.

### 8. Held-Out Evaluation & Generic Baseline Comparison
- **Decision:** Added `fixtures/held_out_eval.json` (10 independent cases) alongside the 25-case regression suite in `src/eval.py`, plus `src/founder_eval.py` for side-by-side comparison against a generic LLM baseline.
- **Rationale:** Proving system correctness requires evaluating on held-out cases that were not used during initial prompt engineering.

## Verification & Test Results

- **Test Suite:** 64 passed in `python -m pytest -q` covering claims, comment mode, context sync, engagement, evidence context, founder context, generator, pipeline, quality, and review.
- **Regression Suite:** 25/25 (100% accuracy, 100% skip accuracy).
- **Held-Out Suite:** 10/10 (100% accuracy, 100% skip accuracy).

## Known Limitations & Next Steps

1. **Embeddings-based Retrieval:** Semantic retrieval is currently high-precision lexical F1. Moving to dense embeddings would improve synonym recall while retaining target-post matching.
2. **Public Provenance URLs:** Public LinkedIn comment examples in `fixtures/voice_examples.json` have provenance notes; original post URLs should continue to be enriched where publicly archived.
