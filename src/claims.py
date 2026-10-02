import re
from pathlib import Path
import json

from src.paths import FACTS_FILE

FIRST_PERSON_PATTERNS = (
    r"\bwe\s+(?:built|made|launched|shipped|tested|measured|reduced|increased)\b",
    r"\bmy\s+experience\b",
    r"\bin\s+my\s+experience\b",
    r"\bi\s+(?:built|made|launched|shipped|tested|measured|used|found)\b",
    r"\bat\s+our\s+(?:company|startup|team)\b",
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
    return set(re.findall(r"(?<![A-Za-z])\$?\d+(?:\.\d+)?%?", text))


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

    # Detect explicit URLs/product-like tokens not present in the source/ledger.
    urls = re.findall(r"https?://[^\s)]+", comment)
    allowed_urls = set(re.findall(r"https?://[^\s)]+", allowed_text))
    unsupported_urls = [u for u in urls if u not in allowed_urls]
    if unsupported_urls:
        warnings.append("Generated URL not present in the post or facts ledger.")

    return warnings
