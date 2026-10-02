# Byro Comment Copilot — Completion Plan

## Product outcome

Help a founder decide whether to join a LinkedIn conversation and, only when
there is a believable contribution to make, propose a comment that sounds like
that founder rather than a generic AI writer. The founder always owns the
decision to use, edit, reject, or publish a comment.

The main product loop is:

```text
post → founder-specific engagement decision → grounded candidate(s)
     → human approve / edit / reject → scoped feedback → later retrieval
```

## Evidence reviewed

`C:\Users\Karan\Downloads\byro.excalidraw` is user-supplied research material.
It contains personal posts and comments for Fathin and Rico, plus posts labelled
`[Written by Byro]`. Treat the latter as company/brand context only, never as a
founder's personal commenting voice. Before final submission, retain a source
URL or a clear provenance note for every public example.

Initial observed patterns to validate, not immutable rules:

- **Fathin:** comments range from terse reactions to specific technical
  observations and questions. His stronger longer comments name a concrete
  distinction, challenge an assumption, or ask a question tied to the post's
  mechanism (for example, evaluation unit, recovery path, ownership, or
  evidence). They should not be imitated through repeated stock phrases.
- **Rico:** comments are usually very short, informal, contextual, and often
  playful. Words such as `W`, `Facts`, or `young goats` work only where the
  source post gives them a natural reason; a word in his history is not a
  universal template.

## Definition of a useful draft

A candidate is useful only when all of these are true:

1. It reacts to one specific idea, achievement, tension, or question in the
   source post.
2. Its response shape fits the founder and the context: reaction,
   congratulations, contextual joke, observation, or question.
3. It does not invent a fact, relationship, experience, result, or opinion for
   the founder.
4. It would still make sense if founder vocabulary were removed from the
   prompt. Vocabulary can refine wording, never supply the content.
5. It has no generic LinkedIn filler and no copied wording from an unrelated
   historical comment.
6. The founder can approve it, lightly edit it, or reject it; the system never
   publishes it.

## P0 — Repair the learning and evidence loop

- [ ] **Create one canonical founder-evidence model.** Merge the currently
  separate `src/context.py` and `src/founder_context.py` flows. One founder
  record must contain observed examples, source/provenance, founder-provided
  preferences, approved/edited feedback, rejection patterns, and synthetic
  calibration.
- [ ] **Fix the current context disconnect.** Edits made in the Founder Context
  UI currently save to `data/founder_context_overrides.json`, whereas generation
  reads a different data path. Make a saved edit visible in the next generation
  prompt and cover it with a regression test.
- [ ] **Remove display-only calibration ambiguity.** The calibration examples
  displayed by the pipeline and the calibration data consulted by generation
  currently come from different stores. Either use one record in both places or
  label a record as not used for generation.
- [ ] **Add explicit evidence types and authority.** `observed_comment`,
  `observed_post`, `founder_preference`, `human_approved_feedback`,
  `human_edited_feedback`, `human_rejection`, and `synthetic_calibration` must
  remain distinguishable in storage, UI, retrieval, and prompts.
- [ ] **Scope all learning.** Retrieve feedback only for the same founder and a
  relevant post/mode. Store feedback event metadata: original draft, final text,
  decision, edit magnitude, optional reason, source post, and timestamp.
- [ ] **Make feedback reversible.** Preserve delete/correction controls and
  ensure deleted records cannot be retrieved later.

## P0 — Make generation founder-specific rather than vocabulary-driven

- [ ] **Choose the contribution before choosing the words.** Add a planning
  step that identifies: the post's one meaningful hook, its context type, the
  founder's plausible contribution, an appropriate response shape, and the
  evidence allowed to influence style.
- [ ] **Use context-sensitive retrieval.** Retrieve historical comments by
  similarity of their target posts, response shape, founder, and authority.
  Unrelated comments may inform brevity or punctuation only; they must not lend
  their topic, joke, or call-to-action to a new post.
- [ ] **Generate two candidates only when justified.** Produce distinct,
  grounded options (for example, a concise reaction and a specific question),
  or return one candidate / `CANNOT_GENERATE` if a second option would become
  generic. Do not create artificial variety.
