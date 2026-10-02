from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent

CONTEXT_FILE = ROOT / "fixtures" / "founder_context.json"
COMMENT_BANK_FILE = ROOT / "fixtures" / "founder_comment_bank.json"
OVERRIDES_FILE = ROOT / "data" / "founder_context_overrides.json"


def _tokens(text: str) -> set[str]:
    words = re.findall(r"[a-zA-Z0-9']+", text.lower())

    stopwords = {
        "the",
        "a",
        "an",
        "and",
        "or",
        "to",
        "of",
        "in",
        "on",
        "for",
        "is",
        "it",
        "this",
        "that",
        "with",
        "as",
        "be",
        "are",
        "was",
        "were",
        "from",
        "by",
        "at",
        "into",
        "we",
        "i",
        "you",
        "your",
        "our",
        "they",
        "their",
    }

    return {
        word
        for word in words
        if word not in stopwords and len(word) > 2
    }


def _load_json(path: Path, default: Any):
    if not path.exists():
        return default

    try:
        return json.loads(
            path.read_text(encoding="utf-8")
        )
    except (json.JSONDecodeError, OSError):
        return default


def _deep_merge(base: dict, override: dict) -> dict:
    result = dict(base)

    for key, value in override.items():
        if (
            isinstance(value, dict)
            and isinstance(result.get(key), dict)
        ):
            result[key] = _deep_merge(
                result[key],
                value,
            )
        else:
            result[key] = value

    return result


def load_contexts() -> dict[str, dict]:
    base = _load_json(
        CONTEXT_FILE,
        {},
    )

    overrides = _load_json(
        OVERRIDES_FILE,
        {},
    )

    merged = {}

    for founder, context in base.items():
        founder_override = overrides.get(
            founder,
            {},
        )

        merged[founder] = _deep_merge(
            context,
            founder_override,
        )

    return merged


def get_founder_context(founder: str) -> dict:
    contexts = load_contexts()

    return contexts.get(
        founder,
        {},
    )


def save_founder_context(
    founder: str,
    updates: dict,
) -> None:

    current = _load_json(
        OVERRIDES_FILE,
        {},
    )

    existing = current.get(
        founder,
        {},
    )

    current[founder] = _deep_merge(
        existing,
        updates,
    )

    OVERRIDES_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OVERRIDES_FILE.write_text(
        json.dumps(
            current,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def load_comment_bank(
    founder: str | None = None,
) -> list[dict]:

    data = _load_json(
        COMMENT_BANK_FILE,
        [],
    )

    if founder is None:
        return data

    return [
        item
        for item in data
        if item.get("founder") == founder
    ]


def retrieve_reference_pairs(
    post_text: str,
    founder: str,
    mode: str | None = None,
    top_k: int = 4,
) -> list[dict]:

    post_tokens = _tokens(post_text)

    candidates = load_comment_bank(
        founder=founder,
    )

    scored = []

    context = get_founder_context(
        founder,
    )

    interest_topics = context.get(
        "interest_topics",
        [],
    )

    for item in candidates:

        candidate_tokens = _tokens(
            item.get("post", "")
        )

        overlap = len(
            post_tokens.intersection(
                candidate_tokens
            )
        )

        score = float(overlap)

        if mode and item.get("mode") == mode:
            score += 3.0

        topic = item.get(
            "topic",
            "",
        ).lower()

        for interest in interest_topics:
            if interest.lower() in topic:
                score += 0.5

        scored.append(
            (
                score,
                item,
            )
        )

    scored.sort(
        key=lambda pair: pair[0],
        reverse=True,
    )

    return [
        item
        for score, item in scored[:top_k]
        if score > 0
    ]


def format_context_for_prompt(
    founder: str,
) -> str:

    context = get_founder_context(
        founder,
    )

    if not context:
        return "No founder context is available."

    observed_vocab = ", ".join(
        context.get(
            "observed_vocabulary",
            [],
        )
    )

    candidate_vocab = ", ".join(
        context.get(
            "candidate_vocabulary",
            [],
        )
    )

    preferred_moves = ", ".join(
        context.get(
            "preferred_moves",
            [],
        )
    )

    avoid_patterns = ", ".join(
        context.get(
            "avoid_patterns",
            [],
        )
    )

    return f"""
FOUNDER: {founder}

INTERESTS:
{", ".join(context.get("interest_topics", []))}

TONE:
{", ".join(context.get("tone", []))}

PREFERRED LENGTH:
{context.get("preferred_length", "unknown")}

HUMOR LEVEL:
{context.get("humor_level", "unknown")}

TECHNICAL DEPTH:
{context.get("technical_depth", "unknown")}

OBSERVED VOCABULARY:
{observed_vocab}

CANDIDATE VOCABULARY:
{candidate_vocab}

PREFERRED COMMENT MOVES:
{preferred_moves}

AVOID PATTERNS:
{avoid_patterns}
""".strip()