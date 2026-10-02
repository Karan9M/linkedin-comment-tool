import hashlib
import json
from difflib import SequenceMatcher
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from src.models import CommentMode, Review, ReviewDecision
from src.paths import FEEDBACK_FILE


def _stable_id(founder: str, post_text: str, candidate_text: str, decision: str) -> str:
    raw = "|".join([founder.strip(), post_text.strip(), candidate_text.strip(), decision])
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def _edit_magnitude(candidate_text: str, final_text: str, decision: ReviewDecision) -> str | None:
    """Classify a human edit without pretending it is a quality score."""

    if decision != ReviewDecision.EDIT:
        return None
    similarity = SequenceMatcher(
        None,
        " ".join(candidate_text.lower().split()),
        " ".join(final_text.lower().split()),
    ).ratio()
    return "light" if similarity >= 0.70 else "substantial"


def save_review(
    review: Review,
    feedback_file: Path = FEEDBACK_FILE,
) -> None:
    feedback_file.parent.mkdir(parents=True, exist_ok=True)
    existing = load_reviews(feedback_file)

    decision = review.decision.value
    record_id = _stable_id(review.founder, review.post_text, review.candidate_text, decision)

    if any(item.get("id") == record_id for item in existing):
        return

    final_text = review.edited_text if review.decision == ReviewDecision.EDIT else review.candidate_text

    record = {
        "id": record_id,
        "founder": review.founder,
        "post_text": review.post_text,
        "comment_mode": review.comment_mode.value if review.comment_mode else None,
        "ai_draft": review.candidate_text,
        "final_text": final_text,
        "decision": decision,
        "reason": review.rejection_reason,
        "edit_magnitude": _edit_magnitude(
            review.candidate_text,
            final_text or "",
            review.decision,
        ),
        "quality_warnings": review.quality_warnings,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        # Backward-compatible fields for the first prototype's tests/data.
        "candidate_text": review.candidate_text,
        "edited_text": review.edited_text,
        "rejection_reason": review.rejection_reason,
    }
    existing.append(record)
    feedback_file.write_text(json.dumps(existing, indent=2, ensure_ascii=False), encoding="utf-8")


def load_reviews(feedback_file: Path = FEEDBACK_FILE) -> list[dict]:
    if not feedback_file.exists():
        return []
    try:
        data = json.loads(feedback_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    return data if isinstance(data, list) else []


def list_reviews(feedback_file: Path = FEEDBACK_FILE, founder: Optional[str] = None) -> list[dict]:
    reviews = load_reviews(feedback_file)
    if founder:
        return [r for r in reviews if r.get("founder", "").lower() == founder.lower()]
    return reviews


def delete_review(review_id: str, feedback_file: Path = FEEDBACK_FILE) -> bool:
    reviews = load_reviews(feedback_file)
    filtered = [r for r in reviews if r.get("id") != review_id]
    changed = len(filtered) != len(reviews)
    if changed:
        feedback_file.parent.mkdir(parents=True, exist_ok=True)
        feedback_file.write_text(json.dumps(filtered, indent=2, ensure_ascii=False), encoding="utf-8")
    return changed


def _context_score(post_text: str, feedback_post: str) -> float:
    def tokens(text: str) -> set[str]:
        return {t for t in text.lower().split() if len(t) > 3}
    a, b = tokens(post_text), tokens(feedback_post)
    if not a or not b:
        return 0.0
    return len(a & b) / len(a)


def get_relevant_feedback(
    founder: str,
    mode: CommentMode | None,
    post_text: str,
    feedback_file: Path = FEEDBACK_FILE,
    limit: int = 5,
) -> list[dict]:
    reviews = list_reviews(feedback_file, founder)
    positive = [
        r for r in reviews
        if r.get("decision") in {ReviewDecision.APPROVE.value, ReviewDecision.EDIT.value}
    ]
    scored: list[tuple[float, dict]] = []
    for item in positive:
        score = _context_score(post_text, item.get("post_text", ""))
        if mode and item.get("comment_mode") == mode.value:
            score += 0.25
        scored.append((score, item))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [item for score, item in scored[:limit]]


def get_rejection_patterns(
    founder: str,
    mode: CommentMode | None,
    feedback_file: Path = FEEDBACK_FILE,
    limit: int = 5,
) -> list[str]:
    reviews = list_reviews(feedback_file, founder)
    reasons = []
    for item in reversed(reviews):
        if item.get("decision") != ReviewDecision.REJECT.value:
            continue
        if mode and item.get("comment_mode") not in {None, mode.value}:
            continue
        reason = (item.get("reason") or "").strip()
        if reason and reason not in reasons:
            reasons.append(reason)
        if len(reasons) >= limit:
            break
    return reasons


def get_positive_feedback(feedback_file: Path = FEEDBACK_FILE, founder: str = "", mode: Optional[CommentMode] = None, post_text: str = "") -> list[str]:
    """Backward-compatible helper returning only relevant final texts."""
    if founder and post_text:
        return [r.get("final_text", "") for r in get_relevant_feedback(founder, mode, post_text, feedback_file) if r.get("final_text")]
    return [
        r.get("final_text", "")
        for r in load_reviews(feedback_file)
        if r.get("decision") in {ReviewDecision.APPROVE.value, ReviewDecision.EDIT.value}
        and r.get("final_text")
    ]
