import json
import re
from pathlib import Path
from typing import Optional

from src.models import CommentMode, VoiceExample
from src.paths import BASE_DIR, FIXTURE_DIR, FEEDBACK_FILE, VOICE_PROFILE_FILE

CONTEXT_FILE = BASE_DIR / "data" / "founder_context.json"
CALIBRATION_FILE = BASE_DIR / "data" / "calibration_responses.json"
CALIBRATION_POSTS_FILE = FIXTURE_DIR / "context_posts.json"

# Evidence hierarchy. These weights are used for retrieval, not as a model score.
# Higher-authority evidence should constrain style more strongly than synthetic examples.
EVIDENCE_AUTHORITY = {
    "observed_comment": 1.00,
    "observed_post": 0.85,
    "human_edited_feedback": 0.80,
    "human_approved_feedback": 0.80,
    "founder_verified_calibration": 0.75,
    "founder_context": 0.70,
    "candidate_curated_calibration": 0.35,
}


def _load_json(path: Path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def load_founder_context(founder: str, path: Path = CONTEXT_FILE) -> dict:
    base_data = _load_json(VOICE_PROFILE_FILE, {})
    base = base_data.get(founder, {})
    overrides = _load_json(path, {}).get(founder, {})

    merged = dict(base)
    merged.update(overrides)
    merged["vocabulary"] = list(dict.fromkeys(
        (base.get("vocabulary") or []) + (overrides.get("vocabulary") or [])
    ))
    merged["avoid"] = list(dict.fromkeys(
        (base.get("avoid") or []) + (overrides.get("avoid") or [])
    ))
    return merged


def save_founder_context(
    founder: str,
    vocabulary: list[str],
    context_notes: str,
    avoid: list[str],
    path: Path = CONTEXT_FILE,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = _load_json(path, {})
    data[founder] = {
        "vocabulary": [x.strip() for x in vocabulary if x.strip()],
        "context_notes": context_notes.strip(),
        "avoid": [x.strip() for x in avoid if x.strip()],
    }
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def load_calibration_posts(path: Path = CALIBRATION_POSTS_FILE) -> list[dict]:
    data = _load_json(path, [])
    return data if isinstance(data, list) else []


def load_calibration_responses(path: Path = CALIBRATION_FILE) -> list[dict]:
    data = _load_json(path, [])
    return data if isinstance(data, list) else []


def save_calibration_response(
    founder: str,
    post_id: str,
    post_text: str,
    response: str,
    mode: Optional[CommentMode],
    verification: str = "candidate_curated",
    path: Path = CALIBRATION_FILE,
) -> None:
    if not response.strip():
        return

    path.parent.mkdir(parents=True, exist_ok=True)
    existing = load_calibration_responses(path)

    record = {
        "id": f"{founder.lower()}::{post_id}",
        "founder": founder,
        "post_id": post_id,
        "post_text": post_text,
        "response": response.strip(),
        "comment_mode": mode.value if mode else None,
        "verification": verification,
    }

    for index, item in enumerate(existing):
        if item.get("id") == record["id"]:
            existing[index] = record
            break
    else:
        existing.append(record)

    path.write_text(json.dumps(existing, indent=2, ensure_ascii=False), encoding="utf-8")


def delete_calibration_response(
    response_id: str,
    path: Path = CALIBRATION_FILE,
) -> bool:
    existing = load_calibration_responses(path)
    filtered = [item for item in existing if item.get("id") != response_id]
    changed = len(filtered) != len(existing)
    if changed:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(filtered, indent=2, ensure_ascii=False), encoding="utf-8")
    return changed


def _tokens(text: str) -> set[str]:
    words = re.findall(r"[a-zA-Z0-9']+", text.lower())
    stop = {
        "the", "a", "an", "and", "or", "to", "of", "in", "on", "for", "is",
        "it", "this", "that", "with", "as", "be", "are", "was", "were", "from",
        "by", "at", "into", "we", "i", "you", "your", "our", "they", "their",
        "my", "but", "what", "how", "why", "do", "does", "did", "can", "could",
    }
    return {w for w in words if len(w) > 2 and w not in stop}


def _similarity(target: str, source: str) -> float:
    a = _tokens(target)
    b = _tokens(source)
    if not a or not b:
        return 0.0

    overlap = len(a & b)
    recall = overlap / len(a)
    precision = overlap / len(b)
    if recall + precision == 0:
        return 0.0
    # Lexical F1 is safer than target-only overlap: one generic word shared
    # with a long historical post should not make that example look relevant.
    return 2 * recall * precision / (recall + precision)


def _feedback_records(founder: str) -> list[dict]:
    data = _load_json(FEEDBACK_FILE, [])
    if not isinstance(data, list):
        return []
    return [
        item for item in data
        if item.get("founder", "").lower() == founder.lower()
    ]


def get_relevant_calibration_responses(
    founder: str,
    post_text: str,
    mode: Optional[CommentMode] = None,
    limit: int = 4,
    path: Path = CALIBRATION_FILE,
) -> list[dict]:
    candidates = [
        item for item in load_calibration_responses(path)
        if item.get("founder", "").lower() == founder.lower()
        and item.get("response")
    ]

    scored: list[tuple[float, dict]] = []
    for item in candidates:
        score = _similarity(post_text, item.get("post_text", ""))
        if mode and item.get("comment_mode") == mode.value:
            score += 0.15
        verification = item.get("verification")
        score += 0.20 if verification == "founder_verified" else 0.0
        scored.append((score, item))

    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [item for score, item in scored[:limit]]


def _score_observed_example(
    post_text: str,
    example: VoiceExample,
    mode: Optional[CommentMode],
) -> float:
    source_text = example.target_post_excerpt or (
        example.text if example.source_type == "post" else ""
    )
    relevance = _similarity(post_text, source_text)

    score = relevance
    if example.source_type == "comment":
        score += 0.25
    elif example.source_type == "post":
        score += 0.05

    if mode and example.comment_mode == mode:
        score += 0.15

    # A real target-post match is materially stronger than a generic comment.
    if example.source_type == "comment" and relevance == 0:
        score -= 0.12

    return score


def get_relevant_observed_examples(
    founder: str,
    post_text: str,
    examples: list[VoiceExample],
    mode: Optional[CommentMode] = None,
    limit: int = 6,
) -> tuple[list[VoiceExample], list[VoiceExample]]:
    """Split observed evidence into target-matched and style-only examples.

    This prevents an unrelated comment such as "adding this to my to do list"
    from being treated as a content template merely because it is in the dataset.
    """
    candidates = [
        item for item in examples
        if item.person.lower() == founder.lower()
        and item.person.lower() != "byro/company"
    ]

    scored = [
        (_score_observed_example(post_text, item, mode), item)
        for item in candidates
    ]
    scored.sort(key=lambda pair: pair[0], reverse=True)

    matched: list[VoiceExample] = []
    style_only: list[VoiceExample] = []

    for score, item in scored:
        relevance_source = item.target_post_excerpt or (
            item.text if item.source_type == "post" else ""
        )
        relevance = _similarity(post_text, relevance_source)
        # One or two shared generic words are not enough to call a historical
        # comment a semantic match. The similarity score is lexical F1, so both
        # the current post and the historical target must overlap meaningfully.
        if relevance >= 0.12 and len(matched) < limit:
            matched.append(item)
        elif item.source_type == "comment" and len(style_only) < 3:
            style_only.append(item)

    # Preserve a small fallback pool when the post has little lexical overlap.
    if not matched:
        for score, item in scored:
            if item.source_type == "comment" and item not in style_only:
                style_only.append(item)
            if len(style_only) >= 3:
                break

    return matched[:limit], style_only[:3]


def build_founder_evidence_pack(
    founder: str,
    post_text: str,
    mode: Optional[CommentMode],
    voice_examples: list[VoiceExample],
) -> dict:
    """Synchronize all founder knowledge into one structured evidence object.

    The pack is deliberately separated by evidence type and authority. The model
    can use all of it, but cannot treat synthetic calibration as equivalent to an
    observed founder comment.
    """
    profile = load_founder_context(founder)
    matched, style_only = get_relevant_observed_examples(
        founder, post_text, voice_examples, mode
    )

    reviews = _feedback_records(founder)
    relevant_feedback = []
    rejected = []
    for item in reviews:
        similarity = _similarity(post_text, item.get("post_text", ""))
        if item.get("decision") in {"approve", "edit"} and similarity > 0:
            relevant_feedback.append((similarity, item))
        if item.get("decision") == "reject" and (item.get("reason") or item.get("rejection_reason")):
            rejected.append(item.get("reason") or item.get("rejection_reason"))

    relevant_feedback.sort(key=lambda pair: pair[0], reverse=True)

    verified_calibration = []
    candidate_calibration = []
    for item in get_relevant_calibration_responses(founder, post_text, mode, limit=6):
        if item.get("verification") == "founder_verified":
            verified_calibration.append(item)
        else:
            candidate_calibration.append(item)

    return {
        "founder": founder,
        "profile": profile,
        "matched_observed_examples": matched,
        "style_only_observed_comments": style_only,
        "relevant_human_feedback": [item for _, item in relevant_feedback[:4]],
        "verified_calibration": verified_calibration[:4],
        "candidate_calibration": candidate_calibration[:3],
        "rejection_reasons": list(dict.fromkeys(rejected))[:5],
        "hard_rules": [
            "Never invent a personal experience, relationship, fact, metric, or outcome for the founder.",
            "Never copy a comment pattern from an unrelated target post when the content does not support it.",
            "Observed founder comments outrank synthetic calibration examples.",
            "Founder-reviewed feedback outranks candidate-curated calibration.",
            "Vocabulary is a style signal, not a reason to use a word on every post.",
            "Use only the smallest amount of context needed to make the comment feel native.",
        ],
    }
