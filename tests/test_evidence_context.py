from unittest.mock import patch

from src.context import build_founder_evidence_pack, save_founder_context
from src.generator import build_generation_prompt
from src.models import CommentMode, Post
from src.paths import VOICE_FILE
from src.voice import load_voice_examples


def test_saved_founder_preference_reaches_the_generation_prompt(tmp_path):
    overrides_path = tmp_path / "founder_context_overrides.json"
    post = Post(id="rico-context", text="We won a startup hackathon after shipping an MVP.")
    voice = load_voice_examples(VOICE_FILE)

    with patch("src.context.OVERRIDES_FILE", overrides_path):
        save_founder_context(
            "Rico",
            {"candidate_vocabulary": ["earned it"]},
        )
        evidence_pack = build_founder_evidence_pack(
            founder="Rico",
            post_text=post.text,
            mode=CommentMode.QUICK_REACTION,
            voice_examples=voice,
        )

    prompt = build_generation_prompt(
        post=post,
        mode=CommentMode.QUICK_REACTION,
        voice_examples=voice,
        founder="Rico",
        evidence_pack=evidence_pack,
    )

    assert "earned it" in prompt
    assert "Candidate vocabulary may be used only" in prompt


def test_synthetic_calibration_is_available_but_remains_separate_from_voice():
    voice = load_voice_examples(VOICE_FILE)
    pack = build_founder_evidence_pack(
        founder="Rico",
        post_text="We launched an AI product after a hackathon.",
        mode=CommentMode.QUICK_REACTION,
        voice_examples=voice,
    )

    assert pack["candidate_calibration"]
    assert all(item["verification"] == "synthetic_calibration" for item in pack["candidate_calibration"])
    assert all(item.person == "Rico" for item in pack["style_only_observed_comments"])


def test_founder_context_is_not_shared_between_founders(tmp_path):
    overrides_path = tmp_path / "founder_context_overrides.json"
    with patch("src.context.OVERRIDES_FILE", overrides_path):
        save_founder_context("Rico", {"candidate_vocabulary": ["rico-only"]})
        rico_pack = build_founder_evidence_pack(
            "Rico", "A product shipped today.", CommentMode.QUICK_REACTION, []
        )
        fathin_pack = build_founder_evidence_pack(
            "Fathin", "An agent evaluation changed today.", CommentMode.ADD_INSIGHT, []
        )

    assert "rico-only" in rico_pack["profile"]["candidate_vocabulary"]
    assert "rico-only" not in fathin_pack["profile"]["candidate_vocabulary"]
