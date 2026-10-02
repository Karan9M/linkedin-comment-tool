from src.engagement import decide_engagement
from src.models import EngagementDecision, Post


def test_relevant_ai_post_should_engage():
    post = Post(
        id="1",
        text="AI agents are changing how B2B teams build software."
    )

    result = decide_engagement(post)

    assert result.decision == EngagementDecision.ENGAGE
    assert result.confidence > 0.5


def test_unrelated_post_should_skip():
    post = Post(
        id="2",
        text="My favourite recipe for homemade pasta."
    )

    result = decide_engagement(post)

    assert result.decision == EngagementDecision.SKIP


def test_empty_post_should_skip():
    post = Post(
        id="3",
        text=""
    )

    result = decide_engagement(post)

    assert result.decision == EngagementDecision.SKIP
    assert result.confidence == 1.0


def test_configured_skip_topic_should_skip():
    post = Post(
        id="4",
        text="Huge crypto pump coming tonight!"
    )

    result = decide_engagement(post)

    assert result.decision == EngagementDecision.SKIP

def test_word_boundary_prevents_ai_false_positive():
    post = Post(id="5", text="I said we should wait for the email.")
    result = decide_engagement(post)
    assert result.decision == EngagementDecision.SKIP


def test_uncertain_relevant_post_can_ask():
    post = Post(id="6", text="We are building an AI agent. Not sure when it should require approval.")
    result = decide_engagement(post)
    assert result.decision == EngagementDecision.ASK


def test_sensitive_post_is_skipped():
    post = Post(id="7", text="I was hospitalized last week and want to discuss AI.")
    result = decide_engagement(post)
    assert result.decision == EngagementDecision.SKIP

def test_hackathon_shipping_post_should_engage():
    post = Post(
        id="8",
        text=(
            "36 hours. 4 people. Way too much coffee. "
            "Somehow we shipped the whole MVP before the deadline 😂"
        ),
    )

    result = decide_engagement(post)

    assert result.decision == EngagementDecision.ENGAGE