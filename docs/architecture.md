# System Architecture

## Goal

The system helps a founder decide whether a LinkedIn post is worth engaging with and proposes a useful comment while keeping the founder in control of the final response.

## Primary Flow

1. Receive a LinkedIn post as input.
2. Evaluate whether the post is relevant enough to engage with.
3. If not relevant or unsafe to comment on, return "Do not engage" with a reason.
4. If relevant, select an appropriate comment mode.
5. Retrieve relevant voice evidence and previously approved feedback.
6. Generate a small number of candidate comments.
7. Check candidates for unsupported claims, generic wording, and obvious repetition.
8. Present candidates to the founder.
9. Founder approves, edits, or rejects a candidate.
10. Store the decision as feedback for future improvement.

## Components

### 1. Input Layer

Receives the post text and basic metadata.

Input is treated as untrusted external content.

The system does not automatically access or publish to LinkedIn.

### 2. Engagement Decision

Determines whether the founder should engage.

Possible outcomes:

* `ENGAGE`
* `SKIP`

The decision should include a short explanation.

The system should prefer `SKIP` when there is no useful contribution to make or when the response would require unsupported information.

### 3. Comment Mode Selector

For an `ENGAGE` decision, select one of four modes:

* `QUICK_REACTION`
* `HUMOROUS_PERSONAL`
* `ADD_INSIGHT`
* `THOUGHTFUL_QUESTION`

These modes are derived from the collected comment examples. The examples show both very short reactions and longer comments that add a new perspective or ask a specific question.

### 4. Voice Evidence Layer

Provides examples of the founder's observed writing and commenting behaviour.

The evidence should remain separate from generated output.

The system should distinguish:

* observed evidence
* interpretation
* assumptions

Company/brand writing should not automatically be treated as the founder's personal voice. The collected research explicitly labels several examples as "Written by Byro", so these should remain separate from personal voice evidence.

### 5. Comment Generator

Generates a small number of candidate comments using:

* the source post
* selected comment mode
* relevant voice examples
* previously accepted or edited examples

The generator must not invent personal experiences or unsupported facts on behalf of the founder.

### 6. Quality Check

Before human review, candidates are checked for:

* unsupported factual claims
* generic filler
* repetition
* mismatch with selected comment mode
* excessive length
* obvious mismatch with observed voice

A failed check should not silently modify the comment. It should either regenerate or mark the candidate as needing review.

### 7. Human Review

The founder is the final authority.

Available actions:

* `APPROVE`
* `EDIT`
* `REJECT`

The system must not automatically publish the comment.

### 8. Feedback Store

Store the founder's decision and, where relevant, the edited version.

Feedback is used as evidence for future generations.

The prototype will not implement model fine-tuning or autonomous learning. Adaptation will initially happen through retrieval of reviewed examples.

## State Model

```text
RECEIVED
   ↓
EVALUATED
   ├── SKIPPED
   │
   └── ENGAGE
          ↓
       DRAFTED
          ↓
       CHECKED
          ↓
       REVIEWED
       ├── APPROVED
       ├── EDITED
       └── REJECTED
```

Every transition should be explicit and inspectable.

## Data Boundaries

### Supplied Content

Examples:

* LinkedIn post text
* Public source examples
* Synthetic fixtures

This data is treated as untrusted input.

### Generated Content

Examples:

* engagement decision
* selected comment mode
* generated comment candidates
* quality warnings

Generated content must never be treated as ground truth automatically.

### Human Decisions

Examples:

* approval
* edited comment
* rejection
* optional rejection reason

These decisions are the strongest feedback signal available to the prototype.

### External Actions

The prototype performs no real LinkedIn action.

Publishing remains outside the system and under human control.

### Learning

Reviewed examples can be reused as future reference examples.

The prototype does not automatically change its own rules, retrain a model, or publish based on feedback.

## Failure Behaviour

If the system is uncertain whether a post is relevant:

`SKIP`

If no useful comment can be generated:

`SKIP`

If a candidate contains unsupported claims:

`REGENERATE or FLAG`

If the voice evidence is insufficient:

`FLAG LOW CONFIDENCE`

If the model fails:

Return an explicit error and preserve the original post/input.

The system should fail toward non-action rather than inventing a comment.

## Security and Privacy

The prototype will use synthetic fixtures and permitted public research.

It will not use:

* private LinkedIn data
* cookies
* credentials
* logged-in browser sessions
* unauthorized APIs
* automated LinkedIn posting

No external side effect occurs without explicit human action.

## Cost and Operational Trade-off

The prototype intentionally uses a single straightforward generation pipeline instead of multiple autonomous agents.

This reduces:

* implementation time
* token usage
* debugging complexity
* failure surface

More sophisticated ranking, model ensembles, or long-term personalization are deferred until the core usefulness is validated.

## Riskiest Assumption

The most important assumption is that the system can produce comments that are both useful for the specific post and sufficiently aligned with the founder's real commenting behaviour.

The prototype should therefore optimize for evaluating this assumption rather than maximizing feature count.
