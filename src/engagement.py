from dataclasses import dataclass
import re

from src.models import EngagementDecision, EngagementResult, Post


@dataclass
class EngagementConfig:
    # Broad topics that can indicate a useful reason to engage.
    # Keep these concrete enough to avoid engaging with totally unrelated posts.
    relevant_topics: tuple[str, ...] = (
        "ai",
        "artificial intelligence",
        "agent",
        "agents",
        "llm",
        "machine learning",
        "startup",
        "startups",
        "founder",
        "founders",
        "product",
        "product building",
        "software",
        "engineering",
        "developer",
        "marketing",
        "b2b",
        "saas",
        "automation",
        "eval",
        "evaluation",

        # Shipping / builder signals
        "build",
        "building",
        "built",
        "ship",
        "shipping",
        "shipped",
        "launch",
        "launched",
        "hackathon",
        "mvp",
        "prototype",
        "side project",
    )

    skip_topics: tuple[str, ...] = (
        "giveaway",
        "crypto pump",
        "casino",
        "sports betting",
    )

    sensitive_topics: tuple[str, ...] = (
        "death",
        "died",
        "funeral",
        "terminal illness",
        "cancer",
        "hospitalized",
        "suicide",
        "layoff",
        "layoffs",
        "redundancy",
        "election",
        "political campaign",
        "president",
        "politics",
    )

    uncertainty_signals: tuple[str, ...] = (
        "not sure",
        "unclear",
        "i'm unsure",
        "i am unsure",
        "curious whether",
        "would love advice",
        "looking for advice",
        "need advice",
    )

    promotional_signals: tuple[str, ...] = (
        "book a call",
        "limited slots",
        "limited spots",
        "buy now",
        "discount",
        "sale ends",
        "dm me",
        "message me to get",
    )


def _contains_term(text: str, term: str) -> bool:
    if " " in term:
        return term in text

    return re.search(
        rf"\b{re.escape(term)}\b",
        text,
    ) is not None


def _matched(text: str, terms: tuple[str, ...]) -> list[str]:
    return [
        term
        for term in terms
        if _contains_term(text, term)
    ]


def decide_engagement(
    post: Post,
    config: EngagementConfig | None = None,
) -> EngagementResult:
    """
    Inspectable engagement gate.

    The gate answers:
    - ENGAGE: enough topical signal to draft
    - ASK: relevant but contribution is uncertain
    - SKIP: no useful signal or clearly unsafe/low-value context
    """

    config = config or EngagementConfig()
    text = post.text.lower().strip()

    if not text:
        return EngagementResult(
            EngagementDecision.SKIP,
            "Post contains no usable text.",
            1.0,
        )

    if post.already_commented:
        return EngagementResult(
            EngagementDecision.SKIP,
            "Founder already commented on this post recently.",
            0.99,
        )

    # Sensitive contexts always stay human-controlled.
    sensitive = _matched(
        text,
        config.sensitive_topics,
    )

    if sensitive:
        return EngagementResult(
            EngagementDecision.SKIP,
            "Sensitive context requires human judgment rather than "
            "automated drafting: "
            + ", ".join(sensitive[:3]),
            0.96,
        )

    # Explicit do-not-engage topics.
    skip_topics = _matched(
        text,
        config.skip_topics,
    )

    if skip_topics:
        return EngagementResult(
            EngagementDecision.SKIP,
            "Post matches a configured do-not-engage topic: "
            + ", ".join(skip_topics),
            0.95,
        )

    relevant = _matched(
        text,
        config.relevant_topics,
    )

    uncertainty = _matched(
        text,
        config.uncertainty_signals,
    )

    promotion = _matched(
        text,
        config.promotional_signals,
    )

    # Nothing in the post gives us a reason to engage.
    if not relevant:
        return EngagementResult(
            EngagementDecision.SKIP,
            "No relevant founder-topic signal was detected.",
            0.80,
        )

    # Strongly promotional + short = probably not worth a comment.
    word_count = len(
        re.findall(
            r"\b[\w'-]+\b",
            text,
        )
    )

    if len(promotion) >= 2 and word_count < 90:
        return EngagementResult(
            EngagementDecision.SKIP,
            "Post appears primarily promotional with little "
            "substantive discussion.",
            0.78,
        )

    # Relevant, but the author is explicitly asking for uncertain input.
    if uncertainty or (
        len(relevant) == 1
        and "?" in text
        and word_count < 35
    ):
        return EngagementResult(
            EngagementDecision.ASK,
            "Potentially relevant, but the system is not confident "
            "enough about whether the founder has a useful contribution.",
            0.58,
        )

    confidence = min(
        0.62 + (0.07 * len(relevant)),
        0.95,
    )

    return EngagementResult(
        EngagementDecision.ENGAGE,
        "Relevant topic signals detected: "
        + ", ".join(relevant[:5]),
        round(confidence, 2),
    )