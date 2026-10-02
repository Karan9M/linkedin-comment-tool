import json
import re
from pathlib import Path

from src.models import CommentMode, Post, VoiceExample


STOPWORDS = {
    "the", "a", "an", "and", "or", "to", "of", "in", "on", "for", "is",
    "it", "this", "that", "with", "as", "be", "are", "was", "were", "from",
    "by", "at", "into", "we", "i", "you", "your", "our", "they", "their",
    "my", "but", "what", "how", "why", "do", "does", "did", "can", "could",
}


def _tokenize(text: str) -> set[str]:
    words = re.findall(r"[a-zA-Z0-9']+", text.lower())
    return {word for word in words if word not in STOPWORDS and len(word) > 2}


def load_voice_examples(path: str | Path) -> list[VoiceExample]:
    path = Path(path)
    with path.open("r", encoding="utf-8") as file:
        raw_examples = json.load(file)

    result: list[VoiceExample] = []
    for item in raw_examples:
        raw_mode = item.get("comment_mode")
        try:
            mode = CommentMode(raw_mode) if raw_mode else None
        except ValueError:
            mode = None
        result.append(
            VoiceExample(
                id=item["id"],
                person=item["person"],
                source_type=item["source_type"],
                text=item["text"],
                topic=item.get("topic", ""),
                source_url=item.get("source_url"),
                comment_mode=mode,
                target_post_excerpt=item.get("target_post_excerpt", ""),
                evidence_role=item.get("evidence_role", ""),
            )
        )
    return result


def _score_example(post_tokens: set[str], post: Post, example: VoiceExample, desired_mode: CommentMode | None) -> float:
    # For a historical comment, similarity of the *target post* is a better signal
    # than similarity to the comment text itself.
    context_text = example.target_post_excerpt or (example.text if example.source_type == "post" else "")
    context_tokens = _tokenize(context_text)
    if not context_tokens:
        context_score = 0.0
    else:
        overlap = post_tokens.intersection(context_tokens)
        context_score = len(overlap) / len(post_tokens or {""})

    score = context_score
    if example.source_type == "comment":
        score += 0.25
    elif example.source_type == "post":
        score += 0.05

    if desired_mode and example.comment_mode == desired_mode:
        score += 0.25

    return score


def retrieve_voice_examples(
    post: Post,
    person: str,
    examples: list[VoiceExample],
    top_k: int = 5,
    desired_mode: CommentMode | None = None,
) -> list[VoiceExample]:
    candidates = [
        example for example in examples
        if example.person.lower() == person.lower()
        and example.person.lower() != "byro/company"
    ]

    post_tokens = _tokenize(post.text)
    scored: list[tuple[float, VoiceExample]] = []
    for example in candidates:
        scored.append((_score_example(post_tokens, post, example, desired_mode), example))

    scored.sort(key=lambda item: item[0], reverse=True)
    return [example for _, example in scored[:top_k]]
