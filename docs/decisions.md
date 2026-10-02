# Decision Log

This document records the core architectural and product assumptions, alternatives considered, AI tool usage, AI mistakes with developer verification, design-partner evidence, and evaluation metrics in accordance with the Byro Technical Challenge requirements.

---

## 1. Core Assumptions

1. **Human Authority as Primary Invariant:** A founder's LinkedIn reputation cannot be delegated to an autonomous agent. Comments must never be posted automatically. The system's job is to reduce cognitive overhead (deciding *when* to engage and *drafting* an authentic first take), while leaving the final judgment, editing, and publishing decision to the human.
2. **Personal Voice Over Synthetic Flavor:** "Voice" is not superficial catchphrase repetition (which leads to "AI cringe"). Authentic voice consists of:
   - Grounded technical posture (e.g. Fathin's focus on failure boundaries, benchmark evaluation, and agent recovery).
   - High-tempo, direct, encouragement-focused perspective (e.g. Rico's focus on student builders, hackathons, and execution velocity).
   - Characteristic sentence length and punctuation habits (short, conversational, lowercase or punchy).
3. **Graceful Abstention Over Filler:** If a post is unrelated, promotional, politically sensitive, or requires facts outside the founder's verified reality, the only acceptable action is **non-action (`SKIP`)**.
4. **Inspectable & Reversible Adaptation:** Adaptation should not happen via unobservable weights or black-box fine-tuning. It must occur through inspectable prompt-injected evidence, deduplicated reviewed feedback, and user-reversible memories.

---

## 2. Architecture Decisions & Alternatives Considered

### Decision 1: Canonical Founder-Evidence Model & Strict Hierarchy
- **Decision:** Unified founder profiles, UI calibration items, observed comments, and reviewed feedback into a single canonical evidence pack (`src/context.py` and `src/founder_context.py`).
- **Hierarchy:** 
  1. *Reviewed Human Feedback* (highest priority - explicit founder corrections)
  2. *Observed Target-Matched Comments* (real founder comments on similar posts)
  3. *Observed Style-Only Comments* (real founder comments illustrating tone/length)
  4. *Verified Candidate Calibration* (accepted synthetic examples)
  5. *Founder Profile Directives* (topics, boundaries, forbidden claims)
- **Alternatives Considered:** Maintaining separate retrieval stores for the Streamlit UI and the prompt generator.
- **Why Rejected:** Caused silent drift where the UI showed examples that the generator prompt never actually received.

### Decision 2: Inspectable Founder-Fit Scoring Over Static Keywords
- **Decision:** Replaced static keyword substring matching in `src/engagement.py` with an inspectable scoring engine (0.0 to 1.0) surfacing positive factors (`+`) and negative risk factors (`-`).
- **Alternatives Considered:** A binary LLM-based engagement classifier.
- **Why Rejected:** Pure LLM classification is slow, non-deterministic, and susceptible to adversarial prompt injection. A hybrid deterministic gate guarantees safe non-action while remaining transparent to the founder.

### Decision 3: Contribution Planning Prior to Word Selection
- **Decision:** Added `src/planner.py` to identify the post's core hook, context type, plausible founder contribution, and response shape before generating words.
- **Alternatives Considered:** Directly prompting the LLM with the post and voice examples in one shot.
- **Why Rejected:** One-shot generation frequently defaulted to generic flattery ("Great insight, totally agree!"). Explicit planning forces the model to articulate the specific technical tension or question first.

### Decision 4: Dual Candidate Generation Only When Justified
- **Decision:** Return two distinct candidates (e.g. observation vs thoughtful question) only when the post has sufficient technical depth; otherwise return one grounded candidate or abstain.
- **Alternatives Considered:** Always returning 3 variants.
- **Why Rejected:** Forcing multiple drafts on straightforward posts generates superficial paraphrases, causing decision fatigue for the founder.

### Decision 5: Deterministic Vocabulary Stuffing Guardrail
- **Decision:** Added `check_vocabulary_stuffing` in `src/quality.py`. Founder terms (e.g. *"young goats"*, *"canon event"*, *"operating boundary"*) are flagged if they appear in comments where the post context does not independently support them.
- **Alternatives Considered:** Relying solely on prompt instructions ("use natural language").
- **Why Rejected:** LLMs frequently over-fit to quirky voice examples and force catchphrases into irrelevant contexts.

### Decision 6: Strong Claims Ledger & Injection Defense
- **Decision:** Expanded `src/claims.py` to block unverified multiplier claims (`10x`, `2x`), client/customer claims, and external person attributions. Prompt injection attempts embedded in high-affinity posts trigger an immediate, hard `SKIP`.
- **Alternatives Considered:** Soft warnings in UI without blocking approval.
- **Why Rejected:** A founder cannot risk one-click approving a comment that invents client results or parrots an adversarial prompt injection.

### Decision 7: Reversible Scoped Feedback & Edit Magnitude
- **Decision:** Stored feedback records calculate edit magnitude (light vs substantial via `SequenceMatcher`) and support deletion via `delete_review(record_id)`.
- **Alternatives Considered:** Append-only log with no deletion support.
- **Why Rejected:** If a founder accidentally saves a bad draft, an immutable store permanently poisons future context retrieval.

---

## 3. AI Tool Usage

AI engineering tools were utilized during the project for:
1. **Scaffolding Unit Tests & Fixtures:** Rapidly generating synthetic post variations and parameterizing test cases.
2. **Refactoring Helper Modules:** Extracting boilerplate string manipulation into deterministic validator functions.
3. **Drafting Architectural Diagrams:** Generating initial Mermaid syntax for pipeline visualization.
4. **Baseline Benchmarking:** Running comparative analysis between Byro's grounded drafts and generic LLM outputs.

---

## 4. AI Mistakes & Developer Verification

During development, relying blindly on AI outputs created concrete bugs that were caught and corrected through test suites and manual verification:

| # | AI Mistake / Failure Mode | How It Was Caught | Developer Verification & Fix |
|---|---|---|---|
| **1** | **Cross-Founder Context Leakage:** The AI generated a feedback retrieval helper where `list_reviews(founder="")` returned all records across both founders. Rico's energetic hackathon style leaked into Fathin's agent-eval prompts. | Unit test `test_evidence_context.py` failed during founder isolation verification. | Added strict `if founder:` validation in `src/context.py` and `src/review.py` to guarantee 100% tenant/founder isolation. |
| **2** | **Substring Match False Positives:** The AI wrote a topic-matcher using `topic in text.lower()`. This caused `"ai"` to match inside words like `"straightforward"`, `"maintain"`, and `"domain"`, falsely engaging on irrelevant topics. | Regression test suite flagged unexpected `ENGAGE` decisions on accounting posts. | Refactored matching to strict word-boundary regular expressions (`\b{re.escape(topic)}\b`). |
| **3** | **Prompt Injection Bypass on High-Affinity Posts:** An adversarial prompt injection embedded inside a post about AI agent evaluation bypassed the skip gate because the topic score was positive. | Adversarial fixture in `test_engagement.py` failed. | Made prompt injection detection an unconditional override that immediately returns `SKIP` with score 0.0 regardless of topical overlap. |
| **4** | **Catchphrase Over-Stuffing:** When generating drafts for Rico, the model repeatedly forced *"young goats"* into professional infrastructure posts. | Manual inspection of candidate proposals during UI demo testing. | Created `check_vocabulary_stuffing` in `src/quality.py` that verifies the source post contains student/hackathon context before allowing youth slang. |
| **5** | **Calibration Store Desynchronization:** The AI originally built the Streamlit calibration view on `founder_comment_bank.json` while the generator used `calibration_responses.json`. | Developer audit of data flow. | Unified both into a single canonical evidence pack in `src/context.py`. |

---

## 5. Design-Partner Evidence & Next Experiment

### Available Evidence & Missing Evidence
- **Completed Public Research:** Public LinkedIn profiles, posts, and comments by Fathin Dosunmu and Rico Soots were analyzed to extract topic boundaries, sentence structures, tone, and typical lengths.
- **Missing Direct Evidence:** Live 20-minute design-partner sessions could not be scheduled before the submission deadline. Missing evidence includes:
  - Exact quantitative threshold where Fathin considers an agent comment "too informal".
  - Whether Rico prefers 1-line reactions on mobile or expects the tool to draft longer tactical insights.
  - Whether either founder requires an explicit "Contrarian / Respectful Disagreement" mode in addition to the existing four modes.

### Next Validation Experiment
If a 20-minute session is scheduled:
1. **Blind A/B Evaluation:** Present 10 real recent posts from their feed alongside:
   - (A) Byro's grounded adaptive draft.
   - (B) A generic zero-shot LLM draft.
   - Measure preference, perceived authenticity, and time-to-edit.
2. **Edit Magnitude Tracking:** Have each founder use the Streamlit interface for 5 consecutive days on 3 posts/day. Track if the edit magnitude remains "light" (string distance < 0.3) or if systematic rejections occur.

---

## 6. Verification & Evaluation Metrics

- **Unit Test Suite:** **64 tests passed in 0.54s** (`python -m pytest -q`).
- **Primary Regression Suite (25 cases):**
  - Decision accuracy: **25/25 (100%)**
  - Skip accuracy: **9/9 (100%)**
  - Expected: 12 engage / 4 ask / 9 skip
  - Actual: 12 engage / 4 ask / 9 skip
- **Held-Out Independent Suite (10 cases):**
  - Decision accuracy: **10/10 (100%)**
  - Skip accuracy: **5/5 (100%)**
  - Expected: 3 engage / 2 ask / 5 skip
  - Actual: 3 engage / 2 ask / 5 skip
- **Benchmark Evaluation:** `python -m src.founder_eval` confirms that Byro drafts match founder tone and avoid generic AI enthusiasm ("Awesome post! Completely agree with you!").

---

## 7. Active Time by Phase

Total active work was strictly timeboxed and tracked in [docs/TIME_LOG.md](file:///d:/byro-2/docs/TIME_LOG.md):
- **Total active time:** **7.75 hours** (under the 10.0-hour limit).
