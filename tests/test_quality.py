from src.models import CommentMode
from src.quality import check_comment_quality


def test_good_comment_has_no_obvious_warnings():
    comment = (
        "The interesting part is the operating boundary. "
        "More access without a clear recovery path seems risky."
    )

    warnings = check_comment_quality(
        comment=comment,
        mode=CommentMode.ADD_INSIGHT,
        post_text="AI agents need better access controls and recovery paths.",
    )

    assert warnings == []


def test_generic_linkedin_language_is_flagged():
    comment = (
        "Absolutely fascinating. Excited to see how this "
        "game changer evolves."
    )

    warnings = check_comment_quality(
        comment=comment,
        mode=CommentMode.ADD_INSIGHT,
        post_text="AI agents are changing the way teams work.",
    )

    assert len(warnings) > 0


def test_long_comment_is_flagged():
    comment = " ".join(["This is a useful observation."] * 30)

    warnings = check_comment_quality(
        comment=comment,
        mode=CommentMode.ADD_INSIGHT,
        post_text="AI agents are changing software.",
    )

    assert any("too long" in warning.lower() for warning in warnings)


def test_question_mode_requires_question():
    comment = "The operational trade-off here is interesting."

    warnings = check_comment_quality(
        comment=comment,
        mode=CommentMode.THOUGHTFUL_QUESTION,
        post_text="How should AI agents handle permissions?",
    )

    assert any("no question" in warning.lower() for warning in warnings)


def test_empty_comment_is_flagged():
    warnings = check_comment_quality(
        comment="",
        mode=CommentMode.ADD_INSIGHT,
        post_text="AI agents are changing software.",
    )

    assert "Comment is empty." in warnings


def test_vocabulary_stuffing_is_flagged_when_context_unsupported():
    warnings = check_comment_quality(
        comment="young goats in action",
        mode=CommentMode.QUICK_REACTION,
        post_text="We migrated our relational database to a new cloud cluster.",
        founder="Rico",
    )
    assert any("Vocabulary stuffing" in w for w in warnings)


def test_vocabulary_allowed_when_context_is_natural():
    warnings = check_comment_quality(
        comment="young goats \U0001fae1",
        mode=CommentMode.QUICK_REACTION,
        post_text="The student team won the 48-hour hackathon building an MVP.",
        founder="Rico",
    )
    assert not any("Vocabulary stuffing" in w for w in warnings)