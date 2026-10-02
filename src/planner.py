"""Founder contribution planning.

Defines the contribution before choosing the words: identifies the post's core hook,
context type, plausible founder contribution, appropriate response shape, and
inspectable style evidence allowed to influence the draft.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import re

from src.models import CommentMode, Post


@dataclass
class ContributionPlan:
    post_hook: str
    context_type: str
    plausible_contribution: str
    response_shape: str
    allowed_style_evidence_ids: list[str] = field(default_factory=list)
    can_generate_alternative: bool = False
    alternative_shape: str = ""
    alternative_mode: CommentMode | None = None

    def to_dict(self) -> dict:
        return {
            "post_hook": self.post_hook,
            "context_type": self.context_type,
            "plausible_contribution": self.plausible_contribution,
            "response_shape": self.response_shape,
            "allowed_style_evidence_ids": self.allowed_style_evidence_ids,
            "can_generate_alternative": self.can_generate_alternative,
            "alternative_shape": self.alternative_shape,
            "alternative_mode": self.alternative_mode.value if self.alternative_mode else None,
        }


def extract_post_hook(text: str) -> str:
    """Identify the specific tension, milestone, or mechanism in the post."""
    lower = text.lower()

    if "latency" in lower and "failure" in lower:
        return "Latency reduction vs understanding failure modes after restart"
    if "parser" in lower or ("benchmark" in lower and ("chart" in lower or "table" in lower or "form" in lower)):
        return "Average benchmark gains vs failure variations across specific document formats"
    if "receipt" in lower or ("external system" in lower and "done" in lower):
        return "Agent completion claims lacking external verification receipts"
    if "correctness" in lower and "usefulness" in lower:
        return "Distinction between correctness benchmarks and real-world agent usefulness"
    if "hackathon" in lower or ("mvp" in lower and "deadline" in lower):
        return "Shipping a functional MVP under a tight hackathon deadline"
    if "college" in lower or "university" in lower:
        if "pay" in lower or "customer" in lower:
            return "Transition from student projects to first paying customers"
        return "Early student builder journey and startup rites of passage"
    if "onboarding" in lower or "dashboard" in lower:
        return "Improving SaaS onboarding usability and user experience"
    if "hiring" in lower:
        return "Startup growth and talent expansion"

    # Default to the first clear sentence or clause
    first_sentence = re.split(r"[.!?\n]", text)[0].strip()
    return first_sentence[:120] if first_sentence else "General discussion"


def classify_context_type(text: str) -> str:
    lower = text.lower()
    if any(k in lower for k in ("eval", "benchmark", "latency", "failure", "parser", "receipt", "recovery", "architecture")):
        return "technical_architecture"
    if any(k in lower for k in ("hackathon", "shipped", "mvp", "launch", "live", "won")):
        return "shipping_milestone"
    if any(k in lower for k in ("college", "student", "first time", "unreal", "mistake")):
        return "personal_milestone"
    if any(k in lower for k in ("😂", "joke", "hilarious", "wrong tool")):
        return "humor_anecdote"
    if "?" in text:
        return "question_inquiry"
    return "general_discussion"


def plan_contribution(
    post: Post,
    mode: CommentMode,
    founder: str,
    evidence_pack: dict | None = None,
) -> ContributionPlan:
    """
    Construct a grounded plan prior to word selection.
    """
    text = post.text
    hook = extract_post_hook(text)
    context_type = classify_context_type(text)
    founder_lower = founder.lower()

    # Determine allowed style evidence IDs
    allowed_ids = []
    if evidence_pack:
        for ex in evidence_pack.get("matched_observed_examples", []):
            if hasattr(ex, "id"):
                allowed_ids.append(ex.id)
        for ex in evidence_pack.get("style_only_observed_comments", []):
            if hasattr(ex, "id") and ex.id not in allowed_ids:
                allowed_ids.append(ex.id)

    # Plausible founder contribution
    if founder_lower == "fathin":
        if context_type == "technical_architecture":
            contribution = "Highlight operational boundaries, failure cases, or how recovery is verified."
            shape = "observation" if mode == CommentMode.ADD_INSIGHT else "question"
            can_alt = True
            alt_shape = "question" if shape == "observation" else "observation"
            alt_mode = CommentMode.THOUGHTFUL_QUESTION if shape == "observation" else CommentMode.ADD_INSIGHT
        else:
            contribution = "Provide concise, grounded technical feedback or ask a precise mechanism question."
            shape = "observation" if mode != CommentMode.THOUGHTFUL_QUESTION else "question"
            can_alt = False
            alt_shape = ""
            alt_mode = None
    elif founder_lower == "rico":
        if context_type == "shipping_milestone":
            contribution = "Celebrate shipping velocity and builder execution with punchy encouragement."
            shape = "reaction" if mode == CommentMode.QUICK_REACTION else "congratulations"
            can_alt = True
            alt_shape = "congratulations"
            alt_mode = CommentMode.QUICK_REACTION
        elif context_type in {"personal_milestone", "humor_anecdote"}:
            contribution = "Share a playful reaction acknowledging the early startup rite of passage."
            shape = "contextual_joke" if mode == CommentMode.HUMOROUS_PERSONAL else "reaction"
            can_alt = False
            alt_shape = ""
            alt_mode = None
        else:
            contribution = "Offer a brief, positive reaction without generic fluff."
            shape = "reaction"
            can_alt = False
            alt_shape = ""
            alt_mode = None
    else:
        contribution = "Add a relevant, concise contribution directly grounded in the post's core hook."
        shape = "observation" if mode == CommentMode.ADD_INSIGHT else "reaction"
        can_alt = False
        alt_shape = ""
        alt_mode = None

    return ContributionPlan(
        post_hook=hook,
        context_type=context_type,
        plausible_contribution=contribution,
        response_shape=shape,
        allowed_style_evidence_ids=allowed_ids,
        can_generate_alternative=can_alt,
        alternative_shape=alt_shape,
        alternative_mode=alt_mode,
    )
