import re
from pathlib import Path
import json

from src.paths import FACTS_FILE

FIRST_PERSON_PATTERNS = (
    r"\bwe\s+(?:built|made|launched|shipped|tested|measured|reduced|increased|saw|scaled|achieved|discovered|decided|hit)\b",
    r"\b(?:in\s+)?my\s+experience\b",
    r"\bi\s+(?:built|made|launched|shipped|tested|measured|used|found|saw|noticed|achieved|realized)\b",
    r"\bat\s+(?:our\s+)?(?:company|startup|team|byro)\b",
    r"\bwe\s+always\b",
    r"\bi\s+personally\b",
)

CUSTOMER_PATTERNS = (
    r"\b(?:our\s+)?(?:clients|customers|users)\s+(?:saw|reported|experienced|told\s+us|achieved)\b",
)


def load_facts(path: str | Path = FACTS_FILE) -> dict:
    path = Path(path)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _number_tokens(text: str) -> set[str]:
    # Match numbers with currency, decimals, percentages, or multipliers ($100, 40%, 10x, 2.5k)
    return set(re.findall(r"(?<![A-Za-z])\$?\d+(?:\.\d+)?(?:%|[xXkKmM])?", text))


def _allowed_text(founder: str, post_text: str, facts: dict) -> str:
    founder_facts = facts.get(founder, {}) if isinstance(facts, dict) else {}
    claims = founder_facts.get("approved_claims", []) if isinstance(founder_facts, dict) else []
    return post_text + " " + " ".join(str(c) for c in claims)


def validate_claims(comment: str, post_text: str, founder: str, facts: dict | None = None) -> list[str]:
    facts = facts or load_facts()
    warnings: list[str] = []
    allowed_text = _allowed_text(founder, post_text, facts)

    generated_numbers = _number_tokens(comment)
    allowed_numbers = _number_tokens(allowed_text)
    unsupported_numbers = sorted(generated_numbers - allowed_numbers)
    if unsupported_numbers:
        warnings.append("Unsupported numeric claim(s): " + ", ".join(unsupported_numbers))

    lower = comment.lower()
    for pattern in FIRST_PERSON_PATTERNS:
        if re.search(pattern, lower):
            warnings.append("Unsupported first-person experience or result claim.")
            break

    for pattern in CUSTOMER_PATTERNS:
        if re.search(pattern, lower):
            warnings.append("Unsupported customer/client metric or experience claim.")
            break

    # Unsupported external attribution check
    # e.g., "As Andrej Karpathy pointed out..." when not in post or facts
    attributions = re.findall(
        r"\b(?:[aA]s|according\s+to)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:pointed\s+out|said|mentioned|argued|noted|claimed)\b",
        comment,
    )
    for name in attributions:
        if name.lower() not in allowed_text.lower():
            warnings.append(f"Unsupported external attribution to '{name}'.")

    # Detect explicit URLs/product-like tokens not present in the source/ledger.
    urls = re.findall(r"https?://[^\s)]+", comment)
    allowed_urls = set(re.findall(r"https?://[^\s)]+", allowed_text))
    unsupported_urls = [u for u in urls if u not in allowed_urls]
    if unsupported_urls:
        warnings.append("Generated URL not present in the post or facts ledger.")

    return warnings
