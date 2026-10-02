import re
from collections import Counter

from src.models import CommentMode


GENERIC_PHRASES = (
    "absolutely fascinating", "great insights", "game changer", "game-changer",
    "excited to see", "this is so interesting", "great post", "well said",
    "couldn't agree more", "love this", "what an amazing", "so valuable",
)



def check_comment_quality(comment: str, mode: CommentMode, post_text: str, recent_comments: list[str] | None = None) -> list[str]:
    warnings: list[str] = []
    text = comment.strip()
    lower = text.lower()
    if not text:
        return ["Comment is empty."]

    word_count = len(re.findall(r"\b[\w'-]+\b", text))
    if word_count > 80:
        warnings.append("Comment is too long.")

    matched_generic = [phrase for phrase in GENERIC_PHRASES if phrase in lower]
    if matched_generic:
        warnings.append("Contains generic LinkedIn language: " + ", ".join(matched_generic))

    if "—" in text and not ("—" in post_text):
        warnings.append("Uses an em dash not observed in the source post; review for polished/AI-ish phrasing.")

    post_words = set(re.findall(r"\b[a-zA-Z]{4,}\b", post_text.lower()))
    comment_words = set(re.findall(r"\b[a-zA-Z]{4,}\b", lower))
    if post_words:
        overlap = len(post_words.intersection(comment_words))
        overlap_ratio = overlap / len(comment_words or {""})
        if overlap_ratio > 0.70 and len(comment_words) >= 8:
            warnings.append("Comment may be repeating too much of the original post.")

    if mode == CommentMode.THOUGHTFUL_QUESTION and "?" not in text:
        warnings.append("Selected mode is thoughtful_question but the comment contains no question.")

    if recent_comments:
        normalized = " ".join(lower.split())
        for previous in recent_comments:
            if normalized and normalized == " ".join(previous.lower().split()):
                warnings.append("Comment repeats a recent approved comment.")
                break

    return list(dict.fromkeys(warnings))