- [ ] **Require structured generation output.** Return candidate text,
  selected mode, source-post evidence, style-evidence IDs, confidence, and a
  reason to abstain. Validate this schema before rendering it.
- [ ] **Ground every candidate.** Reject or flag drafts whose substantive idea
  cannot be traced to the source post or an explicitly approved founder fact.
- [ ] **Prevent vocabulary stuffing.** Add a test that a founder-associated
  term is absent unless it is natural for the source-post context.

## P0 — Improve engagement and safety decisions

- [ ] **Replace the broad topic allow-list with an inspectable founder-fit
  score.** Consider founder interests, post type, a specific contribution
  opportunity, sensitivity, promotion, recent engagement, and uncertainty.
- [ ] **Explain each decision.** Display the positive and negative factors for
  `ENGAGE`, `ASK`, and `SKIP`; record a human override when Draft Anyway is used.
- [ ] **Strengthen claim checks.** Keep deterministic URL/number/persona checks,
  but add support checks for attribution, misleading paraphrase, unsupported
  opinions presented as founder experience, and irrelevant copied claims.
- [ ] **Treat post text as untrusted.** Expand injection tests to include posts
  that contain both a relevant topic and malicious instructions.
- [ ] **Fail toward non-action.** If grounding, retrieval, generation, or
  validation fails, return an explicit reason and preserve the original input.

## P1 — Product experience

- [ ] Show the engagement explanation, selected response shape, and the small
  set of evidence used for each draft.
- [ ] Clearly label observed evidence, founder preference, reviewed feedback,
  and synthetic calibration in the UI.
- [ ] Let the founder record a structured rejection reason (too generic, wrong
  tone, wrong context, inaccurate, too long, other) plus optional free text.
- [ ] On an edit, show what changed between AI draft and final version and
  classify it as light or substantial. Use that signal in learning and metrics.
- [ ] Keep the local mock handoff. Do not add LinkedIn authentication,
  scraping, or automated publishing.

## P1 — Validation and tests

- [ ] Make `python -m pytest -q` and `python -m src.eval` runnable from a clean
  environment using the documented setup command.
- [ ] Keep the existing synthetic deterministic evaluation as a regression
  suite, but do not present its accuracy as proof of founder value.
- [ ] Add held-out evaluation cases written independently of the routing rules.
- [ ] Add tests for evidence provenance, founder isolation, context persistence
  into prompts, relevance retrieval, vocabulary stuffing, deletion, duplicate
  feedback, and high-topic prompt injection.
- [ ] Run a small founder evaluation using fixed posts and a generic baseline.
  For each candidate, collect: approve, light edit, heavy edit, reject;
  “sounds like me”; “adds value”; and an optional reason.
- [ ] Define success before the session: an acceptance-or-light-edit rate and a
  founder-voice rating that beat the generic baseline. Record failures as future
  evaluation cases.

## P2 — Architecture and delivery hygiene

- [ ] Replace ad-hoc JSON persistence with a small local SQLite store if the
  evidence and feedback model becomes difficult to query or audit. Keep the
  repository small and reproducible.
- [ ] Add an architecture diagram showing input, supplied evidence, generated
  proposals, human decisions, feedback storage, and mock handoff boundaries.
- [ ] Document retention/deletion behavior and model-provider failure handling.
- [ ] Create and initialize the required Git repository; preserve a clean,
  reproducible setup.
- [ ] Complete submission material: source provenance, decision log, actual
  time log, demo/walkthrough, repository URL, final commit SHA, and either
  design-partner evidence or the explicit next validation experiment.

## Build order

1. Canonical evidence/feedback model and context-persistence fix.
2. Grounded planning, retrieval, structured generation, and validation.
3. UX for evidence, alternatives, and rich feedback capture.
4. Regression tests and held-out evaluation.
5. Founder evaluation, iteration from real failures, and submission polish.

## Explicit non-goals for this challenge

- Automated LinkedIn access, posting, scraping, credentials, or private data.
- Fine-tuning a model before reviewed-feedback retrieval has been validated.
- A large multi-agent architecture, authentication, billing, or production
  deployment.
