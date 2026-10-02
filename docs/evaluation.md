# Evaluation Notes

The deterministic evaluation set contains 25 cases covering relevant posts, uncertain/ASK cases, sensitive contexts, promotion, unrelated posts, and a prompt-injection fixture.

Latest deterministic run:

- Cases: 25
- Decision accuracy: 25/25 (100%)
- Skip accuracy: 9/9 (100%)
- Expected: 12 engage / 4 ask / 9 skip
- Actual: 12 engage / 4 ask / 9 skip
- Drafts flagged by quality checks: 12
- Drafts blocked by claims guard: 1
- Mode distribution: 4 add_insight, 1 humorous_personal, 6 quick_reaction, 1 thoughtful_question

These metrics are only for the deterministic stub. They are a reproducibility/safety baseline, not evidence that the live LLM's comments are good.
