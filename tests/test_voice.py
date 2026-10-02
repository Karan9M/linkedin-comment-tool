from pathlib import Path

from src.models import Post
from src.voice import load_voice_examples, retrieve_voice_examples


FIXTURE_PATH = Path("fixtures/voice_examples.json")


def test_load_voice_examples():
    examples = load_voice_examples(FIXTURE_PATH)

    assert len(examples) > 0


def test_retrieves_fathin_examples():
    examples = load_voice_examples(FIXTURE_PATH)

    post = Post(
        id="1",
        text="How should we evaluate AI agents and their failure modes?"
    )

    results = retrieve_voice_examples(
        post=post,
        person="Fathin",
        examples=examples,
        top_k=5,
    )

    assert len(results) > 0
    assert all(example.person == "Fathin" for example in results)


def test_does_not_use_byro_brand_as_personal_voice():
    examples = load_voice_examples(FIXTURE_PATH)

    post = Post(
        id="2",
        text="AI product and engineering"
    )

    results = retrieve_voice_examples(
        post=post,
        person="Fathin",
        examples=examples,
        top_k=10,
    )

    assert all(example.person != "Byro/company" for example in results)


def test_results_are_limited():
    examples = load_voice_examples(FIXTURE_PATH)

    post = Post(
        id="3",
        text="AI agents"
    )

    results = retrieve_voice_examples(
        post=post,
        person="Fathin",
        examples=examples,
        top_k=3,
    )

    assert len(results) <= 3