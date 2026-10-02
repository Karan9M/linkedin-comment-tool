from src.comment_mode import select_comment_mode
from src.context import build_founder_evidence_pack
from src.models import CommentMode, Post
from src.paths import VOICE_FILE
from src.voice import load_voice_examples


def test_rico_personal_shipping_post_uses_humorous_personal_mode():
    post = Post(
        id="rico-test",
        text=(
            "Went from building random projects during college to shipping "
            "something people actually pay for. Still feels unreal."
        ),
    )
    examples = load_voice_examples(VOICE_FILE)

    mode = select_comment_mode(post, "Rico", examples)

    assert mode == CommentMode.HUMOROUS_PERSONAL


def test_unrelated_rico_comments_are_style_only_for_personal_post():
    post = Post(
        id="rico-test",
        text=(
            "Went from building random projects during college to shipping "
            "something people actually pay for. Still feels unreal."
        ),
    )
    examples = load_voice_examples(VOICE_FILE)

    pack = build_founder_evidence_pack(
        founder="Rico",
        post_text=post.text,
        mode=CommentMode.HUMOROUS_PERSONAL,
        voice_examples=examples,
    )

    assert pack["matched_observed_examples"] == []
    assert pack["style_only_observed_comments"]


def test_verified_calibration_is_not_present_when_no_saved_responses_exist():
    post = Post(id="x", text="A simple startup update.")
    examples = load_voice_examples(VOICE_FILE)

    pack = build_founder_evidence_pack(
        founder="Rico",
        post_text=post.text,
        mode=CommentMode.QUICK_REACTION,
        voice_examples=examples,
    )

    assert pack["verified_calibration"] == []

