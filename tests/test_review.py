import json

from src.models import Review, ReviewDecision
from src.review import load_reviews, save_review


def test_save_approved_review(tmp_path):
    feedback_file = tmp_path / "feedback.json"

    review = Review(
        candidate_text="The operational boundary is the interesting part.",
        decision=ReviewDecision.APPROVE,
    )

    save_review(
        review,
        feedback_file=feedback_file,
    )

    data = json.loads(
        feedback_file.read_text(encoding="utf-8")
    )

    assert len(data) == 1
    assert data[0]["decision"] == "approve"
    assert data[0]["candidate_text"] == review.candidate_text
    assert data[0]["final_text"] == review.candidate_text
    assert data[0]["founder"] == ""


def test_save_edited_review(tmp_path):
    feedback_file = tmp_path / "feedback.json"

    review = Review(
        candidate_text="Interesting point.",
        decision=ReviewDecision.EDIT,
        edited_text="The operational trade-off is the interesting part.",
    )

    save_review(
        review,
        feedback_file=feedback_file,
    )

    reviews = load_reviews(feedback_file)

    assert len(reviews) == 1
    assert reviews[0]["decision"] == "edit"
    assert (
        reviews[0]["edited_text"]
        == "The operational trade-off is the interesting part."
    )


def test_save_rejected_review(tmp_path):
    feedback_file = tmp_path / "feedback.json"

    review = Review(
        candidate_text="Great post!",
        decision=ReviewDecision.REJECT,
        rejection_reason="Too generic",
    )

    save_review(
        review,
        feedback_file=feedback_file,
    )

    reviews = load_reviews(feedback_file)

    assert len(reviews) == 1
    assert reviews[0]["decision"] == "reject"
    assert reviews[0]["rejection_reason"] == "Too generic"


def test_missing_feedback_returns_empty_list(tmp_path):
    feedback_file = tmp_path / "does_not_exist.json"

    reviews = load_reviews(feedback_file)

    assert reviews == []

def test_positive_feedback_returns_approved_and_edited(tmp_path):
    feedback_file = tmp_path / "feedback.json"

    save_review(
        Review(
            candidate_text="Interesting point.",
            decision=ReviewDecision.APPROVE,
        ),
        feedback_file,
    )

    save_review(
        Review(
            candidate_text="Great insight.",
            decision=ReviewDecision.EDIT,
            edited_text="The operational detail is the interesting part.",
        ),
        feedback_file,
    )

    save_review(
        Review(
            candidate_text="Great post!",
            decision=ReviewDecision.REJECT,
            rejection_reason="Too generic",
        ),
        feedback_file,
    )

    from src.review import get_positive_feedback

    examples = get_positive_feedback(feedback_file)

    assert examples == [
        "Interesting point.",
        "The operational detail is the interesting part.",
    ]

def test_feedback_is_deduplicated(tmp_path):
    feedback_file = tmp_path / "feedback.json"
    review = Review(
        candidate_text="W thing!",
        decision=ReviewDecision.EDIT,
        edited_text="W thing!",
        founder="Rico",
        post_text="We launched an AI product.",
        comment_mode=None,
    )
    save_review(review, feedback_file)
    save_review(review, feedback_file)
    assert len(load_reviews(feedback_file)) == 1


def test_positive_feedback_is_founder_filtered(tmp_path):
    feedback_file = tmp_path / "feedback.json"
    save_review(
        Review(candidate_text="W thing!", decision=ReviewDecision.APPROVE, founder="Rico", post_text="AI launch"),
        feedback_file,
    )
    save_review(
        Review(candidate_text="The evidence is the interesting part.", decision=ReviewDecision.APPROVE, founder="Fathin", post_text="AI evaluation"),
        feedback_file,
    )
    from src.review import get_relevant_feedback
    rico = get_relevant_feedback("Rico", None, "AI launch", feedback_file)
    assert [x["final_text"] for x in rico] == ["W thing!"]
