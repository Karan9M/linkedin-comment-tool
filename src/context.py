"""Canonical founder evidence and feedback context.

This module is the single path from founder research and reviewed feedback to a
generation prompt. It deliberately keeps observed evidence, founder-provided
preferences, reviewed feedback, and synthetic calibration separate.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Optional

from src.models import CommentMode, VoiceExample
from src.paths import DATA_DIR, FIXTURE_DIR, VOICE_PROFILE_FILE
from src.review import list_reviews

BASE_CONTEXT_FILE = FIXTURE_DIR / "founder_context.json"
OVERRIDES_FILE = DATA_DIR / "founder_context_overrides.json"
COMMENT_BANK_FILE = FIXTURE_DIR / "founder_comment_bank.json"
CALIBRATION_FILE = DATA_DIR / "calibration_responses.json"

# These are retrieval priorities, not claims that an item is true.
EVIDENCE_AUTHORITY = {
    "observed_comment": 1.00,
    "observed_post": 0.85,
    "human_edited_feedback": 0.80,
    "human_approved_feedback": 0.80,
    "founder_verified_calibration": 0.75,
    "founder_preference": 0.70,
    "synthetic_calibration": 0.35,
}


def _load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def _deep_merge(base: dict, override: dict) -> dict:
    result = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def _unique(items: list[str]) -> list[str]:
    return list(dict.fromkeys(item.strip() for item in items if item and item.strip()))


def load_founder_context(
    founder: str,
    base_path: Path | None = None,
    overrides_path: Path | None = None,
    profiles_path: Path | None = None,
) -> dict:
    """Load one merged, generation-ready founder context.

    The fixture supplies candidate-researched context. The override file is the
    founder-editable layer used by the UI. The result preserves both observed and
    editable vocabulary so prompts can state their different authority.
    """

    base_data = _load_json(base_path or BASE_CONTEXT_FILE, {})
    override_data = _load_json(overrides_path or OVERRIDES_FILE, {})
    profile_data = _load_json(profiles_path or VOICE_PROFILE_FILE, {})

    base = base_data.get(founder, {}) if isinstance(base_data, dict) else {}
    override = override_data.get(founder, {}) if isinstance(override_data, dict) else {}
    profile = profile_data.get(founder, {}) if isinstance(profile_data, dict) else {}
    merged = _deep_merge(base, override)

    observed_vocabulary = _unique(merged.get("observed_vocabulary", []))
    candidate_vocabulary = _unique(merged.get("candidate_vocabulary", []))
    explicit_vocabulary = _unique(merged.get("vocabulary", []))
    avoid_patterns = _unique(merged.get("avoid_patterns", []) + merged.get("avoid", []))

    generation_profile = dict(profile)
    generation_profile.update({
        "tone": ", ".join(merged.get("tone", [])) or profile.get("tone", ""),
        "typical_length": merged.get("preferred_length", profile.get("typical_length", "")),
        "humor": merged.get("humor_level", profile.get("humor", "")),
        "technical_depth": merged.get("technical_depth", profile.get("technical_depth", "")),
        "preferred_moves": merged.get("preferred_moves", profile.get("preferred_moves", [])),
        "interest_topics": _unique(merged.get("interest_topics", [])),
        "observed_vocabulary": observed_vocabulary,
        "candidate_vocabulary": candidate_vocabulary,
        "vocabulary": _unique(observed_vocabulary + candidate_vocabulary + explicit_vocabulary),
        "avoid": avoid_patterns,
        "avoid_patterns": avoid_patterns,
        "context_notes": merged.get("context_notes", "").strip(),
    })
    return generation_profile


def get_founder_context(founder: str) -> dict:
    return load_founder_context(founder)


def save_founder_context(
    founder: str,
    updates: dict,
    overrides_path: Path | None = None,
) -> None:
    """Persist founder-editable preferences in the same store generation reads."""

    target_path = overrides_path or OVERRIDES_FILE
    current = _load_json(target_path, {})
    if not isinstance(current, dict):
        current = {}
    current[founder] = _deep_merge(current.get(founder, {}), updates)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(
        json.dumps(current, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def load_comment_bank(
    founder: str | None = None,
    path: Path = COMMENT_BANK_FILE,
) -> list[dict]:
    data = _load_json(path, [])
    if not isinstance(data, list):
        return []
    if founder is None:
        return data
    return [item for item in data if item.get("founder", "").lower() == founder.lower()]


def load_calibration_responses(path: Path = CALIBRATION_FILE) -> list[dict]:
    data = _load_json(path, [])
    return data if isinstance(data, list) else []


def _tokens(text: str) -> set[str]:
    stopwords = {
        "the", "a", "an", "and", "or", "to", "of", "in", "on", "for", "is",
        "it", "this", "that", "with", "as", "be", "are", "was", "were", "from",
        "by", "at", "into", "we", "i", "you", "your", "our", "they", "their",
        "my", "but", "what", "how", "why", "do", "does", "did", "can", "could",
    }
    return {
        word for word in re.findall(r"[a-zA-Z0-9']+", text.lower())
        if len(word) > 2 and word not in stopwords
    }


def _similarity(target: str, source: str) -> float:
    target_tokens, source_tokens = _tokens(target), _tokens(source)
    if not target_tokens or not source_tokens:
        return 0.0
    overlap = len(target_tokens & source_tokens)
    precision = overlap / len(source_tokens)
    recall = overlap / len(target_tokens)
    return (2 * precision * recall / (precision + recall)) if precision + recall else 0.0


def _score_observed_example(
    post_text: str,
    example: VoiceExample,
    mode: Optional[CommentMode],
) -> float:
    source = example.target_post_excerpt or (
        example.text if example.source_type == "post" else ""
    )
    score = _similarity(post_text, source)
    score += 0.25 if example.source_type == "comment" else 0.05
    if mode and example.comment_mode == mode:
        score += 0.15
    return score


def get_relevant_observed_examples(
    founder: str,
    post_text: str,
    examples: list[VoiceExample],
    mode: Optional[CommentMode] = None,
    limit: int = 6,
) -> tuple[list[VoiceExample], list[VoiceExample]]:
    """Return target-matched evidence separately from style-only comments."""

    candidates = [
        item for item in examples
        if item.person.lower() == founder.lower() and item.person.lower() != "byro/company"
    ]
    scored = sorted(
        ((_score_observed_example(post_text, item, mode), item) for item in candidates),
        key=lambda pair: pair[0],
        reverse=True,
    )
    matched: list[VoiceExample] = []
    style_only: list[VoiceExample] = []
    for _, item in scored:
        source = item.target_post_excerpt or (item.text if item.source_type == "post" else "")
        if _similarity(post_text, source) >= 0.12 and len(matched) < limit:
            matched.append(item)
        elif item.source_type == "comment" and len(style_only) < 3:
            style_only.append(item)

    if not matched:
        for _, item in scored:
            if item.source_type == "comment" and item not in style_only:
                style_only.append(item)
            if len(style_only) >= 3:
                break
    return matched[:limit], style_only[:3]


def get_relevant_calibration_responses(
    founder: str,
    post_text: str,
    mode: Optional[CommentMode] = None,
    limit: int = 4,
) -> list[dict]:
    """Retrieve canonical calibration records, preserving their authority."""

    records = []
    for item in load_comment_bank(founder):
        records.append({
            "id": item.get("id"),
            "founder": founder,
            "post_text": item.get("post", ""),
            "response": item.get("reference_comment", ""),
            "comment_mode": item.get("mode"),
            "verification": "synthetic_calibration",
            "synthetic": True,
            "style_note": item.get("style_note", ""),
        })
    records.extend(
        item for item in load_calibration_responses()
        if item.get("founder", "").lower() == founder.lower() and item.get("response")
    )

    scored = []
    for item in records:
        score = _similarity(post_text, item.get("post_text", ""))
        if mode and item.get("comment_mode") == mode.value:
            score += 0.15
        if item.get("verification") == "founder_verified":
            score += 0.20
        scored.append((score, item))
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [item for _, item in scored[:limit]]


def retrieve_reference_pairs(
    post_text: str,
    founder: str,
    mode: str | None = None,
    top_k: int = 4,
) -> list[dict]:
    """UI compatibility adapter backed by the canonical calibration store."""

    selected_mode = CommentMode(mode) if mode else None
    return get_relevant_calibration_responses(founder, post_text, selected_mode, top_k)


def build_founder_evidence_pack(
    founder: str,
    post_text: str,
    mode: Optional[CommentMode],
    voice_examples: list[VoiceExample],
) -> dict:
    """Build the one inspectable evidence pack used by prompt and UI."""

    profile = load_founder_context(founder)
    matched, style_only = get_relevant_observed_examples(
        founder, post_text, voice_examples, mode
    )

    positive_feedback: list[tuple[float, dict]] = []
    rejection_reasons: list[str] = []
    if founder:
        for review in list_reviews(founder=founder):
            similarity = _similarity(post_text, review.get("post_text", ""))
            if review.get("decision") in {"approve", "edit"} and similarity > 0:
                positive_feedback.append((similarity, review))
            if review.get("decision") == "reject":
                reason = (review.get("reason") or review.get("rejection_reason") or "").strip()
                if reason:
                    rejection_reasons.append(reason)
    positive_feedback.sort(key=lambda pair: pair[0], reverse=True)

    calibrations = get_relevant_calibration_responses(founder, post_text, mode, limit=6)
    return {
        "founder": founder,
        "profile": profile,
        "matched_observed_examples": matched,
        "style_only_observed_comments": style_only,
        "relevant_human_feedback": [item for _, item in positive_feedback[:4]],
        "verified_calibration": [
            item for item in calibrations if item.get("verification") == "founder_verified"
        ][:4],
        "candidate_calibration": [
            item for item in calibrations if item.get("verification") != "founder_verified"
        ][:3],
        "rejection_reasons": _unique(rejection_reasons)[:5],
        "hard_rules": [
            "Never invent a personal experience, relationship, fact, metric, or outcome for the founder.",
            "Never copy a comment pattern from an unrelated target post when the content does not support it.",
            "Observed founder comments outrank founder preferences and synthetic calibration.",
            "Founder-reviewed feedback outranks candidate-curated calibration.",
            "Vocabulary is a style signal, not a reason to use a word on every post.",
            "Use only the smallest amount of context needed to make the comment feel native.",
        ],
    }
