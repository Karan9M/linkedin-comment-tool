from collections import Counter

from src.models import CommentMode, Post, VoiceExample


def _observed_mode_preference(person: str, examples: list[VoiceExample]) -> Counter:
    counter: Counter = Counter()
    for example in examples:
        if example.person.lower() == person.lower() and example.source_type == "comment":
            if example.comment_mode is not None:
                counter[example.comment_mode] += 1
    return counter


def select_comment_mode(
    post: Post,
    person: str = "",
    voice_examples: list[VoiceExample] | None = None,
) -> CommentMode:
    """Select a response shape from the target post + observed founder habits.

    This is intentionally separate from vocabulary. Vocabulary influences wording;
    the mode decides what kind of contribution the post calls for.
    """
    text = post.text.lower().strip()
    examples = voice_examples or []
    preference = _observed_mode_preference(person, examples)
    founder = person.lower()

    humour_signals = ("lol", "haha", "😂", "😆", "😅", "joke", "funny", "wild", "chaos")
    personal_signals = (
        "college", "university", "uni", "school", "student", "first job",
        "my journey", "started", "started out", "learned", "learning",
        "shipped", "shipping", "launched", "built", "built this", "paying customers",
        "people pay", "feels unreal", "still feels", "proud", "personal news",
    )

    if "?" in text and founder != "rico":
        return CommentMode.THOUGHTFUL_QUESTION

    if founder == "rico" and any(signal in text for signal in personal_signals):
        if preference[CommentMode.HUMOROUS_PERSONAL] >= preference[CommentMode.QUICK_REACTION]:
            return CommentMode.HUMOROUS_PERSONAL

    if any(signal in text for signal in humour_signals):
        return CommentMode.HUMOROUS_PERSONAL

    technical_signals = (
        "ai", "agent", "agents", "llm", "software", "engineering",
        "product", "system", "architecture", "eval", "evaluation", "automation",
        "security", "reliability", "permissions", "memory",
    )

    if any(signal in text for signal in technical_signals):
        if founder == "fathin":
            return CommentMode.ADD_INSIGHT
        if founder == "rico" and preference[CommentMode.QUICK_REACTION] >= preference[CommentMode.ADD_INSIGHT]:
            return CommentMode.QUICK_REACTION
        return CommentMode.ADD_INSIGHT

    if founder == "rico":
        return (
            CommentMode.HUMOROUS_PERSONAL
            if preference[CommentMode.HUMOROUS_PERSONAL] >= preference[CommentMode.QUICK_REACTION]
            else CommentMode.QUICK_REACTION
        )

    return CommentMode.QUICK_REACTION
