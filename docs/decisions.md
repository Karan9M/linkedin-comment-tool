# Decision Log

## Current implementation decisions

### Deterministic baseline first
A deterministic engagement gate and stub model are used so the core behavior can be tested without model credentials.

### Groq for live generation
The live prototype uses Groq with `openai/gpt-oss-20b`. The provider is replaceable through `BYRO_MODEL_PROVIDER`.

### Human approval remains mandatory
No LinkedIn action is automated. Approval can create only a local/mock handoff.

### Feedback is contextual
Reviewed examples are tied to founder, post context, comment mode, draft, final text, and decision. This avoids cross-founder contamination.

### Claims are blocked, not silently rewritten
Unsupported numeric claims, URLs, and first-person experience claims are surfaced as blocking warnings. The founder must edit or otherwise resolve them.

## Known limitations to test next

- Current voice profiles are structured interpretations from a small evidence set, not learned model weights.
- No production LinkedIn ingestion exists.
- Source URLs are missing from the current research export and must be added before submission where available.
- Semantic retrieval is currently lightweight lexical matching; the next improvement is context-aware retrieval over target posts and reviewed feedback.

## AI use and mistakes

AI tools were used to help draft code and analyze the challenge. Generated code is verified through focused tests and manual demo runs. One recurring AI failure observed in the prototype was fluent but generic LinkedIn language, which motivated the voice profile, feedback memory, rejection patterns, and quality gates.
