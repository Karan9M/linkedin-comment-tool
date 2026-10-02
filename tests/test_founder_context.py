from src.founder_context import (
    get_founder_context,
    load_comment_bank,
    retrieve_reference_pairs,
)


def test_rico_context_exists():
    context = get_founder_context("Rico")

    assert context
    assert len(
        context["observed_vocabulary"]
    ) > 0


def test_fathin_context_exists():
    context = get_founder_context("Fathin")

    assert context
    assert "operating boundary" in (
        context["observed_vocabulary"]
    )


def test_rico_has_ten_synthetic_posts():
    posts = load_comment_bank("Rico")

    assert len(posts) == 10
    assert all(
        item["synthetic"] is True
        for item in posts
    )


def test_fathin_has_ten_synthetic_posts():
    posts = load_comment_bank("Fathin")

    assert len(posts) == 10
    assert all(
        item["synthetic"] is True
        for item in posts
    )


def test_reference_retrieval_is_founder_specific():

    results = retrieve_reference_pairs(
        post_text=(
            "We launched an AI agent into production "
            "and discovered that recovery is the hard part."
        ),
        founder="Rico",
        mode="quick_reaction",
        top_k=4,
    )

    assert results
    assert all(
        item["founder"] == "Rico"
        for item in results
    )