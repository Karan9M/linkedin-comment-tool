from src.claims import validate_claims


def test_unsupported_number_is_blocked():
    warnings = validate_claims(
        "We cut latency by 40%.",
        "We improved latency.",
        "Fathin",
        {"Fathin": {"approved_claims": []}},
    )
    assert any("40" in warning for warning in warnings)


def test_supported_number_in_post_is_allowed():
    warnings = validate_claims(
        "The 40% improvement is interesting.",
        "We improved latency by 40%.",
        "Fathin",
        {"Fathin": {"approved_claims": []}},
    )
    assert warnings == []


def test_first_person_experience_is_blocked():
    warnings = validate_claims(
        "In my experience, agents fail at handoffs.",
        "Agents fail at handoffs.",
        "Fathin",
        {"Fathin": {"approved_claims": []}},
    )
    assert any("first-person" in warning for warning in warnings)


def test_post_url_can_be_repeated():
    warnings = validate_claims(
        "Useful breakdown: https://example.com/article",
        "Useful breakdown: https://example.com/article",
        "Fathin",
        {"Fathin": {"approved_claims": []}},
    )
    assert warnings == []


def test_unsupported_multiplier_is_blocked():
    warnings = validate_claims(
        "This led to a 10x increase in throughput.",
        "Throughput improved after the update.",
        "Rico",
        {"Rico": {"approved_claims": []}},
    )
    assert any("10x" in warning for warning in warnings)


def test_unsupported_customer_claim_is_blocked():
    warnings = validate_claims(
        "Our customers saw great results with this approach.",
        "A discussion about software tooling.",
        "Rico",
        {"Rico": {"approved_claims": []}},
    )
    assert any("customer" in warning.lower() for warning in warnings)


def test_unsupported_external_attribution_is_blocked():
    warnings = validate_claims(
        "As Sam Altman pointed out, models are changing rapidly.",
        "Models are changing rapidly in production.",
        "Fathin",
        {"Fathin": {"approved_claims": []}},
    )
    assert any("Sam Altman" in warning for warning in warnings)

