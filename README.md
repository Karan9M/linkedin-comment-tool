# Byro Adaptive LinkedIn Commenting

A small human-in-the-loop prototype for deciding when a founder should engage on LinkedIn, proposing a founder-specific comment, checking obvious risks, and learning from reviewed feedback.

## Quick start

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Create `.env` from `.env.example` if using Groq. No key is needed for the deterministic stub.

## Run the demo

```bash
streamlit run app.py
```

To force the free deterministic model:

```powershell
$env:BYRO_MODEL_PROVIDER="stub"
streamlit run app.py
```

## Tests

```bash
python -m pytest -q
```

## Deterministic evaluation

```bash
python -m src.eval
```

The evaluation uses 25 synthetic/adversarial cases and the deterministic stub, so it does not require a Groq key. It reports decision accuracy, skip accuracy, quality flags, claims blocks, and mode distribution.

## Current human-control boundary

The system can recommend, draft, block, save feedback, and create a mocked handoff. It never logs into LinkedIn or posts a real comment.

## Data provenance

Fixtures are a mix of candidate-created synthetic data and manually collected public examples. Source URLs are still required for the public voice examples before final submission; they are intentionally not invented.

## Evaluation and audit

See `docs/current_audit.md` and `docs/evaluation.md`. The deterministic evaluation is designed to be reproducible without a model key.

## Security

Never commit `.env`, API keys, cookies, session data, or private LinkedIn data.
