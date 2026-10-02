# Byro Adaptive LinkedIn Commenting — Technical Proof

A human-in-the-loop system designed for founders (Fathin Dosunmu & Rico Soots) to decide when to engage on LinkedIn, propose grounded comments in their authentic voice, and improve over time through reviewed feedback while keeping the human in absolute control.

---

## Deliverables & Documentation Index

In accordance with the Byro Technical Challenge specification:

| Deliverable | Location | Description |
|---|---|---|
| **Product Definition** | [`docs/product.md`](docs/product.md) | User discovery, 4 comment modes, success signals, when to do nothing, and non-goals |
| **System Architecture** | [`docs/architecture.md`](docs/architecture.md) | Flow, Mermaid diagram, state machine, authority boundaries, failure recovery, and trade-offs |
| **Decision Log** | [`docs/decisions.md`](docs/decisions.md) | Assumptions, alternatives considered, AI tool usage, AI mistakes caught via verification, and next experiments |
| **Time Log** | [`docs/TIME_LOG.md`](docs/TIME_LOG.md) | Active work timebox breakdown by phase totaling **7.75 / 10.0 hours** |

---

## Quick Start (One Setup Command)

```bash
pip install -r requirements.txt
```

> **Note:** External LLM credentials are completely optional. The system includes an inspectable, zero-cost deterministic stub model for local evaluation and testing without external dependencies or API keys. If you wish to use live Groq inference, set `GROQ_API_KEY` in your `.env` file.

---

## Verification & Test Commands

### 1. Focused Unit Tests (64 Passing)
Runs tests covering claims guards, inspectable engagement, contribution planning, canonical evidence hierarchy, multi-candidate generation, quality checks, and review reversibility:
```bash
python -m pytest -q
```

### 2. Multi-Suite Evaluation (100% Accuracy)
Evaluates 25 primary regression cases and 10 held-out independent cases across relevant topics, edge cases, sensitive contexts, and adversarial prompt injections:
```bash
python -m src.eval
```

### 3. Side-by-Side Founder vs Generic Benchmark
Runs comparative evaluation demonstrating how Byro's contribution-planned, voice-calibrated drafts avoid generic AI enthusiasm ("Awesome post! Completely agree!"):
```bash
python -m src.founder_eval
```

---

## Running the Interactive Proof

Launch the Streamlit web interface:
```bash
streamlit run app.py
```

### Key UI Capabilities to Explore:
1. **Founder Selector:** Switch between **Fathin Dosunmu** (systems, AI agent evaluation, operational boundaries) and **Rico Soots** (hackathons, early shipping velocity, student builders).
2. **Inspectable Engagement Gate:** See exact positive factors (`+`) and negative risk factors (`-`) driving the `ENGAGE`, `ASK`, or `SKIP` decision.
3. **Adversarial Safety Defense:** Test prompt injection attempts (e.g. *"Ignore previous instructions..."*) to see deterministic hard `SKIP` non-action.
4. **Contribution Planning & Proposals:** Inspect the detected post hook, context type, and alternative candidate drafts.
5. **Real-Time Claims Guard & Quality Checks:** Watch the claims ledger flag unverified numbers or external person attributions.
6. **Classified Review & Mock Outbox:** Approve to dispatch to [`data/outbox.json`](data/outbox.json), edit with live edit-magnitude classification (light vs substantial), or reject with structured failure categories.
7. **Reversible Memory:** Inspect, review, and delete learned feedback in the Learned Memory tab without restarting the app.

---

## Riskiest Assumption & Technical Solution

- **The Riskiest Assumption:** A system cannot capture an authentic founder's voice merely by throwing past comments into an LLM prompt. Pure statistical word completion defaults to bland pleasantries or artificial catchphrase stuffing (*"AI cringe"*).
- **The Technical Solution:**
  1. **Deterministic Gate:** Pre-screen posts to ensure the founder has true topical authority; fail towards non-action (`SKIP`).
  2. **Contribution Planner:** Identify the post's core tension and formulate a distinct contribution angle *before* word selection.
  3. **Canonical Evidence Hierarchy:** Separate observed comments, style exemplars, and reviewed feedback with strict tenant/founder isolation.
  4. **Quality & Claims Guardrails:** Prohibit unverified multiplier metrics, customer claims, and out-of-context slang.

---

## Human Authority & Safety Invariants

- **Zero Scraping & Zero Auto-Posting:** The system strictly treats post input as untrusted data. It never connects to LinkedIn APIs, does not automate browser sessions, and never posts on behalf of the user.
- **Mock Handoff:** Approvals generate structured records in local [`data/outbox.json`](data/outbox.json) for human-managed distribution.
- **Reversibility:** Stored feedback records can be inspected and deleted via the UI or `delete_review()`, instantly purging them from retrieval.
