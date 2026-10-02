from src.comment_mode import select_comment_mode
from src.models import CommentMode, Post


def test_question_post():
    post = Post(
        id="1",
        text="How do you think AI agents will change product teams?"
    )

    assert select_comment_mode(post) == CommentMode.THOUGHTFUL_QUESTION


def test_humorous_post():
    post = Post(
        id="2",
        text="We shipped it. Somehow nothing caught fire 😂"
    )

    assert select_comment_mode(post) == CommentMode.HUMOROUS_PERSONAL


def test_technical_post():
    post = Post(
        id="3",
        text="We redesigned our agent architecture to improve reliability."
    )

    assert select_comment_mode(post) == CommentMode.ADD_INSIGHT


def test_generic_post():
    post = Post(
        id="4",
        text="Had a great time at the event today."
    )

    assert select_comment_mode(post) == CommentMode.QUICK_REACTION